# Google Form Template

## Form Title

Fire Maintenance Site Notes Submission

## Form Description

Use this form to submit on-site fire maintenance records for AI-assisted draft report generation.

Important:
- Submit factual observations only.
- Do not make final compliance decisions in this form.
- The generated report is a draft and requires qualified human review before issue to the client.

## Final Question Structure

### Module 1: Header

#### 1. Technician Name
- Type: Short answer
- Required: Yes
- Question text: `Technician Name`

#### 2. Date of Service
- Type: Date
- Required: Yes
- Question text: `Date of Service`

#### 3. Client Name
- Type: Short answer
- Required: Yes
- Question text: `Client Name`

#### 4. Site Address
- Type: Paragraph
- Required: Yes
- Question text: `Site Address`

### Module 2: Service Scope & Frequency

#### 5. Service Level
- Type: Multiple choice
- Required: Yes
- Question text: `Service Level`
- Options:
  - `3-Monthly`
  - `6-Monthly`
  - `Yearly`
  - `5-Yearly`

### Module 3: Site Inspection Log

#### 6. Raw Inspection Notes
- Type: Paragraph
- Required: Yes
- Question text: `Raw Inspection Notes`
- Help text:
  `Enter fragmented site notes exactly as observed. Include locations, defects, actions taken, and follow-up needs if known. Maximum 8,000 characters.`

#### 7. Site Photos
- Type: File upload
- Required: No
- Question text:
  `Site Photos`
- Replace the temporary text item with a real Google Forms `File upload` field.

### Module 4: Defects & Rectifications Summary

#### 8. Were any Critical Defects identified during this service?
- Type: Multiple choice
- Required: Yes
- Options:
  - `Yes`
  - `No`

#### 9. Defect Details & Recommendations
- Type: Paragraph
- Required: No
- Question text: `Defect Details & Recommendations`

### Module 5: Declaration & Sign-off

#### 10. Declaration
- Type: Checkbox
- Required: Yes
- Question text: `Declaration`
- Option text:
  `I confirm this service was completed in accordance with the relevant AS 1851 service level and the notes above reflect the observed site condition.`

#### 11. Digital Signature
- Type: Short answer
- Required: Yes
- Question text: `Digital Signature`

## Recommended Settings

- Collect email addresses: Optional
- Limit to 1 response: Off
- Allow response editing: Optional
- Show link to submit another response: On

Confirmation message:

`Submission received. A draft fire maintenance report will be generated for internal review.`

## Google Sheets Link

After creating the form:

1. Open the `Responses` tab
2. Click the green Google Sheets icon
3. Create the linked response spreadsheet
4. Use that response sheet only as the backend data source for Zapier

## Zapier Mapping

### Step 1: Google Forms
- App: `Google Forms`
- Event: `New Form Response`

### Step 2: Formatter by Zapier
- App: `Formatter by Zapier`
- Event: `Date / Time`
- Transform: `Format`
- Input: `Date of Service`
- To Format: `YYYY-MM-DD`

### Step 3: Webhooks by Zapier -> POST

Map the form fields to the FastAPI request body like this:

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

## MVP Notes

- The API now accepts the updated Google Form structure directly.
- `site_photo_references` is optional. In Zapier, map whatever Google Forms returns for uploaded files.
- `declaration_confirmed` is normalized to a boolean in FastAPI, so checkbox output from Zapier is acceptable.
- The system still generates a `[DRAFT]` report only. Final client issue must happen after human review.
