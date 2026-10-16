"""Offline, checksum-verified current quotes and constant-rate cost scenarios."""
import hashlib
import json
from decimal import Decimal, localcontext
from pathlib import Path
import numpy as np
import pandas as pd
from collect_current import VAULTS, USDC

ROOT=Path(__file__).resolve().parent
ORDER=['aave_v4','steakhouse_v2','gauntlet_v2','sgov']
NAMES={'aave_v4':'Aave V4 · Main','steakhouse_v2':'Morpho V2 · Steakhouse Prime',
       'gauntlet_v2':'Morpho V2 · Gauntlet Prime','sgov':'SGOV · Treasury ETF'}
SCENARIOS={'Low':(5,0,.00005),'Base':(10,.0005,.00005),'High':(50,.0025,.00025)}

def net_balance(capital, rate, days, fixed, spread):
    assert capital>2*fixed and rate>-1 and 0<=spread<1 and days>0
    return (capital-fixed)*(1-spread)*(1+rate)**(days/365)*(1-spread)-fixed

def load():
    manifest=json.loads((ROOT/'data/current_manifest.json').read_text())
    for name,digest in manifest['inputs'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, name
    def raw(name): return json.loads((ROOT/f'data/raw/current/{name}.json').read_text())
    def body(name): return raw(name)['response']['data']
    a=body('aave_v4')['reserves']
    a=[r for r in a if r['chain']['chainId']==1 and r['asset']['underlying']['address'].lower()==USDC
       and r['spoke']['address'].lower()=='0x94e7a5dcbe816e498b89ab752661904e2f56c485']
    assert len(a)==1
    a=a[0];asset=a['asset'];summary=asset['summary']
    assert a['spoke']['name']=='Main' and asset['hub']['name']=='Core'
    assert asset['hub']['address'].lower()=='0xcca852bc40e560adc3b1cc58ca5b55638ce826c9'
    assert asset['underlying']['info']=={'symbol':'USDC','decimals':6}
    assert a['status']['active'] and not a['status']['paused']
    rate=float(a['summary']['supplyApy']['value'])
    assert np.isclose(rate*100,float(a['summary']['supplyApy']['normalized']))
    rows=[dict(product='aave_v4',name=NAMES['aave_v4'],quote_rate=rate,effective_scenario_rate=rate,
        convention='Variable supply APY',lookback_30d_apy=None,
        source_as_of=raw('aave_v4')['retrieved_utc'],indexed_block=None,
        address=a['spoke']['address'],available_usdc=float(summary['availableLiquidity']['amount']['value']),
        denominator_usdc=float(summary['supplied']['amount']['value']),
        denominator_scope='Core Hub total supply; shared across Spokes',idle_usdc=None,
        main_supply_usdc=float(a['summary']['supplied']['amount']['value']),
        capacity_scope='Core Hub available liquidity, not reserved for Main or one wallet')]
    directory=body('morpho_v2_directory')
    for key,address in VAULTS.items():
        selected=[x for x in directory if x['vault_address'].lower()==address.lower()]
        assert len(selected)==1
        info=selected[0]
        assert info['version']=='2.0' and info['chain_id']==1 and info['asset_address'].lower()==USDC
        state=body(key+'_state');short=body(key+'_six_hours');long=body(key+'_thirty_days')
        for obj in [state,short,long]:
            assert obj['chain_id']==1
            assert obj.get('address',obj.get('vault_address')).lower()==address.lower()
        assert short['lookback']=='six_hours' and long['lookback']=='thirty_days'
        # Endpoint snapshots are not atomic. Preserve each exact block in raw data.
        rows.append(dict(product=key,name=NAMES[key],quote_rate=float(short['apy']),
            effective_scenario_rate=float(short['apy']),convention='6-hour realized post-fee APY',
            lookback_30d_apy=float(long['apy']),source_as_of=raw(key+'_six_hours')['retrieved_utc'],
            indexed_block=int(state['last_indexed_block']),address=address,
            available_usdc=int(state['withdrawable_assets'])/1e6,
            denominator_usdc=int(state['total_assets'])/1e6,idle_usdc=int(state['idle_assets'])/1e6,
            main_supply_usdc=None,denominator_scope='Selected vault total assets',
            capacity_scope='API-reported withdrawable assets; execution not simulated'))
    sg=raw('sgov_quote');sec=sg['fields']['sec_yield']
    assert sec['value']>=0
    rows.append(dict(product='sgov',name=NAMES['sgov'],quote_rate=sec['value'],
        effective_scenario_rate=(1+sec['value']/2)**2-1,convention='30-day SEC yield (not APY)',
        lookback_30d_apy=None,source_as_of=sec['as_of'],indexed_block=None,address=None,
        available_usdc=None,denominator_usdc=None,idle_usdc=None,main_supply_usdc=None,
        denominator_scope='Not comparable to on-chain available cash',
        capacity_scope='Exchange-hours sale; bid/ask spread; ordinary T+1 settlement'))
    rates=pd.DataFrame(rows).set_index('product').loc[ORDER]
    rates['cash_fraction']=rates.available_usdc/rates.denominator_usdc
    assert np.isfinite(rates.quote_rate).all() and (rates.quote_rate>-1).all()
    assert (rates.loc[ORDER[:-1],'available_usdc']>=0).all()
    assert rates.loc[ORDER[:-1],'cash_fraction'].between(0,1).all()
    # Conservative stale-vintage guard: issuer quote must be within seven days.
    assert 0 <= (pd.Timestamp(manifest['finished_utc']).date()-pd.Timestamp(sec['as_of']).date()).days <= 7
    scenarios=[]
    for capital in [1000,10000,100000]:
        for days in [30,90,365]:
            for scenario,(fixed,spread,sg_spread) in SCENARIOS.items():
                sg_net=net_balance(capital,rates.loc['sgov','effective_scenario_rate'],days,0,sg_spread)
                for key,row in rates.iterrows():
                    f,s=(0,sg_spread) if key=='sgov' else (fixed,spread)
                    end=net_balance(capital,row.effective_scenario_rate,days,f,s)
                    # Independent high-precision evaluation of growth and two-sided costs.
                    with localcontext() as ctx:
                        ctx.prec=40
                        c,r,d,ff,ss=map(lambda x:Decimal(str(x)),[capital,row.effective_scenario_rate,days,f,s])
                        check=(c-ff)*(1-ss)*((1+r).ln()*d/Decimal(365)).exp()*(1-ss)-ff
                    assert abs(end-float(check))<1e-8
                    scenarios.append(dict(product=key,capital=capital,days=days,scenario=scenario,
                        fixed_each_side=f,spread_each_side=s,net_final=end,net_profit=end-capital,
                        extra_vs_sgov=end-sg_net,rate_held_constant=row.effective_scenario_rate))
    return rates,pd.DataFrame(scenarios),manifest

def build():
    rates,costs,manifest=load();reports=ROOT/'reports';reports.mkdir(exist_ok=True)
    rates.to_csv(reports/'current_rates.csv')
    costs.to_csv(reports/'current_scenarios.csv',index=False)
    checks={'snapshot_started_utc':manifest['started_utc'],'snapshot_finished_utc':manifest['finished_utc'],
        'sha256_verified_files':len(manifest['inputs']),'independently_verified_scenarios':len(costs),
        'identities':'Exact Ethereum contracts and native USDC; no V3/V1 substitution',
        'observed_transaction_costs':False,'guaranteed_withdrawals':False,
        'forward_return_forecast':False}
    (reports/'current_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    return rates,costs,manifest

if __name__=='__main__':
    r,c,m=build();print(r[['quote_rate','lookback_30d_apy','available_usdc','denominator_usdc','cash_fraction']].to_string())
    print(c.query("capital==10000 and scenario=='Base'").pivot(index='product',columns='days',values='extra_vs_sgov').to_string())
