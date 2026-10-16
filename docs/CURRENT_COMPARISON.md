# Current products: dated snapshot, not a backtest

This exploratory extension follows the user's Aave Pro screenshot. It is separate from the frozen V3/V1 historical benchmark. Initial API inspection preceded this document; this is not a preregistration.

## Selection

Ethereum native USDC only: Aave V4 Core Hub / Main Spoke; Morpho Vaults V2 Steakhouse Prime USDC and Gauntlet USDC Prime. The curators retain context from the historical comparison, but these are different contracts and exposures. Selection is by product identity, not yield ranking. No claim that they represent every V4/V2 opportunity.

## Inputs and rate conventions

- Aave: official V4 GraphQL API, exact reserve/Spoke/Hub identities, supply APY, active/paused status, Main supply and Hub supply/liquidity. APY is variable and excludes external rewards. Capture the raw response, query and retrieval time; it is not a block-pinned response.
- Morpho: official V2 directory, state, six-hour and 30-day realized post-fee APY endpoints. Retain indexed blocks, raw responses and retrieval times. Use the documented post-fee share-price APY rather than interpreting similarly named GraphQL fields ambiguously. Token rewards excluded. Zero idle cash is distinct from zero withdrawal capacity.
- SGOV: issuer's dated 30-day SEC yield, expense ratio and quoted spread. This is a Treasury ETF income proxy, not a directly held bill or guaranteed forward return. SEC yield is not APY. Preserve issuer date separately from retrieval time. Fund expenses are already included.

## Costs and horizons

Report original rates with their conventions. For scenario arithmetic only, convert SEC yield y to an effective annual rate `(1+y/2)^2-1`, consistent with its semiannual annualization convention; this is a constant-income/reinvestment illustration, not projected SGOV total return. DeFi effective annual rates use the APY directly. Show 30-, 90- and 365-day horizons, USD 1,000/10,000/100,000, and the historical study's Low/Base/High entry/exit cost assumptions. Base: DeFi USD 10 + 5 bps each side; SGOV 0.5 bp each side and zero commission. All execution assumptions are scenarios, not measured fills or gas estimates. No additional vault fee subtraction. Hold rates fixed only within illustrations, assume USDC = USD 1, exclude tax, rewards, depeg losses and market-price/NAV changes. Current point-in-time and lookback rates have different information windows; do not label a spread as realized excess return.

## Liquidity

Aave Hub available liquidity is shared across Spokes. Use Hub supplies as denominator, not Main supplies; do not call capacity-filled a utilization rate. Morpho `withdrawable_assets` is provider-reported capacity, not a guaranteed transaction result. Report idle assets separately. Capacities may overlap across vaults and must not be summed. Do not infer a safety ranking from cash ratios or assume public-allocator, forced, or in-kind exits are free immediate USDC. Actual gates, positions, collateral use, transaction ordering and fees can restrict exits. SGOV sells during exchange hours and ordinarily settles T+1; no fictitious on-demand cash ratio is assigned.

## Evidence and delivery

Save numeric source extracts, raw API responses and checksums. Fail on missing or ambiguous selected products; never substitute V1/V3 data. Validate costs independently, rates/units, dates, identifiers, and notebook execution before regenerating the video. Current results lead; historical narrowing and the April V3 incident are explicitly labelled historical context, never V4 evidence. The video must read the checked current-result files and retain a dated snapshot label.
