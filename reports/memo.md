# First-Response SLA: Operations Decision Memo

**To:** Neha Kulkarni

**Subject:** Pilot Morning-shift queue balancing before adding headcount

## Decision in brief
The cleaned dataset contains **11,200 tickets** and **2,440 first-response breaches (21.8%)**. The Morning shift carries the largest recorded burden: **2,018 breaches among 6,264 tickets (32.2% rate; 82.7% of all breaches)**. Within that shift, **chat** has the largest breach count. This shows concentration, not proof that shift or channel caused each breach.

## Business goal and value scenario
Proposed pilot goal: lower the overall breach rate from **21.8% to 15%** by rebalancing queue intake and shift handoff, then compare the same measure after four weeks. The 15% is a management test target—not a threshold inferred by the dataset. At about **650 tickets/week**, a quarter is **650 x 13 = 8,450 tickets**. If the target were sustained, the policy-based exposure reduction would be approximately **(21.8% - 15%) x 8,450 x Rs 350 = Rs 200,688 per quarter**. This is potential credit exposure, not verified cash savings.

## Recommended action
Run a four-week queue-balancing pilot focused on Morning chat work: review arrival/backlog timing, agree an overflow trigger with the adjacent shift, and monitor weekly breach rate and volume. Keep current staffing during the test; review staffing only after measuring demand and handoff effects. Do not use the agent table as a punitive ranking.

## Confidence and caveats
SLA thresholds and the Rs 350 credit rule come from the supplied support policy. The pipeline deduplicates 616 repeated ticket IDs and reports roster mismatches (1 zero-match; 0 multiple-match). Data-quality checks requiring review: resolution_timestamp_validation, missing_critical_fields, impossible_csat_values. The theme model is exploratory and has no human-labeled accuracy score; read examples before acting. Credit exposure assumes the policy applies to every breach and is not an audited payout total. Re-run the pipeline when the source data changes.
