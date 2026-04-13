# AI-Powered Fire Compliance Report Generator

FastAPI MVP for a Zapier-driven workflow that turns unstructured fire maintenance notes into a structured JSON payload and a `[DRAFT]` Markdown report for human review.

## What This Service Does

- Accepts technician notes from Zapier or any HTTP client.
- Validates a simple bearer token so the webhook is not exposed publicly.
- Sends the notes to OpenAI for structured extraction and professional wording.
- Returns Zapier-friendly fields for Google Docs templating and admin review.

## API Contract

### Endpoint

`POST /api/v1/generate-report`

### Auth Header

`Authorization: Bearer <API_BEARER_TOKEN>`

### Request Body

```json
{
  "client_name": "ABC Property Management",
  "site_address": "12 Queen St, Perth WA",
  "service_date": "2026-04-13",
  "technician_name": "Justin Lu",
  "system_type": "Mixed fire safety equipment",
  "raw_notes": "2nd floor extinguisher pressure low, replaced tag. pump ok. basement panel showing minor fault on zone 3, needs follow up."
}
```

### Response Body

```json
{
  "status": "success",
  "report_summary": "Routine maintenance draft completed for mixed fire safety equipment. Some systems appeared operational based on the technician notes, while specific issues were identified for follow-up. This draft requires review by a qualified person before issue.",
  "inspected_items_count": 3,
  "formatted_markdown": "# [DRAFT] Fire Maintenance Report\n\n...",
  "issues_found_list": "1. Fire extinguisher on Level 2 recorded with low pressure.\n2. Fire indicator panel in the basement recorded a minor fault on Zone 3.",
  "actions_taken_list": "1. Replaced tag on the Level 2 fire extinguisher.",
  "follow_up_required": "Yes - the reported Zone 3 panel fault requires further investigation.",
  "review_status": "Draft - Requires Admin Review",
  "inspected_items": [
    {
      "item_name": "Portable fire extinguisher",
      "location": "Level 2",
      "observation": "Pressure noted as low.",
      "issue_found": "Low pressure condition recorded.",
      "action_taken": "Tag replaced.",
      "follow_up": "Pressure condition should be assessed by a qualified person."
    }
  ],
  "missing_information": [
    "Asset identifiers were not provided in technician notes."
  ]
}
```

## Environment Variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `API_BEARER_TOKEN` | Yes | Shared secret checked on incoming Zapier webhook calls |
| `OPENAI_API_KEY` | Yes | API key for the OpenAI request |
| `OPENAI_MODEL` | No | Defaults to `gpt-5.4-mini` |
| `OPENAI_TIMEOUT_SECONDS` | No | Defaults to `45` |

You can now store these values in a local `.env` file. The app loads `.env` automatically on startup.

## Deployment

### Render

Render is the fastest option for this project. This repository now includes a `render.yaml` blueprint.

1. Push the project to GitHub.
2. In Render, choose `New +` -> `Blueprint`.
3. Select your GitHub repository.
4. Render will detect `render.yaml` and create a web service.
5. In the service settings, set the environment variables:
   - `API_BEARER_TOKEN`
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL`
   - `OPENAI_TIMEOUT_SECONDS`
6. Deploy and test:

```bash
curl https://YOUR-RENDER-URL.onrender.com/healthz
```

Render web services must listen on `0.0.0.0`, and Render expects a public HTTP service on its assigned port. This project's start command in `render.yaml` is configured accordingly.

### Railway

This repository also includes `railway.json`.

1. Push the project to GitHub.
2. In Railway, click `New Project`.
3. Choose `Deploy from GitHub repo`.
4. Select this repository.
5. In the service settings, click `Generate Domain` so Zapier can reach it publicly.
6. Add the same environment variables as above.
7. Deploy and test the generated domain.

### Fly.io

Fly.io is workable, but it is more CLI-oriented than Render or Railway for a small API-only MVP.

1. Install `flyctl` and sign in.
2. From the project directory, run:

```bash
fly launch
```

3. When prompted, either let Fly generate config or point it to the included `Dockerfile`.
4. Set secrets:

```bash
fly secrets set API_BEARER_TOKEN=... OPENAI_API_KEY=... OPENAI_MODEL=gpt-5.4-mini OPENAI_TIMEOUT_SECONDS=45
```

5. Deploy:

```bash
fly deploy
```

### Recommended Order

1. Use Render if you want the simplest public deployment.
2. Use Railway if you prefer GitHub-first deployment and an integrated dashboard.
3. Use Fly.io only if you are comfortable managing deployment via CLI and Docker-style packaging.

## Local Run

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Fill in `.env`:

Open the local `.env` file and replace the placeholder values with your real token and API key.

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
    "client_name": "ABC Property Management",
    "site_address": "12 Queen St, Perth WA",
    "service_date": "2026-04-13",
    "technician_name": "Justin Lu",
    "system_type": "Mixed fire safety equipment",
    "raw_notes": "2nd floor extinguisher pressure low, replaced tag. pump ok. basement panel showing minor fault on zone 3, needs follow up."
  }'
```

## Zapier Flow

1. Trigger: Google Forms or Typeform submission.
2. Action: `Webhooks by Zapier` sends a `POST` request to this FastAPI endpoint.
3. Action: Zapier maps response fields into a Google Docs template.
4. Action: Zapier emails the generated draft link to an admin for review.

## Risk Controls

- The report title is always marked `[DRAFT]`.
- The prompt explicitly forbids invented data.
- The service does not make legal compliance decisions or automated pass/fail determinations.
- Final issuance still requires review and sign-off by a qualified person.
