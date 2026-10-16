"""Build cleaned, linked CSV tables from the seed workbook plus researched additions.
Run from project root:  python scripts/01_build_tables.py
Rule: blank = not collected/unknown, never zero. No figures are invented.
"""
import re
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
D = ROOT / "data"
seed = pd.read_excel(D / "raw_seed_workbook.xlsx", sheet_name=None)

# ---------- 1. events: dedupe the seed census ----------
e = seed["Event_Census_Working"].copy()


def norm(s):
    s = str(s).lower().replace("zach ", "zachary ")
    s = re.sub(r"[^a-z ;]", "", s)
    parts = sorted(p.strip() for p in re.split(r";| vs ", s) if p.strip())
    return "|".join(parts)


e["_key"] = e.participants.map(norm) + "|" + e.partnership
e["has_date"] = e.date.notna()
e = e.sort_values(["_key", "has_date"], ascending=[True, False])
# NOTE: key = same participants + same partnership. Different dates for the same pairing
# (e.g. Hard To Kill vs Impact! episode rematches) are kept only if the date differs.
e["_key2"] = e._key + "|" + e.date.astype(str)
e["dup_same_date"] = e.duplicated("_key2", keep="first") & e.has_date
e["dup_undated_lead"] = e.duplicated("_key", keep="first") & ~e.has_date
e["duplicate_of_lead"] = e.dup_same_date | e.dup_undated_lead
dups = e[e.duplicate_of_lead][["event_id", "participants", "show_name"]]
clean = (
    e[~e.duplicate_of_lead]
    .drop(columns=["_key", "_key2", "has_date", "dup_same_date", "dup_undated_lead", "duplicate_of_lead"])
    .sort_values(["partnership", "date", "event_id"])
)


def tier(v):
    v = str(v)
    if "Primary-source verified" in v or "Official show page" in v:
        return "A_primary"
    if "Non-match" in v:
        return "S_segment"
    return "C_secondary_lead"


clean["evidence_tier"] = clean.verification_status.map(tier)
clean["partnership_code"] = clean.partnership.map({"TNA/Impact–AEW": "AEW", "TNA–WWE/NXT": "NXT"})
clean.to_csv(D / "events_clean.csv", index=False)
dups.to_csv(D / "events_removed_duplicates.csv", index=False)

# ---------- 2. participants + inventory ----------
p = seed["Participant_Rows"]
p = p[p.event_id.isin(clean.event_id)].copy()
p["participant_or_team_text"] = p.participant_or_team_text.str.replace("Zach ", "Zachary ", regex=False)
p.to_csv(D / "participants_clean.csv", index=False)
seed["Talent_Inventory"].to_csv(D / "talent_inventory.csv", index=False)

# ---------- 3. title reigns (researched Oct 2026; every row carries a source) ----------
S = {
    "ko_list": "https://en.wikipedia.org/wiki/List_of_TNA_Knockouts_World_Champions",
    "cult_omega": "https://cultaholic.com/posts/christian-cage-scheduled-for-impact-wrestling-tapings",
    "fight_rampage": "https://www.fightful.com/wrestling/aew-rampage-results-81321-omega-vs-christian-cage-impact-championship-three-title-matches",
    "f4w_cage": "https://www.f4wonline.com/tna-news/christian-cage-vs-josh-alexander-set-impact-bound-glory-353826",
    "f4w_santana": "https://www.f4wonline.com/news/tna-wrestling/mike-santana-wins-world-title-tna-bound-for-glory",
    "wc_williams": "https://whatculture.com/wwe/trick-williams-becomes-first-wwe-contracted-talent-to-win-tna-world-title-wwe-news",
    "tna_hardys": "https://tnawrestling.com/news/the-hardys-become-nxt-tag-team-champions-at-the-historic-showdown-between-tna-and-nxt",
    "tna_lee": "https://tnawrestling.com/news/and-new-lei-ying-lee-becomes-tna-knockouts-world-champion-with-historic-victory-at-nxt-gold-rush",
    "wiki_ns26": "https://en.wikipedia.org/wiki/No_Surrender_(2026)",
    "f4w_grace": "https://www.f4wonline.com/news/tna-wrestling/new-knockouts-champion-crowned-at-tna-no-surrender",
}
cols = ["reign_id", "title", "title_owner", "champion", "date_won", "won_at_event", "won_on_host_show",
        "cross_promotional_match", "opponent_or_prior", "date_lost", "lost_at_event", "lost_on_host_show",
        "days_held_reported", "defenses_reported", "partnership", "source_url", "verification_status", "notes"]
R = [
    ["T01", "Impact World Championship", "TNA/Impact", "Kenny Omega", "2021-04-25", "Rebellion 2021", "Impact", 1,
     "Rich Swann (winner-takes-all vs AEW World title)", "2021-08-13", "AEW Rampage #1", "AEW", 110,
     "2 (Moose, Sami Callihan), both on Impact shows", "AEW", S["cult_omega"],
     "Cross-checked: 3 sources", "AEW World title also at stake in the win."],
    ["T02", "Impact World Championship", "TNA/Impact", "Christian Cage", "2021-08-13", "AEW Rampage #1", "AEW", 1,
     "Kenny Omega", "2021-10-23", "Bound for Glory 2021", "Impact", 71,
     "2 (Brian Myers at Emergence; Ace Austin at Victory Road 2021-09-18), both on Impact shows", "AEW",
     S["f4w_cage"], "Cross-checked: 3 sources", "Lost to Josh Alexander."],
    ["T03", "TNA World Championship", "TNA", "Trick Williams", "2025-05-25", "NXT Battleground", "NXT", 1,
     "Joe Hendry", "2025-10-12", "Bound for Glory 2025", "TNA", 140, "6 (reported)", "NXT", S["f4w_santana"],
     "Cross-checked: 3 sources", "Preceding reign (Hendry) 126 days. Ended by Mike Santana."],
    ["T04", "TNA Knockouts World Championship", "TNA", "Jacy Jayne", "2025-07-20", "Slammiversary 2025", "TNA", 1,
     "Masha Slamovich (title vs title; NXT Women's title also at stake)", "2025-08-24", "NXT Heatwave 2025", "NXT",
     35, "", "NXT", S["ko_list"], "Wikipedia list + cited PWDN report; verify on TNA site", ""],
    ["T05", "TNA Knockouts World Championship", "TNA", "Ash by Elegance", "2025-08-24", "NXT Heatwave 2025", "NXT", 1,
     "Jacy Jayne; Masha Slamovich (triple threat)", "2025-09-26", "Victory Road 2025 (vacated)", "TNA", 33, "", "NXT",
     S["ko_list"], "Wikipedia list + cited PWDN report; verify on TNA site",
     "Listed as a WWE NXT event. Title vacated for time away from the ring."],
    ["T06", "TNA Knockouts World Championship", "TNA", "Kelani Jordan", "2025-09-26", "Victory Road 2025", "TNA", 1,
     "Lei Ying Lee (vacant title)", "2025-11-18", "NXT Gold Rush Night 2", "NXT", 53,
     "1 (M by Elegance, Turning Point)", "NXT", S["ko_list"], "Wikipedia list + Wikipedia bio; verify on TNA site",
     "Resolves earlier conflict: event date 2025-09-26; she won the vacant title vs Lee."],
    ["T07", "TNA Knockouts World Championship", "TNA", "Lei Ying Lee (reign 1)", "2025-11-18", "NXT Gold Rush Night 2",
     "NXT", 1, "Kelani Jordan; Jordynne Grace (triple threat)", "2026-02-13", "No Surrender 2026", "TNA", 87, "",
     "NXT", S["tna_lee"], "Official TNA report + Wikipedia list",
     "Taped 2025-11-18, aired 2025-11-25. Recorded only by where it was won (NXT)."],
    ["T08", "TNA Knockouts World Championship", "TNA", "Arianna Grace", "2026-02-13", "No Surrender 2026", "TNA", 1,
     "Lei Ying Lee", "2026-04-15", "Impact taping (aired 2026-05-07)", "TNA", 61, "", "NXT", S["f4w_grace"],
     "Cross-checked: F4W, Wrestlezone, Wikipedia", "Resolves earlier contradictory notes."],
    ["T09", "TNA Knockouts World Championship", "TNA", "Lei Ying Lee (reign 2)", "2026-04-15",
     "Impact taping (aired 2026-05-07)", "TNA", "", "Arianna Grace", "2026-06-28", "Slammiversary 2026", "TNA", 74, "",
     "NXT", S["ko_list"], "Wikipedia list; verify",
     "Sources do not say whether this match was framed as a crossover; left blank."],
    ["T10", "TNA International Championship", "TNA", "Channing 'Stacks' Lorenzo", "2025-12-05", "Final Resolution 2025",
     "TNA", 1, "Steve Maclin", "2026-02-13", "No Surrender 2026", "TNA", 70, "", "NXT", S["wiki_ns26"],
     "Win date from earlier TNA report; loss date from Wikipedia; days computed", "Lost to Trey Miguel."],
    ["T11", "NXT Tag Team Championship", "NXT", "The Hardys (Matt Hardy; Jeff Hardy)", "2025-10-07",
     "NXT vs. TNA Showdown", "NXT / joint show", 1, "DarkState (Winners Take All)", "", "", "", None, "", "NXT",
     S["tna_hardys"], "Official TNA report + SI report",
     "Reverse direction (NXT-owned title). A reported 2025-10-25 loss date from earlier notes is UNVERIFIED and not "
     "used; an Oct 12 report still lists them as NXT tag champions."],
]
t = pd.DataFrame(R, columns=cols)
for c in ("date_won", "date_lost"):
    t[c] = pd.to_datetime(t[c], errors="coerce")
t["days_computed"] = (t.date_lost - t.date_won).dt.days


def chk(r):
    if pd.isna(r.days_computed) or pd.isna(r.days_held_reported):
        return ""
    return "match" if abs(r.days_computed - r.days_held_reported) <= 1 else "MISMATCH"


t["days_check"] = t.apply(chk, axis=1)
t.to_csv(D / "title_reigns.csv", index=False, date_format="%Y-%m-%d")

# ---------- 4. talent movement ----------
tm = pd.DataFrame([
    ["M01", "Jordynne Grace", "TNA", "WWE", "Contracted TNA talent; 2024 NXT appearances", "2025-01-27", "2024-06-04",
     "2024-11", "Reported multi-year WWE contract (Fightful)", "Debuted in 2025 Royal Rumble", "TNA->WWE", "NXT",
     "https://www.f4wonline.com/news/wwe/report-jordynne-grace-signs-multi-year-contract-with-wwe",
     "Reputable trade report",
     "TNA aware; she asked for a shorter contract. Last TNA match Genesis 2025-01-19."],
    ["M02", "Joe Hendry", "TNA", "WWE", "Contracted TNA talent; former TNA World champion", "2025-11-13", "2024-06-18",
     "2025-07-01", "Reported WWE contract; WWE bought out remainder of TNA deal",
     "Royal Rumble 2025; WrestleMania 41 vs Randy Orton; NXT roster", "TNA->WWE", "NXT",
     "https://cultaholic.com/posts/joe-hendry-officially-signs-with-wwe", "Reputable trade reports",
     "Date is the report date."],
    ["M03", "Mike Santana", "TNA", "WWE (NXT, as Cruz Montana)", "Former TNA World champion", "2026-07", "2025",
     "2026-06-28", "Reported departure after Slammiversary; NXT arrival July 2026",
     "Appeared on NXT while TNA champion earlier in 2026", "TNA->WWE", "NXT",
     "https://wrestletalk.com/features/tna-wrestling-stars-to-sign-with-wwe-2/",
     "Reputable trade reports (PWInsider via PostWrestling; WrestleTalk)",
     "Month precision only; verify the official signing date."],
    ["M04", "Mike Santana", "AEW", "TNA", "Returned to TNA", "2024", "", "", "Returned to TNA after leaving AEW",
     "Won TNA World title Oct 2025", "AEW->TNA", "none (context)", "https://www.postwrestling.com/?p=137333",
     "Reputable trade report", "Context row; not caused by either partnership."],
    ["M05", "Moose", "TNA", "TNA (re-signed)", "Retention during AEW crossover", "2021-06", "", "",
     "Re-signed with Impact; other companies reportedly interested", "Challenged Omega for Impact World title",
     "retention", "AEW", "https://wrestletalk.com/?p=271274", "Trade report", "Approximate date from article context."],
    ["M06", "Rich Swann", "TNA", "TNA (re-signed)", "Retention after AEW crossover", "2022-12", "", "",
     "Re-signed two years", "Lost title to Omega at Rebellion 2021", "retention", "AEW",
     "https://www.f4wonline.com/news/tna-wrestling/rich-swann-re-signs-contract-with-impact-wrestling",
     "Trade report", "Date from podcast interview publication."],
], columns=["movement_id", "wrestler", "previous_promotion", "new_promotion", "tna_connection", "movement_date",
            "first_crossover_appearance", "last_crossover_appearance", "contract_status", "subsequent_outcomes",
            "direction", "partnership", "source_url", "source_type", "notes"])
tm["verification_status"] = "Reported by trade press; official confirmation not checked"
tm.to_csv(D / "talent_movement.csv", index=False)

# ---------- 5. TV audience (observed values only) ----------
F4W = "https://www.f4wonline.com/tna-news/impact-wrestling-draws-best-ratings-december-8-333551"
F4W2 = "https://www.f4wonline.com/tna-news/impact-wrestling-ratings-down-thursday-debut-338931"
au = [
    ("2020-12-01", 166000, 0.05, "week before Omega's debut", F4W, 0, 0),
    ("2020-12-08", 221000, 0.08, "Omega's first Impact appearance", F4W, 1, 0),
    ("2020-12-15", 177000, 0.04, "Omega segment", F4W, 1, 0),
    ("2020-12-22", 133000, 0.03, "Best of 2020 pt 1 (holiday repeat)", F4W, 0, 1),
    ("2020-12-29", 103000, 0.01, "Best of 2020 pt 2 (holiday repeat)", F4W, 0, 1),
    ("2021-01-05", 148000, 0.04, "", F4W, 0, 0),
    ("2021-01-12", 161000, 0.05, "Hard to Kill go-home; Omega appears", F4W, 1, 0),
    ("2021-01-19", 147000, 0.03, "Eve of inauguration; unadvertised AEW appearances", F4W, 1, 0),
    ("2021-01-26", 186000, 0.05, "", F4W, 0, 0),
    ("2021-02-02", 173000, 0.05, "", F4W, 0, 0),
    ("2021-02-09", 153000, 0.04, "", F4W, 0, 0),
    ("2021-02-16", 197000, None, "NJPW appearance; No Surrender fallout", F4W, 0, 0),
    ("2021-04-08", 168000, 0.06, "First Thursday show; Omega in action; vs NXT TakeOver", F4W2, 1, 0),
    ("2021-04-15", 132000, 0.04, "Omega/Swann press conference", F4W2, 1, 0),
]
a = pd.DataFrame(au, columns=["date", "viewers", "demo_18_49", "note", "source_url", "partner_on_show",
                              "special_repeat_episode"])
a.insert(1, "promotion", "TNA/Impact")
a.insert(2, "show", "Impact! (AXS TV)")
a["metric"] = "Nielsen live+same-day (reported by F4W / ProWrestling.net)"
a["verification_status"] = "Secondary trade-press report; values repeated consistently across multiple articles"
a.to_csv(D / "audience_tv_impact_aew_era.csv", index=False)

ctx = pd.DataFrame([
    ["2020-10-27..12-01", "Impact on AXS mean, pre-Omega baseline", 141000, "viewers",
     "Cultaholic summary of Wrestlenomics data",
     "https://cultaholic.com/posts/was-kenny-omega-s-first-impact-wrestling-run-a-success",
     "Mean only; episode values not obtained"],
    ["2020-12-08", "TNA press release multiplatform total ('750,000+')", 750000, "mixed TV viewers + online views",
     "TNA press release (self-reported)", "https://tnawrestling.com/?p=17510",
     "Mixes Nielsen TV with Facebook/YouTube views; NOT comparable to Nielsen averages"],
    ["2024-01-18", "Impact on AXS, TNA-rebrand return episode", 112000, "viewers", "SpoilerTV via Cultaholic",
     "https://cultaholic.com/en/posts/tna-impact-return-episode-averages-112-000-viewers",
     "Pre-WWE-partnership reference"],
    ["2024-2025", "Impact on AXS typical range", "80000-100000", "viewers", "PWTorch (sporadic data)",
     "https://www.pwtorch.com/site/?p=214066", "Not a full series; Wrestlenomics calls AXS audience 'unknown to the public'"],
    ["2026-01-15..", "Impact on AMC, first 7 weeks mean", 245571, "viewers", "PWTorch (Nielsen, new methodology)",
     "https://www.pwtorch.com/site/?p=214066",
     "Network change + new Nielsen methodology confounds any NXT-era before/after comparison"],
    ["2025-Q1", "WWE NXT on The CW, quarter avg (P2+)", 784000, "viewers", "Wrestlenomics",
     "https://wrestlenomics.com/tv-ratings/2025/wwe-nxt-feb-11-on-cw-801000-viewers-0-18-p18-49-rating-tv-ratings-analysis/",
     "Size of partner audience (exposure ceiling), not TNA's audience"],
    ["2025-Q3", "WWE NXT on The CW, quarter avg (P2+)", 680000, "viewers", "Wrestlenomics",
     "https://wrestlenomics.com/tv-ratings/2025/wwe-nxt-sep-23-on-cw-617000-viewers-0-12-p18-49-rating-tv-ratings-analysis/",
     "Size of partner audience (exposure ceiling), not TNA's audience"],
], columns=["period", "measure", "value", "unit", "source", "source_url", "caveat"])
ctx.to_csv(D / "audience_context.csv", index=False)

# ---------- 6. sources ----------
src = seed["Source_Register"].copy()
extra = [[k, u, "Title reign dates/results", "Secondary/primary mix (see title_reigns.verification_status)"]
         for k, u in S.items()]
for u, use in [
    (F4W, "Impact viewers/demo Dec 2020-Feb 2021"),
    (F2 := F4W2, "Impact viewers April 2021"),
    ("https://www.pwtorch.com/site/?p=214066", "Impact AXS vs AMC viewership"),
    ("https://wrestlenomics.com/articles/2025/tna-moves-to-amc-in-2026-and-a-historical-look-at-impacts-tv-ratings-2005-2023/",
     "Historical Impact ratings context"),
]:
    extra.append(["audience", u, use, "Secondary (trade press)"])
src = pd.concat([src, pd.DataFrame(extra, columns=src.columns)]).drop_duplicates("url")
src.to_csv(D / "sources.csv", index=False)

# ---------- 7. completeness audit ----------
aud = []
for code, name in [("AEW", "TNA/Impact-AEW"), ("NXT", "TNA-WWE/NXT")]:
    ev = clean[clean.partnership_code == code]
    m = ev[ev.item_type == "Match"]
    aud += [
        [name, "event rows after dedupe", len(ev)],
        [name, "match rows with a date", int(m.date.notna().sum())],
        [name, "match rows primary-source verified", int((m.evidence_tier == "A_primary").sum())],
        [name, "episode-level TNA TV viewership points", int(len(a)) if code == "AEW" else 0],
        [name, "title reigns documented", int((t.partnership == code).sum())],
        [name, "talent movement rows", int(tm.partnership.astype(str).str.contains(code).sum())],
    ]
pd.DataFrame(aud, columns=["partnership", "indicator", "count"]).to_csv(D / "completeness_audit.csv", index=False)

print("events:", len(seed["Event_Census_Working"]), "->", len(clean), "| removed:", len(dups))
print(pd.read_csv(D / "completeness_audit.csv").pivot(index="indicator", columns="partnership", values="count"))
print(t[["reign_id", "champion", "days_computed", "days_held_reported", "days_check"]])
