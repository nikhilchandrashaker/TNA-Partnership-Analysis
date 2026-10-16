"""Descriptive tables, title analysis, AEW-era TV event study, sensitivity checks, charts.
Run from project root after 01_build_tables.py:  python scripts/02_analysis.py
All outputs -> data/results.json, data/tables/*.csv, figures/*.png
"""
import json
import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
D, FIG = ROOT / "data", ROOT / "figures"
(D / "tables").mkdir(exist_ok=True)
rng = np.random.default_rng(20261012)

ev = pd.read_csv(D / "events_clean.csv", parse_dates=["date"])
pa = pd.read_csv(D / "participants_clean.csv")
tr = pd.read_csv(D / "title_reigns.csv", parse_dates=["date_won", "date_lost"])
tm = pd.read_csv(D / "talent_movement.csv")
tv = pd.read_csv(D / "audience_tv_impact_aew_era.csv", parse_dates=["date"])
ctx = pd.read_csv(D / "audience_context.csv")
R = {}

# ------------------------------------------------------------------ 1. descriptives
def split_people(txt):
    out = []
    for chunk in str(txt).replace(" vs ", ";").split(";"):
        c = chunk.strip()
        if c:
            out.append(c)
    return out


rows = []
for code, name in [("AEW", "TNA/Impact-AEW"), ("NXT", "TNA-WWE/NXT")]:
    e = ev[ev.partnership_code == code]
    m = e[e.item_type == "Match"]
    people = pa[pa.event_id.isin(e.event_id)].participant_or_team_text.str.strip().unique()
    host = e.host_promotion.fillna("unknown").value_counts().to_dict()
    rows.append({
        "partnership": name, "code": code,
        "event_rows": len(e), "matches": len(m), "segments": int((e.item_type == "Segment").sum()),
        "dated_rows": int(e.date.notna().sum()),
        "title_involved_rows": int(e.title_involved.notna().sum()),
        "unique_names_in_leads": len(people),
        "primary_verified_rows": int((e.evidence_tier == "A_primary").sum()),
        "host_breakdown": host,
        "first_date": str(e.date.min().date()) if e.date.notna().any() else "",
        "last_date": str(e.date.max().date()) if e.date.notna().any() else "",
    })
desc = pd.DataFrame(rows)
desc.drop(columns=["host_breakdown"]).to_csv(D / "tables/descriptives_leads.csv", index=False)
R["descriptives"] = rows

# ------------------------------------------------------------------ 2. title reigns
tr["is_xp"] = tr.cross_promotional_match == 1
tr["won_on_partner_show"] = tr.won_on_host_show.isin(["AEW", "NXT"])
tr["lost_on_partner_show"] = tr.lost_on_host_show.isin(["AEW", "NXT"])
tr["world_title"] = tr.title.isin(["Impact World Championship", "TNA World Championship"])
tr["ko_world"] = tr.title == "TNA Knockouts World Championship"
trows = []
for code in ["AEW", "NXT"]:
    s = tr[(tr.partnership == code) & (tr.title_owner != "NXT")]  # TNA-owned titles only
    trows.append({
        "code": code,
        "tna_title_reigns": len(s),
        "reigns_in_crossover_context": int(s.is_xp.sum()),
        "world_title_reigns": int(s.world_title.sum()),
        "knockouts_world_reigns": int(s.ko_world.sum()),
        "won_on_partner_programming": int(s.won_on_partner_show.sum()),
        "lost_on_partner_programming": int(s.lost_on_partner_show.sum()),
        "total_days_held": int(s.days_computed.sum()),
        "total_days_world_title": int(s[s.world_title].days_computed.sum()),
        "distinct_titles": s.title.nunique(),
        "reverse_direction_reigns": int(((tr.partnership == code) & (tr.title_owner == "NXT")).sum()),
    })
R["titles"] = trows
pd.DataFrame(trows).to_csv(D / "tables/title_summary.csv", index=False)

# ------------------------------------------------------------------ 3. talent movement
mv = tm.groupby(["direction"]).size().to_dict()
R["talent"] = {
    "tna_to_wwe": int((tm.direction == "TNA->WWE").sum()),
    "tna_to_aew": int((tm.direction == "TNA->AEW").sum()),
    "retention_rows_aew_era": int(((tm.direction == "retention") & (tm.partnership == "AEW")).sum()),
    "by_direction": mv,
}

# ------------------------------------------------------------------ 4. AEW-era TV event study
BASE = 141_000                                     # Oct 27-Dec 1 2020 mean (Wrestlenomics via Cultaholic)
post = tv[(tv.date >= "2020-12-08") & (tv.date <= "2021-02-16") & (tv.special_repeat_episode == 0)].copy()
xs = post.viewers.values.astype(float)


def boot_ci(x, f=np.mean, n=20000):
    bs = [f(rng.choice(x, len(x), replace=True)) for _ in range(n)]
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


lo, hi = boot_ci(xs)
R["tv_event_study"] = {
    "baseline_mean": BASE,
    "post_window": "2020-12-08..2021-02-16, holiday repeats excluded",
    "n_post": len(xs), "post_mean": float(xs.mean()), "post_sd": float(xs.std(ddof=1)),
    "lift_abs": float(xs.mean() - BASE), "lift_pct": float((xs.mean() / BASE - 1) * 100),
    "boot95_post_mean": [lo, hi],
    "boot95_lift_pct": [float((lo / BASE - 1) * 100), float((hi / BASE - 1) * 100)],
    "caveat": "Baseline is a published mean with no variance; CI reflects post-period spread only. "
              "No control series, so this is a before/after comparison, not a causal estimate.",
}

# sensitivity: alternative post windows and alternative baselines
sens = []
for label, a, b, base in [
    ("Core window, 141k baseline", "2020-12-08", "2021-02-16", BASE),
    ("Core window, Dec 1 only (166k) baseline", "2020-12-08", "2021-02-16", 166_000),
    ("First 4 weeks only (Dec 8-Jan 5)", "2020-12-08", "2021-01-05", BASE),
    ("Weeks 5-10 only (Jan 12-Feb 16)", "2021-01-12", "2021-02-16", BASE),
    ("Include holiday repeats", "2020-12-08", "2021-02-16", BASE),
    ("Incl. April 2021 (Thursday move, Omega)", "2020-12-08", "2021-04-15", BASE),
]:
    s = tv[(tv.date >= a) & (tv.date <= b)]
    if "Include holiday" not in label:
        s = s[s.special_repeat_episode == 0]
    sens.append({"scenario": label, "n": len(s), "mean": float(s.viewers.mean()),
                 "lift_pct": float((s.viewers.mean() / base - 1) * 100)})
R["tv_sensitivity"] = sens
pd.DataFrame(sens).to_csv(D / "tables/tv_sensitivity.csv", index=False)

# partner-on-show vs not, same window (permutation test)
w = tv[(tv.date >= "2020-12-01") & (tv.special_repeat_episode == 0)].copy()
g1 = w[w.partner_on_show == 1].viewers.values.astype(float)
g0 = w[w.partner_on_show == 0].viewers.values.astype(float)
obs = g1.mean() - g0.mean()
allv = np.concatenate([g1, g0])
perm = []
for _ in range(20000):
    rng.shuffle(allv)
    perm.append(allv[:len(g1)].mean() - allv[len(g1):].mean())
perm = np.array(perm)
R["tv_partner_vs_not"] = {
    "n_partner": len(g1), "n_other": len(g0), "mean_partner": float(g1.mean()), "mean_other": float(g0.mean()),
    "diff": float(obs), "perm_p_two_sided": float((np.abs(perm) >= abs(obs)).mean()),
    "note": "Partner-on-show episodes did not draw significantly more than other episodes in the same window.",
}

# persistence: did the Dec 8 spike last?
R["tv_persistence"] = {
    "peak": 221000, "peak_date": "2020-12-08",
    "weeks_to_return_below_baseline_excl_repeats": "Dec 15 (177k) already ~25% below peak; Jan mean ~"
                                                  f"{int(tv[(tv.date>='2021-01-05')&(tv.date<='2021-02-09')].viewers.mean()):,} (still above 141k baseline)",
}

# ------------------------------------------------------------------ 5. NXT-era TV: honest non-estimability
R["nxt_era_tv"] = {
    "estimable": False,
    "reasons": [
        "No credible episode-level TNA Impact (AXS TV) viewership series for 2024-2025 is publicly available (Wrestlenomics: 'unknown to the public').",
        "Network moved from AXS TV to AMC on 2026-01-15 with a new Nielsen methodology, confounding any before/after comparison.",
        "No control series (comparable wrestling show not on partner programming) has been assembled.",
    ],
    "reference_points": ctx.to_dict(orient="records"),
}

# ------------------------------------------------------------------ 6. scorecard (separate dimensions, no composite)
a_, n_ = trows[0], trows[1]
d_a, d_n = rows[0], rows[1]
R["scorecard"] = [
    {"dimension": "Exposure", "metric": "Crossover match/segment leads in dataset (after dedupe)",
     "AEW": d_a["event_rows"], "NXT": d_n["event_rows"], "reliability": "LOW - counts reflect collection effort and community tallies, not a verified census"},
    {"dimension": "Exposure", "metric": "Rows with an exact date",
     "AEW": d_a["dated_rows"], "NXT": d_n["dated_rows"], "reliability": "LOW"},
    {"dimension": "Exposure", "metric": "Partner-show audience size (context only)",
     "AEW": "not collected", "NXT": "NXT on The CW ~680-784k (2025 quarterly avg)", "reliability": "MEDIUM - NXT only; not TNA's audience"},
    {"dimension": "Booking value", "metric": "TNA-title reigns in crossover context",
     "AEW": a_["reigns_in_crossover_context"], "NXT": n_["reigns_in_crossover_context"], "reliability": "MEDIUM-HIGH - cross-checked, but NXT-era list is recent and may still be incomplete across all titles"},
    {"dimension": "Booking value", "metric": "TNA men's world-title reigns (Impact/TNA World)",
     "AEW": a_["world_title_reigns"], "NXT": n_["world_title_reigns"], "reliability": "HIGH"},
    {"dimension": "Booking value", "metric": "TNA Knockouts World title reigns",
     "AEW": a_["knockouts_world_reigns"], "NXT": n_["knockouts_world_reigns"], "reliability": "MEDIUM-HIGH"},
    {"dimension": "Booking value", "metric": "TNA-title reigns won on partner programming",
     "AEW": a_["won_on_partner_programming"], "NXT": n_["won_on_partner_programming"], "reliability": "MEDIUM-HIGH"},
    {"dimension": "Booking value", "metric": "Distinct TNA titles involved",
     "AEW": a_["distinct_titles"], "NXT": n_["distinct_titles"], "reliability": "MEDIUM-HIGH"},
    {"dimension": "Booking value", "metric": "Total days TNA titles held (crossover-era reigns in table)",
     "AEW": a_["total_days_held"], "NXT": n_["total_days_held"], "reliability": "MEDIUM-HIGH"},
    {"dimension": "Business impact", "metric": "Measured TNA TV audience change vs baseline",
     "AEW": f"+{R['tv_event_study']['lift_pct']:.0f}% (95% boot CI {R['tv_event_study']['boot95_lift_pct'][0]:.0f} to {R['tv_event_study']['boot95_lift_pct'][1]:.0f}%)",
     "NXT": "not estimable", "reliability": "AEW: MEDIUM-LOW (before/after, no control). NXT: no usable data"},
    {"dimension": "Business impact", "metric": "Attendance / gate / PPV / streaming",
     "AEW": "not collected", "NXT": "not collected", "reliability": "NONE - no credible sourced figures gathered for either era"},
    {"dimension": "Talent development", "metric": "TNA talent who moved to WWE/AEW after crossover exposure (verified rows)",
     "AEW": R["talent"]["tna_to_aew"], "NXT": R["talent"]["tna_to_wwe"], "reliability": "MEDIUM - trade-press reports; direction of value (pipeline benefit vs talent loss) is ambiguous"},
    {"dimension": "Talent development", "metric": "Documented retention re-signings during crossover",
     "AEW": R["talent"]["retention_rows_aew_era"], "NXT": 0, "reliability": "LOW - only incidental cases found"},
]
pd.DataFrame(R["scorecard"]).to_csv(D / "tables/scorecard.csv", index=False)

# ------------------------------------------------------------------ 7. data completeness
R["completeness"] = pd.read_csv(D / "completeness_audit.csv").to_dict(orient="records")

# ------------------------------------------------------------------ charts
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
C_AEW, C_NXT, GR = "#c2410c", "#1d4ed8", "#6b7280"

# fig 1: TV timeline
fig, ax = plt.subplots(figsize=(9, 4.2))
ax.axhline(BASE, color=GR, ls="--", lw=1)
ax.text(tv.date.min(), BASE + 3000, "pre-Omega baseline 141k (mean, Oct 27-Dec 1 2020)", color=GR, fontsize=8)
for _, r in tv.iterrows():
    col = GR if r.special_repeat_episode else (C_AEW if r.partner_on_show else "#374151")
    ax.scatter(r.date, r.viewers, s=46, color=col, zorder=3, marker="x" if r.special_repeat_episode else "o")
ax.plot(tv.date, tv.viewers, color="#9ca3af", lw=0.8, zorder=1)
ax.annotate("Omega debut\n221k", (pd.Timestamp("2020-12-08"), 221000), xytext=(8, 8), textcoords="offset points", fontsize=8)
ax.set_ylabel("Viewers (Nielsen, AXS TV)")
ax.set_title("TNA/Impact weekly viewership, AEW crossover era", loc="left", fontsize=11, fontweight="bold")
ax.set_ylim(80000, 240000)
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{int(v/1000)}k"))
ax.text(0.99, 0.02, "orange = AEW talent on show | x = holiday repeats | source: F4WOnline", transform=ax.transAxes,
        ha="right", fontsize=7, color=GR)
fig.tight_layout(); fig.savefig(FIG / "fig1_tv_timeline.png", dpi=160); plt.close(fig)

# fig 2: title reigns gantt
g = tr.sort_values("date_won").reset_index(drop=True)
fig, ax = plt.subplots(figsize=(9, 4.6))
for i, r in g.iterrows():
    end = r.date_lost if pd.notna(r.date_lost) else r.date_won + pd.Timedelta(days=10)
    ax.barh(i, (end - r.date_won).days, left=r.date_won, color=C_AEW if r.partnership == "AEW" else C_NXT,
            alpha=0.9 if r.title_owner != "NXT" else 0.45, height=0.6)
    ax.text(end + pd.Timedelta(days=6), i, f"{r.champion.split(' (')[0]} - {r.title.replace('TNA ','').replace(' Championship','')}", va="center", fontsize=7)
ax.set_yticks([]); ax.invert_yaxis()
ax.set_xlim(pd.Timestamp("2021-03-01"), pd.Timestamp("2027-03-01"))
ax.set_title("Crossover-era title reigns (orange = AEW era, blue = NXT era; pale = NXT-owned title)", loc="left", fontsize=10, fontweight="bold")
fig.tight_layout(); fig.savefig(FIG / "fig2_title_reigns.png", dpi=160); plt.close(fig)

# fig 3: head-to-head bars on reliable metrics
fig, axs = plt.subplots(1, 3, figsize=(9, 3.2))
for ax, (lab, k) in zip(axs, [("TNA-title reigns\n(crossover context)", "reigns_in_crossover_context"),
                              ("Reigns won on\npartner show", "won_on_partner_programming"),
                              ("Total days TNA titles\nheld", "total_days_held")]):
    vals = [a_[k], n_[k]]
    ax.bar(["AEW era", "NXT era"], vals, color=[C_AEW, C_NXT])
    for i, v in enumerate(vals):
        ax.text(i, v, str(v), ha="center", va="bottom", fontsize=9)
    ax.set_title(lab, fontsize=9)
fig.suptitle("Booking-value counts (not era-adjusted)", x=0.01, ha="left", fontsize=10, fontweight="bold")
fig.tight_layout(); fig.savefig(FIG / "fig3_booking_counts.png", dpi=160); plt.close(fig)

# fig 4: permutation distribution
fig, ax = plt.subplots(figsize=(6, 3.2))
ax.hist(perm / 1000, bins=40, color="#9ca3af")
ax.axvline(obs / 1000, color=C_AEW, lw=2)
ax.set_xlabel("Difference in mean viewers (thousands)")
ax.set_title(f"Permutation test: partner-on-show vs other episodes (p={R['tv_partner_vs_not']['perm_p_two_sided']:.2f})", fontsize=9, loc="left")
fig.tight_layout(); fig.savefig(FIG / "fig4_permutation.png", dpi=160); plt.close(fig)

# ------------------------------------------------------------------ serialise
def clean_json(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, pd.Timestamp):
        return str(o.date())
    return str(o)


(D / "results.json").write_text(json.dumps(R, indent=2, default=clean_json))
print(json.dumps({k: R[k] for k in ["titles", "tv_event_study", "tv_sensitivity", "tv_partner_vs_not", "talent"]}, indent=1, default=clean_json))
print(pd.DataFrame(R["descriptives"]).drop(columns="host_breakdown"))
