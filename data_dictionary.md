# Data dictionary
Blank = unknown / not collected. Never zero-filled. All tables in `data/`.

**events_clean.csv** (71 rows) event_id; date; partnership / partnership_code (AEW|NXT); show_name; host_promotion; item_type (Match|Segment); cross_promotional (1/0); participants; result_or_outcome; title_involved; source_type; source_url; verification_status; evidence_tier (A_primary | C_secondary_lead | S_segment).
**events_removed_duplicates.csv** seed rows dropped as duplicates (same participants, same date or an undated copy of a dated lead).
**participants_clean.csv / talent_inventory.csv** participant rows linked by event_id; roster-level discovery leads.
**title_reigns.csv** reign_id; title; title_owner; champion; date_won; won_at_event; won_on_host_show (where it was won; no promotion-affiliation label by design); cross_promotional_match (1 = sources frame it as crossover; blank = unstated); opponent_or_prior; date_lost; lost_at_event; lost_on_host_show; days_held_reported; days_computed; days_check; defenses_reported; partnership; source_url; verification_status; notes.
**talent_movement.csv** movement_id; wrestler; previous_promotion; new_promotion; tna_connection; movement_date (may be month/year); first/last_crossover_appearance; contract_status; subsequent_outcomes; direction (TNA->WWE, AEW->TNA, retention); partnership; source_url; source_type; verification_status; notes.
**audience_tv_impact_aew_era.csv** date; viewers (Nielsen live+same-day); demo_18_49; note; partner_on_show (1 = AEW talent on that episode); special_repeat_episode (1 = holiday repeat, excluded from main estimate); source_url; verification_status.
**audience_context.csv** period; measure; value; unit; source; source_url; caveat. Mixed metrics; not for direct comparison.
**sources.csv / completeness_audit.csv** source register; counts of documented items per partnership.
**tables/** derived outputs; **results.json** all numeric results used by dashboard and paper.
