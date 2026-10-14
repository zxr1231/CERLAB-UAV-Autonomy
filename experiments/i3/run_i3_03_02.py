#!/usr/bin/env python3
"""Freeze all historical global events; four pinned workers, no gain-based selection."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import threading
import time

REPO=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RUN=Path('/home/zxr2/cerlab_benchmark_ws/results/EXP-I2-06-HELD-OUT-SEED4-V1/environment_seed_004/planner_seed_004/20261012T140548')
sys.path.insert(0,str(REPO/'exploration_benchmark/src'))
from exploration_benchmark.sensor_shadow import CameraShadowConfig


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def require(ok,msg):
    if not ok:raise ValueError(msg)


def register(directory):
    directory.mkdir(exist_ok=False,parents=True)
    events=[json.loads(line) for line in (RUN/'route_controls.jsonl').read_text().splitlines()]
    require([e['global_sequence'] for e in events]==list(range(1,39)),'Expected complete38event source')
    mapping=REPO/'autonomous_flight/cfg/dynamic_exploration/mapping_param.yaml'
    require(sha(mapping)=='a0efc81649cce8f185ccca775a4820e1d4b23107c30d50868669f2eab215cd9a','Mapping config changed')
    cases=[]
    for item in events:
        seq=item['global_sequence'];e=item['route_controls'];folder=RUN/'snapshots'/('snapshot_%06d'%seq)
        planner=read(folder/'planner.json');manifest=read(folder/'manifest.json')
        require(manifest['capture_kind']=='global_plan','Not a global snapshot')
        idx=e['selected_candidate'];candidate=next(p for p in planner['candidate_paths'] if p['id']==idx)
        choice=e['selected_routes'][idx];pool=next(p for p in e['pools'] if p['goal_id']==choice['goal_id'])
        original=next(p for p in pool['candidates'] if p['pool_index']==choice['pool_index'])
        for key,name in [('raw','raw_waypoints'),('shortcut','waypoints')]:
            require(len(original[key])==len(candidate[name]),'Path size')
            require(all(max(abs(a-b) for a,b in zip(e['graph_nodes'][n],w['position']))<=1e-12 for n,w in zip(original[key],candidate[name])),'Geometry mismatch')
        camera=CameraShadowConfig.from_yaml(mapping,planner['planning_region']['min'],planner['planning_region']['max'])
        req={'sequence':seq,'map_version':planner['map_version'],'accepted':e['validation_route_safe'],
             'goal':choice['goal_id'],'start_yaw':e['start_yaw'],'terminal_yaw':candidate['waypoints'][-1]['yaw'],
             'nodes':e['graph_nodes'],'edges':e['graph_edges'],'raw':original['raw'],'reference':original['shortcut'],'camera':camera.provenance()}
        filename='request_%06d.json'%seq;write(directory/filename,req)
        cases.append({'sequence':seq,'snapshot':str(folder),'snapshot_sha256':{p.name:sha(p) for p in folder.iterdir() if p.is_file()},
                      'request':str(directory/filename),'request_sha256':sha(directory/filename),'accepted_at_recording':req['accepted'],
                      'subset':'historical_development' if seq in (1,13,14,26,27,38) else 'expanded_development',
                      'stage':'early' if seq<=13 else ('middle' if seq<=26 else 'late')})
    reg={'task':'I3-03-02','source_run':str(RUN),'source_route_log_sha256':sha(RUN/'route_controls.jsonl'),
         'mapping_yaml_sha256':sha(mapping),'protocol_sha256':sha(HERE/'I3_03_02_PROTOCOL.md'),'cases':cases,
         'environment_seed':4,'planner_seed':4,'new_simulation':False,'independent_seed_runs':1,
         'worker_physical_cores':[0,2,4,6],'primary_quality':{'wins_each_control_min':2,'mean_absolute_difference_min_exclusive':1e-9,'median_difference_min':-1e-9},
         'budget_completion_fraction_min':.9,'method_revisions_after_results':0}
    write(directory/'inputs.json',reg);write(HERE/'I3_03_02_INPUTS.json',reg)
    print('Registered',len(cases),'states; no prototype experiment run.')


def validate(reg):
    require(sha(HERE/'I3_03_02_PROTOCOL.md')==reg['protocol_sha256'],'Protocol changed')
    require(sha(RUN/'route_controls.jsonl')==reg['source_route_log_sha256'],'Route log changed')
    for c in reg['cases']:
        require(sha(c['request'])==c['request_sha256'],'Request changed')
        require({p.name:sha(p) for p in Path(c['snapshot']).iterdir() if p.is_file()}==c['snapshot_sha256'],'Snapshot changed')


def run(inputs,output,runner):
    reg=read(inputs);validate(reg);output.mkdir(exist_ok=False,parents=True)
    cores=reg['worker_physical_cores'];require(set(cores)<=os.sched_getaffinity(0),'Unavailable CPU cores')
    identity={'started_utc':datetime.now(timezone.utc).isoformat(),'parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
              'global_planner_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO/'global_planner',text=True).strip(),
              'runner_sha256':sha(runner),'library_sha256':sha(REPO.parents[1]/'devel/lib/libglobal_planner.so'),
              'inputs_sha256':sha(inputs),'protocol_sha256':reg['protocol_sha256'],'platform':platform.platform(),
              'parallel_workers':4,'physical_cpu_affinities':cores,'regimes':['mechanism','budget'],'new_simulation':False}
    write(output/'identity.json',identity);shutil.copy2(inputs,output/'inputs.json')
    buckets=[[] for _ in cores]
    for c in reg['cases']:
        for regime in ('mechanism','budget'):
            for mode in range(4):buckets[(c['sequence']+mode)%4].append((c,regime,mode))
    lock=threading.Lock();completed=[]
    def worker(cpu,jobs):
        for c,regime,mode in jobs:
            tag='s%03d_%s_m%d'%(c['sequence'],regime,mode);resource=output/(tag+'_resource.json')
            command=['taskset','-c',str(cpu),'/usr/bin/time','-f','{"peak_rss_kib":%M,"user_cpu_s":%U,"system_cpu_s":%S}','-o',str(resource),str(runner),c['snapshot'],c['request'],str(mode),regime]
            start=time.perf_counter()
            try:
                p=subprocess.run(command,text=True,capture_output=True,timeout=180)
                (output/(tag+'.stdout.json')).write_text(p.stdout);(output/(tag+'.stderr.log')).write_text(p.stderr)
                record={'job':tag,'sequence':c['sequence'],'regime':regime,'mode':mode,'cpu':cpu,'returncode':p.returncode,'wall_s':time.perf_counter()-start}
                if resource.exists():record.update(read(resource))
                if p.returncode==0:record['output_sha256']=sha(output/(tag+'.stdout.json'))
                else:record['status']='TOOL_ERROR_NO_AUTOMATIC_RETRY'
            except subprocess.TimeoutExpired as e:
                (output/(tag+'.stderr.log')).write_text(str(e));record={'job':tag,'status':'PROCESS_TIMEOUT_NO_AUTOMATIC_RETRY','sequence':c['sequence'],'regime':regime,'mode':mode,'cpu':cpu}
            write(output/(tag+'_receipt.json'),record)
            with lock:
                completed.append(record);write(output/'batch_state.json',{'status':'RUNNING','completed_jobs':completed,'jobs_expected':304})
                if len(completed)%8==0:print('completed',len(completed),'/304',tag,flush=True)
        return True
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(worker,cpu,jobs) for cpu,jobs in zip(cores,buckets)]
        for f in futures:f.result()
    validate(reg)
    write(output/'batch_state.json',{'status':'COMPLETE','completed_jobs':completed,'jobs_expected':304,'frozen_inputs_unchanged':True})
    print('COMPLETE',len(completed),'jobs; failed jobs preserved; no automatic retry.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','run']);p.add_argument('--inputs',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--runner',type=Path)
    a=p.parse_args()
    if a.action=='register':register(a.output)
    else:run(a.inputs,a.output,a.runner)
