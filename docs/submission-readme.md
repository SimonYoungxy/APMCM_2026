# APMCM 2026 Problem C — submission package

Reproducible analysis of African penguin sea-surface calls, playback responses and
communication range.

## Contents

```
APMCM2026_C/
├── paper.tex            main paper (official apmcmthesis class, pdflatex)
├── paper.pdf            compiled paper  (51 pages: 25 body incl. references + code appendix)
├── ControlSheet.tex     control sheet (fill team number, then print and sign)
├── ControlSheet.pdf     printable control sheet
├── apmcmthesis.cls      official class file (do not edit)
├── apmcmthesis.cfg      official configuration
├── figures/             fig01 .. fig11 (PNG, 320 dpi)
├── tables/              tab01 .. tab10, generated automatically from results/*.json
├── results/             eda.json, q1.json ... q4.json — the single source of truth
├── eda/                 eda_report.md, the data audit report
├── code/                all analysis scripts
├── env.txt              exact package versions (pip freeze)
└── README.md
```

## Environment

Python 3.14 with the versions pinned in `env.txt`. Key packages:

| Package | Version | Used for |
|---|---|---|
| pandas | 2.3.3 | data handling |
| numpy | 2.4.6 | numerics |
| scipy | 1.18.1 | Kruskal-Wallis, Mann-Whitney, Fisher exact, curve fitting |
| statsmodels | 0.15.0 | GLM binomial, ordered logit, multinomial logit |
| scikit-learn | 1.9.1 | random forest, LDA, SVM, cross-validation |
| lifelines | 0.30.3 | Kaplan-Meier, Cox, Weibull AFT |
| scikit-posthocs | 0.18.0 | Dunn post-hoc tests |
| matplotlib / seaborn | 3.11.2 / 0.13.2 | figures |

All paths are resolved relative to `code/common.py`, so the package runs from any
directory. The raw data are bundled in `data/`; set the environment variable
`APMCM_DATA` to point at another copy if needed.

## Reproduce every number in the paper

Run in this order. Each script writes its own JSON into `results/`.

```powershell
cd D:\Grade 2\数学建模\APMCM2026_C
python code\00_eda.py      # -> results/eda.json, eda/eda_report.md
python code\01_q1.py       # -> results/q1.json, fig01-fig03
python code\02_q2.py       # -> results/q2.json, fig04-fig06   (~1-2 min, 1000 bootstrap)
python code\03_q3.py       # -> results/q3.json, fig07-fig09
python code\04_q4.py       # -> results/q4.json, fig10-fig11
python code\05_tables.py   # -> tables/tab01..tab10.tex
```

All random processes use `seed = 42` (see `common.py`). Re-running the pipeline from a
clean `results/` reproduces the same JSON values and therefore the same tables.

## Compile the paper

```powershell
cd D:\Grade 2\数学建模\APMCM2026_C
pdflatex paper.tex
pdflatex paper.tex
```

Two passes are required: the first builds the cross-references and the table of contents,
the second resolves `\pageref{LastPage}` in the header. Expected result: 0 errors,
0 undefined references. Warnings about `\headheight` are suppressed via
`\setlength{\headheight}{15pt}`.

## Traceability contract

Every number printed in the paper comes from `results/*.json`. The tables are not typed
by hand: `05_tables.py` formats the JSON directly into `tables/*.tex`, and `paper.tex`
includes those files. To check a claim, open the corresponding JSON key.

Two statements are worth checking explicitly because they are the core of the analysis:

- `results/q1.json → classifiers`: accuracy 0.481 (six raw measures), 0.639 (engineered),
  0.944 (raw plus structural flags, leakage audit only).
- `results/q2.json → radius_m` and `model_form_radius_m`: the point estimate and the
  model-form band reported in Table 6.

## Before submission

1. Replace `apmcm26311695` in `paper.tex` and `ControlSheet.tex` with the real team number
   (three places: `\baominghao`, and the header is generated automatically).
2. Fill school, member names and supervisor in `ControlSheet.tex`, recompile, print and
   sign it, then scan to `Capmcm26311695cns.pdf`.
3. Rename `paper.pdf` to `Capmcm26311695.pdf`.
4. Keep the header free of names and institutions; the main body must stay at or below
   25 pages (currently 25).
