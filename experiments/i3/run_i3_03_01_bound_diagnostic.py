#!/usr/bin/env python3
"""Once-only D0; ranks without reading alternative full-gain labels.

No camera evaluator or geometry generator is imported. Historical labels are
opened only after every ranking and its SHA256 have been saved.
"""
import argparse
import hashlib
import json
import math
import platform
import struct
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TOL = 1e-9


def read(path):
    return json.loads(Path(path).read_text())


def write(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def require(test, message):
    if not test:
        raise ValueError(message)


def check_hashes(reg):
    checked = {}
    for c in reg['cases']:
        for name, digest in c['snapshot_sha256'].items():
            checked[str(Path(c['snapshot_directory']) / name)] = digest
        for name, digest in c['source_sha256'].items():
            checked[str(Path(reg['source_root']) / name)] = digest
        checked.update(c['diagnostic_artifacts'])
    for path, digest in checked.items():
        require(sha(path) == digest, 'Frozen input hash mismatch: ' + path)
    return checked


def close_pose(a, b):
    return max(abs(x-y) for x, y in zip(a['position'], b['position'])) <= TOL and abs(a['yaw']-b['yaw']) <= TOL


def unchanged(samples, left, right):
    def at(p, q):
        return max(abs(x-y) for x, y in zip(p['position'], q)) <= TOL
    first = next(i for i, p in enumerate(samples) if at(p, left))
    last = max(i for i, p in enumerate(samples) if at(p, right))
    require(first <= last, 'Changed-window boundary order')
    return samples[:first], samples[last+1:]


def prepare(reg, c):
    source = read(c['request_file'])
    ctx = c['context']
    require(fingerprint(ctx) == c['context_fingerprint'], 'Context fingerprint')
    require(fingerprint(ctx['camera']) == c['camera_fingerprint'], 'Camera fingerprint')
    for key in ('accepted', 'map_version', 'camera', 'start_yaw', 'terminal_yaw', 'goal'):
        require(source[key] == ctx[key], 'Context disagreement: ' + key)
    if not ctx['accepted']:
        require(not c['routes'], 'Negative control must have no routes')
        return {'accepted': False}, []
    require(source['nodes'][0] == ctx['start_position'], 'Start position changed')
    planner = read(Path(c['snapshot_directory']) / 'planner.json')
    require(planner['motion_model'] == ctx['motion_model'], 'Motion model changed')
    require(planner['planning_region'] == ctx['planning_region'], 'Planning region changed')
    root = Path(reg['old_scored_corpus'])
    pool = read(root / ('s%03d_pool.json' % c['sequence']))
    reference = read(root / ('s%03d_reference.json' % c['sequence']))
    require(reference['valid'] and reference['map_version'] == ctx['map_version'], 'Reference invalid')
    require(reference['unique_addresses'] == sorted(set(reference['unique_addresses'])), 'Reference set invalid')
    require(len(reference['unique_addresses']) == reference['unique_gain'], 'Reference count')
    require(pool['pool'] == c['route_record_ids'], 'Candidate pool changed')
    records = {r['record_id']: r for r in pool['records']}
    request = {'accepted': True, 'map_version': ctx['map_version'], 'camera': ctx['camera'],
               'reference_addresses': reference['unique_addresses'], 'routes': []}
    checks = []
    for r in c['routes']:
        saved = records[r['record_id']]
        e = r['reference_segment']
        ref = source['reference']
        require(r['path'] == ref[:e+1] + [r['anchor_id']] + ref[e+1:], 'Not a saved single insertion')
        require(saved['path'] == r['path'] and saved['edge'] == e and saved['anchor'] == r['anchor_id'], 'Record mismatch')
        require(not saved['reasons'] and saved['motion'] == r['motion'], 'Saved safety/motion contract')
        require(math.isfinite(r['motion']['time']) and r['motion']['time'] > 1e-6, 'Invalid time')
        require(math.isfinite(r['motion']['length']) and r['motion']['length'] > 0, 'Invalid length')
        left, anchor, right = (source['nodes'][j] for j in (ref[e], r['anchor_id'], ref[e+1]))
        a, b = unchanged(pool['reference_samples'], left, right), unchanged(saved['samples'], left, right)
        require(all(len(x) == len(y) and all(close_pose(p, q) for p, q in zip(x, y)) for x, y in zip(a, b)), 'Unchanged prefix/suffix sample contract')
        checks.append({'record_id': r['record_id'], 'unchanged_prefix_samples': len(a[0]), 'unchanged_suffix_samples': len(a[1]), 'passed': True})
        request['routes'].append({k: r[k] for k in ('record_id', 'reference_segment', 'anchor_id', 'motion')})
        request['routes'][-1]['segments'] = [[left, anchor], [anchor, right]]
    return request, checks


def grid(path):
    data = Path(path).read_bytes()
    require(data[:7] == b'CR1MAP1', 'Invalid map header')
    dims = struct.unpack_from('<3i', data, 76)
    count = struct.unpack_from('<Q', data, 104)[0]
    require(math.prod(dims) == count and len(data) == 112+2*count, 'Map layout mismatch')
    return dims, memoryview(data)[112:]


def xyz(address, dims):
    return (address // (dims[1]*dims[2]), (address // dims[2]) % dims[1], address % dims[2])


def inside(box, p):
    return all(l <= x <= h for l, x, h in zip(box['lo'], p, box['hi']))


def brute_counts(dims, states, roi, boxes, reference):
    # Independent scan of voxel states, no prefix-table implementation reused.
    lo = [max(roi['lo'][k], min(b['lo'][k] for b in boxes)) for k in range(3)]
    hi = [min(roi['hi'][k], max(b['hi'][k] for b in boxes)) for k in range(3)]
    n = q = 0
    for x in range(lo[0], hi[0]+1):
        for y in range(lo[1], hi[1]+1):
            for z in range(lo[2], hi[2]+1):
                address = (x*dims[1]+y)*dims[2]+z
                if states[2*address] == 255 and any(inside(b, (x,y,z)) for b in boxes):
                    n += 1
                    q += address not in reference
    return n, q


def curve(order, utility, reference, k):
    visited = order[:k]
    effective = max([reference] + [utility[r] for r in visited])
    best = max([reference] + list(utility.values()))
    return {'K': k, 'visited': visited, 'raw_candidate_utilities': [utility[r] for r in visited],
            'effective_utility': effective, 'relative_utility': None if reference == 0 else effective/reference-1,
            'best_regret': best-effective}


def first_positive(order, utility, reference):
    return next((i+1 for i, r in enumerate(order) if utility[r] > reference + TOL), len(order)+1)


def quality(cases):
    valid = [c for c in cases if c['accepted']]
    means = {}
    for name in ('motion', 'N', 'Q'):
        values = [c['curves'][name]['K1']['relative_utility'] for c in valid]
        means[name] = None if any(v is None for v in values) else sum(values)/len(valid)
    wins = {name: sum(c['curves']['Q']['K1']['effective_utility'] > c['curves'][name]['K1']['effective_utility']+TOL for c in valid) for name in ('motion', 'N')}
    positives = [c for c in valid if c['positive_records']]
    no_later = all(c['first_positive']['Q'] <= c['first_positive']['motion'] for c in positives)
    evaluable = all(v is not None for v in means.values())
    mean_gate = evaluable and all(means['Q']+TOL >= means[n] for n in ('motion','N'))
    return {'mean_relative_utility_K1': means, 'strict_better_states_K1': wins,
            'known_positive_states': [c['sequence'] for c in positives], 'no_later_than_motion': no_later,
            'means_not_lower': mean_gate, 'evaluable': evaluable,
            'passed': evaluable and all(v >= 1 for v in wins.values()) and no_later and mean_gate}


def outcome(engineering, cost, metrics):
    if not engineering:
        return 'BOUND_ENGINEERING_FAIL'
    if not cost:
        return 'BOUND_PREPARATION_FAIL'
    if not metrics['evaluable']:
        return 'INCONCLUSIVE_QUALITY_METRICS'
    return 'DIAGNOSTIC_SIGNAL_ONLY' if metrics['passed'] else 'NO_USEFUL_CONDITIONING_SIGNAL'


def run(args):
    reg = read(HERE / 'I3_G1_D0_INPUTS.json')
    protocol = read(HERE / 'I3_G1_D0_PROTOCOL.json')
    require(protocol['attempt_batches_max'] == 1 and protocol['primary_K'] == 1, 'Protocol changed')
    checked = check_hashes(reg)
    prepared = [(c, *prepare(reg, c)) for c in reg['cases']]
    args.output.mkdir(parents=True, exist_ok=False)  # Never overwrite/re-measure a batch.
    identity = {'protocol': protocol['protocol_id'], 'task': 'I3-03-01', 'parent_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=REPO, text=True).strip(),
                'global_planner_commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=REPO/'global_planner', text=True).strip(),
                'runner': str(args.runner), 'runner_sha256': sha(args.runner),
                'protocol_sha256': sha(HERE/'I3_G1_D0_PROTOCOL.json'), 'inputs_sha256': sha(HERE/'I3_G1_D0_INPUTS.json'),
                'source_file_sha256': sha(__file__), 'frozen_source_files': checked,
                'new_camera_queries': 0, 'new_routes_generated': 0, 'new_seeds': 0, 'attempt': 1}
    identity['started_utc'] = datetime.now(timezone.utc).isoformat()
    identity['platform'] = platform.platform()
    identity['cpu_model'] = next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), 'unknown')
    identity['process_affinity'] = subprocess.check_output(['taskset','-pc',str(__import__('os').getpid())],text=True).strip()
    identity['resource_measurement'] = 'sequential processes; one measured preparation per N/Q, fixed N then Q, no explicit warmup; /usr/bin/time maximum RSS'
    write(args.output/'identity.json', identity)
    rankings = {}
    for c, request, checks in prepared:
        s = c['sequence']
        request_path = args.output/('request_%06d.json' % s)
        write(request_path, request)
        resource_path = args.output/('resource_%06d.json' % s)
        start = time.perf_counter()
        process = subprocess.run(['/usr/bin/time', '-f', '{"process_peak_rss_kib":%M}', '-o', str(resource_path), str(args.runner), c['snapshot_directory'], str(request_path)], text=True, capture_output=True)
        (args.output/('stderr_%06d.log'%s)).write_text(process.stderr)
        (args.output/('stdout_%06d.json'%s)).write_text(process.stdout)
        require(process.returncode == 0, 'Runner failure state%d; raw logs preserved'%s)
        r = json.loads(process.stdout)
        r.update(read(resource_path))
        r['process_wall_ms_including_io'] = 1000*(time.perf_counter()-start)
        r['unchanged_window_checks'] = checks
        rankings[s] = r
        write(args.output/('ranking_%06d.json'%s), r)
        write(args.output/'checkpoint.json', {'stage':'RANKING', 'completed_states':list(rankings), 'alternative_labels_opened':False})
    seal = {'ranking_sha256': {str(s):sha(args.output/('ranking_%06d.json'%s)) for s in rankings}, 'alternative_labels_opened': False}
    write(args.output/'rankings_frozen.json', seal)
    # This line is the first read of the historical alternative FULL gains.
    results = []
    for c, request, checks in prepared:
        s = c['sequence']; r = rankings[s]
        if not c['context']['accepted']:
            require(r['status']=='SKIP_NEGATIVE_CONTROL' and r['tables_built']==0, 'Negative work')
            results.append({'sequence':s,'accepted':False,'status':r['status'],'process_peak_rss_kib':r['process_peak_rss_kib']})
            continue
        require(r['camera_queries']==0 and not r['camera_model_constructed'] and r['new_routes_generated']==0,'Isolation violated')
        reference = read(Path(reg['old_scored_corpus'])/('s%03d_reference.json'%s))
        refset = set(reference['unique_addresses']); dims, states = grid(Path(c['snapshot_directory'])/'map.bin')
        labels = {}; rows = []; start = time.perf_counter()
        nrows = {x['record_id']:x for x in r['N']['scores']}; qrows = {x['record_id']:x for x in r['Q']['scores']}
        bounds = {x['record_id']:x['boxes'] for x in r['rows']}
        for route in c['routes']:
            rid = route['record_id']; label = read(route['full_output'])
            require(label['valid'] and label['map_version']==c['context']['map_version'], 'Invalid full label')
            observed = set(label['unique_addresses']); require(len(observed)==label['unique_gain'],'Label count')
            require(all(0 <= a < math.prod(dims) and states[2*a]==255 and inside(r['roi'],xyz(a,dims)) for a in observed),'Label outside Unknown region')
            novel = observed-refset
            require(all(any(inside(b,xyz(a,dims)) for b in bounds[rid]) for a in novel),'Bound missed a novel voxel')
            n,q = brute_counts(dims,states,r['roi'],bounds[rid],refset)
            require(n==nrows[rid]['count'] and q==qrows[rid]['count'],'Prefix count differs from independent scan')
            for name,count in [('N',n),('Q',q)]:
                expected = (len(refset)+count)/route['motion']['time']
                require(abs(r[name]['scores'][r[name]['order'].index(rid)]['upper_utility']-expected)<=TOL,'Upper utility arithmetic')
            utility = label['unique_gain']/route['motion']['time']
            require(abs(utility-label['utility'])<=TOL and utility<=qrows[rid]['upper_utility']+TOL,'Upper utility invalid')
            require(len(novel)<=q,'New gain bound invalid')
            labels[rid]=utility
            rows.append({'record_id':rid,'unique_gain':label['unique_gain'],'new_voxels':len(novel),'actual_model_utility':utility,'N_count':n,'Q_count':q,'Q_upper_utility':qrows[rid]['upper_utility'],'containment_passed':True})
        orders = {'motion':r['motion_order'],'N':r['N']['order'],'Q':r['Q']['order']}
        for order in orders.values():
            require(sorted(order)==sorted(c['route_record_ids']),'Candidate permutation mismatch')
        stable = lambda x:(x['motion']['time'],x['motion']['length'],x['anchor_id'],x['reference_segment'],x['record_id'])
        require(orders['motion']==[x['record_id'] for x in sorted(c['routes'],key=stable)],'Motion tie rule')
        for name in ('N','Q'):
            scores = {x['record_id']:x for x in r[name]['scores']}
            require(orders[name]==[x['record_id'] for x in sorted(c['routes'],key=lambda x:(-scores[x['record_id']]['upper_utility'],)+stable(x))],'Bound tie rule')
        if c['routes']:
            require(r['N']['mask_total']-r['Q']['mask_total']==len(refset),'N/Q mask total inconsistency')
        else:
            require(all(r[n]['table_storage_bytes']==r[n]['total_preparation_ms']==0 for n in ('N','Q')),'Empty-pool index work')
        curves = {name:{'K1':curve(order,labels,reference['utility'],1), 'K2':curve(order,labels,reference['utility'],2), 'Kmax':curve(order,labels,reference['utility'],min(5,len(order)))} for name,order in orders.items()}
        costs = {name:{k:r[name][k] for k in ('index_build_ms','union_queries_ms','sort_ms','total_preparation_ms','tracked_scratch_peak_bytes','table_storage_bytes')} for name in ('N','Q')}
        cost_passed = all(v['total_preparation_ms']<=50 and v['tracked_scratch_peak_bytes']<=268435456 for v in costs.values())
        results.append({'sequence':s,'accepted':True,'reference_utility':reference['utility'],'reference_unique_gain':len(refset),'candidate_count':len(labels),'rows':rows,'orders':orders,'curves':curves,
                        'positive_records':[i for i,u in labels.items() if u>reference['utility']+TOL],
                        'first_positive':{n:first_positive(o,labels,reference['utility']) for n,o in orders.items()},
                        'costs':costs,'cost_passed':cost_passed,'process_peak_rss_kib':r['process_peak_rss_kib'], 'input_io_and_geometry_ms':r['input_io_and_geometry_ms'],
                        'independent_count_and_label_validation_ms':1000*(time.perf_counter()-start),
                        'new_camera_queries':0,'new_routes_generated':0,'containment_passed':True})
    metrics=quality(results); cost=all(c.get('cost_passed',True) for c in results)
    require(check_hashes(reg)==checked,'Frozen inputs changed')
    require(all(sha(args.output/('ranking_%06d.json'%int(s)))==h for s,h in seal['ranking_sha256'].items()),'Ranking changed after labels')
    report={'task':'I3-03-01','outcome':outcome(True,cost,metrics),'engineering_passed':True,'preparation_cost_passed':cost,'quality':metrics,'cases':results,
            'new_camera_queries':0,'new_routes_generated':0,'whole_500ms_admission':'not tested','model_allocated_capacity':'not_measured_not_constructed',
            'limitations':['retrospective 14-route development corpus, not held-out','optimistic bound ignores FoV/yaw/occlusion','saved reference camera cost not free online','one measured batch, no timing reruns','does not validate actual observation or exploration improvement']}
    write(args.output/'results.json',report)
    write(args.output/'checkpoint.json',{'stage':'COMPLETE','completed_states':list(rankings),'report_sha256':sha(args.output/'results.json'),'outcome':report['outcome']})
    print(json.dumps({k:report[k] for k in ('outcome','engineering_passed','preparation_cost_passed','quality')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--runner',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; neither repeat the batch nor overwrite prior results')
    try:
        run(args)
    except Exception as e:
        if args.output.exists():
            write(args.output/'failure.json',{'outcome':'BOUND_ENGINEERING_FAIL','error':str(e),'no_automatic_retry':True})
        raise
