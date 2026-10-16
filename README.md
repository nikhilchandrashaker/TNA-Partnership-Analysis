# TNA partnership analytics: AEW (2020-21) vs WWE/NXT (2024-26)

Contents: `data/` cleaned CSVs + results.json | `scripts/` regenerate everything | `notebooks/analysis.ipynb` | `docs/paper.md`, `docs/data_dictionary.md` | `figures/` | `dashboard/index.html` | `tna_partnership_analytics_comprehensive_working.xlsx`.

Reproduce: `pip install -r requirements.txt && ./run_all.sh` (run from this folder).

Key rules: blank = unknown, never zero; titles recorded by where they were won, not by promotion affiliation; every row carries a source and verification status; composite scores are deliberately not computed.
Status: dataset is a research seed (event rows mostly secondary leads). Title reigns, AEW-era TV audience and talent moves were researched and cross-checked Oct 2026. NXT-era audience/business data and all attendance/revenue data are missing. See paper section 6.
