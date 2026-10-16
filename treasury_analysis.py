"""Matched Treasury ETF total returns, transparent execution costs and sensitivities."""
import json
import math
from decimal import Decimal, localcontext
import numpy as np
import pandas as pd
from collect import ROOT, sha, START, END
from analyse import load_panel, NAMES

SCENARIOS={
    'Low': {'defi_fixed':5.,'defi_bps':0.,'sgov_bps':.5},
    'Base':{'defi_fixed':10.,'defi_bps':5.,'sgov_bps':.5},
    'High':{'defi_fixed':50.,'defi_bps':25.,'sgov_bps':2.5},
}
LABELS={'sgov':'Treasury bills · SGOV',**NAMES}


def net_balance(capital, gross_multiple, product, scenario='Base', terminal_haircut=0.):
    costs=SCENARIOS[scenario]
    fixed=0. if product=='sgov' else costs['defi_fixed']
    spread=(costs['sgov_bps'] if product=='sgov' else costs['defi_bps'])/10000
    # Both sides' percentage fees operate on exchanged amounts. Entry fixed cost
    # is paid from the starting capital; exit fixed cost is deducted only at exit.
    invested=(capital-fixed)*(1-spread)
    return invested*gross_multiple*(1-terminal_haircut)*(1-spread)-fixed


def sgov_history():
    manifest=json.loads((ROOT/'data/treasury_manifest.json').read_text())
    assert sha(ROOT/'docs/TREASURY_COMPARISON.md')==manifest['protocol_sha256']
    for item in manifest['files']:
        assert sha(ROOT/item['path'])==item['sha256']
    raw=json.loads((ROOT/'data/raw/treasury/sgov.json').read_text())
    nav=pd.DataFrame(raw['historical']).sort_values('date')
    nav['date']=pd.to_datetime(nav.date)
    for col in ['nav','ex_distribution']:
        nav[col]=pd.to_numeric(nav[col])
    assert not nav.date.duplicated().any() and nav.nav.gt(0).all()
    assert nav.date.iloc[0]<=pd.Timestamp('2024-05-31') and nav.date.iloc[-1]==pd.Timestamp('2026-10-14')
    dist=pd.DataFrame(raw['distributions']);dist['ex_date']=pd.to_datetime(dist.ex_date)
    dist['distribution']=pd.to_numeric(dist.distribution)
    check=nav[nav.ex_distribution.ne(0)].merge(dist,left_on='date',right_on='ex_date',validate='one_to_one')
    assert len(check)==len(dist)==nav.ex_distribution.ne(0).sum()
    assert np.allclose(check.ex_distribution,check.distribution,rtol=0,atol=1e-10)
    nav['gross_factor']=(nav.nav+nav.ex_distribution)/nav.nav.shift(1)
    nav['total_return_index']=nav.gross_factor.fillna(1).cumprod()
    # Conservative publication convention: all issuer observations become available
    # at 4pm New York, including any shortened trading sessions.
    nav['valuation_utc']=(nav.date+pd.Timedelta(hours=16)).dt.tz_localize('America/New_York').dt.tz_convert('UTC').astype('datetime64[ns, UTC]')
    monthly=[]
    for row in raw['monthly_published_returns']:
        end=pd.Timestamp(row['month_end']);start=end.replace(day=1)
        prior=nav[nav.date<start].iloc[-1].total_return_index
        last=nav[nav.date<=end].iloc[-1].total_return_index
        computed=100*(last/prior-1)
        monthly.append({**row,'reconstructed_pct':computed,'difference_pp':computed-row['nav_total_return_pct']})
    monthly=pd.DataFrame(monthly)
    assert len(monthly)==28
    # Allow 0.001 percentage points for reconstruction / published-convention differences.
    assert monthly.difference_pp.abs().max()<.001,monthly.to_string()
    monthly.to_csv(ROOT/'reports/treasury_monthly_checks.csv',index=False)
    nav.to_csv(ROOT/'data/processed/sgov_nav.csv',index=False)
    return nav,monthly


def compare():
    panel,daily,eth=load_panel()
    nav,checks=sgov_history()
    anchors=daily[daily['product']=='aave'][['timestamp','date']].sort_values('date')
    anchors['date']=anchors.date.astype('datetime64[ns, UTC]')
    aligned=pd.merge_asof(anchors,nav[['date','valuation_utc','total_return_index']].rename(columns={'date':'nav_date'}),
                          left_on='date',right_on='valuation_utc',direction='backward')
    assert aligned.total_return_index.notna().all() and (aligned.valuation_utc<=aligned.date).all()
    assert aligned.nav_date.iloc[0]==pd.Timestamp('2024-05-31')
    assert aligned.nav_date.iloc[-1]==pd.Timestamp('2026-10-14')
    aligned['sgov_multiple']=aligned.total_return_index/aligned.total_return_index.iloc[0]
    years=(pd.Timestamp(END)-pd.Timestamp(START)).days/365
    assert (pd.Timestamp(END)-pd.Timestamp(START)).days==866
    joined=daily.merge(aligned[['timestamp','nav_date','valuation_utc','sgov_multiple']],on='timestamp',validate='many_to_one')
    joined['gross_multiple']=joined.balance_10000/10000
    joined['gross_extra_vs_sgov']=10000*(joined.gross_multiple-joined.sgov_multiple)
    # Independent high-precision daily product; endpoint includes all distributions.
    with localcontext() as ctx:
        ctx.prec=40
        relevant=nav[nav.date.ge('2024-05-31')]
        product=Decimal(1)
        for prev,cur in zip(relevant.iloc[:-1].itertuples(),relevant.iloc[1:].itertuples()):
            product*= (Decimal(str(cur.nav))+Decimal(str(cur.ex_distribution)))/Decimal(str(prev.nav))
        assert math.isclose(float(product),aligned.sgov_multiple.iloc[-1],rel_tol=1e-12)
    multiples={'sgov':aligned.sgov_multiple.iloc[-1]}
    multiples.update(joined.groupby('product').gross_multiple.last().to_dict())
    rows=[];sensitivity=[]
    for scenario in SCENARIOS:
        for capital in [1000,10000,100000]:
            treasury=net_balance(capital,multiples['sgov'],'sgov',scenario)
            for key,multiple in multiples.items():
                final=net_balance(capital,multiple,key,scenario)
                # Exact additional terminal conversion haircut which removes positive premium.
                fixed=0 if key=='sgov' else SCENARIOS[scenario]['defi_fixed']
                break_even=(final-treasury)/(final+fixed)
                sensitivity.append({'product':key,'scenario':scenario,'initial_capital':capital,
                    'net_final':final,'net_profit':final-capital,'extra_vs_sgov':final-treasury,
                    'net_annualized_pct':100*((final/capital)**(1/years)-1),
                    'excess_annualized_pp':100*((final/capital)**(1/years)-(treasury/capital)**(1/years)),
                    'break_even_terminal_haircut_pct':100*break_even})
    costs=pd.DataFrame(sensitivity)
    for key,multiple in multiples.items():
        r=costs[(costs['product']==key)&(costs.scenario=='Base')&(costs.initial_capital==10000)].iloc[0]
        rows.append({'product':key,'name':LABELS[key],'gross_multiple':multiple,
                     'gross_profit':10000*(multiple-1),'gross_annualized_pct':100*(multiple**(1/years)-1),
                     'base_execution_cost_drag':10000*multiple-r.net_final,**r.to_dict()})
    result=pd.DataFrame(rows).set_index('product')
    haircut=[]
    for h in np.linspace(0,.02,201):
        for key in NAMES:
            haircut.append({'product':key,'terminal_haircut_pct':100*h,
                'net_extra_vs_sgov':net_balance(10000,multiples[key],key,'Base',h)-net_balance(10000,multiples['sgov'],'sgov','Base')})
    pd.DataFrame(haircut).to_csv(ROOT/'reports/treasury_haircut_sensitivity.csv',index=False)
    result.to_csv(ROOT/'reports/treasury_comparison.csv')
    costs.to_csv(ROOT/'reports/treasury_cost_sensitivity.csv',index=False)
    joined.to_csv(ROOT/'data/processed/treasury_comparison.csv',index=False)
    aligned.to_csv(ROOT/'data/processed/sgov_aligned.csv',index=False)
    (ROOT/'reports/treasury_checks.json').write_text(json.dumps({
        'daily_anchors':len(aligned),'first_nav_date':str(aligned.nav_date.iloc[0].date()),
        'last_nav_date':str(aligned.nav_date.iloc[-1].date()),'monthly_checks':len(checks),
        'max_monthly_difference_pp':checks.difference_pp.abs().max(),'independent_decimal_multiple':str(product),
        'no_future_valuations':True,'usdc_usd_assumption':1,'years':years},indent=2)+'\n')
    return result,costs,joined,aligned,panel,daily,eth


if __name__=='__main__':
    print(compare()[0].to_string())
