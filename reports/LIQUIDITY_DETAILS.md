# USDC yield and withdrawal liquidity: findings

**Native yield differed little, while sampled withdrawal liquidity differed considerably.** This result concerns Aave V3 Ethereum Core and two specified Morpho V1 vaults over 1 June 2024–15 October 2026 UTC.

[Executed notebook](../notebooks/02_liquidity_details.ipynb) · [source catalogue](../docs/DATA_SOURCES.md) · [raw-data hashes](../data/manifest.json) · [reproduction instructions](../README.md#reproduce).

## Earned native USDC

| Product | Annualized return | Interest per 10,000 initial USDC | Extra interest versus Aave |
|---|---:|---:|---:|
| Aave V3 Core | 4.61% | 1,129.26 USDC | — |
| Steakhouse USDC V1 | 4.68% | 1,145.15 USDC | 15.89 USDC |
| Gauntlet USDC Prime V1 | 4.72% | 1,156.32 USDC | 27.07 USDC |

These are **866-day holding-period outcomes**, not annual cash payments or current advertised APYs. Annualized advantages were only 0.063 and 0.107 percentage points. The positions include accrued native interest after vault fees, but exclude separately distributed token rewards, transaction costs and taxes. USDC units are not guaranteed dollars.

A small additional execution cost could erase these premiums. A hypothetical terminal haircut of only **0.143%** of the Steakhouse balance or **0.243%** of the Gauntlet balance would also erase the corresponding premium over Aave, holding Aave's observed balance fixed. This is a break-even calculation, not an estimate of the probability of loss or an assumption that Aave is safe.

## What happened to withdrawal capacity?

Median cash available relative to claims was **14.9% for Aave**, **24.0% for Steakhouse**, and **59.1% for Gauntlet**. Relative cash buffers favored these Morpho vaults on this sample. The protocol architectures and product sizes differ; the buffer statistic alone does not explain why.

Of 867 daily observations, cash was insufficient for a hypothetical existing 1-million-USDC withdrawal in **38 Aave observations** and **none for the two Morpho vaults**. For a 10,000-USDC request, the corresponding counts were **2, 0 and 0**. These are sampled static-capacity shortfalls, not observed failed transactions. Other users may consume cash before an individual withdraws.

For a collective request of 25% of claims, cash was sufficient in **146/867 Aave snapshots (16.8%)**, **409/867 Steakhouse snapshots (47.2%)**, and **855/867 Gauntlet snapshots (98.6%)**. The capacity curve uses only daily observations, so stress windows do not receive extra weight.

## Stress does not always mean the same thing

In the three preselected market sell-offs, liquidity changes were heterogeneous:

| Window | Aave minimum cash / claims | Steakhouse minimum | Gauntlet minimum |
|---|---:|---:|---:|
| August 2024 | 8.0% | 14.2% | 45.4% |
| April 2025 | 26.2% | 11.1% | 31.7% |
| October 2025 | 7.7% | 13.0% | 43.7% |

Each window runs three days before through seven days after its event date, sampled every six hours. **Aave retained a larger relative buffer than Steakhouse in the April 2025 window.** Neither “Morpho always has more liquidity” nor “a market sell-off always drains cash” fits the evidence.

The systematic daily ETH-decline screen found 24 days with declines of at least 7%. End-of-day median capacity on these days was not lower than on other days for any of the three products. This descriptive comparison does not establish protection against future stress; it shows why ETH price declines alone are an incomplete liquidity-risk indicator.

### Exploratory April 2026 diagnostic

The full-panel minimum occurred on **21 April 2026 at 00:00 UTC**: Aave's USDC reserve held **6,519.184610 USDC**, against approximately **2.095 billion USDC of supplier claims**. The read at [Ethereum block 24,924,560](https://etherscan.io/block/24924560) matched across dRPC and 1RPC. The two Morpho vaults individually had approximately **48.68 million** and **48.41 million USDC** accessible at that same block, respectively; these capacities are not independent or additive.

This coincides with the [rsETH incident documented by Aave service providers](https://governance.aave.com/t/rseth-incident-report-april-20-2026/24580). The originating exploit concerned the rsETH bridge, not Aave contract code. The [April 2026 zoom](../figures/05_april_2026_liquidity.png) was selected **after** locating the minimum, as documented in the [diagnostic note](../docs/EXPLORATORY_DIAGNOSTIC.md). No causal decomposition or realized USDC haircut is inferred.

## Different vault names can still share exit liquidity

On **25 September 2024**, both Morpho vaults' calculated capacity was **1,049,920.706322 USDC**, drawn from the same three markets: approximately 272,822 USDC in the wstETH market, 776,856 in WBTC, and 242 in cbBTC. Each vault's claim exceeded the available cash in those markets. Both could individually access the same cash, but that cash could not satisfy both amounts simultaneously. See the saved state for [block 20,823,901](https://etherscan.io/block/20823901).

This is evidence of a shared liquidity dependency, not proof of losses. Allocating between curator names does not necessarily diversify the underlying exit route.

## Was the extra yield worth the risk?

**The native-yield premium was too small to make a persuasive decision on its own.** In this specific history the selected Morpho vaults also generally had larger relative cash buffers, so the measured trade-off was not simply “more yield for less liquidity.” A decision still depends on the exact collateral, curator, contract and exit needs, as well as rewards and costs omitted here.

The most useful finding is that **interest can keep accruing while immediate cash availability becomes severely constrained**. A smooth earnings curve is not sufficient evidence of safety or liquidity.

## Scope and limits

- Selected surviving products, not a representative universe; no ecosystem-wide causal or safety ranking.
- V1 vaults only. The later Steakhouse Prime V2 product has different mechanics and cannot be inserted into the earlier event windows.
- Snapshots rather than every block; six-hour sampling can miss temporary minima.
- Native USDC accounting returns; no full USD peg, exploit-loss or executed-withdrawal reconstruction.
- Incentives, taxes and actual gas excluded; hypothetical costs are separated explicitly.
- Dependent observations and few events; no statistical-significance claim.

The next study should reconstruct V2 adapter liquidity over a separate common period and include discontinued vaults. A broader risk-adjusted-return claim would also require a complete ledger of rewards, executed exits and principal losses.
