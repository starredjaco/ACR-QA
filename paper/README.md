# ACR-QA Thesis Paper

LaTeX source for the IEEE-style thesis paper that accompanies the
ACR-QA platform. Drafted in Phases A.4–A.5 of the v5.0.0 plan.

## Build

```bash
cd paper/
pdflatex acrqa_thesis.tex
bibtex   acrqa_thesis
pdflatex acrqa_thesis.tex
pdflatex acrqa_thesis.tex
```

(`pdflatex` and `bibtex` must be installed locally; we don't ship them.)

## Status

| Section | Status |
|---|---|
| Abstract | ✅ drafted (A.4) |
| 1. Introduction | ✅ drafted (A.4) |
| 2. Related Work | ✅ drafted (A.4) |
| 3. Methodology | ✅ drafted (A.4) |
| 4. Heuristic Risk Predictor | ⏳ A.5 |
| 5. Time-Travel Analyzer | ⏳ A.5 |
| 6. Evaluation | ⏳ A.5 |
| 7. Discussion | ⏳ A.5 |
| 8. Conclusion | ⏳ A.5 |

Dr. Samy review: scheduled for end of Phase A.5.
