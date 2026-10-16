# Validation scope

Question: how much incremental income did three selected DeFi positions earn over a Treasury-bill ETF under explicit cost assumptions, and what sampled withdrawal capacity accompanied the DeFi returns?

## Completed checks — 15 October 2026

- All **957 common-block snapshots** are present, including **867 daily anchors** per product.
- All **1,914 Morpho vault observations** reconcile exactly to on-chain `totalAssets()` in integer micro-USDC.
- Five automated tests passed, covering integer accrual, cash conservation, complete history, independent return reconstruction, cost arithmetic and Treasury valuation timing.
- Both notebooks executed from start to finish with no cell errors. The three new main figures and portrait export were inspected at full size and the portrait at 720 px width; the main notebook was also rendered to HTML for layout review. Original detailed figures remain in the appendix.
- The minimum Aave reserve cash was independently confirmed at the same block through [a second RPC provider](../data/raw/crosschecks/aave_minimum_1rpc.io.json).
- The stress-day classification contains **24 stress days and 842 other days** per product. The initial anchor lacks a prior close-to-close return and is excluded from that classification; all 867 anchors remain in the overall liquidity analysis.

## Treasury extension checks

- The extension design was committed before computing the Treasury comparison; it does not alter the original frozen DeFi protocol.
- The saved issuer extract and design hashes are verified on every build. SGOV distributions reconcile independently between the issuer's historical and distribution sheets.
- All **867 UTC anchors** use a preceding NAV valuation. Endpoint NAV dates are **31 May 2024** and **14 October 2026**; no future or interpolated NAV is used.
- **28 monthly returns** reconcile to issuer-published returns within **0.001 percentage point**; maximum absolute difference is **0.0008526 pp**. Reconstruction/convention differences are preserved.
- Independent 40-digit daily compounding matches the endpoint total-return factor **1.1040608212508246**.
- Entry and exit costs, capital-size sensitivity and the exact break-even haircut are checked algebraically. Fund/vault fees are not charged twice. Costs and USDC par conversion are assumptions, not recorded fills.
- The published results preserve all four investments and all 36 product/cost/size combinations. Currency and annualized-versus-holding-period labels are explicit.
- Relative presentation links were checked; source links and provenance appear beside the charts. The shareable figure is an export only; no social post or visibility change was made.

[Machine-readable checks](treasury_checks.json) · [monthly checks](treasury_monthly_checks.csv) · [cost scenarios](treasury_cost_sensitivity.csv).

## Accounting and provenance checks

The offline build verifies every raw-data checksum, the frozen protocol hash, the full expected timestamp set, a common Ethereum block across all products, and the anchor/next-block timestamp bounds. It rejects missing states rather than silently shrinking the sample.

At every Morpho observation, reconstructed positions after interest accrual must sum exactly to the vault's own `totalAssets()`. Capacity is bounded by the vault's claims, its underlying markets' cash and the actual singleton USDC balance. The tests independently reconstruct accrued interest with rational arithmetic and verify that interest accrual does not itself create withdrawable cash.

[Independent Morpho API checks](api_crosscheck.json) compare two additional current observations at identical blocks: assets, available liquidity and share value. These checks do not enter the historical return panel. [Aave scaled-supply checks](../data/raw/crosschecks/aave_scaled_supply.json) compare scaled claims times the income index with aToken total supply at three historical blocks, including the start and end of the study.

## Statistical and interpretation checks

- Returns are independently reconstructed from both endpoint ratios and summed log changes.
- Overall frequencies use daily snapshots only; six-hour event oversampling does not change their weighting.
- ETH candles are placed at their closing timestamps. Stress classifications do not attach future closes to start-of-day states.
- No empirical withdrawal frequency is described as a default probability, confidence interval or trading signal.
- Morpho V1 and V2 are kept separate. No claim is made that the selected surviving products represent all vaults.
- The capacity tests describe static shared cash, not guaranteed individual withdrawals or cash recovery times.

## Limitations required for sharing

Share this as a **retrospective case study with caveats**. Contract exploits, collateral losses, historical pauses between observations, USDC depeg exposure and actual execution costs are not comprehensively measured. There are only three chosen stress-event windows; hundreds of dependent daily observations do not create hundreds of independent stress tests.

The notebook does not recommend depositing money or identify a universally safest product. Public RPC access may change; the archived snapshots enable offline reproduction. No wallet action was performed.
