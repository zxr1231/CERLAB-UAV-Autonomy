#!/usr/bin/env python3
"""Execute the single registered I3-02A batch without changing frozen inputs."""
import argparse, hashlib, json, math, subprocess
from collections import Counter
from pathlib import Path
from i3_single_anchor import choose, route_effect, gates

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run_json(command, output, stderr):
    result = subprocess.run(command, text=True, capture_output=True, timeout=180)
    stderr.write_text(result.stderr)
    result.check_returncode()
    data = json.loads(result.stdout)
    output.write_text(json.dumps(data, indent=2) + '\n')
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parents[2]
    protocol_file = repo / 'experiments/i3/I3_02A_PROTOCOL.json'
    protocol = json.loads(protocol_file.read_text())
    source = Path(protocol['source_root'])
    previous = Path('/home/zxr2/cerlab_benchmark_ws/results/EXP-I3-01C-OBSERVATION-LOSS-V1')
    runner = Path('/home/zxr2/cerlab_benchmark_ws/devel/lib/global_planner/single_anchor_fixture_runner')
    batch = {
        'schema': 'i3-02a-batch-state-v1', 'status': 'RUNNING',
        'protocol_sha256': sha(protocol_file),
        'source_parent_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
        'states': []
    }
    def save():
        (out / 'batch_state.json').write_text(json.dumps(batch, indent=2) + '\n')
    save()
    states = []
    for case in protocol['cases']:
        seq = case['sequence']
        snapshot = Path(case['directory'])
        actual_snapshot = {p.name: sha(p) for p in snapshot.iterdir() if p.is_file()}
        assert case['snapshot_sha256'] == actual_snapshot
        assert case['source_files'] == {name: sha(source / name) for name in case['source_files']}
        entry = {'sequence': seq, 'status': 'RUNNING'}
        batch['states'].append(entry); save()
        request = source / ('request_%06d.json' % seq)
        pool = run_json([str(runner), 'pool', str(snapshot), str(request)],
                        out / ('s%03d_pool.json' % seq), out / ('s%03d_pool.stderr' % seq))
        if case['status'] == 'SKIP_B_NEGATIVE_CONTROL':
            assert pool['status'] == 'SKIP_B_NEGATIVE_CONTROL' and pool['camera_calls'] == 0 and not pool['records']
            entry['status'] = 'SKIPPED_NEGATIVE_CONTROL'; save(); continue
        assert pool['status'] == 'CONTEXT_VALID' and pool['camera_calls'] == 0
        original = json.loads(request.read_text())
        def gain(label, samples, estimated_time):
            req = {'accepted': True, 'map_version': original['map_version'], 'camera': original['camera'],
                   'samples': samples, 'estimated_time': estimated_time}
            req_file = out / (label + '.input.json'); req_file.write_text(json.dumps(req) + '\n')
            result = run_json([str(runner), 'gain', str(snapshot), str(req_file)],
                              out / (label + '.json'), out / (label + '.stderr'))
            assert result['valid'] and result['map_version'] == original['map_version']
            assert len(result['unique_addresses']) == len(set(result['unique_addresses'])) == result['unique_gain']
            assert sum(result['marginal_gains']) == result['unique_gain'] <= result['raw_gain']
            return result
        reference = gain('s%03d_reference' % seq, pool['reference_samples'], pool['reference_motion']['time'])
        old = json.loads((previous / ('s%03d_p00_full_final.json' % seq)).read_text())
        parity_keys = ['raw_gain', 'unique_gain', 'unique_addresses', 'marginal_gains']
        assert all(reference[k] == old[k] for k in parity_keys)
        ref_set = set(reference['unique_addresses']); ref_u = reference['unique_gain'] / pool['reference_motion']['time']
        proxies = []
        for record_id in pool['pool']:
            record = pool['records'][record_id]
            anchor = original['nodes'][record['anchor']]
            proxy = gain('s%03d_r%05d_proxy' % (seq, record_id),
                         [{'position': anchor, 'yaw': record['anchor_yaw']}], 1.0)
            proxies.append({'record_id': record_id, 'anchor': record['anchor'], 'edge': record['edge'],
                            'time': record['motion']['time'], 'length': record['motion']['length'],
                            'new_voxels': len(set(proxy['unique_addresses']) - ref_set),
                            'visible_voxels': proxy['unique_gain'], 'artifact': 's%03d_r%05d_proxy.json' % (seq, record_id)})
        selections = choose(proxies, reference['unique_gain'], pool['reference_motion']['time'])
        preoracle = {'sequence': seq, 'reference_unique': reference['unique_gain'],
                     'reference_time': pool['reference_motion']['time'], 'reference_utility': ref_u,
                     'proxies': proxies, 'selections_frozen_before_full_route_oracle': selections}
        preoracle_file = out / ('s%03d_preoracle_selection.json' % seq)
        preoracle_file.write_text(json.dumps(preoracle, indent=2) + '\n')
        entry['selection_checkpoint_sha256'] = sha(preoracle_file); entry['status'] = 'SELECTION_FROZEN'; save()
        evaluated = []
        by_id = {}
        proxy_by_id = {p['record_id']: p for p in proxies}
        for record_id in pool['pool']:
            record = pool['records'][record_id]
            full = gain('s%03d_r%05d_full' % (seq, record_id), record['samples'], record['motion']['time'])
            effect = route_effect(reference['unique_addresses'], full['unique_addresses'],
                                  pool['reference_motion']['time'], record['motion']['time'],
                                  proxy_by_id[record_id]['new_voxels'])
            row = {'record_id': record_id, 'anchor': record['anchor'], 'edge': record['edge'],
                   'path': record['path'], 'motion': record['motion'], 'proxy': proxy_by_id[record_id],
                   'unique_gain': full['unique_gain'], 'raw_gain': full['raw_gain'],
                   'utility': full['unique_gain'] / record['motion']['time'],
                   'effect': effect, 'artifact': 's%03d_r%05d_full.json' % (seq, record_id)}
            evaluated.append(row); by_id[record_id] = row
        selected = {}
        for mode, record_id in selections.items():
            if record_id is None:
                selected[mode] = {'record_id': None, 'final_choice': 'reference',
                                  'effective_utility': ref_u, 'effective_relative_rate': 0. if ref_u else None,
                                  'raw_relative_rate': None}
            else:
                e = by_id[record_id]['effect']
                selected[mode] = {'record_id': record_id, **e}
        state = {'sequence': seq, 'status': 'COMPLETE', 'reference_unique': reference['unique_gain'],
                 'reference_raw': reference['raw_gain'], 'reference_time': pool['reference_motion']['time'],
                 'reference_utility': ref_u, 'possible_pairs': pool['possible_pairs'],
                 'enumerated_pairs': len(pool['records']), 'truncated': pool['truncated'],
                 'qualified_before_stratification': len(pool['ordered']), 'pool_size': len(pool['pool']),
                 'pool_record_ids': pool['pool'], 'rejection_counts': dict(Counter(x for r in pool['records'] for x in r['reasons'])),
                 'proxies': proxies, 'selections_frozen_before_oracle': selections,
                 'evaluated': evaluated, 'selectors': selected,
                 'reference_parity_with_i3_01c': True,
                 'generation_component_ms': pool['generation_component_ms']}
        (out / ('state_%06d.json' % seq)).write_text(json.dumps(state, indent=2) + '\n')
        states.append(state); entry['status'] = 'COMPLETE'; entry['pool_size'] = len(pool['pool']); save()
        assert case['snapshot_sha256'] == {p.name: sha(p) for p in snapshot.iterdir() if p.is_file()}
        assert case['source_files'] == {name: sha(source / name) for name in case['source_files']}
    decision = gates(states, protocol['strict_utility_tolerance'])
    summary = {'schema': 'i3-02a-single-anchor-summary-v1', 'protocol_sha256': sha(protocol_file),
               'states': states, 'negative_control': 13, **decision,
               'total_possible_pairs': sum(s['possible_pairs'] for s in states),
               'total_enumerated_pairs': sum(s['enumerated_pairs'] for s in states),
               'total_pool_routes': sum(s['pool_size'] for s in states),
               'all_reference_parity': all(s['reference_parity_with_i3_01c'] for s in states),
               'no_new_simulation': True, 'online_planner_modified': False,
               'whole_stage_500ms_admitted': False,
               'limitations': ['five correlated development snapshots in one held-out static run',
                  'prospective frozen-map visibility, not executed B-spline or actual observation',
                  'single existing-PRM anchor and direct safe segments only',
                  'component timings are not whole-stage budget evidence']}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    batch['status'] = 'COMPLETE'; batch['decision'] = decision['decision']; save()
    print(json.dumps({k: v for k, v in summary.items() if k != 'states'}, indent=2))

if __name__ == '__main__':
    main()
