import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
spec=importlib.util.spec_from_file_location('matrix_runner',Path(__file__).resolve().parents[1]/'scripts/run_matrix.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
class MatrixRunnerTest(unittest.TestCase):
 def run_case(self,invalid=False):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);results=root/'results';run=results/'trial';run.mkdir(parents=True)
   manifest={'outcome':'HOME_REACHED','resource_metrics_status':'VALID','trajectory_metrics_status':'VALID','collision_measurement_status':'VALID','coverage_status':'VALID_ACCESSIBLE_FREE_V2','main_commit':'frozen','git_status':'','environment_seed':1,'planner_seed':1,'route_control_mode':'historical_legacy','path_gain_mode':'unique_shadow','files':{'world':'hash'},'submodules':['fixed']}
   if invalid:manifest['trajectory_metrics_status']='INVALID'
   (run/'run.json').write_text(json.dumps(manifest))
   config=root/'config.json';config.write_text(json.dumps({'schema_version':1,'experiment_id':'M','seed_pairs':[[1,1]],'path_gain_modes':['unique_shadow'],'route_control_modes':['historical_legacy','distance_single']}))
   calls=[]
   def fake(command,**kwargs):
    calls.append(command)
    if command==['rosnode','list']:return subprocess.CompletedProcess(command,1)
    return subprocess.CompletedProcess(command,0,str(run)+'\n','')
   args=['run_matrix','--config',str(config),'--workspace',str(root),'--results-root',str(results),'--max-tasks','1']
   with patch.object(sys,'argv',args),patch.object(runner.subprocess,'run',side_effect=fake),patch.object(runner.subprocess,'check_output',return_value='frozen\n'):
    code=runner.main()
   state=json.loads((results/'M/batch_state.json').read_text())
   self.assertEqual(state['tasks'][1]['status'],'PENDING')
   self.assertIn('--route-control-mode',calls[-1])
   self.assertEqual(state['source_commit'],'frozen')
   return code,state['tasks'][0]
 def test_route_forwarding_and_terminal_record(self):
  code,task=self.run_case();self.assertEqual(code,0);self.assertEqual(task['status'],'SUCCESS');self.assertEqual(len(task['attempts']),1)
 def test_invalid_measurement_is_not_success(self):
  code,task=self.run_case(True);self.assertEqual(code,1);self.assertEqual(task['status'],'MEASUREMENT_INVALID');self.assertIn('trajectory_metrics_status',task['attempts'][0]['measurement_errors'])
if __name__=='__main__':unittest.main()
