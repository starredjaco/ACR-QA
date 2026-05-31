# X4 — Time-Travel Predictive Risk Backtest

**Date:** 2026-05-31
**Dataset:** Django CVE history 2019–2023 (30 CVEs)
**Checkpoints:** 10 Django releases (2.2–4.2)
**Predictor:** ACR-QA `RiskPredictor` — 6-feature weighted linear model
**Top-N evaluated:** top-20 files per checkpoint

## Overview

This evaluation backtests ACR-QA's `RiskPredictor` engine against Django's
documented CVE history. At each of 10 Django release checkpoints, the predictor
is run in "time-travel" mode: git statistics (churn, author count, file age) are
computed as of the release date, not the present. The top-20 highest-risk
files are compared against files actually patched by CVEs in the following 12
months. A Fisher's exact test measures whether the overlap exceeds chance.

## Results

| Checkpoint | Files | CVEs | CVE-files | Overlap | P@20 | R@CVE | p-value |
|---|---|---|---|---|---|---|---|
| Django 2.2 | 382 | 8 | 6 | 1 | 0.050 | 0.167 | 0.2774  |
| Django 3.0 | 373 | 5 | 3 | 1 | 0.050 | 0.333 | 0.1528  |
| Django 3.1 | 375 | 6 | 6 | 1 | 0.050 | 0.167 | 0.2819  |
| Django 3.2 | 380 | 7 | 7 | 0 | 0.000 | 0.000 | 1.0000  |
| Django 4.0 | 382 | 7 | 6 | 0 | 0.000 | 0.000 | 1.0000  |
| Django 4.1 | 384 | 6 | 5 | 0 | 0.000 | 0.000 | 1.0000  |
| Django 4.2 | 390 | 4 | 4 | 1 | 0.050 | 0.250 | 0.1906  |
| Django 3.0.4 | 373 | 4 | 3 | 1 | 0.050 | 0.333 | 0.1528  |
| Django 3.1.5 | 375 | 6 | 6 | 0 | 0.000 | 0.000 | 1.0000  |
| Django 3.2.10 | 380 | 7 | 6 | 0 | 0.000 | 0.000 | 1.0000  |

**Aggregate (pooled Fisher's exact):** p = 0.1366, OR = 1.935, lift = 1.83×

Legend: ✓ p<0.05, ~ p<0.10; P@20 = precision at top-20; R@CVE = recall on CVE-affected files

## CVE Ground Truth

30 Django CVEs from 2019–2023 were sourced from Django's official
security release changelog. Each CVE is associated with the file(s) patched in its
fix commit:

| CVE | Fix Date | Affected Files |
|---|---|---|
| CVE-2019-6975 | 2019-02-11 | `django/utils/numberformat.py` |
| CVE-2019-12308 | 2019-06-03 | `django/contrib/admin/options.py` |
| CVE-2019-14232 | 2019-08-01 | `django/utils/text.py` |
| CVE-2019-14233 | 2019-08-01 | `django/utils/html.py` |
| CVE-2019-14234 | 2019-08-01 | `django/db/models/sql/query.py` |
| CVE-2019-14235 | 2019-08-01 | `django/utils/encoding.py` |
| CVE-2019-19844 | 2019-12-18 | `django/contrib/auth/forms.py` |
| CVE-2020-7471 | 2020-02-03 | `django/contrib/postgres/aggregates/mixins.py` |
| CVE-2020-9402 | 2020-03-04 | `django/contrib/gis/db/models/sql/conversion.py` |
| CVE-2020-13254 | 2020-06-03 | `django/core/cache/backends/memcached.py` |
| CVE-2020-13596 | 2020-06-03 | `django/contrib/admin/options.py` |
| CVE-2021-3281 | 2021-02-01 | `django/utils/archive.py` |
| CVE-2021-28658 | 2021-04-06 | `django/core/files/uploadhandler.py` |
| CVE-2021-31542 | 2021-05-06 | `django/core/files/storage.py`, `django/http/multipartparser.py` |
| CVE-2021-33203 | 2021-06-02 | `django/contrib/admindocs/views.py` |
| CVE-2021-33571 | 2021-06-02 | `django/core/validators.py` |
| CVE-2021-35042 | 2021-07-01 | `django/db/models/sql/compiler.py` |
| CVE-2022-22818 | 2022-02-01 | `django/template/defaulttags.py` |
| CVE-2022-23833 | 2022-02-01 | `django/utils/http.py` |
| CVE-2022-28346 | 2022-04-11 | `django/db/models/sql/compiler.py` |
| CVE-2022-28347 | 2022-04-11 | `django/db/models/sql/compiler.py` |
| CVE-2022-34265 | 2022-07-04 | `django/db/models/functions/datetime.py` |
| CVE-2022-36359 | 2022-08-03 | `django/views/static.py` |
| CVE-2022-41323 | 2022-10-04 | `django/utils/translation/__init__.py` |
| CVE-2023-23969 | 2023-02-01 | `django/http/multipartparser.py` |
| CVE-2023-24580 | 2023-02-01 | `django/http/multipartparser.py` |
| CVE-2023-31047 | 2023-05-03 | `django/core/validators.py` |
| CVE-2023-36053 | 2023-07-03 | `django/utils/regex_helper.py` |
| CVE-2023-41164 | 2023-09-04 | `django/utils/encoding.py` |
| CVE-2023-43665 | 2023-10-04 | `django/contrib/admin/templatetags/admin_list.py` |

## Methodology

1. **Time-aware scoring:** At each checkpoint, git statistics are bounded by
   the release date — `churn_90d` uses commits in `[release_date - 90d, release_date]`,
   `author_count` uses commits `--until=release_date`, and `age_days` measures
   from the file's first commit up to the release date. This prevents information
   leakage from future commits.

2. **Scope:** Scanning is restricted to 8 security-relevant directories
   (`django/db/`, `django/http/`, `django/utils/`, `django/contrib/auth/`,
   `django/contrib/admin/`, `django/core/`, `django/views/`, `django/template/`).
   This matches the directories where 100% of the 30 curated CVEs reside.

3. **Scoring:** ACR-QA `RiskPredictor` uses a 6-feature weighted linear model:
   complexity (0.20), churn (0.20), age (0.05), authors (0.10), coverage gap (0.15),
   HIGH finding density (0.30). The HIGH-density feature is the strongest predictor
   and is computed from Bandit findings on the checkout.

4. **Statistical test:** Fisher's exact test (one-sided, alternative="greater")
   on the 2×2 contingency table: top-20 × CVE-affected. Null hypothesis:
   predicted top-20 files are no more likely to contain CVEs than random files.

## Interpretation

The pooled result is not statistically significant at p < 0.05.
The predictor shows a weak signal with a lift of 1.83× over random baseline.

**Critical caveat:** The RiskPredictor was designed to prioritize analyst
attention, not to predict specific CVEs. The HIGH-density feature (weight 0.30)
dominates the score and measures *current* vulnerability density, not future
risk from latent flaws. A predictor with 0 current findings will score low even
if the file has structural complexity that will attract future vulnerabilities.
The backtest therefore measures a necessary but not sufficient condition:
"ACR-QA flags the right files" rather than "ACR-QA predicts the future."

The lift metric (1.83×) compares precision@20 against the baseline
precision (fraction of all files that are CVE-affected). A lift > 1.0 means the
predictor is better than random; the absolute value depends on dataset sparsity.

Results file: `TESTS/evaluation/results/time_travel_backtest.json`
Supporting script: `scripts/run_time_travel_backtest.py`
