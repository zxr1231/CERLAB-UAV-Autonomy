# I3-01A source-to-contract audit

Read-only review2026-10-12; code remains unchanged. Paths below relative to project.

| Source | Evidence / integration implication |
|---|---|
| global_planner/include/global_planner/dep.cpp::makePlan | frontier/PRM/update/prefilter precede single-distance control; Legacy path scoring; snapshot and pose for new controls; final fresh-map validation can clear bestPath |
| global_planner/include/global_planner/dep.cpp::findBestPath | intermediate nodes ANDGoal recomputed/summed; scored Legacy gain feedback exists; camera5m must not overwrite it |
| global_planner/include/global_planner/routeControls.cpp | distance_single uses fixed pose/map and Dijkstra; historical branch uses PRM A*; selected_candidate logged before later validation, so proposal differs from accepted path |
| global_planner/include/global_planner/dep.cpp end of makePlan | routeSnapshot_/gainSources cleared; futureB must explicitly retain an immutable context, not silently combine fresh live data andold candidate poses |
| autonomous_flight/include/autonomous_flight/simulation/dynamicExploration.cpp::exploreReplan | completion/reachable gain/sensor checks happen AFTER makePlan; insertB only after continuing exploration is decided, before final path publication/consumption; preserve completion and returning-home behavior |
| same file global event publication | A global event currently identifies its selected PRM path; B needs a separate versioned final-route event/link to local input/B-spline/odom, not relabel A index as B index |
| global_planner/include/global_planner/diagnosticSnapshot.cpp | selectedCandidate derives from matching bestPath; -1 at state13 is expected after safety rejection; exporter vehiclepose is live, not necessarily fixed planning pose |
| experiments/i2/I2_01_PROTOCOL.json | historical raw pool6/routes-per-goal3/global30,50ms aftermandatory refs; proposed single-goal2 candidates and inclusiveB500ms are an explicitly NEW contract |

No integration changes made. The next minimal test replays recordedA selections and
validates the exportedmap/graph; it cannot claim to reconstruct original onlineA from
that later map. No source defect is being patched merely to make this scope pass.

Prior novelty audit was consulted for claim boundaries only: fixed-goal residual route
construction must beat simple marginal insertion andgeneric paths; two-stage splitting,
voxel union and ordinary caching are not newly proven contributions. This is not a new
literature search or assertion of novelty as of today.
