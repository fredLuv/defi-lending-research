"""Checks the new comparison's consequential accounting and timing assumptions."""
import math
import numpy as np
from treasury_analysis import compare, net_balance, SCENARIOS


def test_entry_exit_costs_and_break_even():
    # Hand-calculated case: ($1000-$10)*.9995*1.10*.9995-$10.
    expected=(1000-10)*(1-5/10000)*1.10*(1-5/10000)-10
    assert math.isclose(net_balance(1000,1.10,'aave'),expected,abs_tol=1e-10)
    assert math.isclose(net_balance(1000,1.04,'sgov'),1000*.99995*1.04*.99995,abs_tol=1e-10)
    treasury=net_balance(10000,1.10,'sgov')
    defi=net_balance(10000,1.12,'aave')
    haircut=(defi-treasury)/(defi+10)
    assert math.isclose(net_balance(10000,1.12,'aave',terminal_haircut=haircut),treasury,abs_tol=1e-9)
    assert net_balance(10000,1.12,'aave','High')<net_balance(10000,1.12,'aave','Base')<net_balance(10000,1.12,'aave','Low')


def test_real_series_alignment_and_independent_returns():
    result,costs,joined,aligned,*_=compare()
    assert len(aligned)==867 and len(joined)==867*3
    assert (aligned.valuation_utc<=aligned.date).all()
    # 1 and 2 June are a weekend; only the preceding Friday NAV can be used.
    assert aligned.iloc[:3].nav_date.nunique()==1
    assert set(result.index)=={'sgov','aave','steakhouse_v1','gauntlet_v1'}
    assert len(costs)==4*3*3
    assert np.allclose(result.net_profit,result.net_final-10000)
    assert np.allclose(result.extra_vs_sgov,result.net_final-result.loc['sgov','net_final'])
    for key in ['aave','steakhouse_v1','gauntlet_v1']:
        h=result.loc[key,'break_even_terminal_haircut_pct']/100
        assert math.isclose(net_balance(10000,result.loc[key,'gross_multiple'],key,terminal_haircut=h),result.loc['sgov','net_final'],abs_tol=1e-8)
