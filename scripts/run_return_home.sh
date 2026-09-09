#!/usr/bin/env bash
set -e
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
workspace_dir="$(cd -- "$project_dir/../.." && pwd)"
source /opt/ros/noetic/setup.bash
source "$workspace_dir/devel/setup.bash"
mode="${1:-exploration}"
if [ "$#" -gt 0 ]; then shift; fi
case "$mode" in
  simulator)
    source "$project_dir/uav_simulator/gazeboSetup.bash"
    exec roslaunch uav_simulator start.launch "$@" ;;
  rviz) exec roslaunch remote_control exploration_rviz.launch "$@" ;;
  exploration) exec roslaunch autonomous_flight dynamic_exploration.launch "$@" ;;
  smoke) exec roslaunch autonomous_flight return_home_smoke.launch "$@" ;;
  *) echo "Usage: $0 {simulator|rviz|exploration|smoke}" >&2; exit 2 ;;
esac
