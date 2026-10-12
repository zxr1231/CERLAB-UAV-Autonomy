"""Explicit prospective route poses; no changes to historical I1 sampler."""
import math
SAMPLER='route_translation_and_stationary_shortest_yaw_v1'

def sample_route(waypoints,initial_yaw,spacing=.25,yaw_spacing=.1,include_rotations=True):
    if not waypoints or not all(math.isfinite(x) and x>0 for x in [spacing,yaw_spacing]) or not math.isfinite(initial_yaw):
        raise ValueError('invalid route sampling inputs')
    for p in waypoints:
        if len(p['position'])!=3 or not all(math.isfinite(v) for v in p['position']) or not math.isfinite(p['yaw']):
            raise ValueError('invalid route waypoint')
    samples=[];yaw=initial_yaw;distance=0.;yaw_distance=0.
    def append(position,angle):
        value={'position':list(position),'yaw':angle}
        if samples and math.dist(samples[-1]['position'],position)<=1e-12 and abs(math.remainder(samples[-1]['yaw']-angle,2*math.pi))<=1e-12:return
        samples.append(value)
    append(waypoints[0]['position'],yaw)
    def rotate(position,target):
        nonlocal yaw,yaw_distance
        delta=math.remainder(target-yaw,2*math.pi);yaw_distance+=abs(delta)
        if include_rotations:
            n=math.ceil(abs(delta)/yaw_spacing)
            begin=yaw
            for i in range(1,n+1):append(position,begin+delta*i/n)
        yaw=target
        append(position,yaw)
    for a,b in zip(waypoints,waypoints[1:]):
        length=math.dist(a['position'],b['position'])
        if length<=1e-12:continue
        heading=math.atan2(b['position'][1]-a['position'][1],b['position'][0]-a['position'][0])
        rotate(a['position'],heading)
        n=math.ceil(length/spacing)
        for i in range(1,n+1):append([a['position'][axis]+(b['position'][axis]-a['position'][axis])*i/n for axis in range(3)],heading)
        distance+=length
    rotate(waypoints[-1]['position'],waypoints[-1]['yaw'])
    return {'samples':samples,'length':distance,'yaw_distance':yaw_distance,'sampler':SAMPLER,'include_rotations':include_rotations}
