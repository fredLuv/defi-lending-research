# Does crypto drawdown coincide with less withdrawal liquidity?

**Exploratory follow-up, 15 October 2026.** This analysis responds to a question raised after the original results. It is not a prespecified test and does not alter the original protocol or notebook conclusions.

## Definition and sources

ETH drawdown is `1 − daily closing price / highest closing price over the latest 90 completed days`. The first 89 days are excluded. Each completed daily candle is matched to withdrawal capacity at its closing midnight UTC. This is a contemporaneous descriptive association, not a forecasting test. A 90-day drawdown is not an all-time-high drawdown or a one-day price decline.

The common sample is 29 August 2024–15 October 2026: **778 daily observations per product**. ETH candles come from [Coinbase Exchange](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles); liquidity comes from the same historical contract reads as the main study. [Exact contracts and source catalogue](../docs/DATA_SOURCES.md) · [raw response checksums](../data/manifest.json).

Run `python drawdown_diagnostic.py` in the study environment. The [script](../drawdown_diagnostic.py) revalidates the underlying snapshots before analysis. [Joined observations](../data/processed/drawdown_diagnostic.csv) retain block numbers and source paths; [results](drawdown_diagnostic.csv) retain unrounded values.

## Results

| Product | Median cash / claims: ETH <20% below recent peak (375 days) | Median cash / claims: ETH ≥20% below recent peak (403 days) | Rank correlation: drawdown magnitude versus cash fraction |
|---|---:|---:|---:|
| Aave V3 Core | 10.6% | 20.0% | +0.606 |
| Steakhouse USDC V1 | 21.7% | 25.0% | +0.060 |
| Gauntlet USDC Prime V1 | 60.3% | 58.1% | +0.012 |

Positive correlation means deeper drawdowns accompany **more** cash relative to claims. The Aave association therefore runs against a simple claim that every crypto drawdown creates a withdrawal squeeze. The selected Morpho vaults show little monotonic relationship under this definition. The threshold comparison and rank correlation answer different descriptive questions and need not have the same sign.

The original one-day stress screen likewise found no lower median cash buffer on days when ETH declined at least 7%. That separate result is in [all_stress_days.csv](all_stress_days.csv).

## Interpretation and limits

- A crypto price decline can raise collateral-loss risk while debt repayment and liquidation return USDC to lending markets. Supplier withdrawals can act in the opposite direction. These aggregate balances do not identify the individual flows or establish causality. [Liquidation mechanics](https://docs.morpho.org/developers/borrow/concepts/liquidation/).
- Available cash measures withdrawal liquidity, not borrower solvency, eventual principal losses, USDC peg risk or overall investment risk. The snapshot also does not model competing requests or gas costs.
- Persistent drawdowns and changing vault allocations can generate associations across time. These are dependent daily observations; no p-values, significance, causal effects or out-of-sample predictive claims are asserted.
- A 90-day lookback and 20% threshold were selected for this question before calculating this diagnostic, but after seeing the original study. Other definitions and lead/lag relationships have not been tested. All three product results are reported.
- The April 2026 Aave minimum coincided with the rsETH incident. An external collateral/bridge event is different from a generic ETH drawdown; the study does not attribute every change in reserve cash to that incident. [Incident source](https://governance.aave.com/t/rseth-incident-report-april-20-2026/24580).

## Investment question this leaves open

An unleveraged USDC supplier earns interest rather than directly participating in crypto collateral appreciation, but retains credit, liquidity and operational tail exposures. This is an asymmetric lending payoff; the present data do not estimate its convexity or establish that it is undercompensated. Variable interest rates can rise during high utilization.

To assess compensation, compare net USDC lending outcomes with an accessible cash alternative over identical dates, including rewards, execution costs and USD peg effects. The full 4.6–4.7% annualized native return is not automatically an excess return for bearing DeFi risk. Comparing Morpho only with Aave cannot answer that allocation question.
