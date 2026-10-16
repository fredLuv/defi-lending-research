# Treasury benchmark and cost extension

Recorded 15 October 2026 after the original DeFi results, before calculating comparative Treasury outcomes. This is an explicit extension, not a revision of the original frozen protocol.

## Benchmark and dates

Use **SGOV, the iShares 0–3 Month Treasury Bond ETF**, as an accessible Treasury-bill investment proxy. Its issuer supplies daily NAVs, ex-distributions and independent monthly total-return figures. Do not call a quoted Treasury yield an earned return, or describe ETF returns as a directly held bill ladder. The ETF carries expenses and small market-price/NAV differences.

Use the original anchors, 1 June 2024 00:00 UTC through 15 October 2026 00:00 UTC. At each anchor use only the latest already-published 4 p.m. New York NAV; carry that valuation through nonvaluation days, without inventing weekend prices. Endpoint NAV dates are expected to be 31 May 2024 and 14 October 2026. Ethereum observations remain the original common blocks. These are existing-position, matched valuation periods, not an executable Saturday purchase or an actual funded-wallet trade.

Calculate SGOV total return as the cumulative product of `(NAV_t + ex_distribution_t) / NAV_(t-1)`, reinvesting distributions at ex-date NAV. This is the standard hypothetical total-return convention, not a guarantee of ex-date cash availability. Cross-check reconstructed monthly returns against the issuer's independent monthly figures. Fund expenses are already reflected; do not subtract them twice.

## Currency and costs

Compare native USDC accrual with USD Treasury returns under an explicit **1 USDC = 1 USD conversion assumption**. Present separate terminal conversion/haircut sensitivity, rather than mislabeling the native series as measured USD cash recovery. No stablecoin reward tokens or taxes are included. No complete historical on/off-ramp or gas ledger is claimed.

Report gross-of-execution and three transparent **assumed** cost scenarios on the same 10,000 initial capital:

| Scenario | DeFi entry / exit fixed cost | DeFi entry / exit conversion spread | SGOV entry / exit spread | Broker commission |
|---|---:|---:|---:|---:|
| Low | $5 / $5 | 0 / 0 bps | 0.5 / 0.5 bps | $0 |
| Base | $10 / $10 | 5 / 5 bps | 0.5 / 0.5 bps | $0 |
| High | $50 / $50 | 25 / 25 bps | 2.5 / 2.5 bps | $0 |

SGOV's reported current median quoted spread is context, not a historical observation of every trade. All spread assumptions are per-side execution deductions, not measured fills. Entry costs reduce invested capital; exit costs apply to the ending balance. Show exact net dollars and annualized excess returns, plus sensitivity to capital size ($1,000, $10,000 and $100,000) and a terminal 0–2% USDC conversion haircut. Apply costs once. No repeated trading is assumed.

## Liquidity interpretation

Keep existing DeFi withdrawal-capacity evidence. Do **not** assign SGOV a fictional 100% immediate cash buffer: its shares trade during market hours, sale prices can differ from NAV, and ordinary ETF sale settlement is T+1. Direct bills held in TreasuryDirect have separate transfer restrictions. Distinguish interest/accounting return, sale proceeds, and spendable cash.

Net excess return is an observed conditional premium, not an estimated fair price of risk. Static capacity shortfalls are not default probabilities or observed failed withdrawals. No Sharpe ratio from smooth accounting indices and no claim that either protocol is safer overall.

## Presentation and validation

Consolidate the main notebook around three figures: (1) cumulative extra income versus SGOV and net endpoint comparison; (2) costs and break-even terminal haircut; (3) withdrawal-capacity comparison and the documented April 2026 squeeze. Provide a separate portrait summary suitable for LinkedIn with sources and assumptions embedded. Preserve the longer historical analysis as an appendix notebook.

Require input checksums, distribution-date alignment, no future NAVs, monthly-return reconciliation, independently computed endpoint return, transparent cost arithmetic, and successful offline notebook execution. Save compact numerical extracts, source URLs, retrieval times and hashes. Keep the issuer's complete workbook locally cached rather than redistributing its unrelated holdings and legal text.

Sources: [issuer product and download page](https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf), [SEC ETF settlement guidance](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/new-t1-settlement-cycle-what-investors-need-know-investor-bulletin), [TreasuryDirect sale/transfer rules](https://www.treasurydirect.gov/marketable-securities/selling-marketable-securities/).
