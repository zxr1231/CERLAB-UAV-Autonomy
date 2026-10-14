#!/usr/bin/env python3
"""Plot saved final summaries; never execute planners or alter results."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(root):
    report=json.loads((root/'summary.json').read_text())
    cases=[r for r in report['cases'] if r['status']=='VALID']
    figure,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    for control,label,marker in [(1,'Guided - motion','o'),(2,'Guided - diverse','x')]:
        for subset,color in [('expanded_development','#1769aa'),('historical_development','#c55a11')]:
            rows=[r for r in cases if r['subset']==subset and r['reference_utility']!=0]
            axes[0].scatter([r['sequence'] for r in rows],[100*(r['equal_count']['3']-r['equal_count'][str(control)])/r['reference_utility'] for r in rows],
                            color=color,marker=marker,s=35,label=label+' ('+('expanded' if subset=='expanded_development' else 'old')+')')
    axes[0].axhline(0,color='gray',linewidth=.8)
    axes[0].set(xlabel='Frozen global planning event',ylabel='Paired utility delta / reference (%)',title='Equal actual extra-score count')
    axes[0].legend(fontsize=7)
    counts=[sum(r['budget_complete'][str(m)] for r in cases) for m in range(4)]
    rates=[100*n/(3*len(cases)) for n in counts]
    axes[1].bar(['Reference','Motion','Diverse','Guided'],rates,color=['#999999','#6fa7d0','#7dba8b','#c55a11'])
    axes[1].axhline(90,color='black',linestyle='--',linewidth=1,label='Registered 90% gate')
    for i,(rate,n) in enumerate(zip(rates,counts)):axes[1].text(i,rate+1.5,f'{rate:.1f}%\n{n}/{3*len(cases)}',ha='center',fontsize=8)
    axes[1].set(ylim=(0,115),ylabel='Complete within 500 ms (%)',title='Four pinned workers; 3 timing repeats')
    axes[1].legend(fontsize=8)
    figure.suptitle('I3-03-02: one historical scene/seed; predicted utility only',fontsize=11)
    for ext in ('png','pdf'):figure.savefig(root/('final_comparison.'+ext),dpi=160)
    plt.close(figure)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);main(p.parse_args().root)
