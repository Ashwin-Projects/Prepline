"""
Dashboard 'Download report (PDF)' (read-only): one PDF per target with the provisional S_comp, confidence indicators,
top priority gaps, what to study next, versions and a disclaimer.

GET /api/v1/report/{target_id}

Built from the saved results file and the study data (backend/study.py); scores are never recomputed. Confidence uses
the same rules as the dashboard badge (dashboard/web/src/lib/confidence.ts).
"""
import io
from typing import Any, Dict, List
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from backend.dashboard import DASHBOARD, MIN_REPORTS, _raw_report_count, _read_json, _results_path, _target
from backend.study import study_for

router = APIRouter(prefix="/api/v1", tags=["PREPLINE Dashboard"])

DISCLAIMER = (
    "PREPLINE scores are provisional. They come from public interview reports (GeeksforGeeks interview experiences), "
    "a frozen embedding matcher with known mapping errors and a fixed taxonomy (v1.0). Each company has its own topic "
    "set, so similar scores across companies are not a ranking. A score is not a prediction of interview outcomes. "
    "Practice links are third-party pages, checked when listed but not endorsed."
)


def confidence_of(result: Dict[str, Any], min_reports: int) -> Dict[str, Any]:
    """Mirror of confidenceOf(): no reasons -> High, one -> Medium, more -> Low."""
    if result.get("status") != "SUCCESS":
        return {"level": "Insufficient data",
                "reasons": [f"{result.get('report_count')} of {min_reports} reports needed after filtering"]}
    reasons = []
    margin = result["report_count"] - min_reports
    if margin < 3:
        reasons.append(f"only {margin} report{'' if margin == 1 else 's'} above the {min_reports}-report gate")
    universe = result.get("scoring_universe_size") or 0
    if universe < 10:
        reasons.append(f"fewer than 10 topics carry the score ({universe})")
    fallback = ((result.get("depth_counts") or {}).get("present_topics") or {}).get("fallback") or 0
    if fallback > 0:
        reasons.append(f"{fallback} covered topics use fallback depth")
    level = "High" if not reasons else "Medium" if len(reasons) == 1 else "Low"
    return {"level": level, "reasons": reasons}


def build_pdf(target: Dict[str, Any], result: Dict[str, Any], raw_reports: int, study: Dict[str, Any]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    label = f"{target['company']} {target['role']}"
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=10.5, textColor=colors.HexColor("#52514e"))
    h1, h2 = styles["Title"], ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12.5, spaceBefore=10)
    p = lambda text, style=body: Paragraph(escape(str(text)), style)
    rule = colors.HexColor("#e6e5e0")
    grid = TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#0b0b0b")),
                       ("LINEBELOW", (0, 1), (-1, -1), 0.4, rule), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                       ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("TOPPADDING", (0, 0), (-1, -1), 3),
                       ("BOTTOMPADDING", (0, 0), (-1, -1), 3)])

    story: List[Any] = [p(f"PREPLINE report — {label}", h1)]
    confidence = confidence_of(result, MIN_REPORTS)
    if result.get("status") == "SUCCESS":
        story += [p(f"Provisional composite alignment S_comp: {result['S_comp']:.1f} / 100 "
                    f"({confidence['level']} confidence)", h2),
                  p(f"Importance-weighted coverage of the {result.get('scoring_universe_size')} topics {label} "
                    "interviewers ask about, by the VIT CSE 2024-25 core syllabus.")]
    else:
        story += [p("Insufficient data — no score", h2),
                  p(f"{label} has {result.get('report_count')} of {MIN_REPORTS} usable interview reports needed "
                    f"({raw_reports} collected). No score is shown rather than one built on too few reports.")]

    story += [p("Confidence indicators", h2),
              p(f"Level: {confidence['level']}. Reports: {raw_reports} collected, {result.get('report_count')} usable "
                f"(gate {MIN_REPORTS}).")]
    story += [p(f"• {reason}") for reason in confidence["reasons"]] or [p("• No caution flags.")]

    gaps = result.get("top_priority_gaps", [])[:10] if result.get("status") == "SUCCESS" else []
    if gaps:
        rows = [["#", "Topic", "Importance", "Coverage", "Priority gap"]]
        rows += [[g["rank"], p(g["topic_name"]), f"{g['importance']:.3f}", f"{g['coverage'] * 100:.0f}%",
                  f"{g['priority_gap']:.3f}"] for g in gaps]
        story += [p("Top priority gaps", h2), p("PriorityGap = importance × (1 − coverage).", small),
                  Table(rows, colWidths=[8 * mm, 92 * mm, 22 * mm, 20 * mm, 24 * mm], style=grid, repeatRows=1)]

    if study["items"]:
        story += [p("What to study next", h2),
                  p("VIT core modules the topic's coverage comes from (strongest matches first; a similarity near "
                    "0.50 is a loose match), and two practice pages. Links checked on "
                    f"{study['links_verified_on']}.", small)]
        rows = [["#", "Topic", "Modules to revise", "Practice"]]
        for item in study["items"]:
            modules = "<br/>".join(
                escape(f"{m['course_code']} M{m['module_number']} {m['module_title']} ({m['similarity']:.2f})")
                for m in item["modules"][:2]) or escape(item["note"])
            links = "<br/>".join(f"<link href=\"{escape(x['url'])}\" color=\"#1f5fb0\">{escape(x['title'])}</link>"
                                 f"<br/><font size=6.5>{escape(x['url'])}</font>"
                                 for x in item["practice"])
            rows.append([item["rank"], p(item["topic_name"]), Paragraph(modules, small), Paragraph(links, small)])
        story.append(Table(rows, colWidths=[8 * mm, 42 * mm, 58 * mm, 58 * mm], style=grid, repeatRows=1))

    cfg = result.get("scoring_config") or {}
    story += [p("Versions", h2),
              p(f"results {DASHBOARD['results_version']} · taxonomy {result.get('taxonomy_version') or 'v1.0'} · "
                f"config {result.get('scoring_config_version')} (γ = {cfg.get('gamma')}, "
                f"τ = {cfg.get('similarity_threshold')}) · syllabus {result.get('syllabus_id')} · "
                f"generated {str(result.get('generated_at'))[:10]}"),
              p("Disclaimer", h2), p(DISCLAIMER, small)]

    buffer = io.BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, title=f"PREPLINE report — {label}", author="PREPLINE",
                      leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm).build(story)
    return buffer.getvalue()


@router.get("/report/{target_id}")
def get_report(target_id: str) -> Response:
    target = _target(target_id)
    result = _read_json(_results_path(target["id"]))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No saved results for '{target_id}'.")
    pdf = build_pdf(target, result, _raw_report_count(target), study_for(target["id"]))
    filename = f"prepline_{target['id']}_{DASHBOARD['results_version']}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})
