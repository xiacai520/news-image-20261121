# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/xiacai520/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/xiacai520/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

One image that sums up the world news of Saturday 21 November 2026,
laid out as a newspaper front page:

- **Anthropic makes history** — the Claude maker raised $81.3B at $83
  a share in the biggest IPO on record, its valuation topping $2T on
  debut and passing SpaceX's June issue.
- **Taiwan stocks: worst week in 35 years** — TAIEX shed 7,642 points
  (-17.5%) in five days; Friday alone fell 2,394 to 36,033, and TSMC
  slipped to NT$1,970.
- **Trump and Xi meet a third time** — at the APEC summit in Shenzhen
  the leaders agreed to work together on AI safety rules, Trump said
  Xi backed his push to limit nuclear arms, and a US-China-Russia
  summit issued a peace declaration.
- **NT$20,000 payout passes 50-46** — Taiwan's legislature approved a
  cash handout for all; the Premier's Office called it
  unconstitutional and a fiscal risk.
- Plus a ticker: the ICJ finding Myanmar guilty of Rohingya genocide,
  a Russian missile hitting a Kyiv bridge (3 dead), European youth
  marching against war and living costs, and Taiwan rushing to steady
  its markets.

`main.py` paints the page itself in pure Python 3 standard library:
an RGB buffer, a hand-built stroke typeface (every glyph a set of
polylines on a 5x7 grid, drawn with Bresenham lines), a falling-week
chart and vote-tally bars, a globe pictogram, and its own PNG writer
(zlib + struct). It reads no files, uses no network, clock or
randomness, so every run writes byte-identical output. `entry.png` in
this repository is what it currently produces.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Without `MAKEFUN_OUTPUT_DIR` it writes to `/output/entry.png`.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>
