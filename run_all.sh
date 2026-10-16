#!/usr/bin/env bash
set -e
python scripts/01_build_tables.py
python scripts/02_analysis.py
python scripts/03_build_dashboard.py
python scripts/04_export_workbook.py
