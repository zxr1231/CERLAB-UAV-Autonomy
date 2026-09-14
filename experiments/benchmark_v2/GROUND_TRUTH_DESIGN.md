# Ground-truth mask feasibility decision

## Source audit

`floorplan2_dynamic_5.world` embeds the static `floorplan2` model directly. It has 13
collision links, all represented by oriented boxes with explicit size and pose. Four
20.15 m walls form the outer boundary and nine shorter walls form the interior. The
model pose is `(0.335161,-0.328557,0)` and the walls span z=0 to z=2.5 m.

The five moving-person models are separate non-static models. Their motion plugin
reads fixed waypoints, velocity, and angular velocity and does not call a random
generator. Gazebo seed therefore does not change these waypoint paths in the current
world.

The occupancy map reserves 4.8 million voxels over 40 × 40 × 3 m, substantially larger
than the enclosed floorplan. Counting every known voxel in that reserved map would
include exterior and above-wall observations and is rejected as the normalized
Coverage definition.

## Options considered

1. **SDF collision voxelization — selected for floorplan worlds.** It is independent
   of planner output, deterministic, geometrically aligned with Gazebo collision
   boxes, and requires no new dependency.
2. **Gazebo oracle raycasting — deferred to visibility refinement.** It can determine
   sensor-observable subsets and handle arbitrary geometry, but is slower and couples
   mask generation to a running simulator.
3. **Final online occupancy map — rejected as denominator.** It depends on the tested
   planner, mapper thresholds, artificial free regions, and run duration, causing a
   circular and biased metric.
4. **Visual/mesh voxelization — unnecessary for floorplan2.** Visual person meshes and
   other scenarios may need a mesh backend later, but floorplan2 collision geometry is
   already primitive and authoritative for safety.

## Prototype boundary

The first artifact provides `static_occupied`, `accessible_free`, `static_surface`,
`inflated_occupied`, `flight_reachable`, and `unreachable_free`. It does not yet claim
that every accessible voxel is visible under the camera model. Oracle visibility and
online sensor-provenance integration are separate gated tasks.
