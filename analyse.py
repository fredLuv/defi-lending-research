"""Offline accounting, quality checks, and figures for the frozen USDC study."""
from pathlib import Path
import json, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import PercentFormatter, FuncFormatter
from eth_abi import decode
from collect import ROOT, RAW, VAULTS, EVENTS, START, END, stamp, timestamps, load, sha, accrued_market

NAMES={'aave':'Aave V3 Core','steakhouse_v1':'Morpho · Steakhouse V1','gauntlet_v1':'Morpho · Gauntlet Prime V1'}
COLORS={'aave':'#3476A8','steakhouse_v1':'#C87936','gauntlet_v1':'#8E4D20'}
STYLES={'aave':'-','steakhouse_v1':'--','gauntlet_v1':':'}
FIG=ROOT/'figures';REPORT=ROOT/'reports';PROCESSED=ROOT/'data/processed'
for p in [FIG,REPORT,PROCESSED]:p.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,'axes.labelsize':11,
                     'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#92979E',
                     'text.color':'#262D35','axes.labelcolor':'#262D35','xtick.color':'#46515C',
                     'ytick.color':'#46515C','figure.facecolor':'white','axes.facecolor':'white',
                     'axes.grid':True,'grid.color':'#E9EBED','grid.linewidth':0.6,'lines.linewidth':1.8})


def raw_values(snapshot):
    out={}
    for c in snapshot['calls']:
        x=decode(c['output_types'],bytes.fromhex(c['result'][2:]))
        out[c['key']]=x[0] if len(x)==1 else list(x)
    return out


def load_panel():
    manifest=load(ROOT/'data/manifest.json')
    for f in manifest['files']:
        assert sha(ROOT/f['path'])==f['sha256'],f['path']
    assert sha(ROOT/'docs/PROTOCOL.md')==manifest['protocol_sha256']
    rows=[];checks=[]
    for p in sorted((RAW/'states').glob('*.json.gz')):
        s=load(p);b=raw_values(s);ts=s['anchor_timestamp'];bt=int(s['block']['timestamp'],16)
        assert bt<=ts<int(s['next_block']['timestamp'],16)
        assert s['next_block']['parentHash']==s['block']['hash']
        for k,stored in s['products'].items():
            if k=='aave':
                claims=b['aave_claims'];capacity=min(claims,b['aave_cash']);index=b['aave_index']
                if not ((b['aave_config']>>56)&1) or (b['aave_config']>>60)&1:capacity=0
            else:
                index=b[k+'_price'];claims=b[k+'_assets'];alloc=[]
                for i in range(b[k+'_queue_length']):
                    mid=b[f'{k}_{i}'].hex()
                    sa,ss,ba,_=accrued_market(b[mid+'_market'],b.get(mid,0),bt)
                    asset_claim=b[mid+'_'+k][0]*(sa+1)//(ss+10**6)
                    alloc.append((asset_claim,min(asset_claim,sa-ba)))
                assert sum(a for a,c in alloc)==claims,(k,ts,'totalAssets mismatch')
                capacity=min(claims,b['morpho_cash'],sum(c for a,c in alloc))
                checks.append({'timestamp':ts,'product':k,'reconciliation_micro_usdc':sum(a for a,c in alloc)-claims})
            assert str(index)==stored['index'] and capacity==int(stored['capacity_units'])
            assert claims>0 and index>0 and 0<=capacity<=claims
            rows.append({'timestamp':ts,'date':pd.to_datetime(ts,unit='s',utc=True),'block':int(s['block']['number'],16),
                         'block_timestamp':bt,'block_hash':s['block']['hash'],'product':k,'index':float(index),
                         'claims_usdc':claims/1e6,'capacity_usdc':capacity/1e6,'cash_fraction':capacity/claims,
                         'raw_file':str(p.relative_to(ROOT)),'raw_sha256':sha(p)})
    panel=pd.DataFrame(rows).sort_values(['date','product']).reset_index(drop=True)
    assert set(panel.timestamp.unique())==set(timestamps()),'Missing or unexpected states; do not silently shrink the sample.'
    assert not panel.duplicated(['timestamp','product']).any()
    assert (panel.groupby('timestamp').size()==3).all()
    daily=panel[panel.timestamp%86400==0].copy()
    assert daily.groupby('product').size().nunique()==1
    for k in NAMES:
        idx=daily.index[daily['product']==k];values=daily.loc[idx,'index']
        daily.loc[idx,'balance_10000']=values/values.iloc[0]*10000
        daily.loc[idx,'interest_10000']=daily.loc[idx,'balance_10000']-10000
        daily.loc[idx,'return_1d']=values.pct_change(fill_method=None)
        seconds=daily.loc[idx,'block_timestamp'].diff(30)
        daily.loc[idx,'trailing30_annualized']=(values/values.shift(30))**(31536000/seconds)-1
    candles=[]
    for p in sorted((RAW/'prices').glob('*.json.gz')):
        candles.extend(load(p)['data'])
    prices=pd.DataFrame(candles,columns=['timestamp','low','high','open','close','volume']).sort_values('timestamp')
    # Coinbase can include boundary candles in neighboring requests; require identical duplicated values.
    assert (prices.groupby('timestamp')['close'].nunique()==1).all()
    prices=prices.drop_duplicates('timestamp').set_index('timestamp')
    prices['date']=pd.to_datetime(prices.index,unit='s',utc=True)
    prices['return_1d']=prices['close'].pct_change(fill_method=None)
    prices['close_timestamp']=prices.index+86400
    prices=prices[prices.close_timestamp<=stamp(END)]
    needed=set(range(stamp(START)-86400,stamp(END),86400))
    assert needed.issubset(prices.index),'Missing ETH candles'
    pd.DataFrame(checks).to_csv(REPORT/'accounting_checks.csv',index=False)
    panel.to_csv(PROCESSED/'intraday_panel.csv',index=False);daily.to_csv(PROCESSED/'daily_panel.csv',index=False)
    prices.to_csv(PROCESSED/'eth_candles.csv')
    return panel,daily,prices


def summarize(panel,daily,prices):
    rows=[]
    for k,g in daily.groupby('product',sort=False):
        g=g.sort_values('timestamp');ratio=g['index'].iloc[-1]/g['index'].iloc[0]
        years=(g.block_timestamp.iloc[-1]-g.block_timestamp.iloc[0])/31536000
        # Independent log-return reconstruction of the endpoint return.
        assert math.isclose(math.exp(np.log(g['index']).diff().dropna().sum()),ratio,rel_tol=1e-12)
        row={'product':k,'name':NAMES[k],'annualized_return_pct':100*(ratio**(1/years)-1),
             'total_return_pct':100*(ratio-1),'interest_per_10000':10000*(ratio-1),
             'liquidity_median_pct':100*g.cash_fraction.median(),'liquidity_min_pct':100*g.cash_fraction.min(),
             'liquidity_p05_pct':100*g.cash_fraction.quantile(.05),'minimum_capacity_usdc':g.capacity_usdc.min(),
             'daily_observations':len(g),'negative_daily_index_changes':int((g.return_1d< -1e-12).sum())}
        for size in [10000,100000,1000000]:row[f'capacity_below_{size}_count']=int((g.capacity_usdc<size).sum())
        for f in [.05,.1,.25,.5]:row[f'shortfall_{int(f*100)}pct_days']=int((g.cash_fraction<f).sum())
        rows.append(row)
    summary=pd.DataFrame(rows).set_index('product').loc[list(NAMES)]
    summary['extra_interest_vs_aave']=summary.interest_per_10000-summary.loc['aave','interest_per_10000']
    summary['terminal_haircut_erasing_premium_pct']=100*summary.extra_interest_vs_aave/(10000+summary.interest_per_10000)
    summary.to_csv(REPORT/'summary.csv')
    events=[]
    for date,label in EVENTS.items():
        t=stamp(date);p=panel[(panel.timestamp>=t-3*86400)&(panel.timestamp<=t+7*86400)]
        eth=prices[(prices.index>=t-3*86400)&(prices.index<t+7*86400)]
        for k,g in p.groupby('product'):
            start=g.sort_values('timestamp').iloc[0];worst=g.loc[g.cash_fraction.idxmin()]
            events.append({'event':label,'event_date':date,'product':k,'samples':len(g),
                           'initial_liquidity_pct':start.cash_fraction*100,'minimum_liquidity_pct':worst.cash_fraction*100,
                           'min_liquidity_time':worst.date.isoformat(),'minimum_capacity_usdc':g.capacity_usdc.min(),
                           'minimum_daily_eth_return_pct':eth.return_1d.min()*100,
                           'shortfall_25pct_count':int((g.cash_fraction<.25).sum())})
    events=pd.DataFrame(events);events.to_csv(REPORT/'stress_windows.csv',index=False)
    # Pair the close-to-close market return for day D with capacity at D+1 midnight.
    # No future return is attached to the START-of-day capacity.
    stress_dates=set(prices.loc[prices.return_1d<=-.07,'close_timestamp'].astype(int))
    stress=[]
    covered_dates=set(prices.loc[prices.return_1d.notna(),'close_timestamp'].astype(int))
    for k,g in daily.groupby('product'):
        g=g[g.timestamp.isin(covered_dates)]  # exclude the initial anchor without a prior close-to-close return
        for name,mask in [('ETH daily decline >=7%',g.timestamp.isin(stress_dates)),('Other days',~g.timestamp.isin(stress_dates))]:
            v=g[mask]
            stress.append({'product':k,'regime':name,'n':len(v),'median_capacity_pct':100*v.cash_fraction.median(),
                           'below_25pct_count':int((v.cash_fraction<.25).sum())})
    stress=pd.DataFrame(stress);stress.to_csv(REPORT/'all_stress_days.csv',index=False)
    return summary,events,stress


def finish(fig,name,source,top=.80,bottom=.15):
    fig.subplots_adjust(left=.095,right=.98,top=top,bottom=bottom,hspace=.40,wspace=.22)
    fig.text(.095,.035,source,fontsize=8.2,color='#56616D',va='bottom')
    fig.text(.095,.006,'Data sources and exact contracts →',fontsize=8,color='#3476A8',url='https://github.com/fredLuv/defi-lending-research/blob/main/docs/DATA_SOURCES.md')
    for ext in ['png','svg','pdf']:fig.savefig(FIG/f'{name}.{ext}',dpi=170,facecolor='white')
    plt.close(fig)
    return FIG/f'{name}.png'

def legend(fig):
    from matplotlib.lines import Line2D
    handles=[Line2D([0],[0],color=COLORS[k],ls=STYLES[k],label=NAMES[k]) for k in NAMES]
    fig.legend(handles=handles,loc='upper left',bbox_to_anchor=(.09,.895),ncol=3,frameon=False,fontsize=10)

def dates(ax):
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4,maxticks=7))
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))

def build_figures(panel,daily,prices,summary):
    paths=[]
    source='Source: Ethereum archive contract reads via dRPC; exact blocks and raw-response hashes in data/manifest.json.\nNative USDC accounting return; vault fees included, token rewards/gas/taxes excluded. USDC is not guaranteed USD.'
    fig,axs=plt.subplots(2,1,figsize=(11.8,8.4),sharex=True)
    fig.suptitle('Earned native USDC yield',x=.095,ha='left',y=.985,fontsize=19,fontweight='bold')
    fig.text(.095,.93,'Same starting capital and dates · 1 June 2024–15 October 2026 (UTC)',fontsize=11,va='top')
    legend(fig)
    for k in NAMES:
        g=daily[daily['product']==k]
        axs[0].plot(g.date,g.interest_10000,color=COLORS[k],ls=STYLES[k])
        axs[1].plot(g.date,g.trailing30_annualized*100,color=COLORS[k],ls=STYLES[k])
    axs[0].set_ylabel('Interest on 10,000 USDC');axs[0].set_ylim(bottom=0)
    axs[0].set_title('Cumulative interest from supply-index / vault-share value',loc='left',fontsize=11)
    axs[1].set_title('Trailing 30-day return, annualized — not a forward APY quote',loc='left',fontsize=11)
    axs[1].set_ylabel('Annualized return (%)');axs[1].set_ylim(bottom=min(0,axs[1].get_ylim()[0]));dates(axs[1])
    paths.append(finish(fig,'01_native_yield',source,bottom=.15))

    fig,axs=plt.subplots(2,1,figsize=(11.8,8.4),sharex=True)
    fig.suptitle('Cash available for withdrawals',x=.095,ha='left',y=.985,fontsize=19,fontweight='bold')
    fig.text(.095,.93,'Daily block snapshots · capacity is shared by depositors, not reserved per wallet',fontsize=11,va='top')
    legend(fig)
    for k in NAMES:
        g=daily[daily['product']==k]
        axs[0].plot(g.date,g.cash_fraction*100,color=COLORS[k],ls=STYLES[k])
        axs[1].plot(g.date,g.capacity_usdc/1e6,color=COLORS[k],ls=STYLES[k])
    axs[0].set_ylabel('Capacity / supplier claims (%)');axs[0].set_ylim(0,103)
    axs[0].axhline(25,color='#737B83',ls='--',lw=1);axs[0].text(daily.date.iloc[0],26,'25% collective withdrawal',fontsize=8,color='#5B6269')
    axs[1].set_ylabel('Available USDC (millions)');axs[1].set_yscale('log');axs[1].set_title('Absolute capacity · logarithmic scale',loc='left',fontsize=11);dates(axs[1])
    paths.append(finish(fig,'02_withdrawal_liquidity','Source: same-block Ethereum reads; Aave reserve cash and Morpho historical withdrawal queues.\nStatic cash capacity, not observed failed withdrawals. Different Morpho vaults can compete for the same underlying cash.'))

    fig,axs=plt.subplots(2,3,figsize=(13,8.0),sharey='row')
    fig.suptitle('Withdrawal capacity around market sell-offs',x=.075,ha='left',y=.985,fontsize=19,fontweight='bold')
    fig.text(.075,.93,'Six-hour protocol snapshots · fixed windows, three days before to seven days after',fontsize=11,va='top')
    legend(fig)
    for c,(date,label) in enumerate(EVENTS.items()):
        t=stamp(date);p=panel[(panel.timestamp>=t-3*86400)&(panel.timestamp<=t+7*86400)]
        eth=prices[(prices.index>=t-3*86400)&(prices.index<t+7*86400)]
        x=(eth.close_timestamp-t)/86400
        axs[0,c].plot(x,eth.close/eth.close.iloc[0]*100,color='#57636F')
        axs[0,c].set_title(label+'\n'+date,fontsize=11)
        for k in NAMES:
            g=p[p['product']==k]
            axs[1,c].plot((g.timestamp-t)/86400,g.cash_fraction*100,color=COLORS[k],ls=STYLES[k])
        for ax in axs[:,c]:ax.axvline(0,color='#8B9198',lw=.9,ls='--');ax.set_xlim(-3,7)
        axs[1,c].set_xlabel('Days from event date (UTC)');axs[1,c].set_ylim(0,103)
    axs[0,0].set_ylabel('ETH close (first close = 100)');axs[1,0].set_ylabel('Withdrawal capacity / claims (%)')
    paths.append(finish(fig,'03_stress_windows','Sources: Ethereum archive contract reads and Coinbase Exchange ETH/USD daily candles.\nETH points are placed at candle CLOSE time. Market sell-offs need not produce a lender liquidity squeeze; snapshots can miss intraday troughs.',top=.77))

    fig,ax=plt.subplots(figsize=(11.8,6.6))
    fig.suptitle('How often was cash sufficient for a collective withdrawal?',x=.095,ha='left',y=.98,fontsize=18,fontweight='bold')
    fig.text(.095,.90,'Historical frequency of enough cash · daily observations weighted equally',fontsize=11)
    x=np.linspace(1,100,100)
    for k in NAMES:
        g=daily[daily['product']==k]
        y=[100*(g.cash_fraction>=v/100).mean() for v in x]
        ax.plot(x,y,color=COLORS[k],ls=STYLES[k],label=NAMES[k])
    ax.set_xlim(0,100);ax.set_ylim(0,103);ax.set_xlabel('Requested withdrawal (% of all supplier claims)');ax.set_ylabel('Snapshots with enough cash (%)')
    ax.legend(frameon=False,loc='upper right',fontsize=10)
    paths.append(finish(fig,'04_withdrawal_capacity_curve','Source: same-block Ethereum reads, 1 June 2024–15 October 2026 UTC.\nNo new deposits, repayments or competing withdrawals. This historical coverage curve is NOT a forecast default probability.',top=.80,bottom=.18))
    # Exploratory diagnostic: chosen after locating the full-panel Aave minimum.
    fig,ax=plt.subplots(figsize=(11.8,6.6))
    fig.suptitle('April 2026: a USDC withdrawal-liquidity squeeze',x=.095,ha='left',y=.98,fontsize=18,fontweight='bold')
    fig.text(.095,.90,'Exploratory zoom chosen after finding the full-sample minimum · daily snapshots',fontsize=11)
    for k in NAMES:
        g=daily[(daily['product']==k)&(daily.date>=pd.Timestamp('2026-04-15',tz='UTC'))&(daily.date<=pd.Timestamp('2026-05-01',tz='UTC'))]
        ax.plot(g.date,g.capacity_usdc,color=COLORS[k],ls=STYLES[k],marker='o',ms=3,label=NAMES[k])
    low=daily[daily['product']=='aave'].loc[lambda x:x.capacity_usdc.idxmin()]
    ax.annotate(f'{low.capacity_usdc:,.0f} USDC'+chr(10)+'21 Apr, 00:00 UTC',xy=(low.date,low.capacity_usdc),
                xytext=(35,28),textcoords='offset points',fontsize=10,arrowprops={'arrowstyle':'-','color':'#57636F'})
    ax.axvline(pd.Timestamp('2026-04-18 17:35',tz='UTC'),color='#737B83',ls='--',lw=1)
    ax.set_yscale('log');ax.set_ylabel('Available USDC (logarithmic scale)');dates(ax)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v/1e6:g}m' if v>=1e6 else f'{v/1e3:g}k'))
    ax.legend(frameon=False,loc='upper right',fontsize=10)
    paths.append(finish(fig,'05_april_2026_liquidity','Sources: Ethereum contract reads; minimum cross-checked through dRPC and 1RPC at block 24,924,560.\nDashed vertical line: rsETH incident time from Aave governance report. Cash shortfall is distinct from a realized USDC principal loss.',top=.80,bottom=.18))
    return paths


def render_all():
    panel,daily,prices=load_panel();summary,events,stress=summarize(panel,daily,prices)
    paths=build_figures(panel,daily,prices,summary)
    return panel,daily,prices,summary,events,stress,paths
if __name__=='__main__':
    _,_,_,s,e,_,_=render_all();print(s.round(3).to_string());print(e.round(3).to_string(index=False))
