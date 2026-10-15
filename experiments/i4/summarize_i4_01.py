#!/usr/bin/env python3
import hashlib,json,statistics,sys,math
from pathlib import Path
def percentile(values,q):
 a=sorted(values);f=(len(a)-1)*q;lo=math.floor(f);hi=math.ceil(f);return a[lo]+(a[hi]-a[lo])*(f-lo)
def summarize(root):
 rows={};checks=0
 for p in root.glob('r*_s*_m*.jsonl'):
  repeat,segment,mode=map(int,[s[1:] for s in p.stem.split('_')])
  for line in p.read_text().splitlines():
   r=json.loads(line);key=(repeat,mode,r['sequence']);assert key not in rows;rows[key]=r
 assert len(rows)==456,len(rows)
 for repeat in range(3):
  for seq in range(1,39):
   reference=rows[repeat,0,seq]
   for mode in range(1,4):
    r=rows[repeat,mode,seq];assert reference['routes']==r['routes'],('gain mismatch',repeat,seq,mode)
    assert reference['winner']==r['winner'],('winner mismatch',repeat,seq,mode)
    assert r['charged_cache_bytes']<=256*1024*1024
    assert not r['allocation_limit_rejected'];checks+=len(r['routes'])
 timings={m:[statistics.median(rows[r,m,s]['total_ms'] for r in range(3)) for s in range(1,39)] for m in range(4)}
 modes=[]
 for m in range(4):
  rs=[v for (r,mode,s),v in rows.items() if mode==m];cold=[v['total_ms'] for (r,mode,s),v in rows.items() if mode==m and s in (1,14,27)]
  modes.append({'mode':m,'median_ms':statistics.median(timings[m]),'p95_ms':percentile(timings[m],.95),'maximum_ms':max(timings[m]),'total_median_event_ms':sum(timings[m]),'cold_median_ms':statistics.median(cold),'max_cache_mib':max(x['charged_cache_bytes'] for x in rs)/2**20,'tracked_working_peak_mib':max(x['tracked_working_peak_bytes'] for x in rs)/2**20,'process_peak_rss_mib':max(x['process_peak_rss_kib'] for x in rs)/1024,'recomputed':sum(x['recomputed_poses'] for x in rs),'reused':sum(x['reused_poses'] for x in rs),'membership_updates':sum(x['membership_updates'] for x in rs),'propagated_memberships':sum(x['propagated_memberships'] for x in rs),'evictions':sum(x['evictions'] for x in rs),'segments':[{'segment':i,'median_total_ms':statistics.median(sum(rows[r,m,s]['total_ms'] for s in range(lo,hi+1)) for r in range(3))} for i,(lo,hi) in enumerate([(1,13),(14,26),(27,38)])]})
 reductions={str(m):1-modes[3]['median_ms']/modes[m]['median_ms'] for m in range(3)}
 passed=reductions['0']>=.30 and reductions['2']>=.15
 out={'task':'I4-01','status':'PROTOTYPE_COST_GATE_PASS' if passed else 'PROTOTYPE_COST_GATE_FAIL','correctness':True,'route_comparisons_to_oracle':checks,'events':38,'independent_runs':1,'modes':modes,'median_reduction_dependency_vs':reductions,'all_event_medians_ms':timings,'formal_exploration_metrics_measured':False,'limitations':['one historical static-scene run and sparse maps','three correlated temporal segments, three computation repeats','parallel cores share memory/cache/turbo','charged retained cache is not total process memory','no online default or frozen prior experiment changed']}
 (root/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
 return out
if __name__=='__main__':summarize(Path(sys.argv[1]))
