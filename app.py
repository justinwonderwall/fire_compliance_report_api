import json
import logging
import os
from datetime import date, datetime
from functools import lru_cache
from typing import List, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator


load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NOT_PROVIDED_TEXT = "Not provided in form submission."

# ── Capability 7: Auto report number generation ──────────────────────
def generate_report_number() -> str:
    """Auto-generate a unique report number based on timestamp."""
    return f"FR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


# ── Input model ──────────────────────────────────────────────────────
class GenerateReportRequest(BaseModel):
    technician_name: str = Field(min_length=1, max_length=120)
    date_of_service: date
    client_name: str = Field(min_length=1, max_length=200)
    site_address: str = Field(min_length=1, max_length=1000)
    service_level: str = Field(default=NOT_PROVIDED_TEXT, max_length=50)
    raw_inspection_notes: str = Field(min_length=1, max_length=8000)
    site_photo_references: List[str] = Field(default_factory=list)
    critical_defects_identified: str = Field(default=NOT_PROVIDED_TEXT, max_length=20)
    defect_details_and_recommendations: str = Field(
        default=NOT_PROVIDED_TEXT,
        max_length=5000,
    )
    declaration_confirmed: bool = False
    digital_signature: str = Field(default=NOT_PROVIDED_TEXT, max_length=200)

    @model_validator(mode="before")
    @classmethod
    def support_legacy_field_names(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        mapped = dict(data)
        if "date_of_service" not in mapped and "service_date" in mapped:
            mapped["date_of_service"] = mapped["service_date"]
        if "raw_inspection_notes" not in mapped and "raw_notes" in mapped:
            mapped["raw_inspection_notes"] = mapped["raw_notes"]
        if "service_level" not in mapped and "system_type" in mapped:
            mapped["service_level"] = mapped["system_type"]
        return mapped

    @field_validator(
        "service_level",
        "critical_defects_identified",
        "defect_details_and_recommendations",
        "digital_signature",
        mode="before",
    )
    @classmethod
    def default_missing_text_fields(cls, value: object) -> str:
        if value is None:
            return NOT_PROVIDED_TEXT
        text = str(value).strip()
        return text if text else NOT_PROVIDED_TEXT

    @field_validator("site_photo_references", mode="before")
    @classmethod
    def normalize_site_photo_references(cls, value: object) -> List[str]:
        if value in (None, "", []):
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            separators_normalized = value.replace("\r", "\n").replace(",", "\n")
            return [
                item.strip()
                for item in separators_normalized.split("\n")
                if item.strip()
            ]
        return [str(value).strip()]

    @field_validator("declaration_confirmed", mode="before")
    @classmethod
    def normalize_declaration_confirmed(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, list):
            return any(str(item).strip() for item in value)
        normalized = str(value).strip().lower()
        if normalized in {"", "false", "no", "0", "unchecked"}:
            return False
        return True


# ── AI output schema ─────────────────────────────────────────────────
# Capability 1: Device/location/status extraction
# Capability 3: Batch extraction of multiple items
# Capability 4: AS1851 clause mapping
# Capability 5: Compliance status judgment (PASS/FAIL/ACTION REQUIRED)
# Capability 6: AS1851 formal language rewrite
# Capability 8: Next service interval
# Capability 9: Professional summary paragraph

class InspectedItem(BaseModel):
    item_number: int = Field(description="Sequential item number starting at 1")
    item_name: str = Field(
        description="Standardised equipment type, e.g. 'Portable Fire Extinguisher (CO2)'"
    )
    location: str = Field(
        description="Standardised building location, e.g. 'Level 2 – East Corridor'"
    )
    # Capability 5: Compliance status
    compliance_status: Literal["PASS", "FAIL", "ACTION REQUIRED"] = Field(
        description=(
            "PASS = serviceable, no defects. "
            "FAIL = unserviceable or safety-critical defect. "
            "ACTION REQUIRED = defect found but not immediately unserviceable."
        )
    )
    # Capability 4: AS1851 clause reference
    as1851_clause: str = Field(
        description=(
            "Relevant AS1851-2012 clause. Use: "
            "Clause 10 (portable extinguishers), Clause 11 (hose reels), "
            "Clause 16 (hydrants), Clause 17 (sprinklers), Clause 18 (fire pumps), "
            "Clause 20 (fire alarm systems), Clause 22 (emergency lighting), "
            "Clause 23 (exit signs). Reference table number where applicable."
        )
    )
    # Capability 6: Formal observation rewrite
    observation: str = Field(
        description=(
            "Professional AS1851-compliant description of the item's condition. "
            "Rewrite technician's informal note into formal English."
        )
    )
    issue_found: str = Field(
        description="Specific defect found, or 'No defects identified' if PASS."
    )
    action_taken: str = Field(
        description="Actions completed on-site. Use 'No action required.' if PASS."
    )
    action_required: str = Field(
        description=(
            "Specific remediation action needed after this visit, "
            "with reference to the AS1851 clause. "
            "Use 'None.' if compliance_status is PASS."
        )
    )
    # Capability 8: Service interval
    next_service_months: int = Field(
        description=(
            "Recommended next service interval in months per AS1851-2012 schedule. "
            "Typically 6 for critical systems, 12 for standard items."
        )
    )
    follow_up: str = Field(
        description="Any outstanding follow-up note for this item."
    )


class StructuredReportDraft(BaseModel):
    # Capability 9: Professional overall summary
    overall_compliance: Literal["COMPLIANT", "NON-COMPLIANT", "CONDITIONALLY COMPLIANT"] = Field(
        description=(
            "COMPLIANT = all items PASS. "
            "NON-COMPLIANT = one or more FAIL items. "
            "CONDITIONALLY COMPLIANT = ACTION REQUIRED items present, no FAIL."
        )
    )
    report_summary: str = Field(
        description=(
            "3-5 sentences. State: (1) service level and what was inspected, "
            "(2) overall compliance outcome, "
            "(3) number of PASS / FAIL / ACTION REQUIRED items, "
            "(4) most critical finding if any. "
            "Write in formal third-person English suitable for a client-facing report."
        )
    )
    inspected_items: List[InspectedItem]
    issues_found: List[str] = Field(
        description="All defects found, as concise bullet-point strings."
    )
    actions_taken: List[str] = Field(
        description="All on-site actions completed, as concise strings."
    )
    follow_up_required: str = Field(
        description="Short sentence beginning with 'Yes' or 'No'. If yes, explain."
    )
    missing_information: List[str] = Field(
        description="Data gaps that prevent a finalised compliance report."
    )


# ── Response model ───────────────────────────────────────────────────
class GenerateReportResponse(BaseModel):
    status: str
    report_number: str
    draft_title: str
    client_name: str
    site_address: str
    date_of_service: str
    technician_name: str
    service_level: str
    critical_defects_identified: str
    defect_details_and_recommendations: str
    declaration_status: str
    digital_signature: str
    site_photo_references: List[str]
    site_photo_references_list: str
    overall_compliance: str
    report_summary: str
    inspected_items_count: int
    pass_count: int
    fail_count: int
    action_required_count: int
    formatted_markdown: str
    issues_found_list: str
    actions_taken_list: str
    follow_up_required: str
    review_status: str
    inspected_items: List[InspectedItem]
    missing_information: List[str]


# ── Settings ─────────────────────────────────────────────────────────
class Settings(BaseModel):
    api_bearer_token: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: float = 45.0


@lru_cache
def get_settings() -> Settings:
    return Settings(
        api_bearer_token=os.getenv("API_BEARER_TOKEN"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        openai_timeout_seconds=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45")),
    )


@lru_cache
def get_openai_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.openai_timeout_seconds,
    )


# ── Auth ─────────────────────────────────────────────────────────────
def require_api_token(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.api_bearer_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_BEARER_TOKEN is not configured on the server.",
        )
    expected_header = f"Bearer {settings.api_bearer_token}"
    if authorization != expected_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing bearer token.",
        )


# ── Prompts ──────────────────────────────────────────────────────────
def build_system_prompt() -> str:
    # Capability 2: explicitly handle mixed-language input
    # Capability 4-6: instruct AS1851 mapping, status judgment, formal rewrite
    return (
        "You are a senior Australian fire protection compliance officer with expert "
        "knowledge of AS1851-2012 (Routine Service of Fire Protection Systems and Equipment). "
        "\n\n"
        "Your role is to transform informal technician field notes into a structured, "
        "professional compliance report draft aligned with AS1851-2012. "
        "\n\n"
        "COMPLIANCE STATUS RULES — you MUST apply these to every inspected item:\n"
        "  - PASS: Equipment is serviceable, pressure/condition within acceptable range, "
        "no defects found, maintenance tag current.\n"
        "  - FAIL: Equipment is unserviceable or presents an immediate safety risk "
        "(e.g. missing safety pin, pressure in red zone, broken glass, inoperable panel zone).\n"
        "  - ACTION REQUIRED: Defect found but equipment is not immediately unserviceable "
        "(e.g. tag expired, minor corrosion, sprinkler head painted over, fault light on).\n"
        "\n"
        "AS1851 CLAUSE MAPPING — always reference the correct clause:\n"
        "  - Portable extinguishers: Clause 10, Table 10.1\n"
        "  - Hose reels: Clause 11\n"
        "  - Hydrant systems: Clause 16\n"
        "  - Sprinkler systems: Clause 17\n"
        "  - Fire pumps: Clause 18\n"
        "  - Fire alarm / detection systems: Clause 20\n"
        "  - Emergency lighting: Clause 22\n"
        "  - Exit signs: Clause 23\n"
        "\n"
        "FORMAL LANGUAGE: Rewrite informal notes into AS1851-compliant terminology. "
        "Example: 'pressure low' → "
        "'Pressure gauge reading below serviceable range as defined in AS1851-2012 Table 10.1. "
        "Extinguisher removed from service.' "
        "\n\n"
        "INTEGRITY RULES:\n"
        "  - Never invent specific measurements, dates, or names not in the notes.\n"
        "  - If a detail is genuinely absent, use 'Not recorded in technician notes.'\n"
        "  - Flag all missing information needed for a finalised compliance report.\n"
        "  - This output is a [DRAFT] requiring qualified human sign-off.\n"
        "\n"
        "Output valid JSON matching the provided Pydantic schema exactly."
    )


def build_user_prompt(payload: GenerateReportRequest) -> str:
    # Capability 3: prompt explicitly asks AI to split batch notes into per-item records
    return json.dumps(
        {
            "task": (
                "Extract a structured AS1851-2012 fire maintenance report from the "
                "technician's field notes below. "
                "Split the notes into individual inspected_items — one entry per "
                "distinct equipment item or observation cluster. "
                "Apply compliance_status (PASS/FAIL/ACTION REQUIRED) and the correct "
                "AS1851-2012 clause to every item. "
                "Rewrite all observations in professional AS1851-compliant English. "
                "Output is a [DRAFT] for qualified human review."
            ),
            "record": {
                "technician_name": payload.technician_name,
                "date_of_service": payload.date_of_service.isoformat(),
                "client_name": payload.client_name,
                "site_address": payload.site_address,
                "service_level": payload.service_level,
                "raw_inspection_notes": payload.raw_inspection_notes,
                "site_photo_references": payload.site_photo_references,
                "critical_defects_identified": payload.critical_defects_identified,
                "defect_details_and_recommendations": (
                    payload.defect_details_and_recommendations
                ),
                "declaration_confirmed": payload.declaration_confirmed,
                "digital_signature": payload.digital_signature,
            },
            "field_rules": {
                "overall_compliance": (
                    "COMPLIANT if all items PASS. NON-COMPLIANT if any item FAIL. "
                    "CONDITIONALLY COMPLIANT if ACTION REQUIRED present but no FAIL."
                ),
                "report_summary": (
                    "3-5 sentences covering: service scope, overall compliance outcome, "
                    "item counts (PASS/FAIL/ACTION REQUIRED), and most critical finding."
                ),
                "inspected_items": (
                    "One entry per distinct piece of equipment or observation cluster. "
                    "Every item must include compliance_status, as1851_clause, "
                    "action_required, and next_service_months."
                ),
                "issues_found": "Concise list of all defects. Empty list if none.",
                "actions_taken": "Concise list of all on-site actions completed.",
                "follow_up_required": (
                    "Begin with 'Yes' or 'No'. If yes, list what follow-up is needed."
                ),
                "missing_information": (
                    "Data gaps that would prevent a finalised compliance report."
                ),
            },
        },
        ensure_ascii=True,
    )


# ── OpenAI call ───────────────────────────────────────────────────────
def call_openai_for_report(payload: GenerateReportRequest) -> StructuredReportDraft:
    settings = get_settings()

    try:
        client = get_openai_client()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    try:
        # Use beta.chat.completions.parse for reliable structured output
        response = client.beta.chat.completions.parse(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": build_user_prompt(payload)},
            ],
            response_format=StructuredReportDraft,
            temperature=0.2,    # Low temperature: consistent, deterministic output
        )
    except Exception as exc:
        logger.exception("OpenAI request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI request failed: {exc}",
        ) from exc

    parsed = response.choices[0].message.parsed
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI response did not include a parsed structured payload.",
        )

    return parsed


# ── Rendering helpers ─────────────────────────────────────────────────
def render_numbered_list(items: List[str], empty_message: str) -> str:
    cleaned_items = [item.strip() for item in items if item.strip()]
    if not cleaned_items:
        return empty_message
    return "\n".join(
        f"{index}. {item}" for index, item in enumerate(cleaned_items, start=1)
    )


def render_photo_references(items: List[str]) -> str:
    if not items:
        return "No site photos were attached in the form submission."
    return "\n".join(
        f"{index}. {item}" for index, item in enumerate(items, start=1)
    )


def format_declaration_status(payload: GenerateReportRequest) -> str:
    return (
        "Confirmed by technician in form submission."
        if payload.declaration_confirmed
        else "Not confirmed in form submission."
    )


def build_draft_title(payload: GenerateReportRequest, report_number: str) -> str:
    return (
        f"[DRAFT] Fire Protection Maintenance Report — {payload.client_name} — "
        f"{payload.date_of_service.isoformat()} ({report_number})"
    )


def count_by_status(items: List[InspectedItem], status_value: str) -> int:
    return sum(1 for item in items if item.compliance_status == status_value)


# ── Markdown renderer ─────────────────────────────────────────────────
def render_markdown(
    payload: GenerateReportRequest,
    structured_report: StructuredReportDraft,
    report_number: str,
) -> str:
    # Per-item sections with all new fields
    inspected_sections = []
    for item in structured_report.inspected_items:
        status_badge = {
            "PASS": "✅ PASS",
            "FAIL": "❌ FAIL",
            "ACTION REQUIRED": "⚠️ ACTION REQUIRED",
        }.get(item.compliance_status, item.compliance_status)

        inspected_sections.append(
            "\n".join([
                f"### {item.item_number}. {item.item_name}",
                f"- **Status:** {status_badge}",
                f"- **AS1851-2012 Reference:** {item.as1851_clause}",
                f"- **Location:** {item.location}",
                f"- **Observation:** {item.observation}",
                f"- **Issue Found:** {item.issue_found}",
                f"- **Action Taken:** {item.action_taken}",
                f"- **Action Required:** {item.action_required}",
                f"- **Next Service:** {item.next_service_months} months",
                f"- **Follow Up:** {item.follow_up}",
            ])
        )

    inspected_items_md = (
        "\n\n".join(inspected_sections)
        if inspected_sections
        else "No inspected items could be confidently extracted from the technician notes."
    )

    pass_count = count_by_status(structured_report.inspected_items, "PASS")
    fail_count = count_by_status(structured_report.inspected_items, "FAIL")
    action_count = count_by_status(structured_report.inspected_items, "ACTION REQUIRED")

    compliance_badge = {
        "COMPLIANT": "✅ COMPLIANT",
        "NON-COMPLIANT": "❌ NON-COMPLIANT",
        "CONDITIONALLY COMPLIANT": "⚠️ CONDITIONALLY COMPLIANT",
    }.get(structured_report.overall_compliance, structured_report.overall_compliance)

    missing_information_md = render_numbered_list(
        structured_report.missing_information,
        "No missing information identified.",
    )

    return "\n".join([
        f"# {build_draft_title(payload, report_number)}",
        "",
        "## Service Details",
        f"- **Report Number:** {report_number}",
        f"- **Standard:** AS1851-2012 Routine Service of Fire Protection Systems",
        f"- **Technician Name:** {payload.technician_name}",
        f"- **Date of Service:** {payload.date_of_service.isoformat()}",
        f"- **Client Name:** {payload.client_name}",
        f"- **Site Address:** {payload.site_address}",
        f"- **Service Level:** {payload.service_level}",
        f"- **Critical Defects Identified:** {payload.critical_defects_identified}",
        f"- **Declaration Status:** {format_declaration_status(payload)}",
        f"- **Digital Signature:** {payload.digital_signature}",
        "",
        "## Overall Compliance Status",
        f"**{compliance_badge}**",
        "",
        f"| Items Inspected | PASS | FAIL | ACTION REQUIRED |",
        f"|---|---|---|---|",
        f"| {len(structured_report.inspected_items)} | {pass_count} | {fail_count} | {action_count} |",
        "",
        "## Executive Summary",
        structured_report.report_summary,
        "",
        "## Raw Inspection Notes",
        "> *Original technician notes — unmodified*",
        payload.raw_inspection_notes,
        "",
        "## Inspected Items",
        inspected_items_md,
        "",
        "## Defects and Recommendations",
        payload.defect_details_and_recommendations,
        "",
        "## Issues Found",
        render_numbered_list(
            structured_report.issues_found,
            "No issues explicitly recorded in technician notes.",
        ),
        "",
        "## Actions Taken",
        render_numbered_list(
            structured_report.actions_taken,
            "No actions explicitly recorded in technician notes.",
        ),
        "",
        "## Follow Up Required",
        structured_report.follow_up_required,
        "",
        "## Missing Information",
        missing_information_md,
        "",
        "## Site Photo References",
        render_photo_references(payload.site_photo_references),
        "",
        "## Compliance Notice",
        (
            "This document is an AI-generated draft for administrative assistance only. "
            "It must be reviewed and approved by a qualified fire protection technician "
            "before it is used as compliance evidence or issued to a client. "
            "Prepared with reference to AS1851-2012."
        ),
    ])


# ── FastAPI app ───────────────────────────────────────────────────────
app = FastAPI(
    title="AI-Powered Fire Compliance Report Generator",
    version="0.2.0",
    description=(
        "FastAPI middleware for Zapier-driven fire maintenance draft report generation. "
        "Aligned with AS1851-2012."
    ),
)


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/v1/generate-report",
    response_model=GenerateReportResponse,
    dependencies=[Depends(require_api_token)],
)
def generate_report(payload: GenerateReportRequest) -> GenerateReportResponse:
    # Capability 7: auto-generate report number
    report_number = generate_report_number()

    structured_report = call_openai_for_report(payload)
    formatted_markdown = render_markdown(payload, structured_report, report_number)

    pass_count = count_by_status(structured_report.inspected_items, "PASS")
    fail_count = count_by_status(structured_report.inspected_items, "FAIL")
    action_count = count_by_status(structured_report.inspected_items, "ACTION REQUIRED")

    return GenerateReportResponse(
        status="success",
        report_number=report_number,
        draft_title=build_draft_title(payload, report_number),
        client_name=payload.client_name,
        site_address=payload.site_address,
        date_of_service=payload.date_of_service.isoformat(),
        technician_name=payload.technician_name,
        service_level=payload.service_level,
        critical_defects_identified=payload.critical_defects_identified,
        defect_details_and_recommendations=payload.defect_details_and_recommendations,
        declaration_status=format_declaration_status(payload),
        digital_signature=payload.digital_signature,
        site_photo_references=payload.site_photo_references,
        site_photo_references_list=render_photo_references(payload.site_photo_references),
        overall_compliance=structured_report.overall_compliance,
        report_summary=structured_report.report_summary,
        inspected_items_count=len(structured_report.inspected_items),
        pass_count=pass_count,
        fail_count=fail_count,
        action_required_count=action_count,
        formatted_markdown=formatted_markdown,
        issues_found_list=render_numbered_list(
            structured_report.issues_found,
            "No issues explicitly recorded in technician notes.",
        ),
        actions_taken_list=render_numbered_list(
            structured_report.actions_taken,
            "No actions explicitly recorded in technician notes.",
        ),
        follow_up_required=structured_report.follow_up_required,
        review_status="Draft — Requires Qualified Technician Sign-off",
        inspected_items=structured_report.inspected_items,
        missing_information=structured_report.missing_information,
    )