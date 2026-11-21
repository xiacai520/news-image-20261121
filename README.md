# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/xiacai520/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/xiacai520/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

A newspaper front page that sums up the world news of Saturday
21 November 2026 in one 1024x1024 image: the Nasdaq erasing all
its 2026 gains (-5.28% to 22,617.73) as the S&P 500 (-3.70%) and
Dow (-949.73) fell into correction, Asia's rout deepening with
the Taiex down 6.23% in its worst week since 1991, Nvidia sinking
14% on an SEC accounting probe, Anthropic sliding 8.5% on its
second day of trading, gold slumping to $3,514, Russian missiles
landing in Poland and the COP31 climate talks in Antalya running
into overtime, plus a ticker of the day's other stories.

The program is pure Python 3 standard library: it draws the page
with a built-in 5x7 bitmap font and writes the PNG itself (zlib +
struct), so it runs offline and produces byte-identical output on
every run. `entry.png` in this repository is its current output,
verified deterministic across repeated runs.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>
