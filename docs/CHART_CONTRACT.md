# Figure design and QA

Audience: a stablecoin supplier comparing historical native interest with the ability to retrieve cash. Notebook is the primary artifact; static PNG plus SVG/PDF exports support reuse.

| Figure | Question | Grain and encoding |
|---|---|---|
| Native yield | How much interest accrued, and how did earning rates change? | Daily, common blocks; cumulative USDC interest and trailing 30-day annualized return in aligned panels. |
| Withdrawal liquidity | How much cash was available relative to claims and in absolute terms? | Daily capacity ratio and absolute USDC; absolute panel uses a labelled log scale. |
| Stress windows | Did cash availability change during the selected sell-offs? | Three fixed events, six-hour capacity; independent ETH daily-close context. |
| Capacity curve | How frequently was there enough cash to meet different collective requests? | Equal-weight daily snapshots, requested share versus empirical coverage. No probability-of-default interpretation. |

Aave: blue solid. Morpho: orange dashed and dark-orange dotted, consistently across all figures. Neutral market context and benchmarks. No dual axes or decorative background. Every export names sources, period and a material interpretation limit. Show exact source links immediately below figures in the notebook and README; a machine-readable manifest links each observation to its raw contract reads and block.

QA: inspect all exports, notebook outputs and mobile-scale text; verify endpoint values, shared axes, source captions and no missing-data interpolation. Keep six-hour event oversampling out of overall frequency calculations.

## Treasury comparison consolidation — 15 October 2026

Primary surface remains a fully executed notebook; standalone exports are Matplotlib PNG/PDF/SVG, with a portrait summary for LinkedIn. The previous five figures remain in an appendix. No decorative logo or implied institutional affiliation.

| Main figure | Question | Encoding and sufficient data |
|---|---|---|
| 01 · Income versus Treasury bills | How much income was incremental? | Three daily excess-income series over 867 anchors, with a zero SGOV baseline; adjacent horizontal net-excess-income bars for the three DeFi products, zero-based. Exact endpoint labels. |
| 02 · What can erase the premium? | How sensitive is the conclusion to execution costs and a conversion loss? | Three fixed cost-scenario dots per DeFi product, plus a 0–2% terminal-haircut sensitivity curve. No probability or confidence-interval interpretation. |
| 03 · Return is not access to cash | How much withdrawal liquidity existed, and what happened in April 2026? | Three comparable capacity curves and a log-scale time-series inset over 17 daily observations. SGOV settlement described in prose, never plotted as an invented 100% cash buffer. |
| LinkedIn summary | What did the comparison actually find? | Portrait layout: net excess income by product, then the April 2026 cash-availability time series; short interpretation and method/source footer. Two related findings, clearly separated. |

White background, charcoal text, large readable type, ample padding. Palette: blue Aave, orange and dark orange Morpho V1, charcoal SGOV. Solid/dashed/dotted lines and direct labels provide non-color distinctions. Two non-neutral color roots; no red/green default. Date range, 10,000 starting capital, assumed costs, par conversion, ETF proxy status and sources must remain legible in exports. Inspect full-size and 720px-width previews; keep detailed methodology in the notebook rather than tiny chart footnotes. Charts do not promise LinkedIn engagement.

## ManimGX animation

Question: how did the earned yield advantage change, and was earning income equivalent to accessing cash? A 38.1-second, 1080p/30fps companion uses the same frozen observations. The opening comparison uses nine grouped bars: three products across June–December 2024, calendar 2025, and 1 January–15 October 2026 UTC. Each bar is the product's annualized holding-period return minus SGOV's annualized return, in percentage points, before entry/exit costs but after embedded fund/vault fees. These are three discrete period summaries, not a continuous trend or forward APY. Shared signed scale, visible zero, product colors plus fixed ordering and exact signed labels. Reveal whole period groups without interpolating values. Period endpoints and denominators are retained in a compact evidence CSV; compounded subperiod returns must reconcile to full-period returns.

The second scene retains 17 daily observations per product on a labelled logarithmic cash scale. The selected April window is explicitly exploratory. The final scene retains the $58–$85 full-period net premium on $10,000, clearly separated from the opening percentage-point spread. Delivery: ManimGX 1920 × 1080 master, 1920 × 1320 captioned LinkedIn export. Check the grouped bars and signed labels at full size and mobile width.
No decorative 3D, additional financial models, inferred intra-day observations or liquidity-loss claims. Noto Sans, white background, the study's blue/orange palette, direct labels and full unit/date captions. Numerical provenance and reproduction are linked beside the video. Check all play-end layouts, representative decoded video frames and a reduced-size preview before release.

The LinkedIn export adds a 240px subtitle/disclaimer band beneath the unchanged chart region, producing 1920 × 1320 pixels. Subtitles use 48px Noto Sans with at most two lines; the persistent educational-purpose/not-financial-advice disclaimer uses 32px text. The final slide is reduced to one conclusion, one measured result and one UX implication. Audio is copied from the Voicebox version. Inspect the longest subtitle and final-slide frames at full size and 720px width.
