#!/usr/bin/env python3
"""Run the preregistered 36 isolated jobs; no retries or parameter search."""
import concurrent.futures,hashlib,json,os,subprocess,sys,time
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 inputs=Path(sys.argv[1]);output=Path(sys.argv[2]);output.mkdir(parents=True,exist_ok=False)
 repo=Path(__file__).resolve().parents[2];manifest=json.loads((inputs/'manifest.json').read_text())
 for f,d in manifest['protected'].items():assert sha(Path(f))==d,f
 assert sha(Path(__file__).with_name('I4_01_PROTOCOL.md'))==manifest['protocol_sha256']
 runner=Path('/home/zxr2/cerlab_benchmark_ws/devel/lib/global_planner/incremental_gain_runner')
 identity={'parent':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'global_planner':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo/'global_planner',text=True).strip(),'input_manifest_sha256':sha(inputs/'manifest.json'),'protocol_sha256':manifest['protocol_sha256'],'binary_sha256':sha(runner),'libraries':{p.name:sha(p) for p in [runner.parents[1]/'libglobal_planner.so',runner.parents[1]/'libincremental_gain_prototype.so']},'cpuinfo':subprocess.check_output(['lscpu'],text=True),'schedule':[]}
 env=os.environ.copy();env['LD_LIBRARY_PATH']='/home/zxr2/cerlab_benchmark_ws/devel/lib:'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='1';env['OPENBLAS_NUM_THREADS']='1'
 for repeat in range(3):
  for phase in range(4):
   jobs=[{'repeat':repeat,'segment':(repeat+slot)%3,'mode':(phase+slot)%4,'cpu':[0,2,4][slot]} for slot in range(3)]
   identity['schedule'].extend(jobs)
 (output/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
 def run(job):
  tag='r{repeat}_s{segment}_m{mode}'.format(**job);start=time.monotonic()
  with (output/(tag+'.stderr')).open('w') as log:
   r=subprocess.run(['taskset','-c',str(job['cpu']),str(runner),str(inputs/('segment_%d.json'%job['segment'])),str(job['mode']),str(output/(tag+'.jsonl'))],env=env,stderr=log,timeout=1800)
  record=dict(job,exit_code=r.returncode,wall_seconds=time.monotonic()-start)
  (output/(tag+'.receipt.json')).write_text(json.dumps(record,indent=2)+'\n');print(tag,r.returncode,round(record['wall_seconds'],2),flush=True)
  if r.returncode:raise RuntimeError('job failed, retained without retry: '+tag)
  return record
 receipts=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for offset in range(0,36,3):
   futures=[pool.submit(run,j) for j in identity['schedule'][offset:offset+3]]
   receipts.extend(f.result() for f in futures)
   (output/'progress.json').write_text(json.dumps(receipts,indent=2)+'\n')
 for f,d in manifest['protected'].items():assert sha(Path(f))==d,f
 (output/'complete.json').write_text(json.dumps({'jobs':len(receipts),'protected_inputs_unchanged':True},indent=2)+'\n')
if __name__=='__main__':main()
