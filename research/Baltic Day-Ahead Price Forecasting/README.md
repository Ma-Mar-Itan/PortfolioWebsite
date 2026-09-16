# Day-Ahead Electricity Price Forecasting in the Baltic States

Source for the research page at `research/Baltic Day-Ahead Price Forecasting/`.

## Layout

| Path | What it is |
|---|---|
| `index.qmd` | the manuscript |
| `_theme.py` | figure theme — palettes, rc block, the light/dark render pair, table helpers |
| `_figures.py` | one builder per figure, plus `build_all()` |
| `_data/` | the evaluation output the figures and tables are computed from |
| `figures/` | rendered output, `fig-<name>-{light,dark}.svg` |

## Rebuilding the figures

The setup chunk in `index.qmd` calls `_figures.build_all()` automatically when
`figures/fig-rmae-light.svg` is missing, so a clean checkout builds itself on
the first render. To force a rebuild after editing a builder:

```bash
cd "research/Baltic Day-Ahead Price Forecasting"
python -c "import matplotlib; matplotlib.use('Agg'); import _figures; _figures.build_all()"
```

Every figure is rendered twice, once per site theme, and shown through Quarto's
`.light-content` / `.dark-content` classes. Those classes only get their display
rules when the project declares a light **and** a dark theme, which
`_quarto.yml` does — rendering this file standalone will show both copies
stacked.

## Colour discipline

The hue is the bidding zone and nothing else:

| Zone | Light | Dark |
|---|---|---|
| Estonia | `#2a78d6` | `#3987e5` |
| Latvia | `#eb6834` | `#d95926` |
| Lithuania | `#1baf7a` | `#199e70` |

Where the three LEAR specifications appear inside a zone they are three steps of
that zone's own hue, weakest to strongest (8w, 12w, ensemble), always with direct
value labels so the model is never carried by shade alone. The weekly naive
benchmark is never given a hue — it is the grey reference the coloured marks are
measured against.

The three zone hues clear every all-pairs colour-vision gate in both modes
(CVD ΔE 9.2 light / 9.4 dark; normal-vision ΔE 24.0 light / 20.9 dark).

## Data

`_data/` holds the committed evaluation output from the forecasting project, not
raw ENTSO-E data:

- `all_metrics.csv` — MAE, RMSE and rMAE per zone and model, overall and either
  side of the 9 February 2025 synchronisation.
- `{EE,LV,LT}_forecasts_all.csv.gz` — the full 964-day forecast archive, one row
  per delivery day, 24 columns per model.
- `volatile_periods.csv`, `volatile_21d_model_metrics.csv` — the most volatile
  21-day window per zone and performance inside it.
- `{EE,LV,LT}_hourly_metrics.csv`, `{EE,LV,LT}_daily_metrics.csv` — profiles
  **inside the stress window only**, from the volatile-period analysis. Full
  sample profiles are recomputed from the forecast archive in `_figures.py`.
