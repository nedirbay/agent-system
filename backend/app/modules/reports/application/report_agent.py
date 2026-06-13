"""Specialized Reporting Agent (Roadmap Task 17).

Turns the structured output of an Analysis Agent run (an ``AnalysisJob`` result)
into a human-readable report. The rendered document is persisted as a ``Report``
row (its body in ``content``) so it can be listed, fetched, and later exported.

Rendering is deterministic and offline — no LLM dependency — so report
generation always succeeds once an analysis job exists.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.core.exceptions import AppError, NotFoundError
from app.modules.analysis.domain.repositories import AnalysisJobRepository
from app.modules.reports.domain.entities import Report
from app.modules.reports.domain.repositories import ReportRepository

_SUPPORTED_FORMATS = {"markdown", "text"}


@dataclass(frozen=True)
class ReportAgentResult:
    report_id: uuid.UUID
    analysis_job_id: uuid.UUID
    name: str
    format: str
    content: str


class ReportAgentService:
    def __init__(
        self,
        *,
        jobs: AnalysisJobRepository,
        reports: ReportRepository,
    ) -> None:
        self._jobs = jobs
        self._reports = reports

    async def generate_from_analysis(
        self,
        analysis_job_id: uuid.UUID,
        *,
        name: str | None = None,
        report_format: str = "markdown",
        user_id: uuid.UUID | None = None,
    ) -> ReportAgentResult:
        fmt = report_format.lower()
        if fmt not in _SUPPORTED_FORMATS:
            raise AppError(f"Unsupported report format: {report_format}")

        job = await self._jobs.get(analysis_job_id)
        if job is None:
            raise NotFoundError("Analysis job not found")
        if not job.result:
            raise AppError("Analysis job has no result to report on")

        report_name = name or f"Analysis Report {analysis_job_id}"
        content = self._render(report_name, job.result, fmt)

        report = await self._reports.add(
            Report(
                user_id=user_id,
                task_id=job.task_id,
                name=report_name,
                format=fmt,
                content=content,
            )
        )
        return ReportAgentResult(
            report_id=report.id,
            analysis_job_id=analysis_job_id,
            name=report_name,
            format=fmt,
            content=content,
        )

    def _render(self, name: str, result: dict, fmt: str) -> str:
        summary = str(result.get("summary") or "").strip()
        statistics = result.get("statistics") if isinstance(result.get("statistics"), dict) else {}
        trends = [str(t) for t in result.get("trends", []) if t]
        findings = [str(f) for f in result.get("findings", []) if f]
        recommendations = [str(r) for r in result.get("recommendations", []) if r]

        if fmt == "markdown":
            return self._render_markdown(name, summary, statistics, trends, findings, recommendations)
        return self._render_text(name, summary, statistics, trends, findings, recommendations)

    @staticmethod
    def _render_markdown(
        name: str,
        summary: str,
        statistics: dict,
        trends: list[str],
        findings: list[str],
        recommendations: list[str],
    ) -> str:
        lines = [f"# {name}", ""]
        if summary:
            lines += ["## Summary", summary, ""]
        if statistics:
            lines += ["## Statistics"]
            lines += [f"- **{_humanize(k)}**: {_format_value(v)}" for k, v in statistics.items()]
            lines.append("")
        for title, items in (
            ("Trends", trends),
            ("Findings", findings),
            ("Recommendations", recommendations),
        ):
            if items:
                lines.append(f"## {title}")
                lines += [f"- {item}" for item in items]
                lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _render_text(
        name: str,
        summary: str,
        statistics: dict,
        trends: list[str],
        findings: list[str],
        recommendations: list[str],
    ) -> str:
        lines = [name, "=" * len(name), ""]
        if summary:
            lines += ["SUMMARY", summary, ""]
        if statistics:
            lines.append("STATISTICS")
            lines += [f"  {_humanize(k)}: {_format_value(v)}" for k, v in statistics.items()]
            lines.append("")
        for title, items in (
            ("TRENDS", trends),
            ("FINDINGS", findings),
            ("RECOMMENDATIONS", recommendations),
        ):
            if items:
                lines.append(title)
                lines += [f"  - {item}" for item in items]
                lines.append("")
        return "\n".join(lines).rstrip() + "\n"


def _humanize(key: str) -> str:
    return key.replace("_", " ").strip().capitalize()


def _format_value(value) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{k}: {v}" for k, v in value.items()) or "none"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value) or "none"
    return str(value)
