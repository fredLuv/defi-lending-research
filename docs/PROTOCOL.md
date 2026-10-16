# USDC lending: earned yield and withdrawal capacity

Design recorded 15 October 2026, before collecting the comparative historical panel. This is a retrospective case study, not a preregistered prospective experiment.

## Question and scope

Did two named Morpho vaults earn more native USDC interest than Aave V3, and what withdrawal capacity accompanied that return? Study an existing, unleveraged supplier on Ethereum. Do not rank entire protocols or estimate hack/default probabilities from smooth returns.

Products selected for recognizable managers and history extending before the August 2024 sell-off, without inspecting historical outcome rankings:

| Product | Contract | Version |
|---|---|---|
| Aave Ethereum Core USDC | [aUSDC](https://etherscan.io/address/0x98C23E9d8f34FEFb1B7BD6a91B7FF122F4e16F5c), [Pool](https://etherscan.io/address/0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2) | V3 |
| Morpho Steakhouse USDC | [Vault](https://etherscan.io/address/0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB) | V1; not the later Prime V2 vault |
| Morpho Gauntlet USDC Prime | [Vault](https://etherscan.io/address/0xdd0f28e19C1780eb6396170735D45153D261490d) | V1 |

This purposive sample has selection/survivorship bias. It is not an investable universe backtest and does not represent every vault, curator, collateral type or chain.

## Observation design

- Daily UTC anchors from **2024-06-01 00:00 through 2026-10-15 00:00**, inclusive (end of 14 October).
- Resolve the last Ethereum block at or before each anchor; record number, hash and actual block time. All three products use the identical block.
- For the fixed stress dates **2024-08-05, 2025-04-07 and 2025-10-10**, additionally sample every six hours from three days before through seven days after. These are retrospective market-event windows, not evidence that the protocols themselves failed.
- Retrieve ETH/USD daily OHLC candles from Coinbase Exchange as independent market context. Also report all covered daily ETH declines of at least 7%; do not select only events favoring one lender.
- Do not fill missing contract states with nearby outcomes. Retry transient failures; report exact gaps. If historical RPC access fails, disclose reduced coverage instead of substituting an unlabelled APY proxy.

## Return

- **Aave:** ratio of `Pool.getReserveNormalizedIncome(USDC)` at two blocks.
- **Morpho:** ratio of `previewRedeem(10^24 shares)` at two blocks. This fixed large share unit reduces integer rounding and includes accrued vault performance fees. It is an accounting conversion, not a claim that those shares can all be withdrawn immediately. Check the vault asset and share decimals.
- Show cumulative native USDC interest on 10,000 initial USDC, full-window annualized return, and trailing 30-day annualized return. Do not call a quote integrated over time a realized return.
- Exclude separately distributed governance-token rewards, gas, taxes and exchange costs from primary native-interest results. Show illustrative 0/20/100 USDC round-trip costs separately; these are assumptions, not historical execution costs.
- USDC units are not guaranteed dollars. Do not infer USD mark-to-market returns or stablecoin peg safety from these accounting balances.

## Withdrawal capacity

- **Aave:** USDC balance held by the reserve's aToken contract, capped by outstanding aToken claims. Check active/paused flags. Freezing new supply is not itself a withdrawal pause.
- **Morpho V1:** read the historical withdrawal queue. For each included market, reconstruct the vault's accrued asset claim from its supply shares and the market's expected balances, including interest and fee shares. Sum the lesser of that claim and unborrowed market cash, and cap by the Morpho singleton's actual USDC balance and vault assets. Reconcile reconstructed claims with the vault's own `totalAssets()`.
- Use integer accounting matching the documented contracts; read the IRM's historical `borrowRateView` where accrual is needed. Preserve all inputs. Current allocations must never stand in for historical allocations.
- Report capacity in USDC and as a fraction of supplier claims. Capacity belongs to the product collectively: it is **not reserved for an individual wallet**. Morpho vaults can share underlying market cash; never add their capacities as independent liquidity.
- Fixed requests: 10,000, 100,000 and 1,000,000 USDC. Collective shocks: 5%, 10%, 25% and 50% of claims. Immediate service fraction = `min(1, capacity/request)`, assuming no new deposits, repayments or competing withdrawals. This measures a static capacity shortfall, not observed withdrawal failures, time-to-cash, or insolvency.

## Evidence and interpretation

Compare full-window returns, equal-calendar rolling periods, liquidity distributions and the fixed event windows. A deposit that earned extra interest but had less liquidity is not automatically better or worse. Quantify the premium in USDC and compare it with hypothetical principal haircuts; do not assign unobserved loss probabilities.

Validation: same-block alignment, block-time bounds, asset identity, queue uniqueness, integer accrual reconciliation, cash/claims bounds, independently recomputed returns and request-size arithmetic, and clean offline notebook execution. Cross-check selected observations against Morpho's API and Aave's public series where definitions permit. Explain source discrepancies.

## Source links and reproducibility

Primary observations: Ethereum read-only JSON-RPC `eth_call`, `eth_getBlockByNumber`, served by [dRPC](https://eth.drpc.org). Block lookup helper: [DefiLlama block API](https://coins.llama.fi/block/ethereum/1717200000), followed by RPC timestamp checks. Market context: [Coinbase Exchange candles](https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getproductcandles).

Accounting references: [Aave withdrawals](https://aave.com/help/supplying/withdraw-tokens), [Aave V3 Pool](https://aave.com/docs/aave-v3/smart-contracts/pool), [MetaMorpho V1 source](https://github.com/morpho-org/metamorpho/blob/main/src/MetaMorpho.sol), [Morpho expected balances](https://github.com/morpho-org/morpho-blue/blob/main/src/libraries/periphery/MorphoBalancesLib.sol), [Morpho API](https://docs.morpho.org/developers/api/morpho/).

Commit this protocol before downloading the comparison panel. Pin code references and record response hashes, retrieval times and requested parameters. Provide cached offline reproduction and a separate network refresh command. No account keys, paid services, wallet connection or transactions are needed.
