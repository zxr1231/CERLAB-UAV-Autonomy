"""Deterministic labeled sampler and statistics for saved I3-02A outputs."""
import math

def labeled_samples(positions, initial_yaw, terminal_yaw, insertion_edge, candidate,
                    spacing=.25, yaw_spacing=.1):
    samples=[]; labels=[]; yaw=initial_yaw
    def append(position, angle, label):
        value={'position':list(position),'yaw':angle}
        if samples and math.dist(samples[-1]['position'],position)<=1e-12 and abs(math.remainder(samples[-1]['yaw']-angle,2*math.pi))<=1e-12:
            return
        samples.append(value);labels.append(label)
    append(positions[0],yaw,'common_initial')
    last_reference_leg=(len(positions)-2 if not candidate else len(positions)-3)
    def leg_labels(index):
        if candidate:
            if index<insertion_edge:return 'unchanged_prefix','unchanged_prefix'
            if index==insertion_edge:return 'inserted_incoming','inserted_incoming'
            if index==insertion_edge+1:return 'inserted_outgoing','inserted_outgoing'
            rotation='changed_exit' if index==insertion_edge+2 else 'unchanged_suffix'
            return rotation,'unchanged_suffix'
        if index<insertion_edge:return 'unchanged_prefix','unchanged_prefix'
        if index==insertion_edge:return 'replaced_edge','replaced_edge'
        rotation='changed_exit' if index==insertion_edge+1 else 'unchanged_suffix'
        return rotation,'unchanged_suffix'
    def rotate(position,target,label):
        nonlocal yaw
        delta=math.remainder(target-yaw,2*math.pi);n=math.ceil(abs(delta)/yaw_spacing);begin=yaw
        for i in range(1,n+1):append(position,begin+delta*i/n,label)
        yaw=target;append(position,yaw,label)
    for index,(a,b) in enumerate(zip(positions,positions[1:])):
        length=math.dist(a,b)
        if length<=1e-12:continue
        rotation_label,translation_label=leg_labels(index)
        heading=math.atan2(b[1]-a[1],b[0]-a[0]);rotate(a,heading,rotation_label)
        n=math.ceil(length/spacing)
        for i in range(1,n+1):append([a[k]+(b[k]-a[k])*i/n for k in range(3)],heading,translation_label)
    terminal_changed=insertion_edge==last_reference_leg
    rotate(positions[-1],terminal_yaw,'changed_exit' if terminal_changed else 'unchanged_suffix')
    return samples,labels

def average_ranks(values):
    order=sorted(range(len(values)),key=lambda i:values[i]);ranks=[0.]*len(values);start=0
    while start<len(order):
        end=start+1
        while end<len(order) and values[order[end]]==values[order[start]]:end+=1
        rank=(start+1+end)/2
        for i in order[start:end]:ranks[i]=rank
        start=end
    return ranks

def spearman(a,b):
    if len(a)!=len(b) or len(a)<2:raise ValueError('invalid rank vectors')
    x,y=average_ranks(a),average_ranks(b);mx=sum(x)/len(x);my=sum(y)/len(y)
    vx=sum((v-mx)**2 for v in x);vy=sum((v-my)**2 for v in y)
    return None if not vx or not vy else sum((u-mx)*(v-my) for u,v in zip(x,y))/math.sqrt(vx*vy)

def sign(value,tol=1e-9):return 1 if value>tol else (-1 if value<-tol else 0)

def point_segment_distance(p,a,b):
    ab=[b[i]-a[i] for i in range(3)];ap=[p[i]-a[i] for i in range(3)];den=sum(x*x for x in ab)
    t=0 if not den else max(0.,min(1.,sum(ap[i]*ab[i] for i in range(3))/den))
    return math.dist(p,[a[i]+t*ab[i] for i in range(3)])

def components6(addresses,dimensions):
    dy,dz=dimensions[1],dimensions[2];remaining=set(addresses);sizes=[]
    def xyz(v):return v//(dy*dz),(v//dz)%dy,v%dz
    def address(x,y,z):return (x*dy+y)*dz+z
    while remaining:
        root=remaining.pop();stack=[root];size=1
        while stack:
            v=stack.pop();x,y,z=xyz(v)
            for dx,dy0,dz0 in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                q=(x+dx,y+dy0,z+dz0)
                if all(0<=q[i]<dimensions[i] for i in range(3)):
                    n=address(*q)
                    if n in remaining:remaining.remove(n);stack.append(n);size+=1
        sizes.append(size)
    return sorted(sizes,reverse=True)
