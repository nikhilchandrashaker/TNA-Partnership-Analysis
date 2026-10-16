"""Write the cleaned tables back into a single Excel workbook (seed sheets kept)."""
import pathlib, pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
ROOT = pathlib.Path(__file__).resolve().parents[1]; D = ROOT / "data"
wb = load_workbook(D / "raw_seed_workbook.xlsx")
for old in ("Title_Crossover_History", "Talent_Movement"):
    if old in wb.sheetnames: del wb[old]
for name, f in [("Title_Reigns", "title_reigns.csv"), ("Talent_Movement", "talent_movement.csv"),
                ("TV_Audience_AEW_Era", "audience_tv_impact_aew_era.csv"), ("Audience_Context", "audience_context.csv"),
                ("Events_Clean", "events_clean.csv"), ("Completeness_Audit", "completeness_audit.csv"),
                ("Sources_Full", "sources.csv")]:
    df = pd.read_csv(D / f).fillna("")
    if name in wb.sheetnames: del wb[name]
    ws = wb.create_sheet(name); ws.append(list(df.columns))
    for r in df.itertuples(index=False): ws.append(list(r))
    for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F2937")
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    for col in ws.columns: ws.column_dimensions[col[0].column_letter].width = min(48, max(12, max(len(str(c.value or "")) for c in col[:30]) + 2))
wb.save(ROOT / "tna_partnership_analytics_comprehensive_working.xlsx")
print("workbook written")
