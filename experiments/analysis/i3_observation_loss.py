"""Set/cost accounting; never infer observation preservation from counts alone."""
def compare_sets(before,after):
    a,b=set(before),set(after);lost=a-b;added=b-a;union=a|b
    return {'before_count':len(a),'after_count':len(b),'lost_count':len(lost),'added_count':len(added),
            'loss_ratio':len(lost)/len(a) if a else 0.,'net_before_minus_after':len(a)-len(b),
            'jaccard':len(a&b)/len(union) if union else 1.}

def raw_final_constraints(raw,reference,protocol):
    return {'length':raw['length']<=protocol['raw_as_final_length_ratio_max']*reference['length'],
            'time':raw['time']<=protocol['raw_as_final_time_ratio_max']*reference['time'],
            'yaw':raw['yaw_distance']<=reference['yaw_distance']+protocol['raw_as_final_additional_yaw_max']}

def classify(before,after,reference,raw_motion,reference_motion,protocol,extra=True):
    comparison=compare_sets(before,after);cost=raw_final_constraints(raw_motion,reference_motion,protocol)
    u_raw=len(set(before))/raw_motion['time'] if raw_motion['time']>1e-6 else 0.
    u_ref=len(set(reference))/reference_motion['time'] if reference_motion['time']>1e-6 else 0.
    material=comparison['lost_count']>=protocol['material_lost_voxels_min'] and comparison['loss_ratio']>=protocol['material_loss_ratio_min']
    gain=u_raw>u_ref+protocol['utility_improvement_tolerance']
    return {'shortcut_change':comparison,'raw_vs_final_reference':compare_sets(before,reference),
            'raw_as_final_checks':cost,'raw_as_final_motion_pass':all(cost.values()),
            'raw_utility':u_raw,'reference_final_utility':u_ref,'raw_utility_improves':gain,
            'material_predicted_loss':material,'direct_raw_retention_lead':extra and material and all(cost.values()) and gain}
