# Google Docs Report Template

Copy the content below into a new Google Doc.
Every `{{placeholder}}` will be replaced by Zapier when a new report is generated.

---

## How to set up

1. Go to Google Docs → New blank document
2. Name it: `Fire Compliance Report Template`
3. Copy everything in the "Template Content" section below into the document
4. Do NOT change any `{{placeholder}}` text — Zapier replaces these exactly
5. Note the document ID from the URL:
   `https://docs.google.com/document/d/YOUR_DOCUMENT_ID_HERE/edit`
6. In Zapier Step 4, select this document as the template

---

## Template Content

---

# [DRAFT] Fire Protection Maintenance Report

**{{draft_title}}**

---

## Service Details

| Field | Value |
|---|---|
| Report Number | {{report_number}} |
| Standard | AS1851-2012 Routine Service of Fire Protection Systems |
| Technician Name | {{technician_name}} |
| Date of Service | {{date_of_service}} |
| Client Name | {{client_name}} |
| Site Address | {{site_address}} |
| Service Level | {{service_level}} |
| Critical Defects Identified | {{critical_defects_identified}} |
| Declaration Status | {{declaration_status}} |
| Digital Signature | {{digital_signature}} |

---

## Overall Compliance Status

**{{overall_compliance}}**

| Items Inspected | PASS | FAIL | ACTION REQUIRED |
|---|---|---|---|
| {{inspected_items_count}} | {{pass_count}} | {{fail_count}} | {{action_required_count}} |

---

## Executive Summary

{{report_summary}}

---

## Issues Found

{{issues_found_list}}

---

## Actions Taken

{{actions_taken_list}}

---

## Defects & Recommendations

{{defect_details_and_recommendations}}

---

## Follow Up Required

{{follow_up_required}}

---

## Missing Information

{{missing_information}}

---

## Site Photo References

{{site_photo_references_list}}

---

## Full Inspection Report

{{formatted_markdown}}

---

## Compliance Notice

This document is an AI-generated draft for administrative assistance only.
It must be reviewed and approved by a qualified fire protection technician
before it is used as compliance evidence or issued to a client.
Prepared with reference to AS1851-2012.

---

**Review Status:** {{review_status}}
