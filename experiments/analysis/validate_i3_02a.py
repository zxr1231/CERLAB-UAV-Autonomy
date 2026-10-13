#!/usr/bin/env python3
"""Read-only integrity/accounting validation for the one registered I3-02A batch."""
import argparse, hashlib, json
from pathlib import Path
from i3_single_anchor import choose, route_effect, gates

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--write-validation', type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    protocol = json.loads((repo / 'experiments/i3/I3_02A_PROTOCOL.json').read_text())
    summary = json.loads((args.results / 'summary.json').read_text())
    batch = json.loads((args.results / 'batch_state.json').read_text())
    assert batch['status'] == 'COMPLETE' and summary['decision'] == batch['decision']
    assert summary['protocol_sha256'] == batch['protocol_sha256'] == sha(repo / 'experiments/i3/I3_02A_PROTOCOL.json')
    source = Path(protocol['source_root'])
    case_by_sequence = {c['sequence']: c for c in protocol['cases']}
    assert [s['sequence'] for s in batch['states']] == [c['sequence'] for c in protocol['cases']]
    checked = []
    for entry in batch['states']:
        seq = entry['sequence']; case = case_by_sequence[seq]
        snapshot = Path(case['directory'])
        assert case['snapshot_sha256'] == {p.name: sha(p) for p in snapshot.iterdir() if p.is_file()}
        assert case['source_files'] == {name: sha(source / name) for name in case['source_files']}
        pool = json.loads((args.results / ('s%03d_pool.json' % seq)).read_text())
        if seq == 13:
            assert entry['status'] == 'SKIPPED_NEGATIVE_CONTROL'
            assert pool['status'] == 'SKIP_B_NEGATIVE_CONTROL' and pool['camera_calls'] == 0 and not pool['records']
            continue
        state = json.loads((args.results / ('state_%06d.json' % seq)).read_text())
        saved = next(s for s in summary['states'] if s['sequence'] == seq)
        assert state == saved and entry['pool_size'] == state['pool_size']
        pre = args.results / ('s%03d_preoracle_selection.json' % seq)
        assert sha(pre) == entry['selection_checkpoint_sha256']
        frozen = json.loads(pre.read_text())
        assert choose(frozen['proxies'], frozen['reference_unique'], frozen['reference_time']) == frozen['selections_frozen_before_full_route_oracle'] == state['selections_frozen_before_oracle']
        assert pool['possible_pairs'] == len(pool['records']) and not pool['truncated']
        assert all(not pool['records'][i]['reasons'] for i in pool['pool'])
        reference = json.loads((args.results / ('s%03d_reference.json' % seq)).read_text())
        for row in state['evaluated']:
            full = json.loads((args.results / row['artifact']).read_text())
            effect = route_effect(reference['unique_addresses'], full['unique_addresses'],
                                  state['reference_time'], row['motion']['time'], row['proxy']['new_voxels'])
            assert effect == row['effect']
        checked.append(state)
    decision = gates(checked, protocol['strict_utility_tolerance'])
    assert all(summary[k] == v for k, v in decision.items())
    assert summary['total_possible_pairs'] == summary['total_enumerated_pairs'] == 3498
    assert summary['total_pool_routes'] == 14 and summary['all_reference_parity']
    validation = {'schema': 'i3-02a-read-only-validation-v1', 'status': 'PASS',
                  'states_checked': len(checked), 'negative_control_checked': True,
                  'selection_checkpoints_checked': len(checked), 'route_effects_checked': 14,
                  'frozen_input_hashes': 'UNCHANGED', 'decision_recomputed': decision['decision'],
                  'summary_sha256': sha(args.results / 'summary.json'),
                  'batch_state_sha256': sha(args.results / 'batch_state.json')}
    if args.write_validation:
        args.write_validation.write_text(json.dumps(validation, indent=2) + '\n')
    print(json.dumps(validation, indent=2))

if __name__ == '__main__':
    main()
