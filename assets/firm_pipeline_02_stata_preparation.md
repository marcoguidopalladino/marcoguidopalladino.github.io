# Firm Dynamics & Skill — Firm-side accounting pipeline 2/3: Stata preparation

**Status:** current implementation handoff, 8 October 2026  
**Project:** STRUPRO / Firm Dynamics & Skill  
**Code documented:** `panel_firm_LK_pfprep.do`  
**Execution record:** `panel_firm_prepare.smcl`  
**Aggregate diagnostic:** `ts_FARE_aggregates.dta`  
**Scope:** transform the annual SAS exports into the cleaned 2002–2019 SIREN-year accounting panel used for the worker merge.

---

## 1. What this stage does

```text
int_data/raw/ficus_2002.dta
...
int_data/raw/ficus_2019.dta
        |
        | drop invalid SIREN
        | harmonize NAF
        | append years
        | enforce one fid × year
        | keep analytical accounting variables
        | baseline positivity cleaning
        v
int_data/panel_firm_balancesheet.dta
        |
        +--> output/ts_FARE_aggregates.dta
```

The Stata stage fixes the current analytical horizon at:

```stata
global max_year 2019
```

This aligns the firm panel with the current worker-side horizon. Later FARE extracts produced by SAS are not used here.

---

## 2. Annual identifier and industry preparation

For every year, the code first removes records with an unusable firm identifier:

```stata
drop if siren==""
drop if siren=="000000000"
```

These are data-validity exclusions, not economic sample restrictions.

The code then renames the annual industry variable:

```stata
rename nace apet
```

### Pre-2008 industry harmonization

For 2002–2007:

```stata
merge m:1 apet using "...\apet_cw.dta", update
keep if _m==3
```

Only observations successfully matched to the NAF crosswalk are retained.

The common industry variables are then:

```text
nace_5d   harmonized five-digit industry
nace_2d   first two digits of nace_5d
```

### 2008 onward

The SAS export already carries the later industry classification, so the Stata code directly constructs:

```stata
gen nace_2d=substr(apet,1,2)
rename apet nace_5d
```

### Observation counts not available at this point

The current log starts **after** the annual SIREN cleaning, pre-2008 crosswalk, append, and SIREN-year deduplication. Therefore the current SMCL does **not** identify separately:

- how many blank/zero SIRENs are removed;
- how many pre-2008 records fail the industry crosswalk;
- how many SIREN-year duplicates are removed.

Those losses should not be inferred from the later counts.

---

## 3. Adopted SIREN-year perimeter

After appending all annual files:

```stata
rename siren fid
gduplicates drop fid year, force
```

The current operational panel therefore contains at most one observation per:

```text
fid × year
```

### Important implementation choice

`gduplicates drop ..., force` keeps one record when duplicate SIREN-years exist without using an economic selection rule.

This is currently accepted as an operational perimeter for the first PF implementation, but it has two implications:

1. duplicate records are silently resolved according to their existing order;
2. because the log starts after this command, the number of duplicate SIREN-years removed is not currently recorded.

This should eventually be audited, but it is not a blocker for the first estimator.

After these operations, the SMCL records:

```text
38,265,697 SIREN-year observations
```

over 2002–2019.

---

## 4. Variables retained in the analytical accounting panel

The Stata preparation keeps:

```text
fid
year
nace_2d
nace_5d

labcost
amort
interest

revenue
production_total
materials_core
intermediate_consumption
value_added

capital
capital_net
investment
```

Variables constructed in SAS but not required downstream are discarded here.

At this point, no PF choice is imposed between:
- `production_total` and `revenue`;
- `materials_core` and `intermediate_consumption`;
- `capital` and `capital_net`.

The **baseline cleaning**, however, is tied to the current baseline PF variables described below.

---

## 5. Baseline positivity cleaning

The current code applies:

```stata
local vars revenue intermediate_consumption capital
foreach x of local vars {
    keep if `x'>0 & `x'<.
}
```

Thus the cleaned panel requires:

```text
revenue > 0
intermediate_consumption > 0
capital > 0
```

No positivity condition is currently imposed on:
- `production_total`;
- `materials_core`;
- `value_added`;
- `capital_net`;
- `investment`;
- `labcost`;
- `employment` (which is not retained in this Stata output).

This is deliberate: the cleaning is currently minimal and tied only to the baseline log PF objects.

### Sequential observation losses

The SMCL gives the exact losses:

| Step | Additional observations removed | Remaining |
|---|---:|---:|
| Before positivity cleaning | — | 38,265,697 |
| Require `revenue > 0` | 2,835,242 | 35,430,455 |
| Require `intermediate_consumption > 0` | 230,632 | 35,199,823 |
| Require `capital > 0` | 5,295,710 | 29,904,113 |

Relative to the starting harmonized panel:

- the revenue rule removes **7.4%**;
- the intermediate-consumption rule removes an additional **0.6%**;
- the capital rule removes an additional **13.8%**;
- overall, **21.9%** of SIREN-years are removed;
- **78.1%** remain.

The final cleaned firm panel contains:

```text
29,904,113 SIREN-year observations
```

---

## 6. Cleaning by year

![Counts before and after cleaning](firm_stata_doc_assets/stata_counts_before_after_cleaning.png)

The positivity rules do not affect all years equally.

![Retention rate](firm_stata_doc_assets/stata_cleaning_retention_rate.png)

Retention is around 80–85% through most of 2002–2014, then falls sharply:

```text
2014: 81.1%
2015: 66.8%
2016: 62.9%
2017: 61.5%
2018: 74.3%
```

This is a **real diagnostic issue** for the firm pipeline. The current SMCL reports only the total loss from each sequential filter, not the loss **by year and filter**, so the available log does not establish which of `revenue`, `intermediate_consumption`, or `capital` causes the 2015–2017 change.

Before treating the firm sample as fully validated, the code should record annual failure rates for each positivity condition separately.

An important counterpoint is that the aggregate accounting series remain smooth over 2015–2017. The count break therefore does not translate into a comparable break in aggregate revenue or inputs. This is consistent with the excluded observations being disproportionately small, but the current aggregate data alone cannot establish that explanation.

---

## 7. Aggregate accounting diagnostics

After cleaning, the code collapses the surviving panel to annual sums:

```stata
gcollapse (sum) ///
    labcost amort interest revenue production_total ///
    materials_core intermediate_consumption value_added ///
    capital capital_net investment, by(year)
```

and saves:

```text
output/ts_FARE_aggregates.dta
```

These series are diagnostics of the **cleaned firm panel**, not raw FICUS/FARE totals.

### 7.1 Output and intermediate-input aggregates

![Output and intermediate-input aggregates](firm_stata_doc_assets/stata_aggregates_output_inputs_index.png)

The main accounting aggregates are broadly continuous across the FICUS-to-FARE transition and through the later years. The graph indexes each series to 2007 = 100 so that concepts with different levels can be compared on the same scale.

The smoothness of the aggregates is reassuring for the accounting mappings, but it is not by itself proof of conceptual equivalence across regimes.

### 7.2 Accounting ratios

![Aggregate accounting ratios](firm_stata_doc_assets/stata_aggregate_ratios.png)

The aggregate ratios are notably stable over the full 2002–2019 period:

- `intermediate_consumption / revenue` ranges from approximately **0.731 to 0.756**;
- `materials_core / revenue` from **0.441 to 0.463**;
- `value_added / revenue` from **0.266 to 0.285**;
- `capital_net / capital` from **0.482 to 0.517**.

This is a useful harmonization check because it is less sensitive than levels to aggregate growth and inflation.

### 7.3 Capital and investment

![Capital aggregates](firm_stata_doc_assets/stata_aggregates_capital_index.png)

Gross and net capital move closely together and the net/gross ratio is stable around one half.

The clear exception is:

```text
investment = 0 in 2008
```

This reinforces the unresolved status of the provisional 2008 investment mapping. `investment` should not be used for PIM construction until the 2008 source variable is verified.

---

## 8. FICUS-to-FARE transition

The uncleaned downstream count falls from:

```text
2007: 2,171,447
2008: 1,982,041
```

whereas after positivity cleaning it moves from:

```text
2007: 1,736,123
2008: 1,693,485
```

Thus the 2008 transition is visible in the number of available SIREN-years, but much less strongly in the cleaned analytical panel.

The aggregate accounting ratios also remain close around the transition. At this stage the evidence is therefore consistent with a workable FICUS/FARE splice for the baseline accounting concepts.

This does **not** resolve the separate profiling question or prove that every source concept is identical across regimes.

---

## 9. What this stage does not do

The resulting panel is still **not** the PF estimation sample.

In particular, this Stata stage does not yet:

- merge worker-side total hours or skill;
- require positive worker hours;
- impose the materials-share restriction;
- impose the value-added-share restriction;
- deflate revenue, intermediate inputs, or capital;
- restrict on worker-side coverage;
- create GNR or GMM variables.

Those choices belong to the merge / PF-data preparation handoff.

---

## 10. Output

The final firm-side file is:

```text
int_data/panel_firm_balancesheet.dta
```

with:

```text
29,904,113 SIREN-year observations
```

before the worker-side merge.

---

## 11. Choices and diagnostics to carry forward

The current Stata preparation makes the following choices:

1. **Analytical horizon:** stop at 2019 even though SAS extracts later FARE years.
2. **Invalid SIRENs:** drop blank and all-zero identifiers.
3. **Pre-2008 industry:** keep only successful `apet_cw.dta` matches.
4. **SIREN-year duplicates:** force one record per firm-year without a substantive duplicate-selection rule.
5. **Baseline cleaning:** require positive finite `revenue`, `intermediate_consumption`, and `capital` only.
6. **Alternative accounting concepts:** retain `production_total`, `materials_core`, and `capital_net` without making them sample restrictions.
7. **Aggregates:** monitor annual sums and accounting ratios after cleaning.
8. **2015–2017:** the unusually large cleaning-related loss of observations requires a filter-by-filter annual diagnostic.
9. **2008 investment:** do not use until the source mapping is verified.
10. **No deflation yet:** all monetary variables remain nominal in `panel_firm_balancesheet.dta`.

The next handoff should document the **merge with the worker-side SIREN-year panel and construction of the preliminary PF estimation sample**, including annual merge rates and the observation loss from PF-specific share and hours restrictions.
