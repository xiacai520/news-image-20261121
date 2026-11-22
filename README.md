# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/xiacai520/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/xiacai520/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

One image that sums up the world news of Saturday 21 November 2026,
laid out as a newspaper front page: the Nasdaq giving back all of its
2026 gains as the S&P 500 and the Dow fell into correction, Asia's
rout deepening (Taiex -6.23%, its worst week since 1991), Nvidia down
14% on an SEC accounting probe, Anthropic sliding 8.5% on its second
day of trading, gold slumping to $3,514, missiles landing in Poland,
and the COP31 talks in Antalya running into overtime — plus a ticker
of the day's other stories along the bottom.

`main.py` paints the page itself in pure Python 3 standard library:
an RGB buffer, a hand-made 5x7 bitmap typeface, simple pictograms for
each story, and its own PNG writer (zlib + struct). It reads nothing
and uses no clock or randomness, so every run writes byte-identical
output. `entry.png` in this repository is what it currently produces.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Without `MAKEFUN_OUTPUT_DIR` it writes to `/output/entry.png`.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>
