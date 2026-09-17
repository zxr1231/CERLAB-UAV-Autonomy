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
2. **Offline voxel visibility oracle — selected for floorplan2 refinement.** It uses
   every reachable flight voxel, the mapper camera model, nested yaw samples, and
   static voxel occlusion without coupling the result to a tested planner or a running
   simulator. It deliberately fails for non-vertically-extruded geometry; arbitrary
   meshes remain a future backend.
3. **Final online occupancy map — rejected as denominator.** It depends on the tested
   planner, mapper thresholds, artificial free regions, and run duration, causing a
   circular and biased metric.
4. **Visual/mesh voxelization — unnecessary for floorplan2.** Visual person meshes and
   other scenarios may need a mesh backend later, but floorplan2 collision geometry is
   already primitive and authoritative for safety.

## Prototype boundary

The v1 artifact provides `static_occupied`, `accessible_free`, `static_surface`,
`inflated_occupied`, `flight_reachable`, and `unreachable_free`. The v2 artifact adds
`observable_free`, `observable_static_surface`, and their complements. The oracle
assumes level body roll/pitch, allows yaw at every reachable flight voxel, reproduces
the camera transform, vertical sampled-pixel envelope and 5 m raycast, and treats the
five moving people as transient objects rather than static denominator occluders.

For floorplan2, 32, 64, and 128 nested yaw samples all classify every one of the
980,550 accessible-free voxels and every one of the 29,375 static-surface voxels as
observable. This equality validates the existing denominators under the stated static
model; it does not model localization error, dynamic occlusion, camera noise, body
tilt, or arbitrary mesh worlds.
