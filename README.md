# VIREO PULSE | Support Operations Intelligence

This repository implements VIREO PULSE, a small AI-assisted SLA operations intelligence product for Vireo Audio. The reproducible data pipeline cleans the supplied exports, validates quality, matches roster assignments in IST, calculates first-response SLA performance against the support policy, and produces the analytics consumed by the dashboard and executive memo.

## Problem and business objective
The business question is: which agents and shifts are associated with the highest weekly first-response SLA breach burden, and what operational pattern appears to explain it?

This is intentionally not a punitive ranking exercise. It reports volume, breach count, breach rate, channel mix, priority mix, and shift concentration so a support manager can decide what operational action should happen next.

## Business goal and current measurable outcome
Using the current dataset and policy rules, the generated baseline is:
- 11,200 cleaned tickets
- 2,440 breaches
- 21.8% breach rate
- estimated policy-based credit exposure: Rs 854,000

This is a policy-supported estimate based on the rule that each missed first-response target triggers a Rs 350 credit on resolution. It is an operational estimate, not a claim that all breaches are avoidable or that every credit is collectible.

### Proposed measurable pilot goal
Test a reduction in breach rate from the measured 21.8% baseline to 15% over four weeks through queue balancing and shift handoff changes. The 15% is a proposed operational target, not a result established by historical data. At about 650 tickets per week, the quarterly volume is 650 x 13 = 8,450 tickets. If the target were sustained, estimated credit exposure reduction would be (21.7857% - 15%) x 8,450 x Rs 350 = approximately Rs 200,700 per quarter. This is potential policy-based exposure, not audited cash savings; validate the target and credit applicability with operations and finance.

## Architecture
- data ingestion and cleaning
- duplicate handling and validation
- roster assignment matching by date window in IST
- SLA calculation against the policy thresholds
- weekly aggregation and business impact estimation
- AI-assisted exploratory ticket-text theme discovery
- validation and reporting
- reusable server-side dashboard filtering and aggregation
- Streamlit operations interface for shift, agent, ticket, AI evidence, and data-quality investigation

## Vireo Pulse interface
The dark operations workspace includes Command Center, SLA Timeline, Shift Intelligence, Agent Lens, Ticket Explorer, AI Insights, and Data Quality. Site, shift, team, channel, and priority filters are held in one shared state and recalculate the visible metrics and analyses together. Agent and ticket details open in contextual dialogs; the incident table previews a limited result set rather than rendering all raw records into the browser. Demo Mode guides a reviewer through the seven-page story.

The common weekly chart uses a proposed 15% pilot goal as a reference line, not a policy threshold. The policy has different targets per channel, and each ticket's breach is calculated against its own channel threshold before weekly aggregation.

## Policy-backed rules used by this tool
The support policy is treated as the source of truth. The implemented thresholds are:
- chat: 15 minutes
- voice callback: 120 minutes
- social: 240 minutes
- email: 480 minutes

The project also uses the policy's operating assumptions:
- timestamps are exported in UTC and converted to IST for SLA and roster logic
- first response is the first human reply measured from ticket creation
- a breach occurs when the first response exceeds the relevant threshold
- every breached ticket triggers a Rs 350 store credit at resolution
- shifts are defined in IST as Morning 06:00-14:00, Day 14:00-22:00, Night 22:00-06:00

## Data cleaning and validation
The raw export contains duplicated ticket IDs from the migration re-import process. The cleaning logic keeps the current helpdesk record and drops legacy duplicates. The validation layer checks:
- duplicate ticket IDs
- invalid timestamps
- impossible first-response ordering
- missing critical fields
- unexpected status, channel and priority values
- invalid CSAT values
- suspicious negative refunds
- roster match issues

## Roster matching
The roster is maintained as assignment ranges and not as a one-row-per-agent table. The workflow matches each ticket to the relevant roster row using the ticket's `agent_id`, `created_at` timestamp, and date-window logic in IST.

The logic is intentionally conservative:
- ticket timestamp must be within the assignment date window
- blank `to_date` means the assignment is open-ended
- zero-match and multiple-match cases are reported rather than silently normalized away

## AI-assisted component
The tool includes local unsupervised text-theme discovery using TF-IDF features and KMeans clustering over customer messages. Very short and placeholder-only messages are excluded, and common email/transcript boilerplate is removed from theme terms. The dashboard shows cluster sizes, representative terms, and example messages to help an operations manager explore recurring topics. It also retains a deterministic keyword classifier as a heuristic baseline for a reproducible sample.

This is AI-assisted exploratory analysis, not a chatbot or an authoritative root-cause model. Theme quality and semantic classification accuracy are not measured because the project has no human-labeled benchmark. The pipeline reports output coverage and ambiguous labels; a person must review examples before acting. No paid external API is required.

## Cost and AI usage
The local scikit-learn TF-IDF/KMeans model and keyword baseline use no paid API calls. Local runtime/compute and development time are not priced here.

Arithmetic:
- cost per run: Rs 0.00 / USD 0.00
- weekly volume assumption: approximately 650 tickets/week
- estimated monthly volume: 650 x 4.33 ≈ 2,815 (about 2,820) tickets/month
- estimated monthly cost: Rs 0.00 / USD 0.00

This is a local workflow that runs with no external model spend.

## How to run
The repo includes the supplied data and policy PDF; raw inputs should not be edited. From a clean machine with Python 3.11 or newer:

1. Create and activate the environment (Windows PowerShell):
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   On Linux/macOS, activate with `source .venv/bin/activate` instead.
2. Build reports, validation, and text-theme outputs:
   ```bash
   python -m src.pipeline
   ```
3. Launch the interactive dashboard:
   ```bash
   streamlit run app.py
   ```
4. Run regression tests:
   ```bash
   python -m pytest -q
   ```

## Deploy on Streamlit Community Cloud
1. Create a new app from the public repository `Vbhhacl/vireo-sla-tool`.
2. Select branch `main` and main file path `app.py`.
3. Use the available app URL slug `vireo-sla-tool-83j4jnw8um8vy5adqwvcpe` (the resulting URL is `https://vireo-sla-tool-83j4jnw8um8vy5adqwvcpe.streamlit.app`).
4. No secrets or API keys are required. Cloud installs packages from `requirements.txt` and reads the committed data/report CSVs.

**Public-data warning:** this repository and deployed app are public. Ticket/customer text and source data can be viewed through the repository and Ticket Explorer. Deploy only if the supplied data is approved for public access; otherwise make the repository private and confirm the hosting plan supports the desired access controls before deployment.

## Outputs
The pipeline writes the following artifacts:
- data/clean_tickets.csv
- data/clean_tickets_with_roster.csv
- data/validation_report.json
- reports/weekly_report.csv
- reports/agent_summary.csv
- reports/shift_summary.csv
- reports/business_metrics.csv
- reports/memo.md
- reports/validation_report.md
- submission-form.md
- reports/demo_script.md
- outputs/ai_validation.json
- outputs/ai_theme_summary.csv
- outputs/roster_validation.json

## Validation and assumptions
- Timestamps in the API export are UTC and are converted to Asia/Kolkata for SLA and roster logic.
- The support policy is treated as authoritative for thresholds and credit values.
- The local text-theme model and keyword baseline run without external secrets or API calls.
- AI output coverage is not semantic correctness: without human labels, accuracy is unknown.
- Any zero-match or multiple-match roster case is reported, not silently discarded.
- This project uses the provided dataset only and should be re-run for new data.

## Limitations
- Some raw data issues require operational review rather than automatic correction.
- AI driver classification is a lightweight operational tool and should be interpreted alongside the underlying ticket text.
- This project is not a causal analysis of transfers or staffing. It highlights operational concentration and leaves direct-causality claims out.
- The current version does not include paid external model calls, which keeps cost at zero but limits model sophistication.
