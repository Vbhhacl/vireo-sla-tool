# Three-minute screen-recording script

**Recording:** screen capture only; no slides. The text in quotation marks is a read-aloud script. Bracketed text is an on-screen cue, not spoken narration. Keep the pace conversational; this is about 330 words.

## 0:00–0:25 — Prompt and scope
[Show the Vireo Pulse Command Center.]

“ I started with this request: build a small, reliable AI-assisted SLA tool from the supplied README, policy, and data, and show the breach pattern, business impact, validation, and limitations. I then emphasized two constraints: the support policy is the source of truth, and the data must not be used to claim unsupported causes. ”

## 0:25–0:55 — What the numbers say
[Point to the SLA Pulse and shift spotlight.]

“ The cleaned dataset contains 11,200 tickets and 2,440 first-response breaches: 21.79 percent. At the policy’s 350-rupee credit per breach, that is 854,000 rupees of estimated exposure—not audited savings. Morning has 2,018 breaches, or 82.7 percent of all breaches, with a 32.2 percent breach rate. That is concentration in the data, not proof that the shift or its agents caused the breaches. ”

## 0:55–1:25 — Explore and filter
[Open Shift Intelligence; click “Focus Morning”; show the filtered result.]

“ These filters are shared across the views. Selecting Morning updates the analysis to 6,264 tickets and a 32.2 percent breach rate. The proposed four-week pilot target is 15 percent; it is a test target, not a historical result. At 650 tickets per week, the quarter scenario is: the 6.7857 percentage-point reduction times 8,450 tickets times 350 rupees—about 200,700 rupees of potential exposure reduction, not guaranteed cash savings. ”

## 1:25–2:00 — Investigate and explain
[Show Agent Lens, Ticket Explorer, then AI Insights.]

“ Agent Lens shows weekly rates with workload context rather than a punitive ranking. Ticket Explorer lets me search and inspect the underlying message, notes, response time, policy threshold, and roster assignment. The text themes use local TF-IDF and K-means clustering, with a keyword baseline. There is no external LLM, no Mistral call, and no API cost. The themes are exploratory—not verified root causes—and their semantic accuracy has not been measured. ”

## 2:00–2:30 — What changed and what I discarded
[Show Data Quality and the generated validation report.]

“ The first dashboard was a static KPI and table view. I replaced it with Vireo Pulse’s shared filters, shift lanes, agent-week matrix, ticket investigation, evidence panel, and data-quality view. I discarded chatbot behavior, paid or free external LLM calls, causal claims about staffing or transfers, and ‘worst agent’ rankings. They were unnecessary for this decision or unsupported by this observational data. ”

## 2:30–3:00 — Validation and handoff
[Briefly show test results, then the public repository README.]

“ Nine regression tests pass, covering SLA thresholds, time zones, data handling, text-theme reproducibility, and shared filtering. That checks software behavior; it does not prove the AI themes are semantically correct. One ticket has no roster match, and the source also has data-quality warnings, so those need review. The next step is to validate the 15 percent target with operations, run a four-week queue-balancing pilot, and compare the same measures afterward. ”
