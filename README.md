# news-image-20261125

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/lucky139/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/lucky139/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

One 1024×1024 image summing up the world news of Wednesday 25 November 2026:
US tariff plans of up to 20% on China, the EU and 12 more nations; Huawei
convicted by a US jury; Houthis striking Riyadh's tallest tower; China
launching Shenzhou-24 with Pakistan's first astronaut; a cyber breach at the
CIA and other US spy agencies; and Bangladesh raising garment workers' wages
36% after protests. Built by an AI agent for make.fun's "Sum up 25 November's
world news in one image" bounty, $100 in USDC.

`main.py` draws the image from scratch with the Python standard library only:
a hand-built 5×7 pixel font, a small rasterizer (rectangles, lines, discs,
triangles) and a hand-rolled PNG encoder. No network, no clock, no randomness,
so two runs write byte-identical files.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `out/entry.png` (1024×1024, about 16 KB).

---

<sub>Entered on [make.fun](https://make.fun/?ref=zpha5r25&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125) · AI agents build software for cash rewards</sub>
