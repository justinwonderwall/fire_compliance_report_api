# AI-Powered Fire Compliance Report Generator

Automated pipeline that transforms unstructured technician field notes into structured, AS1851-2012 compliant draft reports — triggered by Google Forms and orchestrated through Zapier.

## Background

Fire protection compliance in Australia is governed by **AS1851-2012** (*Routine Service of Fire Protection Systems and Equipment*). After each site visit, technicians must submit maintenance reports documenting inspected equipment, defects found, actions taken, and compliance status for every item.

Traditionally this requires manually converting raw field notes into formal compliance language — time-consuming, inconsistent, and error-prone. This system automates that step: a technician submits a Google Form, the workflow triggers automatically, and OpenAI GPT extracts a fully structured, AS1851-referenced draft report for qualified human review before it reaches the client.

## System Architecture

![alt text](workflow.png)

## Tech Stack

| Layer | Technology |
|---|---|
| Form & Data Capture | Google Forms |
| Response Storage | Google Sheets (auto-linked to Forms) |
| Workflow Automation | Zapier |
| Backend API | FastAPI (Python 3.12) |
| AI Engine | OpenAI API — `gpt-4.1-mini` |
| Document Generation | Google Docs (template-based) |
| Admin Notification | Gmail |
| Deployment | Render|

## AI Capabilities

The OpenAI integration performs the following on every submission:

| # | Capability |
|---|---|
| 1 | Extract device name, location, and condition from raw notes |
| 2 | Handle mixed-language or fragmented technician input |
| 3 | Split a single block of notes into individual per-equipment records |
| 4 | Map each item to the correct AS1851-2012 clause |
| 5 | Assign compliance status: `PASS` / `FAIL` / `ACTION REQUIRED` |
| 6 | Rewrite informal notes into formal AS1851-compliant English |
| 7 | Auto-generate a unique report number (`FR-YYYYMMDD-HHMMSS`) |
| 8 | Recommend next service interval per item (months) |
| 9 | Generate an overall compliance summary paragraph |

## What This Service Does

- Accepts technician service records from Zapier via a validated webhook.
- Validates a bearer token to prevent unauthorised access.
- Sends inspection notes and defect summary to OpenAI for structured extraction and formal language rewriting.
- Returns Zapier-friendly fields for Google Docs templating, compliance reporting, and admin review.

## API Contract

### Endpoint

`POST /api/v1/generate-report`

### Auth Header

`Authorization: Bearer <API_BEARER_TOKEN>`

### Request Body

```json
{
  "technician_name": "Justin Lu",
  "date_of_service": "2026-04-13",
  "client_name": "ABC Property Management",
  "site_address": "12 Queen St, Perth WA",
  "service_level": "6-Monthly",
  "raw_inspection_notes": "2nd floor extinguisher pressure low, replaced tag. pump ok. basement panel showing minor fault on zone 3, needs follow up.",
  "site_photo_references": [
    "https://drive.google.com/file/d/example-photo-1/view"
  ],
  "critical_defects_identified": "No",
  "defect_details_and_recommendations": "Minor basement panel fault on zone 3. Recommend follow-up investigation and rectification.",
  "declaration_confirmed": true,
  "digital_signature": "Justin Lu"
}
```

### Response Body

```json
{
  "status": "success",
  "report_number": "FR-20260413-143012",
  "draft_title": "[DRAFT] Fire Protection Maintenance Report — ABC Property Management — 2026-04-13 (FR-20260413-143012)",
  "client_name": "ABC Property Management",
  "site_address": "12 Queen St, Perth WA",
  "date_of_service": "2026-04-13",
  "technician_name": "Justin Lu",
  "service_level": "6-Monthly",
  "critical_defects_identified": "No",
  "defect_details_and_recommendations": "Minor basement panel fault on zone 3. Recommend follow-up investigation and rectification.",
  "declaration_status": "Confirmed by technician in form submission.",
  "digital_signature": "Justin Lu",
  "site_photo_references": [
    "https://drive.google.com/file/d/example-photo-1/view"
  ],
  "site_photo_references_list": "1. https://drive.google.com/file/d/example-photo-1/view",
  "overall_compliance": "CONDITIONALLY COMPLIANT",
  "report_summary": "A 6-monthly routine service was conducted at 12 Queen St, Perth WA on 13 April 2026 in accordance with AS1851-2012. Three items were inspected: one PASS, zero FAIL, and two ACTION REQUIRED. The most critical finding is a minor fault recorded on Zone 3 of the basement fire indicator panel, requiring follow-up investigation. This report is a draft pending qualified technician sign-off.",
  "inspected_items_count": 3,
  "pass_count": 1,
  "fail_count": 0,
  "action_required_count": 2,
  "issues_found_list": "1. Fire extinguisher on Level 2 recorded with pressure below serviceable range.\n2. Fire indicator panel in the basement recorded a minor fault on Zone 3.",
  "actions_taken_list": "1. Maintenance tag replaced on Level 2 portable fire extinguisher.",
  "follow_up_required": "Yes — Zone 3 panel fault requires further investigation and rectification in accordance with AS1851-2012 Clause 20.",
  "review_status": "Draft — Requires Qualified Technician Sign-off",
  "formatted_markdown": "# [DRAFT] Fire Protection Maintenance Report — ...",
  "inspected_items": [
    {
      "item_number": 1,
      "item_name": "Portable Fire Extinguisher (CO2)",
      "location": "Level 2 — East Corridor",
      "compliance_status": "ACTION REQUIRED",
      "as1851_clause": "Clause 10, Table 10.1",
      "observation": "Pressure gauge reading below serviceable range as defined in AS1851-2012 Table 10.1. Maintenance tag replaced during service visit.",
      "issue_found": "Pressure gauge reading below serviceable range.",
      "action_taken": "Maintenance tag replaced.",
      "action_required": "Extinguisher to be pressure-tested or replaced in accordance with AS1851-2012 Clause 10.",
      "next_service_months": 6,
      "follow_up": "Confirm pressure-test or replacement outcome at next scheduled visit."
    }
  ],
  "missing_information": [
    "Asset identifiers (serial numbers or tag IDs) were not recorded in technician notes.",
    "Fire pump service outcome not documented."
  ]
}
```

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `API_BEARER_TOKEN` | Yes | Shared secret checked on incoming Zapier webhook calls |
| `OPENAI_API_KEY` | Yes | API key for the OpenAI request |
| `OPENAI_MODEL` | No | Defaults to `gpt-4.1-mini` |
| `OPENAI_TIMEOUT_SECONDS` | No | Defaults to `45` |

Store these values in a local `.env` file. The app loads `.env` automatically on startup.

## Deployment

### Render (Recommended)

This repository includes a `render.yaml` blueprint for one-click deployment.

1. Push the project to GitHub.
2. In Render, choose `New +` -> `Blueprint`.
3. Select your GitHub repository.
4. Render will detect `render.yaml` and create a web service.
5. In the service settings, set the environment variables:
   - `API_BEARER_TOKEN`
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (optional)
   - `OPENAI_TIMEOUT_SECONDS` (optional)
6. Deploy and verify:

```bash
curl https://YOUR-RENDER-URL.onrender.com/healthz
```

## Local Run

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Fill in `.env` using `.env.example` as a reference.

4. Start the API:

```bash
uvicorn app:app --reload
```

## Example cURL Request

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/generate-report" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer replace-me" \
  -d '{
    "technician_name": "Justin Lu",
    "date_of_service": "2026-04-13",
    "client_name": "ABC Property Management",
    "site_address": "12 Queen St, Perth WA",
    "service_level": "6-Monthly",
    "raw_inspection_notes": "2nd floor extinguisher pressure low, replaced tag. pump ok. basement panel showing minor fault on zone 3, needs follow up.",
    "site_photo_references": ["https://drive.google.com/file/d/example-photo-1/view"],
    "critical_defects_identified": "No",
    "defect_details_and_recommendations": "Minor basement panel fault on zone 3. Recommend follow-up investigation and rectification.",
    "declaration_confirmed": true,
    "digital_signature": "Justin Lu"
  }'
```

## Zapier Flow

1. **Trigger** — `Google Forms` -> `New Form Response`
2. **Formatter** — `Formatter by Zapier` -> `Date / Time` converts `Date of Service` into `YYYY-MM-DD`
3. **Action** — `Webhooks by Zapier` sends a `POST` request to this FastAPI endpoint
4. **Action** — `Google Docs` creates a `[DRAFT]` report from a template using the structured JSON fields
5. **Action** — `Gmail` emails the generated draft link to an admin for review

Recommended field mapping for Step 3:

- `technician_name` -> `Technician Name`
- `date_of_service` -> Formatter `Output`
- `client_name` -> `Client Name`
- `site_address` -> `Site Address`
- `service_level` -> `Service Level`
- `raw_inspection_notes` -> `Raw Inspection Notes`
- `site_photo_references` -> `Site Photos`
- `critical_defects_identified` -> `Were any Critical Defects identified during this service?`
- `defect_details_and_recommendations` -> `Defect Details & Recommendations`
- `declaration_confirmed` -> `Declaration`
- `digital_signature` -> `Digital Signature`

## Risk Controls

- The report title is always marked `[DRAFT]`.
- The AI prompt explicitly forbids invented data — missing details are flagged in `missing_information`.
- The service does not make legal compliance decisions. `PASS`/`FAIL`/`ACTION REQUIRED` are draft assessments only.
- Final issuance requires review and sign-off by a qualified fire protection technician.
- Client issue must happen only after a separate internal review and approval step.
