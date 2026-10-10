#!/usr/bin/env python3
"""Read-only audit of frozen I2 first attempts; outputs go to a separate directory."""
import argparse
import collections
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def span(items, key):
    values = [float(item[key]) for item in items if item.get(key) not in (None, '')]
    return max(values)-min(values) if values else None


def audit(task):
    assert len(task['attempts']) == 1, 'first attempts only'
    directory = Path(task['attempts'][0]['result_dir'])
    inputs = ['planning.csv', 'trajectory.csv', 'coverage.csv', 'metrics.csv', 'exploration.log',
              'run.json', 'runner_result.json', 'events.jsonl']
    if (directory/'route_controls.jsonl').exists():
        inputs.append('route_controls.jsonl')
    hashes = {name: digest(directory/name) for name in inputs}
    planning = rows(directory/'planning.csv')
    local = [json.loads(r['raw_json']) for r in planning if r['kind'] == 'local']
    trajectory = rows(directory/'trajectory.csv')
    coverage = rows(directory/'coverage.csv')
    metrics = rows(directory/'metrics.csv')
    suffix = []
    for record in reversed(local):
        if record['success']:
            break
        suffix.append(record)
    suffix.reverse()
    end = float(trajectory[-1]['sim_time'])
    start = suffix[0]['sim_time'] if suffix else end
    poses = [r for r in trajectory if float(r['sim_time']) >= start]
    last_minute = [r for r in trajectory if float(r['sim_time']) >= end-60]
    targets = collections.Counter(tuple(round(v, 2) for v in r['input_path_points'][-1])
                                  for r in suffix if r.get('input_path_points'))
    lengths = [r['input_path_length'] for r in suffix if 'input_path_length' in r]
    bspline_times = [r['bspline_ms'] for r in suffix if 'bspline_ms' in r]
    # Coverage rows are deltas, so a stall can have NO new rows. Carry the last counter forward.
    before = [r for r in coverage if float(r['sim_time']) <= start]
    through = [r for r in coverage if float(r['sim_time']) <= end]
    observation_advance = (int(through[-1]['accessible_observed'])-int(before[-1]['accessible_observed'])) if before and through else None
    metrics_suffix = [r for r in metrics if float(r['sim_time']) >= start]
    logs = (directory/'exploration.log').read_text(errors='replace')
    messages = {key: logs.count(text) for key, text in {
        'optimizer_failure': 'Fail because of optimizer not finding a solution.',
        'optimizer_timeout': 'Optimization timeout.',
        'astar_failure': 'Fail because of A* failure.',
        'process_died_messages': 'process has died',
    }.items()}
    comparisons = []
    ready = extra = 0
    routefile = directory/'route_controls.jsonl'
    if routefile.exists():
        with routefile.open() as stream:
            for line in stream:
                log = json.loads(line)['route_controls']
                if log.get('status') == 'ready' and not log.get('fallback'):
                    ready += 1
                    extra += log['selected_count'] > sum(g.get('status') == 'reachable' for g in log['goal_set'])
                comparisons.extend(c for c in log.get('astar_comparisons', [])
                                   if c.get('found') and c.get('snapshot_matches_comparison_map'))
    excess = [c['excess_length'] for c in comparisons]
    total_travel = (float(poses[-1]['mission_distance'])-float(poses[0]['mission_distance'])) if len(poses) > 1 else None
    result = {
        'task_id': task['task_id'], 'status': task['status'], 'result_directory': str(directory),
        'local_calls': len(local), 'local_failures': sum(not r['success'] for r in local),
        'terminal_failure_suffix': {
            'count': len(suffix), 'first_sim': start if suffix else None,
            'last_local_sim': suffix[-1]['sim_time'] if suffix else None,
            'elapsed_until_last_odom': end-start if suffix else 0,
            'persistent': len(suffix) >= 5 and end-start >= 30,
            'global_sequence_count': len({r.get('global_sequence') for r in suffix}),
            'update_success_count': sum(r.get('update_success') is True for r in suffix),
            'dynamic_obstacle_count_max': max((r.get('dynamic_obstacles', 0) for r in suffix), default=None),
            'depth_sequence_advance': span(suffix, 'depth_sequence'),
            'map_version_advance': span(suffix, 'map_version'),
            'travel_m': total_travel,
            'input_length_min_m': min(lengths, default=None),
            'input_length_max_m': max(lengths, default=None),
            'bspline_ms_median': statistics.median(bspline_times) if bspline_times else None,
            'dominant_input_target_cm': targets.most_common(1),
            'dominant_target_fraction': targets.most_common(1)[0][1]/len(suffix) if targets else None,
            'accessible_observation_counter_advance': observation_advance,
            'map_message_count_advance': span(metrics_suffix, 'map_message_count'),
        },
        'last_60s_position_box_diagonal_m': math.sqrt(sum((span(last_minute, a) or 0)**2 for a in ['x','y','z'])),
        'whole_run_log_message_counts': messages,
        'ready_route_plans': ready, 'plans_with_extra_routes': extra,
        'same_snapshot_astar_comparisons': {
            'count': len(excess), 'positive_excess_over_1um_count': sum(x > 1e-6 for x in excess),
            'mean_excess_m': statistics.mean(excess) if excess else None,
            'max_excess_m': max(excess, default=None),
        },
        'input_sha256': hashes,
    }
    assert hashes == {name: digest(directory/name) for name in inputs}, 'source changed during audit'
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-root', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    statepath = args.batch_root/'batch_state.json'
    state = json.loads(statepath.read_text())
    records = []
    for task in state['tasks']:
        record = audit(task)
        records.append(record)
        print(task['task_id'], 'terminal failures', record['terminal_failure_suffix']['count'], flush=True)
    report = {
        'schema': 'i2-06-readonly-execution-audit-v1',
        'batch_state_sha256': digest(statepath), 'frozen_source': state['source_commit'],
        'trial_count': len(records), 'trials': records,
        'limitations': [
            'Terminal failure suffix = all local calls after last successful local call; persistent iff >=5 calls and >=30s until last odom.',
            'Message counts cover whole run; messages lack sequence IDs and cannot be assigned to every failed call.',
            'Depth/map counters advancing prove callbacks, not useful new information or map correctness.',
            'No frozen failure-time occupancy/control points or LBFGS status; exact collision/solver branch cannot be reconstructed.',
            'No counterfactual treatment: neither missing feedback nor A* excess is proven to cause aggregate T95 changes.',
        ],
    }
    args.output_directory.mkdir(parents=True, exist_ok=True)
    (args.output_directory/'execution_audit.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
