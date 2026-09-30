# Three-minute screen-recording script

Record the screen directly; do not use slides. Keep Vireo Pulse, generated reports, and terminal evidence visible as you move through the product.

**0:00–0:25 — Prompt and scope**
- Say the core prompt in one sentence: “Build a small reliable AI-assisted SLA tool from the supplied README, policy, and data; report weekly shift/agent burden, business impact, validation, and limitations.”
- Mention the follow-up constraint: use the policy as source of truth and do not state unsupported causes as facts.
- State the proposed pilot goal visible in the app: reduce the measured 21.8% breach rate to 15% in four weeks; 15% is a test target, not a historical result.

**0:25–0:50 — Data and policy pipeline**
- Show the input data and support policy, then the pipeline command/output.
- Explain deduplication, UTC-to-IST conversion, roster-window matching, and channel-specific response thresholds.
- Note that 1 of 11,200 tickets is unmatched to the roster and is surfaced as REVIEW.

**0:50–1:35 — Command Center and shared filters**
- Show the SLA Pulse: 11,200 tickets, 2,440 breaches, 21.8%, and Rs 854,000 estimated policy exposure.
- Show Morning's 2,018/2,440 breaches (82.7%) and 32.2% rate, explicitly calling it concentration, not causality or an agent verdict.
- Open Shift Intelligence and click “Focus Morning”; show the global filter and filtered analysis update.
- Explain the quarter arithmetic: (21.7857% - 15%) x 650 tickets/week x 13 weeks x Rs 350 ≈ Rs 200,700 potential exposure reduction, not guaranteed savings.

**1:35–2:05 — Investigation and AI evidence**
- Open Agent Lens to show the weekly breach-rate matrix, then Ticket Explorer to search and inspect a ticket incident.
- Open AI Insights. Explain local TF-IDF/KMeans themes and the deterministic evidence readout; all numeric values are computed from the active filter state, with no LLM inventing metrics.
- State semantic accuracy is unknown because there is no human-labeled benchmark; no paid API is used.

**2:05–2:35 — What changed and what was discarded**
- Version 1 was a static KPI/trend/table with a fixed explanation. It was replaced after review with Vireo Pulse: a data-derived shift spotlight, shared filters, investigation views, evidence panel, and local ML text themes.
- Say what was discarded: punitive “worst agent” framing, unsupported causal claims about transfers/staffing, and an external paid LLM/chatbot because they were not needed to answer the operations question and would add cost/dependency.
- Be clear that local clustering is still exploratory, not a validated root-cause engine.

**2:35–3:00 — Validation and close**
- Show Data Quality and generated validation artifacts; show terminal evidence that nine regression tests pass and the pipeline completes.
- State the limits: 0 missing/invalid keyword labels is output coverage only, not semantic correctness; credit exposure is policy-based, not audited payout; pilot impact must be measured after implementation.
- End with the actionable question: test queue balancing around the Morning-shift workload and review the same metrics after four weeks.
