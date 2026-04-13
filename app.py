import json
import logging
import os
from datetime import date
from functools import lru_cache
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException, status
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field


load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GenerateReportRequest(BaseModel):
    client_name: str = Field(min_length=1, max_length=200)
    site_address: str = Field(min_length=1, max_length=300)
    service_date: date
    technician_name: str = Field(min_length=1, max_length=120)
    system_type: str = Field(min_length=1, max_length=200)
    raw_notes: str = Field(min_length=1, max_length=5000)


class InspectedItem(BaseModel):
    item_name: str
    location: str
    observation: str
    issue_found: str
    action_taken: str
    follow_up: str


class StructuredReportDraft(BaseModel):
    report_summary: str
    inspected_items: List[InspectedItem]
    issues_found: List[str]
    actions_taken: List[str]
    follow_up_required: str
    missing_information: List[str]


class GenerateReportResponse(BaseModel):
    status: str
    report_summary: str
    inspected_items_count: int
    formatted_markdown: str
    issues_found_list: str
    actions_taken_list: str
    follow_up_required: str
    review_status: str
    inspected_items: List[InspectedItem]
    missing_information: List[str]


class Settings(BaseModel):
    api_bearer_token: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"
    openai_timeout_seconds: float = 45.0


@lru_cache
def get_settings() -> Settings:
    return Settings(
        api_bearer_token=os.getenv("API_BEARER_TOKEN"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
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


def build_system_prompt() -> str:
    return (
        "You are an Australian fire compliance documentation assistant with deep "
        "familiarity with AS1851 maintenance terminology. Convert fragmented "
        "technician notes into professional written English for a draft report. "
        "This is an assistive workflow only, not a compliance decision engine. "
        "Never invent observations, measurements, pass/fail outcomes, or actions. "
        "If details are missing, say 'Not provided in technician notes'. "
        "Preserve uncertainty and explicitly flag follow-up needs. "
        "Output valid JSON matching the provided schema only."
    )


def build_user_prompt(payload: GenerateReportRequest) -> str:
    return json.dumps(
        {
            "task": (
                "Extract structured fire maintenance report data from the input. "
                "Use professional terminology, keep the report in English, and "
                "treat the output as a [DRAFT] requiring qualified human review."
            ),
            "record": {
                "client_name": payload.client_name,
                "site_address": payload.site_address,
                "service_date": payload.service_date.isoformat(),
                "technician_name": payload.technician_name,
                "system_type": payload.system_type,
                "raw_notes": payload.raw_notes,
            },
            "field_rules": {
                "report_summary": (
                    "2-4 sentences. State what was inspected, what appeared normal, "
                    "what issues were identified, and that the report is a draft."
                ),
                "inspected_items": (
                    "List each discrete system, component, or observation cluster "
                    "mentioned in the notes."
                ),
                "issues_found": "List only actual issues or defects mentioned.",
                "actions_taken": (
                    "List only actions explicitly completed in the notes."
                ),
                "follow_up_required": (
                    "Short sentence beginning with Yes or No. If yes, explain why."
                ),
                "missing_information": (
                    "List missing data needed for a final compliance report."
                ),
            },
        },
        ensure_ascii=True,
    )


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
        response = client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": build_user_prompt(payload)},
            ],
            text_format=StructuredReportDraft,
        )
    except Exception as exc:
        logger.exception("OpenAI request failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI request failed: {exc}",
        ) from exc

    parsed = getattr(response, "output_parsed", None)
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI response did not include a parsed structured payload.",
        )

    return parsed


def render_numbered_list(items: List[str], empty_message: str) -> str:
    cleaned_items = [item.strip() for item in items if item.strip()]
    if not cleaned_items:
        return empty_message

    return "\n".join(
        f"{index}. {item}" for index, item in enumerate(cleaned_items, start=1)
    )


def render_markdown(
    payload: GenerateReportRequest,
    structured_report: StructuredReportDraft,
) -> str:
    inspected_sections = []
    for item in structured_report.inspected_items:
        inspected_sections.append(
            "\n".join(
                [
                    f"### {item.item_name}",
                    f"- Location: {item.location}",
                    f"- Observation: {item.observation}",
                    f"- Issue Found: {item.issue_found}",
                    f"- Action Taken: {item.action_taken}",
                    f"- Follow Up: {item.follow_up}",
                ]
            )
        )

    inspected_items_md = (
        "\n\n".join(inspected_sections)
        if inspected_sections
        else "No inspected items could be confidently extracted from the technician notes."
    )

    missing_information_md = render_numbered_list(
        structured_report.missing_information,
        "1. Not provided in technician notes.",
    )

    return "\n".join(
        [
            "# [DRAFT] Fire Maintenance Report",
            "",
            "## Service Details",
            f"- Client Name: {payload.client_name}",
            f"- Site Address: {payload.site_address}",
            f"- Service Date: {payload.service_date.isoformat()}",
            f"- Technician Name: {payload.technician_name}",
            f"- System Type: {payload.system_type}",
            "",
            "## Executive Summary",
            structured_report.report_summary,
            "",
            "## Inspected Items",
            inspected_items_md,
            "",
            "## Issues Found",
            render_numbered_list(
                structured_report.issues_found,
                "1. No issues explicitly recorded in technician notes.",
            ),
            "",
            "## Actions Taken",
            render_numbered_list(
                structured_report.actions_taken,
                "1. No actions explicitly recorded in technician notes.",
            ),
            "",
            "## Follow Up Required",
            structured_report.follow_up_required,
            "",
            "## Missing Information",
            missing_information_md,
            "",
            "## Compliance Notice",
            "This document is an AI-generated draft for administrative assistance only. "
            "It must be reviewed and signed off by a qualified person before it is used "
            "as compliance evidence or issued to a client.",
        ]
    )


app = FastAPI(
    title="AI-Powered Fire Compliance Report Generator",
    version="0.1.0",
    description=(
        "FastAPI middleware for Zapier-driven fire maintenance draft report generation."
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
    structured_report = call_openai_for_report(payload)
    formatted_markdown = render_markdown(payload, structured_report)

    return GenerateReportResponse(
        status="success",
        report_summary=structured_report.report_summary,
        inspected_items_count=len(structured_report.inspected_items),
        formatted_markdown=formatted_markdown,
        issues_found_list=render_numbered_list(
            structured_report.issues_found,
            "1. No issues explicitly recorded in technician notes.",
        ),
        actions_taken_list=render_numbered_list(
            structured_report.actions_taken,
            "1. No actions explicitly recorded in technician notes.",
        ),
        follow_up_required=structured_report.follow_up_required,
        review_status="Draft - Requires Admin Review",
        inspected_items=structured_report.inspected_items,
        missing_information=structured_report.missing_information,
    )
