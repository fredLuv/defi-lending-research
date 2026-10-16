"""Consolidated research figures and a portrait social-summary export."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from analyse import ROOT, COLORS, STYLES
from treasury_analysis import compare

ORDER=['aave','steakhouse_v1','gauntlet_v1']
SHORT={'aave':'Aave V3 Core','steakhouse_v1':'Steakhouse V1','gauntlet_v1':'Gauntlet Prime V1','sgov':'Treasury ETF · SGOV'}
INK='#17324A';NEUTRAL='#59636E';GRID='#E7EAED'
FIG=ROOT/'figures/treasury';FIG.mkdir(exist_ok=True)
SOURCE='Sources: Ethereum contract reads; iShares SGOV NAVs and distributions. 1 Jun 2024–15 Oct 2026 UTC.'
LINK='https://github.com/fredLuv/defi-lending-research/blob/main/docs/DATA_SOURCES.md'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.labelsize':12,'axes.titlesize':14,
                     'text.color':INK,'axes.labelcolor':INK,'axes.grid':False,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.edgecolor':'#B3BBC2','xtick.color':NEUTRAL,'ytick.color':NEUTRAL,
                     'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white',
                     'text.parse_math':False,'svg.fonttype':'none','svg.hashsalt':'usdc-treasury-v1','pdf.fonttype':42})


def save(fig,name,notes):
    fig.text(.07,.085,notes,fontsize=9.2,color=NEUTRAL,va='top',linespacing=1.5)
    fig.text(.07,.019,'Data, assumptions and reproducible code ↗',fontsize=9.2,color=COLORS['aave'],url=LINK)
    for ext in ['png','svg','pdf']:
        fig.savefig(FIG/f'{name}.{ext}',dpi=200)
    plt.close(fig)
    return FIG/f'{name}.png'


def header(fig,title,sub,tag):
    fig.text(.07,.968,tag.upper(),fontsize=10,color=NEUTRAL,weight='bold')
    fig.text(.07,.91,title,fontsize=23,weight='bold',va='top')
    fig.text(.07,.845,sub,fontsize=12,color=NEUTRAL,va='top')


def date_axis(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))


def money(ax,which='y'):
    fmt=FuncFormatter(lambda v,p:f'−${abs(v):,.0f}' if v<0 else f'${v:,.0f}')
    (ax.yaxis if which=='y' else ax.xaxis).set_major_formatter(fmt)


def legend(ax):
    ax.legend(frameon=False,fontsize=10,loc='best')


def liquidity_zoom(ax,daily,compact=False):
    for k in ORDER:
        g=daily[(daily['product']==k)&(daily.date>=pd.Timestamp('2026-04-15',tz='UTC'))&(daily.date<=pd.Timestamp('2026-05-01',tz='UTC'))]
        ax.plot(g.date,g.capacity_usdc,color=COLORS[k],ls=STYLES[k],lw=2.2,label=SHORT[k],marker='o',ms=3)
    ax.set_yscale('log');ax.grid(axis='y',color=GRID,lw=.7)
    ax.set_ylabel('Cash available (USDC; log scale)')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'{v/1e6:g}m' if v>=1e6 else f'{v/1e3:g}k'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=4));ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.axvline(pd.Timestamp('2026-04-18 17:35',tz='UTC'),color=NEUTRAL,lw=1,ls='--')
    ax.text(.03,.20,'Dashed line: 18 April rsETH incident',transform=ax.transAxes,fontsize=8.5,color=NEUTRAL)
    low=daily[daily['product']=='aave'].loc[lambda x:x.capacity_usdc.idxmin()]
    ax.annotate('Aave: 6,519 USDC\n21 April, 00:00 UTC',xy=(low.date,low.capacity_usdc),xytext=(15,26),
                textcoords='offset points',fontsize=11,arrowprops={'arrowstyle':'-','color':NEUTRAL})
    if compact:
        ax.legend(frameon=False,ncol=1,loc='lower right',fontsize=10)
    else:
        ax.legend(frameon=False,ncol=1,loc='upper right',fontsize=9)


def build(data=None):
    result,costs,joined,aligned,panel,daily,eth=data or compare()
    paths=[]
    # Figure 1: a time-series panel and an endpoint comparison answer distinct questions.
    fig=plt.figure(figsize=(13,8.3));header(fig,'How much income was above Treasury bills?',
        '$10,000 starting capital · same 866-day window · Treasury benchmark: SGOV total return','01 / earned return')
    left=fig.add_axes([.085,.22,.48,.51]);right=fig.add_axes([.755,.29,.20,.39])
    left.set_title('A  Extra income before execution costs',loc='left',pad=15)
    left.axhline(0,color=NEUTRAL,lw=1,ls='--')
    for k in ORDER:
        g=joined[joined['product']==k]
        left.plot(g.date,g.gross_extra_vs_sgov,color=COLORS[k],ls=STYLES[k],lw=2,label=SHORT[k])
    left.grid(axis='y',color=GRID);left.set_ylabel('Extra income versus SGOV');date_axis(left);money(left);legend(left)
    right.set_title('B  After base costs',loc='left',pad=28)
    for i,k in enumerate(ORDER):
        v=result.loc[k,'extra_vs_sgov']
        right.barh(i,v,color=COLORS[k],height=.5,alpha=.90)
        right.text(v+3,i,f'+${v:.0f}',va='center',fontsize=15,weight='bold',color=INK)
    right.set_yticks(range(3),[SHORT[k] for k in ORDER]);right.invert_yaxis()
    right.set_xlim(0,max(result.extra_vs_sgov)*1.34);right.set_xticks([0,50,100]);money(right,'x')
    right.set_xlabel('Extra income vs SGOV');right.grid(axis='x',color=GRID);right.set_axisbelow(True)
    fig.text(.07,.13,'Base net annualized return: SGOV '+f"{result.loc['sgov','net_annualized_pct']:.2f}%"+'  |  '+
             '  ·  '.join(f'{SHORT[k]} {result.loc[k,"net_annualized_pct"]:.2f}%' for k in ORDER),fontsize=11.2)
    paths.append(save(fig,'01_income_vs_treasuries',SOURCE+'\nAssumes USDC = $1; no rewards or taxes. Base costs: DeFi $10 + 5 bps per side; SGOV 0.5 bp per side.'))

    fig=plt.figure(figsize=(13,8.3));header(fig,'Small frictions can absorb the extra income',
        'Net extra income versus SGOV · $10,000 initial capital · scenario assumptions, not observed fills','02 / cost sensitivity')
    left=fig.add_axes([.21,.25,.31,.47]);right=fig.add_axes([.65,.25,.31,.47])
    left.set_title('A  Execution-cost scenarios',loc='left',pad=16)
    left.axvline(0,color=NEUTRAL,lw=1);left.grid(axis='x',color=GRID)
    for i,k in enumerate(ORDER):
        sub=costs[(costs['product']==k)&(costs.initial_capital==10000)].set_index('scenario').loc[['High','Base','Low']]
        left.plot(sub.extra_vs_sgov,[i]*3,color=COLORS[k],lw=1.5)
        for sc,marker in [('High','v'),('Base','o'),('Low','s')]:
            x=sub.loc[sc,'extra_vs_sgov'];left.scatter(x,i,s=75,marker=marker,color=COLORS[k],edgecolor=COLORS[k],facecolor=COLORS[k] if sc=='Base' else 'white',zorder=3)
            left.annotate(f'{x:+.0f}',(x,i),xytext=(0,15 if sc!='Base' else -22),textcoords='offset points',ha='center',fontsize=10)
    left.set_yticks(range(3),[SHORT[k] for k in ORDER]);left.set_ylim(2.6,-.6);left.set_xlim(-140,140);money(left,'x');left.set_xlabel('Net extra income ($)')
    from matplotlib.lines import Line2D
    left.legend(handles=[Line2D([],[],ls='',marker=m,color=NEUTRAL,mfc=NEUTRAL if s=='Base' else 'white',label=s) for s,m in [('High','v'),('Base','o'),('Low','s')]],ncol=3,loc='lower center',bbox_to_anchor=(.5,-.38),frameon=False,fontsize=10)
    right.set_title('B  Additional terminal haircut',loc='left',pad=16)
    haircut=pd.read_csv(ROOT/'reports/treasury_haircut_sensitivity.csv')
    for k in ORDER:
        g=haircut[haircut['product']==k]
        right.plot(g.terminal_haircut_pct,g.net_extra_vs_sgov,color=COLORS[k],ls=STYLES[k],lw=2,label=SHORT[k])
        h=result.loc[k,'break_even_terminal_haircut_pct'];right.scatter(h,0,s=35,color=COLORS[k],zorder=3)
    right.axhline(0,color=NEUTRAL,lw=1);right.grid(axis='y',color=GRID);money(right)
    right.set_xlim(0,2);right.set_xlabel('Additional reduction in final\nUSDC value (%)');right.set_ylabel('Net extra income ($)')
    right.text(.04,.08,'Premium erased by a\n0.52–0.76% terminal haircut',transform=right.transAxes,fontsize=11,weight='bold')
    paths.append(save(fig,'02_cost_and_haircut',SOURCE+'\nHaircut is a break-even scenario, not a loss forecast. Full entry/exit cost assumptions are listed in the notebook.'))

    fig=plt.figure(figsize=(13,8.3));header(fig,'Interest earned is not cash available',
        'Historical DeFi withdrawal capacity · existing suppliers · no assumption of new deposits or repayments','03 / liquidity evidence')
    left=fig.add_axes([.085,.25,.38,.47]);right=fig.add_axes([.60,.25,.36,.47])
    left.set_title('A  Capacity for collective withdrawals',loc='left',pad=16)
    x=np.linspace(1,100,100)
    for k in ORDER:
        g=daily[daily['product']==k];y=[100*g.cash_fraction.ge(v/100).mean() for v in x]
        left.plot(x,y,color=COLORS[k],ls=STYLES[k],lw=2,label=SHORT[k])
    left.set_xlim(0,100);left.set_ylim(0,103);left.set_xlabel('Request (% of supplier claims)');left.set_ylabel('Daily snapshots with enough cash (%)');left.grid(axis='y',color=GRID);legend(left)
    right.set_title('B  April 2026 liquidity squeeze',loc='left',pad=16)
    liquidity_zoom(right,daily)
    fig.text(.07,.13,'SGOV has different frictions: market-hours trading, bid/ask spreads and normally T+1 settlement.\nWe do not assign it a fictional 100% on-demand cash buffer.',fontsize=11.3,linespacing=1.5)
    paths.append(save(fig,'03_liquidity_and_stress','Sources: Ethereum reads; Aave rsETH incident report; SEC T+1 guidance. Capacity curve: 867 daily snapshots.\nApril zoom is exploratory. A cash shortfall is not evidence of principal loss; Morpho vaults can share underlying cash.'))

    # Social version: larger typography, two clean panels; methodological detail stays in the linked notebook.
    fig=plt.figure(figsize=(9,12))
    fig.text(.08,.96,'DEFI LENDING × TREASURY BILLS',fontsize=12,color=NEUTRAL,weight='bold')
    fig.text(.08,.912,'How much extra income\nfor the liquidity risk?',fontsize=29,weight='bold',linespacing=1.12,va='top')
    lo=result.loc[ORDER,'extra_vs_sgov'].min();hi=result.loc[ORDER,'extra_vs_sgov'].max()
    fig.text(.08,.815,f'${lo:.0f}–${hi:.0f} extra per $10,000',fontsize=24,weight='bold',color=COLORS['aave'])
    fig.text(.08,.782,'Over 866 days, after illustrative base costs.\nCompared with SGOV, a 0–3 month Treasury-bill ETF.',fontsize=13.5,linespacing=1.5,va='top')
    ax=fig.add_axes([.31,.55,.57,.17])
    for i,k in enumerate(ORDER):
        v=result.loc[k,'extra_vs_sgov'];ax.barh(i,v,color=COLORS[k],height=.48)
        ax.text(v+2,i,f'+${v:.0f}',fontsize=17,weight='bold',va='center')
    ax.set_yticks(range(3),[SHORT[k] for k in ORDER],fontsize=13);ax.invert_yaxis();ax.set_xlim(0,115);ax.set_xticks([0,50,100]);money(ax,'x');ax.grid(axis='x',color=GRID);ax.set_axisbelow(True);ax.set_xlabel('Net extra income vs SGOV',fontsize=12)
    fig.text(.08,.478,'Interest can accrue while cash is hard to withdraw.',fontsize=15,weight='bold')
    ax=fig.add_axes([.13,.185,.77,.24]);liquidity_zoom(ax,daily,compact=True)
    ax.set_title('April 2026 · exploratory liquidity example',fontsize=12,loc='left',pad=10)
    fig.text(.08,.132,'Cash shortage ≠ principal loss. This study does not price all risks.',fontsize=12,weight='bold')
    fig.text(.08,.095,'1 Jun 2024–15 Oct 2026. USDC = $1 assumed; rewards and taxes excluded.\nCosts per side: DeFi $10 + 5 bps; SGOV 0.5 bp. Fund/vault fees already reflected.\nSources: Ethereum contract reads · iShares SGOV · Aave incident report.',fontsize=9.8,color=NEUTRAL,linespacing=1.65,va='top')
    fig.text(.08,.025,'Reproduce: github.com/fredLuv/defi-lending-research',fontsize=9.3,color=COLORS['aave'],url=LINK)
    for ext in ['png','pdf','svg']:fig.savefig(FIG/f'linkedin_treasury_comparison.{ext}',dpi=200)
    plt.close(fig);paths.append(FIG/'linkedin_treasury_comparison.png')
    (ROOT/'reports/treasury_figure_manifest.json').write_text(json.dumps({'figures':[str(p.relative_to(ROOT)) for p in paths],
        'source_manifest':'data/treasury_manifest.json','cost_scenario':'Base','return_currency_assumption':'1 USDC = 1 USD'},indent=2)+'\n')
    return paths


if __name__=='__main__':
    for p in build():print(p)
