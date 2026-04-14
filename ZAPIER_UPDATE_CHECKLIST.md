# Zapier Update Checklist

Use this checklist after changing the Google Form structure.

## Step 1: Google Forms -> New Form Response

Re-test the trigger so Zapier loads the new fields:

- `Technician Name`
- `Date of Service`
- `Client Name`
- `Site Address`
- `Service Level`
- `Raw Inspection Notes`
- `Site Photos`
- `Were any Critical Defects identified during this service?`
- `Defect Details & Recommendations`
- `Declaration`
- `Digital Signature`

## Step 2: Formatter by Zapier -> Date / Time

- Transform: `Format`
- Input: `Date of Service`
- To Format: `YYYY-MM-DD`

Use Step 2 `Output` for the API field `date_of_service`.

## Step 3: Webhooks by Zapier -> POST

URL:

`https://fire-compliance-report-api.onrender.com/api/v1/generate-report`

Headers:

- `Authorization` -> `Bearer <API_BEARER_TOKEN>`

Payload type:

- `json`

Data mapping:

- `technician_name` -> `Technician Name`
- `date_of_service` -> Step 2 `Output`
- `client_name` -> `Client Name`
- `site_address` -> `Site Address`
- `service_level` -> `Service Level`
- `raw_inspection_notes` -> `Raw Inspection Notes`
- `site_photo_references` -> `Site Photos`
- `critical_defects_identified` -> `Were any Critical Defects identified during this service?`
- `defect_details_and_recommendations` -> `Defect Details & Recommendations`
- `declaration_confirmed` -> `Declaration`
- `digital_signature` -> `Digital Signature`

## Step 4: Google Docs -> Create Document From Template

Template placeholders to use:

- `{{report_number}}`
- `{{draft_title}}`
- `{{client_name}}`
- `{{site_address}}`
- `{{date_of_service}}`
- `{{technician_name}}`
- `{{service_level}}`
- `{{overall_compliance}}`
- `{{report_summary}}`
- `{{inspected_items_count}}`
- `{{pass_count}}`
- `{{fail_count}}`
- `{{action_required_count}}`
- `{{issues_found_list}}`
- `{{actions_taken_list}}`
- `{{follow_up_required}}`
- `{{critical_defects_identified}}`
- `{{defect_details_and_recommendations}}`
- `{{declaration_status}}`
- `{{digital_signature}}`
- `{{site_photo_references_list}}`
- `{{missing_information}}`
- `{{review_status}}`
- `{{formatted_markdown}}`

Field mapping (Step 3 response -> Google Docs placeholder):

- `{{report_number}}` -> Step 3 `Report Number`
- `{{draft_title}}` -> Step 3 `Draft Title`
- `{{client_name}}` -> Step 3 `Client Name`
- `{{site_address}}` -> Step 3 `Site Address`
- `{{date_of_service}}` -> Step 3 `Date Of Service`
- `{{technician_name}}` -> Step 3 `Technician Name`
- `{{service_level}}` -> Step 3 `Service Level`
- `{{overall_compliance}}` -> Step 3 `Overall Compliance`
- `{{report_summary}}` -> Step 3 `Report Summary`
- `{{inspected_items_count}}` -> Step 3 `Inspected Items Count`
- `{{pass_count}}` -> Step 3 `Pass Count`
- `{{fail_count}}` -> Step 3 `Fail Count`
- `{{action_required_count}}` -> Step 3 `Action Required Count`
- `{{issues_found_list}}` -> Step 3 `Issues Found List`
- `{{actions_taken_list}}` -> Step 3 `Actions Taken List`
- `{{follow_up_required}}` -> Step 3 `Follow Up Required`
- `{{critical_defects_identified}}` -> Step 3 `Critical Defects Identified`
- `{{defect_details_and_recommendations}}` -> Step 3 `Defect Details And Recommendations`
- `{{declaration_status}}` -> Step 3 `Declaration Status`
- `{{digital_signature}}` -> Step 3 `Digital Signature`
- `{{site_photo_references_list}}` -> Step 3 `Site Photo References List`
- `{{missing_information}}` -> Step 3 `Missing Information`
- `{{review_status}}` -> Step 3 `Review Status`
- `{{formatted_markdown}}` -> Step 3 `Formatted Markdown`

## Step 5: Gmail -> Send Email

Recommended internal review email:

- Subject:
  `[DRAFT] Fire Compliance Report - {{Client Name}} - {{Step 2 Output}}`

- Body should include:
  - Client name
  - Site address
  - Date of service
  - Overall compliance status
  - Item counts (PASS / FAIL / ACTION REQUIRED)
  - Report summary
  - Follow-up required
  - Missing information (if any)
  - Google Docs draft link

## MVP Boundary

This workflow should generate and notify on a draft only.

Client issue should happen only after a separate internal review / approval step.
