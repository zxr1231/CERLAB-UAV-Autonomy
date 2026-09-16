# Artificial-clear provenance integration validation

Date: 2026-09-16

The `map_manager` rostest constructs the real `occMap` class with a small synthetic
voxel grid. It calls the production map-mutation and sensor-update paths:

1. `setFree()` on one voxel;
2. `freeRegion()` over the map;
3. `updateOccupancyInfo()` to represent a sensor raycast update.

After steps 1 and 2, `SensorObservationTracker::observedTotal()` and the pending delta
size both remain zero. After step 3, both equal one. This verifies that artificial
initial/dynamic clearing changes occupancy but does not enter sensor provenance, while
the actual sensor update path does.

The test runs as `rostest_gtest` with an isolated temporary ROS Master. All three
tracker/integration cases passed. It does not start Gazebo or autonomous exploration.
