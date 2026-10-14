"""Fixed V2 selectors and engineering/value decisions; no generation innovation gate."""
MODES=('geometry_with_u_fallback','new_only_with_u_fallback','exact_net_rerank')
def choices(pool,rows,ref_unique,ref_time):
    if ref_time<=1e-6:raise ValueError('degenerate reference')
    u0=ref_unique/ref_time
    if not rows:return {m:{'extra':None,'final':None,'utility':u0,'extra_utility':None} for m in MODES}
    def key(row):
        r=pool['records'][row['record_id']]
        return (r['motion']['time'],r['motion']['length'],r['u'],r['v'],r['e'])
    selected={MODES[0]:min(rows,key=key),MODES[1]:min(rows,key=lambda r:(-r['new'],)+key(r)),
              MODES[2]:min(rows,key=lambda r:(-r['utility'],)+key(r))}
    return {m:{'extra':r['record_id'],'final':r['record_id'] if r['utility']>u0+1e-9 else None,
               'utility':r['utility'] if r['utility']>u0+1e-9 else u0,'extra_utility':r['utility']} for m,r in selected.items()}
def decision(states):
    valid=[s for s in states if s['status']=='COMPLETE']
    if len(valid)!=5 or not all(s['engineering_parity'] for s in valid):return {'decision':'ENGINEERING_FAIL'}
    supplied=[s['sequence'] for s in valid if s['pool_size'] and not s['truncated']]
    positive=[s['sequence'] for s in valid if s['choices']['exact_net_rerank']['final'] is not None]
    state='FOUNDATION_PASS_COST_STUDY_PENDING'
    if len(supplied)<3:state='LIMITED_POOL_SUPPLY_FAIL'
    elif len(positive)<2:state='LIMITED_POOL_VALUE_FAIL'
    return {'decision':state,'nontruncated_nonempty_states':supplied,'positive_predicted_utility_states':positive,
            'engineering_pass':True,'timing_admitted':False,'guided_generation_admitted':False}
