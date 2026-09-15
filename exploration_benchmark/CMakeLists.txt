cmake_minimum_required(VERSION 3.0.2)
project(exploration_benchmark)

find_package(catkin REQUIRED COMPONENTS
  map_manager
  rospy
  std_msgs
  nav_msgs
  sensor_msgs
)

catkin_python_setup()
catkin_package(CATKIN_DEPENDS map_manager)

catkin_install_python(PROGRAMS
  scripts/benchmark_logger.py
  scripts/generate_ground_truth_mask.py
  scripts/run_experiment.py
  scripts/run_matrix.py
  scripts/summarize_trajectory_alignment.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

if(CATKIN_ENABLE_TESTING)
  catkin_add_nosetests(test/test_benchmark_core.py)
  catkin_add_nosetests(test/test_batch.py)
  catkin_add_nosetests(test/test_coverage.py)
  catkin_add_nosetests(test/test_collision_metrics.py)
  catkin_add_nosetests(test/test_ground_truth.py)
  catkin_add_nosetests(test/test_resource_metrics.py)
  catkin_add_nosetests(test/test_trajectory_metrics.py)
endif()
