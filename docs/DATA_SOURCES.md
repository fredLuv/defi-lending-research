# Data sources and observation provenance

## Treasury-bill benchmark added 15 October 2026

The matched-period benchmark is **SGOV, the iShares 0–3 Month Treasury Bond ETF**, an ETF proxy rather than a directly held bill ladder. [Issuer product page](https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf) · [issuer workbook download](https://www.blackrock.com/varnish-api/blk-one01-product-data/product-data/api/v1/get-fund-document?appType=PRODUCT_PAGE&appSubType=ISHARES&targetSite=us-ishares&locale=en_US&portfolioId=314116&component=fundDownload&userType=individual).

The `Historical` sheet supplies date, NAV per share and ex-distributions. The `Distributions` sheet independently checks amounts and ex-dates; its payable dates show why hypothetical ex-date reinvestment is not an actual cash-receipt claim. The `Performance` sheet supplies 28 monthly NAV total-return cross-checks. Fund expenses are already included in NAV performance.

[Saved numerical extract](../data/raw/treasury/sgov.json) contains the used facts, exact URL, retrieval timestamp and SHA-256 of the original workbook. [Treasury manifest](../data/treasury_manifest.json) hashes that extract and the [extension design](TREASURY_COMPARISON.md). The full issuer workbook remains in ignored local `.cache/`, with its notices retained, rather than redistributing unrelated holdings and legal material. [Collector](../collect_treasury.py) retrieves it again. The parser escapes bare ampersands in a parsing copy of the issuer's XML; the recorded hash is of the unchanged source bytes.

Endpoint NAVs are **31 May 2024** and **14 October 2026**, the latest valuations preceding the original **1 June 2024 and 15 October 2026 midnight UTC anchors**. Each intervening anchor uses only a preceding 4 p.m. New York valuation, conservatively treating shortened sessions the same way. [Aligned daily observations](../data/processed/sgov_aligned.csv) record the NAV date and valuation time. Carrying the latest published NAV through nonvaluation days is not interpolation or evidence that economic value was constant.

The reconstructed endpoint total-return factor is independently checked with high-precision arithmetic. [Monthly checks](../reports/treasury_monthly_checks.csv) differ from issuer-published figures by less than **0.001 percentage point**. Small reconstruction/publication-convention differences are retained rather than overwritten.

**Cost provenance:** all trading, conversion and fixed costs are explicit scenarios, not observed fills. The product page's current quoted spread is context, not historical spread evidence. 1 USDC = $1 is a stated assumption; the study does not reconstruct USD depeg P&L. [Scenario definitions](TREASURY_COMPARISON.md#currency-and-costs) · [calculation code](../treasury_analysis.py).

**Exit-mechanism sources:** [SEC T+1 settlement guidance](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/new-t1-settlement-cycle-what-investors-need-know-investor-bulletin) and [TreasuryDirect holding/transfer rules](https://www.treasurydirect.gov/marketable-securities/selling-marketable-securities/). No empirical SGOV cash-capacity curve is available in this study, so none is invented.

## Original DeFi observation panel

**Primary data are historical Ethereum contract reads, not screenshots or estimates from advertised APYs.** The [manifest](../data/manifest.json) records every saved response's SHA-256 hash. The [daily panel](../data/processed/daily_panel.csv) includes a block number, block hash, actual timestamp, raw-response path and checksum for each plotted row. The [six-hour panel](../data/processed/intraday_panel.csv) adds the event observations.

## Products and direct links

All products use Ethereum mainnet (chain ID 1) and [native USDC](https://etherscan.io/address/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48), with six decimals. No bridged USDC is included.

| Product | Contract and product page | Data read at each historical block |
|---|---|---|
| Aave V3 Ethereum Core | [Pool](https://etherscan.io/address/0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2#code), [aUSDC](https://etherscan.io/address/0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c#code), [app](https://app.aave.com/reserve-overview/?underlyingAsset=0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48&marketName=proto_mainnet_v3) | Normalized supply-income index; aToken total supply; USDC cash held by the aToken; active/paused configuration. |
| Morpho Steakhouse USDC V1 | [Vault](https://etherscan.io/address/0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB#code), [app](https://app.morpho.org/ethereum/vault/0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB) | Fee-aware redemption preview; total assets and shares; withdrawal queue; historical positions and market state. |
| Morpho Gauntlet USDC Prime V1 | [Vault](https://etherscan.io/address/0xdd0f28e19C1780eb6396170735D45153D261490d#code), [app](https://app.morpho.org/ethereum/vault/0xdd0f28e19C1780eb6396170735D45153D261490d) | Same V1 accounting, using this vault's own queue and allocations. |
| Morpho Blue singleton | [Contract](https://etherscan.io/address/0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb#code) | Market assets, borrowings, supply shares, positions, last accrual time, fees and parameters; actual USDC balance. |

An allocation's market ID and collateral address are preserved in every raw state. Interest-rate-model addresses and their `borrowRateView` calls are preserved too. Every calculation uses the sampled historical state, including allocations later removed from a vault.

## Retrieval services

| Service | Explicit source | Role and limits |
|---|---|---|
| Ethereum JSON-RPC via dRPC | [Public endpoint](https://eth.drpc.org), [Ethereum API specification](https://ethereum.org/en/developers/docs/apis/json-rpc/) | Historical `eth_call` and block headers. Public access and rate limits may change. Substitute an archive-capable endpoint using `ETH_ARCHIVE_RPC`. No paid plan or wallet was used. |
| Multicall3 | [Source and deployments](https://github.com/mds1/multicall3), [Ethereum deployment](https://etherscan.io/address/0xcA11bde05977b3631167028862bE2a173976CA11#code) | Groups read calls in one RPC request. No transaction is submitted. Individual calldata and return bytes are saved. |
| DefiLlama block lookup | [Example dated request](https://coins.llama.fi/block/ethereum/1717200000) | Finds a nearby block. We subsequently check the RPC header and the next block to select the **last block at or before** the requested time. |
| Coinbase Exchange | [ETH/USD candles endpoint](https://api.exchange.coinbase.com/products/ETH-USD/candles?granularity=86400), [candle documentation](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles) | Independent ETH market context, daily UTC OHLC. Saved responses include exact start/end query parameters. Candle closes are placed at the end of their interval, not the start. |
| Morpho API | [Endpoint](https://api.morpho.org/graphql), [documentation](https://docs.morpho.org/developers/api/morpho/) | Independent cross-check, **not** a replacement for the historical block panel. The exact GraphQL query and returned state block are saved in [cross-check inputs](../data/raw/crosschecks/morpho_live_api.json). |

Data are retrieved on 15 October 2026. The analysis ends at 15 October 00:00 UTC, excluding the current partial day. Raw state files preserve individual retrieval timestamps. Ethereum block hashes identify the underlying immutable observations; this study does not independently operate a full node.

## Accounting references pinned for this study

- [MetaMorpho V1: `totalAssets`, `previewRedeem` conversions and withdrawal simulation](https://github.com/morpho-org/metamorpho/blob/ded84e59668155b34d3c24906c4f7461c12828af/src/MetaMorpho.sol).
- [Morpho expected balance accounting](https://github.com/morpho-org/morpho-blue/blob/8e26ca6a8dbc5089edcd67fb576248810fd2870a/src/libraries/periphery/MorphoBalancesLib.sol), [share arithmetic](https://github.com/morpho-org/morpho-blue/blob/8e26ca6a8dbc5089edcd67fb576248810fd2870a/src/libraries/SharesMathLib.sol), [interest arithmetic](https://github.com/morpho-org/morpho-blue/blob/8e26ca6a8dbc5089edcd67fb576248810fd2870a/src/libraries/MathLib.sol). These projects publish their own source licenses; we link to them rather than redistribute their code.
- [Aave V3 source revision](https://github.com/aave-dao/aave-v3-origin/tree/8305565ae342f1773c42cd2e4593f175fe5968a0), [Pool documentation](https://aave.com/docs/aave-v3/smart-contracts/pool), [withdrawal conditions](https://aave.com/help/supplying/withdraw-tokens).
- [DefiLlama Aave adapter at the inspected revision](https://github.com/DefiLlama/yield-server/blob/00f3107478b9a366cb686663dff487786347b817/src/adaptors/aave-v3/index.js): its `tvlUsd` is reserve liquidity, and its `apyBase` comes from the liquidity rate. We do **not** treat that field as total claims or integrate it as a realized return. The lend/borrow history endpoint required a paid plan and was not used.

The pinned source revisions document the formulas inspected in October 2026. They are not a claim that every historical Aave implementation had the same bytecode. Historical view calls and reconciliation to the vault's own accounting remain the empirical checks.

## Why V1, and what about V2?

[Steakhouse Prime USDC V2](https://app.morpho.org/ethereum/vault/0xbeef088055857739C12CD3765F20b7679Def0f51) was created on **27 October 2025** according to its [saved API metadata](../data/raw/provenance/morpho_v2_scope.json). It cannot be observed during the three prespecified 2024–2025 sell-offs. This is a history-based scope choice, not evidence that V1 is preferable today.

V2 supports adapters and separates immediately available liquidity from additional force-deallocatable liquidity. See [Morpho's liquidity explanation](https://help.morpho.org/en/articles/14779745-morpho-vaults-and-available-liquidity). Extending this study to V2 requires a separate common-period comparison and historical adapter/withdrawal-state reconstruction. We neither splice V1 and V2 returns nor label V1 findings as results for all Morpho.

## Stress-window context

The dates were fixed before inspecting the comparative panel. These sources document the market events, not the outcome of our selected lending positions:

- [5 August 2024 sell-off — Coinbase institutional commentary](https://www.coinbase.com/institutional/research-insights/research/weekly-market-commentary/weekly-2024-08-09).
- [April 2025 tariff volatility — Coinbase institutional commentary](https://www.coinbase.com/institutional/research-insights/research/weekly-market-commentary/weekly-2025-04-11).
- [10 October 2025 deleveraging — Coinbase institutional commentary](https://www.coinbase.com/en-de/institutional/research-insights/research/weekly-market-commentary/weekly-2025-10-17).

The notebook also includes all daily ETH declines of at least 7% over the sampled period. The March 2023 USDC depeg predates these Morpho vaults and is not a paired stress test in this study.

## Current V4/V2 snapshot

Collected **16 October 2026, 06:03 UTC (15 October, 23:03 PDT)**. This is a new snapshot, not an extension or splice of the historical V3/V1 series. [Raw response hashes and timestamps](../data/current_manifest.json) · [read-only collector](../collect_current.py) · [design and cost assumptions](CURRENT_COMPARISON.md).

| Product | Exact Ethereum identity | Official source |
|---|---|---|
| Aave V4 Main / Core | Main Spoke `0x94e7A5dCbE816e498b89aB752661904E2F56c485`; Core Hub `0xCca852Bc40e560adC3b1Cc58CA5b55638ce826c9`; reserve ID 7, Hub asset ID 5 | [V4 GraphQL](https://api.v4.aave.com/graphql), [saved query and response](../data/raw/current/aave_v4.json), [reserve documentation](https://www.aave.com/docs/aave-v4/liquidity/reserves) |
| Morpho Vaults V2 Steakhouse Prime USDC | `0xbeef088055857739C12CD3765F20b7679Def0f51` | [Live vault](https://app.morpho.org/ethereum/vault/0xbeef088055857739C12CD3765F20b7679Def0f51), [state](https://api.morpho.org/v1/vaults-v2/1:0xbeef088055857739C12CD3765F20b7679Def0f51/state) |
| Morpho Vaults V2 Gauntlet USDC Prime | `0x8c106EEDAd96553e64287A5A6839c3Cc78afA3D0` | [Live vault](https://app.morpho.org/ethereum/vault/0x8c106EEDAd96553e64287A5A6839c3Cc78afA3D0), [state](https://api.morpho.org/v1/vaults-v2/1:0x8c106EEDAd96553e64287A5A6839c3Cc78afA3D0/state) |
| SGOV | iShares 0–3 Month Treasury Bond ETF | [Issuer product page](https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf), [dated numeric extract](../data/raw/current/sgov_quote.json) |

All three DeFi selections use **native USDC**, `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`, six decimals. The [official V2 directory response](../data/raw/current/morpho_v2_directory.json) verifies version, chain, asset and exact addresses. The directory's first page contains both selected vaults; it is not used to claim exhaustive market coverage.

**Aave fields:** reserve `summary.supplyApy.value` is a fractional annualized rate (multiply by 100 for percent). Main supply is distinct from `asset.summary.supplied` (Hub total). `asset.summary.availableLiquidity` is shared Hub cash. These amount values are already decimal-normalized. Aave Pro's capacity-filled percentage is not a withdrawal-liquidity fraction. [Hub mechanics](https://www.aave.com/docs/aave-v4/liquidity/hubs) · [withdrawal conditions](https://www.aave.com/docs/aave-v4/positions/withdraw). The response does not identify one pinned block; retrieval times are retained.

**Morpho fields:** `/v1/vaults-v2/1:{address}/state` gives integer micro-USDC `total_assets`, `withdrawable_assets` and `idle_assets`; divide by 1,000,000. `/apy-averages?lookback=six_hours` and `?lookback=thirty_days` give fractional realized, post-fee share-price APYs, excluding rewards. [Official API and APY definitions](https://docs.morpho.org/developers/earn/tutorials/get-data/). Each endpoint's indexed block and retrieval time are preserved in [raw files](../data/raw/current/). Calls are sequential, not atomic. Withdrawable assets are provider-reported, not an executed withdrawal test; capacities may overlap across vaults. [V2 mechanics](https://docs.morpho.org/learn/concepts/vault-v2/) · [asset routing](https://docs.morpho.org/developers/earn/tutorials/assets-flow/) · [force-deallocation](https://docs.morpho.org/developers/earn/tutorials/force-deallocate/).

**SGOV fields:** 30-day SEC yield **3.74%**, issuer date **14 October 2026**; median full bid/ask spread **0.01%**; expense ratio **0.09%**, already reflected in SEC yield. The full downloaded page is kept in ignored local cache; its SHA-256 and only relevant numerical fields are committed. SEC yield is not APY or a locked bill yield. Scenario arithmetic converts its nominal semiannual annualization to effective annual `(1 + y/2)^2 - 1`; this does not make the different source windows equivalent. No future market-price or NAV return is predicted.

**Costs:** Low/Base/High are explicit assumptions reused from the historical study, not fresh gas estimates or wallet-specific conversion quotes. See [all scenarios](../reports/current_scenarios.csv). Cash availability, protocol risk and Treasury ETF market-hours/T+1 access are distinct dimensions, not one risk score.
