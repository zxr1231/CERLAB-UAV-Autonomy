# I3-00 bounded performance follow-up (V2), 2026-10-12

V1 frozenGP4f135f2 / parentefef180 and verified backup. Exact parity passed12/239,
30-candidate1178.820ms failed500ms; no threshold change or favorable seed repeat.
User explicitly requested continue after backing up V1.

Hardware perf unavailable; do not install packages or change kernel permissions.
One instrumented fixed30 workload records ray-endpoint preparation versus DDA/set
collection time and work counts. Instrumentation results are diagnosis, not admission.

At most TWO concrete semantic-preserving interventions:
1. Endpoint representative deduplication using per-evaluation generation scratch
   (no cross-call visibility/edge/map-results cache), bounded allocation and preserving
   FIRST pixel ray order. Select scratch indexing after phase profile.
2. Precomputed immutable planning-region membership / lean DDA collection using exact
   existing voxel-centre comparisons. No dropping rays/samples or changing yaw/range.

Each version retained. Optimized final non-instrumented build:15 regression tests,
ALL12/239 frozen per-pose/address/raw/unique/marginal checks, same warmup+3 repeats and
actual30-candidate workload. Admission remains p95prefix<=250,max<=500,batch<=500ms.
If parity fails, fix the specific implementation defect; no epsilon tolerance or
changing Python reference. If cost still fails after2 interventions, finish/report
this batch with ONLINE NO-GO and explicit next decision; no endless optimization,
new seed collection, budget increase or core guided-route implementation.
