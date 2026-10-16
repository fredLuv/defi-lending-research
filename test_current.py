"""Consequential checks: frozen identities, correct units, cost and yield conventions."""
import math
import numpy as np
from current_analysis import load, net_balance

def test_frozen_identity_units_and_rate_conventions():
    rates,costs,manifest=load()
    assert len(rates)==4 and len(costs)==108
    assert rates.loc['aave_v4','main_supply_usdc']<rates.loc['aave_v4','denominator_usdc']
    assert rates.loc['sgov','available_usdc']!=rates.loc['sgov','available_usdc'] # missing, not zero
    assert math.isclose(rates.loc['sgov','effective_scenario_rate'],(1+rates.loc['sgov','quote_rate']/2)**2-1)
    assert all('v1' not in k and 'v3' not in k for k in rates.index)
    for _,group in costs.groupby(['capital','days','scenario']):
        sg=group.set_index('product').loc['sgov','net_final']
        assert np.allclose(group.extra_vs_sgov,group.net_final-sg)

def test_costs_with_hand_calculation_and_duration():
    assert math.isclose(net_balance(1000,.10,365,10,.001),990*.999*1.10*.999-10)
    assert math.isclose(net_balance(1000,.21,182.5,0,0),1100)
    # Same yields, higher two-sided costs cannot create an advantage.
    assert net_balance(10000,.05,90,10,.0005)<net_balance(10000,.05,90,0,.00005)
    # Fixed costs matter more for smaller deposits.
    assert net_balance(1000,.05,90,10,.0005)/1000<net_balance(100000,.05,90,10,.0005)/100000
