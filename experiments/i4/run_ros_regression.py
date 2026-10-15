#!/usr/bin/env python3
"""Existing snapshot regression on an ephemeral, private ROS Master; no simulator."""
import os,signal,socket,subprocess,time,xmlrpc.client
from pathlib import Path
def main():
 logroot=Path('/tmp/i4_01_ros_regression');logroot.mkdir(exist_ok=True)
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 env=os.environ.copy();env.update(ROS_MASTER_URI='http://127.0.0.1:%d'%port,ROS_HOSTNAME='localhost',ROS_IP='127.0.0.1',ROS_LOG_DIR=str(logroot))
 with (logroot/'master.log').open('w') as masterlog:
  core=subprocess.Popen(['roscore','-p',str(port)],env=env,stdout=masterlog,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   for _ in range(100):
    if core.poll() is not None:raise RuntimeError('private ROS Master exited')
    try:
     if xmlrpc.client.ServerProxy(env['ROS_MASTER_URI']).getPid('/i4_regression')[0]==1:break
    except OSError:pass
    time.sleep(.1)
   else:raise RuntimeError('private ROS Master did not become ready')
   with Path('/tmp/i4_01_regression_route_snapshot_envfix.log').open('w') as f:
    run=subprocess.run(['taskset','-c','6','/home/zxr2/cerlab_benchmark_ws/devel/lib/global_planner/route_snapshot_test','--gtest_output=xml:/tmp/i4_01_route_snapshot_test.xml'],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=120)
   if run.returncode:raise RuntimeError('snapshot regression failed: '+str(run.returncode))
   print('Private ROS snapshot regression PASS, port',port)
  finally:
   if core.poll() is None:
    os.killpg(core.pid,signal.SIGINT)
    try:core.wait(timeout=15)
    except subprocess.TimeoutExpired:
     os.killpg(core.pid,signal.SIGTERM);core.wait(timeout=10)
if __name__=='__main__':main()
