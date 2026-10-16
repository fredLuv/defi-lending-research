"""Chart contract: dated rates (different conventions), cost scenarios, cash scope.

No trend is inferred from one snapshot. Quote axis begins at zero; signed cost
axis shares zero. Liquidity bars show absolute USDC, with scope labelled in each
panel; fractions are descriptive, not a cross-product safety ranking.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from current_analysis import ROOT, ORDER, build as analyse
COLORS=['#3476A8','#C87936','#8E4D20','#637A66']
SHORT=['Aave V4\nCore / Main','Morpho V2\nSteakhouse Prime','Morpho V2\nGauntlet Prime','SGOV\nTreasury ETF']

def build(data=None):
    rates,costs,manifest=data or analyse()
    out=ROOT/'figures/current';out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.labelcolor':'#17324A','text.color':'#17324A','axes.titleweight':'bold'})
    # Do not hard-code retrieval clock when recollecting.
    import pandas as pd
    date=pd.Timestamp(manifest['finished_utc']).strftime('%d %b %Y, %H:%M UTC')
    fig,(ax,bx)=plt.subplots(1,2,figsize=(15,6.5),gridspec_kw={'width_ratios':[1,1.2]})
    fig.suptitle('Current yield is a quote. Net income depends on time and costs.',fontsize=19,y=.98,weight='bold')
    fig.text(.5,.92,f"Ethereum USDC snapshot: {date} · SGOV issuer yield: {rates.loc['sgov','source_as_of']}",ha='center',color='#59636E')
    x=np.arange(4);values=rates.quote_rate.to_numpy()*100
    ax.bar(x,values,color=COLORS,width=.64)
    for i,v in enumerate(values):ax.text(i,v+.13,f'{v:.2f}%',ha='center',weight='bold',fontsize=14)
    ax.set_xticks(x,SHORT);ax.set_ylim(0,6.5);ax.set_ylabel('Reported annualized rate (%)')
    ax.set_title('Different rate conventions',pad=20)
    ax.text(.5,-.23,'Aave: variable APY · Morpho: 6-hour realized APY\nSGOV: 30-day SEC yield, not APY',transform=ax.transAxes,ha='center',fontsize=10)
    for i,key in enumerate(ORDER[:-1]):
        rows=costs.query("capital==10000 and scenario=='Base' and product==@key").sort_values('days')
        offsets=(i-1)*.22;positions=np.arange(3)+offsets
        bx.bar(positions,rows.extra_vs_sgov,width=.2,color=COLORS[i],label=SHORT[i].replace('\n',' · '))
        for p,v in zip(positions,rows.extra_vs_sgov):bx.text(p,v+(3 if v>=0 else -3),f'{v:+.0f}',ha='center',va='bottom' if v>=0 else 'top',fontsize=10)
    bx.axhline(0,color='#59636E',lw=1);bx.set_xticks(range(3),['30 days','90 days','365 days'])
    bx.set_ylim(-55,180);bx.set_ylabel('Net extra income vs SGOV (USD / USD 10,000)')
    bx.set_title('If rates stayed constant — not a forecast',pad=20)
    bx.legend(frameon=False,loc='upper left',fontsize=9)
    bx.text(.5,-.23,'Base costs each side: DeFi USD 10 + 5 bp; SGOV 0.5 bp.\nSEC yield converted to effective rate for scenario arithmetic only.',transform=bx.transAxes,ha='center',fontsize=10)
    fig.text(.5,.025,'USDC = USD 1; fees reflected in rates; rewards, taxes and price changes excluded. Sources: official Aave/Morpho APIs and iShares.',ha='center',fontsize=10,color='#59636E')
    fig.subplots_adjust(left=.065,right=.98,top=.79,bottom=.27,wspace=.3)
    first=out/'01_current_yield_and_costs.png';fig.savefig(first,dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(15,5.8))
    fig.suptitle('Available cash is shared — it is not a withdrawal guarantee',fontsize=19,weight='bold',y=.97)
    fig.text(.5,.9,f'{date} · Different scopes: Hub liquidity versus vault withdrawal capacity',ha='center',color='#59636E')
    for i,(ax,key) in enumerate(zip(axes,ORDER[:-1])):
        row=rates.loc[key];total=row.denominator_usdc/1e6;cash=row.available_usdc/1e6
        ax.barh([0],[total],color='#E7EAED',height=.45)
        ax.barh([0],[cash],color=COLORS[i],height=.45)
        ax.set_xlim(0,130);ax.set_ylim(-.65,.65);ax.set_yticks([]);ax.set_xlabel('Million USDC · common scale')
        ax.set_title(SHORT[i].replace('\n',' · '),fontsize=12,pad=25)
        ax.text(0,.42,f'{cash:,.2f}m available / {total:,.2f}m total',weight='bold',fontsize=12)
        scope='Core Hub supply across Spokes' if i==0 else 'Selected vault assets'
        ax.text(0,-.47,f'{row.cash_fraction:.1%} of {scope.lower()}',fontsize=10)
        ax.text(.0,-.55,('Shared Hub cash; Main deposits are a subset.' if i==0 else 'API-reported withdrawable assets; idle cash = 0.'),transform=ax.transAxes,fontsize=10)
    fig.text(.5,.18,'Morpho capacities can overlap across vaults: do not add them. These API snapshots are not executed withdrawal tests.',ha='center',fontsize=11)
    fig.text(.5,.105,'SGOV: sell during exchange hours, pay the bid/ask spread, and ordinarily settle T+1. No comparable on-chain cash ratio.',ha='center',fontsize=11)
    fig.text(.5,.04,'Cash can change before execution. Position restrictions, liquidity routing and transaction ordering can affect exits.',ha='center',fontsize=10,color='#59636E')
    fig.subplots_adjust(left=.04,right=.98,top=.69,bottom=.41,wspace=.25)
    second=out/'02_current_withdrawal_liquidity.png';fig.savefig(second,dpi=160);plt.close(fig)
    return first,second

if __name__=='__main__':
    print(*build(),sep='\n')
