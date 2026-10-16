# Exploratory diagnostic added after panel inspection

15 October 2026. The original protocol and its three event windows remain unchanged.

After collecting the full prespecified panel, we found Aave V3 USDC's minimum sampled cash balance at **2026-04-21 00:00 UTC**, Ethereum **block 24,924,560**. We added a daily zoom covering 15 April–1 May 2026 to explain this material result. It is explicitly **post hoc**, not a fourth preselected experiment. No extra observations enter the full-window metrics or daily frequency denominators.

The USDC `balanceOf(aUSDC)` result at the minimum block was independently checked through [1RPC](https://1rpc.io/eth) and matched dRPC's return bytes exactly. The [saved cross-check](../data/raw/crosschecks/aave_minimum_1rpc.io.json) records both method and parameters; the corresponding [Ethereum block](https://etherscan.io/block/24924560) identifies the observation.

[Aave service providers' incident report](https://governance.aave.com/t/rseth-incident-report-april-20-2026/24580) documents the rsETH bridge incident beginning on 18 April 2026. It states that the originating exploit was outside Aave. The contemporaneous [USDC liquidity-buffer discussion](https://governance.aave.com/t/arfc-improve-liquidity-buffer-for-usdc-on-aave-v3-ethereum-core-raise-slope-2-lower-optimal-utilization/24684) provides additional context, not independently established causal evidence.

We report a coincident liquidity squeeze. We do not equate reserve cash depletion with a USDC principal haircut or claim that this descriptive panel identifies all causal flows.
