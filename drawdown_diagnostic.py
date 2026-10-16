"""Exploratory contemporaneous drawdown/liquidity check; not a frozen-protocol test.

Uses existing, verified raw observations. No network requests or new dependencies.
Spearman correlation is Pearson correlation of average ranks, including ties.
"""
from pathlib import Path
import pandas as pd
from analyse import load_panel, NAMES

ROOT = Path(__file__).resolve().parent


def main():
    _, daily, prices = load_panel()
    prices = prices.sort_values('close_timestamp').copy()
    assert prices.index.to_series().diff().dropna().eq(86400).all()
    prices['eth_drawdown_90'] = 1 - prices.close / prices.close.rolling(90, min_periods=90).max()
    joined = daily.merge(
        prices[['close_timestamp', 'eth_drawdown_90']],
        left_on='timestamp', right_on='close_timestamp', validate='many_to_one',
    ).dropna(subset=['eth_drawdown_90'])
    assert joined.timestamp.eq(joined.close_timestamp).all()
    records = []
    for product, group in joined.groupby('product'):
        # Positive correlation means deeper drawdowns accompany MORE cash, not more illiquidity.
        rho = group.eth_drawdown_90.rank().corr(group.cash_fraction.rank())
        for deep, subset in group.groupby(group.eth_drawdown_90.ge(.20)):
            records.append({
                'product': product,
                'drawdown_regime': 'At least 20%' if deep else 'Below 20%',
                'daily_observations': len(subset),
                'median_cash_claims_pct': 100 * subset.cash_fraction.median(),
                'cash_below_1m_count': int(subset.capacity_usdc.lt(1e6).sum()),
                'spearman_drawdown_vs_cash_full_sample': rho,
            })
    result = pd.DataFrame(records)
    result.to_csv(ROOT / 'reports/drawdown_diagnostic.csv', index=False)
    joined[['timestamp', 'product', 'eth_drawdown_90', 'cash_fraction', 'capacity_usdc', 'block', 'raw_file']].to_csv(
        ROOT / 'data/processed/drawdown_diagnostic.csv', index=False)
    print(result.to_string(index=False))
    print('Common period:', joined.date.min(), 'to', joined.date.max())


if __name__ == '__main__':
    main()
