import math
from fractions import Fraction
import numpy as np
from analyse import load_panel, summarize, NAMES, raw_values
from collect import RAW, load, accrued_market

def test_integer_accrual_and_reconciliation():
    # Validate against exact rational arithmetic, and preserve cash when interest accrues.
    for p in sorted((RAW/'states').glob('*.json.gz'))[::23]:
        s=load(p);v=raw_values(s);bt=int(s['block']['timestamp'],16)
        for key,m in v.items():
            if not key.endswith('_market'):continue
            mid=key[:-7];rate=v.get(mid,0);sa,ss,ba,bs,last,fee=m
            a,b,c=accrued_market(m,rate,bt)[:3]
            assert a-c==sa-ba
            if ba and rate and bt>last:
                x=rate*(bt-last);second=int(Fraction(x*x,2*10**18));third=int(Fraction(second*x,3*10**18))
                expected=int(Fraction(ba*(x+second+third),10**18))
                assert a-sa==expected

def test_panel_alignment_and_metrics():
    panel,daily,prices=load_panel();s,events,stress=summarize(panel,daily,prices)
    assert panel.groupby('timestamp').block.nunique().eq(1).all()
    for k,g in daily.groupby('product'):
        growth=g['index'].iloc[-1]/g['index'].iloc[0]
        assert math.isclose((growth-1)*10000,s.loc[k,'interest_per_10000'],abs_tol=1e-8)
        assert (g.capacity_usdc<=g.claims_usdc).all()
        assert all(np.diff([(g.cash_fraction>=x).mean() for x in np.linspace(0,1,101)])<=0)
        assert s.loc[k,'capacity_below_10000_count']<=s.loc[k,'capacity_below_100000_count']<=s.loc[k,'capacity_below_1000000_count']
    assert stress.groupby('product').n.sum().eq(866).all()
    assert events.groupby(['event','product']).samples.sum().eq(41).all()
    assert daily.groupby('timestamp').size().eq(3).all()

def test_static_withdrawal_arithmetic():
    # Capacity is finite shared cash, not an individual entitlement or a default probability.
    capacity=20;claims=100
    assert min(1,capacity/(.1*claims))==1
    assert min(1,capacity/(.5*claims))==.4
    remaining=max(0,capacity-15)
    assert min(1,remaining/10)==.5
