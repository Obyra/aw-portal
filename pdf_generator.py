"""SACS and TCC PDF generators for the Windbrook Client Report Portal.

Pure presentation layer. All numbers come from the report_data dict assembled
by app.py — this module reads, never writes business logic.
"""
from __future__ import annotations

import math
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# ── Brand palette ──────────────────────────────────────────────────────────────
NAVY        = HexColor("#1B4F8C")
NAVY_DARK   = HexColor("#0F3563")
NAVY_DEEP   = HexColor("#0A2748")
NAVY_PALE   = HexColor("#A6BFDB")
NAVY_TINT   = HexColor("#D7E3F2")
BLUE_LIGHT  = HexColor("#2E6DB4")
BLUE_PALE   = HexColor("#EBF2FA")
GREEN       = HexColor("#2D7A3A")
GREEN_LIGHT = HexColor("#3A9E4A")
GREEN_PALE  = HexColor("#E5F4E8")
RED         = HexColor("#B22222")
RED_LIGHT   = HexColor("#D04040")
RED_PALE    = HexColor("#FCEAEA")
GOLD        = HexColor("#B8893B")
GRAY_50     = HexColor("#F8FAFC")
GRAY_100    = HexColor("#F1F5F9")
GRAY_200    = HexColor("#E2E8F0")
GRAY_300    = HexColor("#CBD5E1")
GRAY_400    = HexColor("#94A3B8")
GRAY_500    = HexColor("#64748B")
GRAY_600    = HexColor("#475569")
GRAY_700    = HexColor("#334155")
GRAY_900    = HexColor("#0F172A")
WHITE       = colors.white

PAGE_MARGIN = 50


# ── Formatting helpers ─────────────────────────────────────────────────────────
def fmt(n):
    """US currency formatter — always `$1,234,567` style, no decimals, no locale drift.

    Returns `$0` for None / non-numeric input so the PDF never shows a malformed
    value (e.g. `$69,50` from a stray string or partial input).
    """
    try:
        return f"${float(n):,.0f}"
    except (TypeError, ValueError):
        return "$0"


def full_name(client):
    n1 = (client.get("name1") or "").strip()
    n2 = (client.get("name2") or "").strip()
    last = (client.get("last_name") or "").strip()
    if n2:
        return f"{n1} & {n2} {last}".strip()
    return f"{n1} {last}".strip()


def calc_age(dob_str):
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        today = datetime.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return "—"


# ── Layout primitives ──────────────────────────────────────────────────────────
def draw_header(c, W, H, *, title, name, quarter, date_str, prepared_by, page_label=None):
    """Render the consistent navy header bar at the top of every page."""
    # Solid navy band
    c.setFillColor(NAVY)
    c.rect(0, H - 92, W, 92, fill=1, stroke=0)
    # Deep navy accent stripe at top
    c.setFillColor(NAVY_DEEP)
    c.rect(0, H - 4, W, 4, fill=1, stroke=0)
    # Thin gold under-rule for premium feel
    c.setFillColor(GOLD)
    c.rect(0, H - 92, W, 1.2, fill=1, stroke=0)

    # Title
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 21)
    c.drawString(PAGE_MARGIN, H - 42, title)

    # Subtitle: client · quarter · date
    c.setFillColor(NAVY_TINT)
    c.setFont("Helvetica", 10.5)
    c.drawString(PAGE_MARGIN, H - 59, f"{name}   ·   {quarter}   ·   {date_str}")

    # Prepared by
    c.setFillColor(NAVY_PALE)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(PAGE_MARGIN, H - 75, f"Prepared by {prepared_by}")

    # Right-aligned brand mark
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(W - PAGE_MARGIN, H - 42, "WINDBROOK")
    c.setFillColor(NAVY_PALE)
    c.setFont("Helvetica", 8.5)
    c.drawRightString(W - PAGE_MARGIN, H - 56, "SOLUTIONS  ·  ATLANTA")
    if page_label:
        c.setFillColor(NAVY_PALE)
        c.setFont("Helvetica", 8)
        c.drawRightString(W - PAGE_MARGIN, H - 75, page_label)


def draw_footer(c, W, page_label):
    c.setStrokeColor(GRAY_200)
    c.setLineWidth(0.6)
    c.line(PAGE_MARGIN, 38, W - PAGE_MARGIN, 38)
    c.setFillColor(GRAY_500)
    c.setFont("Helvetica", 8)
    c.drawString(PAGE_MARGIN, 24, "Windbrook Solutions   ·   Confidential   ·   For Client Use Only")
    c.drawRightString(W - PAGE_MARGIN, 24, page_label)


def draw_section_title(c, x, y, w, label, *, eyebrow=None):
    """Uppercase section title with thin gray rule underneath."""
    if eyebrow:
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica", 8.5)
        c.drawString(x, y + 12, eyebrow.upper())
    c.setFillColor(GRAY_900)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, label.upper())
    c.setStrokeColor(GRAY_300)
    c.setLineWidth(0.6)
    c.line(x, y - 6, x + w, y - 6)


def draw_card(c, x, y, w, h, *, accent=None, fill=WHITE, border=GRAY_200, radius=6):
    """Premium card with subtle border and optional left accent stripe."""
    c.setFillColor(fill)
    c.setStrokeColor(border)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    if accent:
        c.setFillColor(accent)
        # Left accent stripe, slightly inset
        c.rect(x, y, 3, h, fill=1, stroke=0)


def draw_arrow_line(c, x1, y1, x2, y2, color, width=1.6, head=7):
    """Clean straight arrow with filled triangular head."""
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.setLineCap(1)
    c.line(x1, y1, x2, y2)
    angle = math.atan2(y2 - y1, x2 - x1)
    c.setFillColor(color)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - head * math.cos(angle - 0.45), y2 - head * math.sin(angle - 0.45))
    p.lineTo(x2 - head * math.cos(angle + 0.45), y2 - head * math.sin(angle + 0.45))
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def draw_dome_arrow(c, x1, y1, x2, y2, peak_y, color, width=1.8, head=8):
    """Symmetric dome-shaped Bezier arrow that rises from x1,y1 to peak then descends to x2,y2.

    Uses control points directly above each endpoint to keep the curve smooth and
    symmetric — no awkward bumps.
    """
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.setLineCap(1)
    path = c.beginPath()
    path.moveTo(x1, y1)
    # Control points directly above endpoints, at peak_y
    path.curveTo(x1, peak_y, x2, peak_y, x2, y2)
    c.drawPath(path, stroke=1, fill=0)
    # Arrowhead direction from approach (control point 2) to endpoint
    angle = math.atan2(y2 - peak_y, x2 - x2 + 0.01) if abs(x2 - x2) < 0.01 else math.atan2(y2 - peak_y, 0)
    # For a dome ending vertically down at x2, the angle is -pi/2
    angle = -math.pi / 2 if y2 < peak_y else math.pi / 2
    c.setFillColor(color)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - head * math.cos(angle - 0.45), y2 - head * math.sin(angle - 0.45))
    p.lineTo(x2 - head * math.cos(angle + 0.45), y2 - head * math.sin(angle + 0.45))
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def draw_flow_circle(c, cx, cy, radius, fill, stroke, *, title, value=None, sub=None):
    """Standardized flow node — used for Inflow, Outflow, Reserve.

    The circle holds ONLY the label. Currency values are intentionally drawn
    outside the circle (by the caller) so no shape, ring, or arrow can ever
    overlap or clip the digits — this is a defense against viewer-side
    rendering quirks that visually truncate the last glyph inside tight shapes.

    `value` and `sub` are kept for backwards compatibility but ignored.
    """
    # Filled disk
    c.setStrokeColor(stroke)
    c.setLineWidth(2.2)
    c.setFillColor(fill)
    c.circle(cx, cy, radius, fill=1, stroke=1)
    # Inner highlight ring
    c.setStrokeColor(WHITE)
    c.setLineWidth(0.6)
    c.circle(cx, cy, radius - 4, fill=0, stroke=1)
    # Label only — split two-word titles onto two lines for legibility
    c.setFillColor(WHITE)
    parts = title.upper().split()
    if len(parts) >= 2 and max(len(p) for p in parts) > 7:
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(cx, cy + 4, parts[0])
        c.drawCentredString(cx, cy - 10, " ".join(parts[1:]))
    else:
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(cx, cy - 4, title.upper())


def draw_value_below(c, cx, top_y, value, sub=None, *, value_size=18, value_color=None):
    """Draw a currency value in open space (no surrounding shape).

    Used below flow circles so the digits are guaranteed to be unobstructed.
    """
    if value_color is None:
        value_color = GRAY_900
    c.setFillColor(value_color)
    c.setFont("Helvetica-Bold", value_size)
    c.drawCentredString(cx, top_y, value)
    if sub:
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica", 9)
        c.drawCentredString(cx, top_y - 14, sub)


def draw_kpi_card(c, x, y, w, h, *, label, value, sub=None, accent=NAVY, value_size=20):
    """Standardized KPI metric card used in summary strips."""
    draw_card(c, x, y, w, h, accent=accent)
    c.setFillColor(GRAY_500)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(x + 14, y + h - 20, label.upper())
    c.setFillColor(GRAY_900)
    c.setFont("Helvetica-Bold", value_size)
    c.drawString(x + 14, y + (h - 20) - value_size - 4, value)
    if sub:
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica", 8.5)
        c.drawString(x + 14, y + 12, sub)


def draw_progress_bar(c, x, y, w, pct, *, fill=NAVY, track=GRAY_100, height=12):
    """Rounded progress bar with track + fill."""
    c.setFillColor(track)
    c.roundRect(x, y, w, height, height / 2, fill=1, stroke=0)
    if pct > 0:
        c.setFillColor(fill)
        c.roundRect(x, y, max(height, w * pct), height, height / 2, fill=1, stroke=0)


# ── SACS PDF ───────────────────────────────────────────────────────────────────
def generate_sacs_pdf(buf, data):
    c = canvas.Canvas(buf, pagesize=letter)
    W, H = letter
    calc = data["calc"]
    client = data["client"]
    quarter = data["quarter"]
    prepared_by = data.get("prepared_by") or data.get("generated_by") or "—"
    name = full_name(client)

    # ─── PAGE 1: Cash Flow Diagram ─────────────────────────────────────────────
    draw_header(c, W, H,
                title="Cash Flow Statement", name=name, quarter=quarter,
                date_str=data["generated_at"], prepared_by=prepared_by,
                page_label="Page 1 of 2")

    # Section heading
    sec_y = H - 122
    draw_section_title(c, PAGE_MARGIN, sec_y, W - 2 * PAGE_MARGIN,
                       "Monthly Cash Flow", eyebrow="Statement of Allocation & Cash Stewardship")

    # Diagram geometry — three equal columns
    col_w = (W - 2 * PAGE_MARGIN) / 3
    inflow_cx  = PAGE_MARGIN + col_w * 0.5
    outflow_cx = PAGE_MARGIN + col_w * 1.5
    reserve_cx = PAGE_MARGIN + col_w * 2.5
    cy = sec_y - 140
    radius = 46  # smaller circles — values render below in open space

    # ── Pass 1: background shapes (arrows) — drawn FIRST so text always sits on top
    # Arrow 1 — Inflow → Outflow (clean horizontal)
    a1_y = cy
    draw_arrow_line(c, inflow_cx + radius + 6, a1_y, outflow_cx - radius - 6, a1_y,
                    RED, width=1.8, head=7)
    # Arrow 2 — Inflow → Reserve (smooth dome arc over Outflow)
    peak_y = cy + radius + 50
    sx, sy = inflow_cx, cy + radius + 2
    ex, ey = reserve_cx, cy + radius + 2
    draw_dome_arrow(c, sx, sy, ex, ey, peak_y, BLUE_LIGHT, width=1.9, head=8)

    # ── Pass 2: filled circles (each only carries its label)
    draw_flow_circle(c, inflow_cx,  cy, radius, GREEN_LIGHT, GREEN,      title="Inflow")
    draw_flow_circle(c, outflow_cx, cy, radius, RED_LIGHT,   RED,        title="Outflow")
    draw_flow_circle(c, reserve_cx, cy, radius, NAVY,        NAVY_DARK,  title="Private Reserve")

    # ── Pass 3: CURRENCY VALUES — rendered LAST in OPEN SPACE below each circle.
    # No shape, ring, stroke, or arrow lives in this vertical band, so the digits
    # cannot be clipped by any other drawing element regardless of viewer.
    value_y = cy - radius - 22
    draw_value_below(c, inflow_cx,  value_y, fmt(calc["inflow"]),                   "per month", value_size=20)
    draw_value_below(c, outflow_cx, value_y, fmt(calc["outflow"]),                  "per month", value_size=20)
    draw_value_below(c, reserve_cx, value_y, fmt(calc["private_reserve_balance"]),
                     f"Target {fmt(calc['private_reserve_target'])}", value_size=20)

    # Arc apex labels — drawn above the arc in clean space
    apex_x = (inflow_cx + reserve_cx) / 2
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(apex_x, peak_y + 12, "MONTHLY EXCESS")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(apex_x, peak_y - 4, fmt(calc["excess"]))

    # Caption — single sentence summary
    cap_y = value_y - 36
    c.setFillColor(GRAY_500)
    c.setFont("Helvetica-Oblique", 9.5)
    c.drawCentredString(W / 2, cap_y,
        f"Excess of {fmt(calc['excess'])} per month flows automatically into the Private Reserve.")

    # ── Summary strip — 3 KPI cards
    kpi_top_y = cap_y - 22
    kpi_h = 74
    kpi_total_w = W - 2 * PAGE_MARGIN
    kpi_w = (kpi_total_w - 24) / 3
    kpi_y = kpi_top_y - kpi_h

    draw_kpi_card(c, PAGE_MARGIN, kpi_y, kpi_w, kpi_h,
                  label="Monthly Excess", value=fmt(calc["excess"]),
                  sub="Available for reserves & investments", accent=GREEN)
    draw_kpi_card(c, PAGE_MARGIN + kpi_w + 12, kpi_y, kpi_w, kpi_h,
                  label="Reserve Balance", value=fmt(calc["private_reserve_balance"]),
                  sub="High-yield savings", accent=NAVY)
    draw_kpi_card(c, PAGE_MARGIN + (kpi_w + 12) * 2, kpi_y, kpi_w, kpi_h,
                  label="Reserve Target", value=fmt(calc["private_reserve_target"]),
                  sub="6× outflow + deductibles", accent=BLUE_LIGHT)

    # ── Reserve funding progress
    prog_top = kpi_y - 36
    target = calc["private_reserve_target"] or 1
    pct = max(0.0, min(calc["private_reserve_balance"] / target, 1.0))
    c.setFillColor(GRAY_900)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(PAGE_MARGIN, prog_top, "RESERVE FUNDING PROGRESS")
    c.setFillColor(GRAY_500)
    c.setFont("Helvetica", 9)
    c.drawRightString(W - PAGE_MARGIN, prog_top,
                      f"{int(pct * 100)}% funded   ·   {fmt(calc['private_reserve_balance'])} of {fmt(calc['private_reserve_target'])}")

    bar_y = prog_top - 20
    draw_progress_bar(c, PAGE_MARGIN, bar_y, W - 2 * PAGE_MARGIN, pct,
                      fill=NAVY, track=GRAY_100, height=12)

    # ── Methodology note (split across two lines so it never overflows the right margin)
    note_y = bar_y - 30
    c.setFillColor(GRAY_500)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(PAGE_MARGIN, note_y, "METHODOLOGY")
    c.setFillColor(GRAY_700)
    c.setFont("Helvetica", 9.5)
    c.drawString(PAGE_MARGIN, note_y - 16,
        "Reserve target equals six months of outflow plus current insurance deductibles.")
    c.drawString(PAGE_MARGIN, note_y - 30,
        "Surplus cash flow is swept into the Private Reserve until target is reached.")

    draw_footer(c, W, "Page 1 of 2  ·  Cash Flow Diagram")
    c.showPage()

    # ─── PAGE 2: Reserve & Investment Summary ──────────────────────────────────
    draw_header(c, W, H,
                title="Reserve & Investment Summary", name=name, quarter=quarter,
                date_str=data["generated_at"], prepared_by=prepared_by,
                page_label="Page 2 of 2")

    sec2_y = H - 122
    draw_section_title(c, PAGE_MARGIN, sec2_y, W - 2 * PAGE_MARGIN,
                       "Reserve & Investment Position",
                       eyebrow="Quarter-end snapshot")

    # Three featured metric cards
    metric_y_top = sec2_y - 18
    metric_h = 124
    metric_total_w = W - 2 * PAGE_MARGIN
    metric_w = (metric_total_w - 24) / 3
    metric_y = metric_y_top - metric_h

    def big_metric(x, label, value, sub, accent):
        draw_card(c, x, metric_y, metric_w, metric_h, accent=accent)
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(x + 16, metric_y + metric_h - 22, label.upper())
        c.setFillColor(GRAY_900)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(x + 16, metric_y + metric_h - 58, value)
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica", 9)
        c.drawString(x + 16, metric_y + 18, sub)

    big_metric(PAGE_MARGIN,
               "Private Reserve Balance", fmt(calc["private_reserve_balance"]),
               "High-yield savings", NAVY)
    big_metric(PAGE_MARGIN + metric_w + 12,
               "Reserve Target", fmt(calc["private_reserve_target"]),
               "6 × outflow + deductibles", GREEN)
    big_metric(PAGE_MARGIN + (metric_w + 12) * 2,
               "Investment Account", fmt(calc["schwab_balance"]),
               "Charles Schwab brokerage", BLUE_LIGHT)

    # Progress bar — Reserve funding
    prog_y = metric_y - 38
    target = calc["private_reserve_target"] or 1
    pct = max(0.0, min(calc["private_reserve_balance"] / target, 1.0))
    c.setFillColor(GRAY_900)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(PAGE_MARGIN, prog_y, "RESERVE FUNDING PROGRESS")
    c.setFillColor(GRAY_500)
    c.setFont("Helvetica", 9)
    c.drawRightString(W - PAGE_MARGIN, prog_y,
                      f"{int(pct * 100)}% funded   ·   {fmt(calc['private_reserve_balance'])} of {fmt(calc['private_reserve_target'])}")

    bar_y = prog_y - 20
    draw_progress_bar(c, PAGE_MARGIN, bar_y, W - 2 * PAGE_MARGIN, pct,
                      fill=NAVY, track=GRAY_100, height=14)

    # ── Cash-flow breakdown card (fills the lower half elegantly)
    bd_top = bar_y - 34
    bd_h = 130
    bd_y = bd_top - bd_h
    draw_card(c, PAGE_MARGIN, bd_y, W - 2 * PAGE_MARGIN, bd_h,
              accent=NAVY, fill=GRAY_50)

    c.setFillColor(GRAY_500)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(PAGE_MARGIN + 18, bd_y + bd_h - 22, "CASH FLOW BREAKDOWN")

    # Three-column mini-table
    inner_x = PAGE_MARGIN + 18
    inner_w = (W - 2 * PAGE_MARGIN) - 36
    col = inner_w / 3
    rows_top = bd_y + bd_h - 50

    def breakdown_col(cx, label, monthly_val, annual_val, color):
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(cx, rows_top, label.upper())
        c.setFillColor(GRAY_900)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(cx, rows_top - 24, fmt(monthly_val))
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica", 8.5)
        c.drawString(cx, rows_top - 38, "per month")
        c.setFillColor(GRAY_700)
        c.setFont("Helvetica", 9)
        c.drawString(cx, rows_top - 58, f"Annual  {fmt(annual_val)}")

    breakdown_col(inner_x,             "Inflow",  calc["inflow"],  calc["inflow"]  * 12, GREEN)
    breakdown_col(inner_x + col,       "Outflow", calc["outflow"], calc["outflow"] * 12, RED)
    breakdown_col(inner_x + col * 2,   "Excess",  calc["excess"],  calc["excess"]  * 12, NAVY)

    # Methodology footnote — split short to stay well inside right margin
    note_y = bd_y - 22
    six_months = 6 * calc["outflow"]
    deductibles = calc["private_reserve_target"] - six_months
    c.setFillColor(GRAY_500)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(PAGE_MARGIN, note_y, "TARGET METHODOLOGY")
    c.setFillColor(GRAY_700)
    c.setFont("Helvetica", 9)
    # Render the methodology as label/value pairs with NO parentheses around
    # the currency values. Some PDF viewers wrap or hyphenate text inside
    # `( ... )` and end up displaying things like "$66, 00" — using a colon
    # separator on its own line eliminates that risk entirely.
    c.drawString(PAGE_MARGIN, note_y - 16,
        f"Six months of expenses:  {fmt(six_months)}")
    c.drawString(PAGE_MARGIN, note_y - 30,
        f"Plus insurance deductibles:  {fmt(deductibles)}")
    c.drawString(PAGE_MARGIN, note_y - 44,
        f"Current monthly contribution:  {fmt(calc['excess'])}")

    draw_footer(c, W, "Page 2 of 2  ·  Reserve & Investment Summary")
    c.showPage()
    c.save()


# ── TCC PDF ────────────────────────────────────────────────────────────────────
def generate_tcc_pdf(buf, data):
    c = canvas.Canvas(buf, pagesize=letter)
    W, H = letter
    calc = data["calc"]
    client = data["client"]
    balances = data["balances"]
    quarter = data["quarter"]
    prepared_by = data.get("prepared_by") or data.get("generated_by") or "—"
    name = full_name(client)

    draw_header(c, W, H,
                title="Total Net Worth Statement", name=name, quarter=quarter,
                date_str=data["generated_at"], prepared_by=prepared_by)

    full_w = W - 2 * PAGE_MARGIN

    # ─── Client Information ───────────────────────────────────────────────────
    sec_y = H - 122
    draw_section_title(c, PAGE_MARGIN, sec_y, full_w,
                       "Client Information", eyebrow="Household")

    info_y = sec_y - 14
    info_h = 56

    def client_info_card(x, w, fname, dob, ssn):
        draw_card(c, x, info_y - info_h, w, info_h, accent=GREEN)
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 14, info_y - 16, "CLIENT")
        c.setFillColor(GRAY_900)
        c.setFont("Helvetica-Bold", 13.5)
        c.drawString(x + 14, info_y - 32, fname)
        age = calc_age(dob)
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica", 9)
        c.drawString(x + 14, info_y - 47,
                     f"Age {age}   ·   DOB {dob or '—'}   ·   SSN XXX-XX-{ssn or 'XXXX'}")

    name1 = client.get("name1", "Client 1")
    name2 = (client.get("name2") or "").strip()
    if name2:
        col = (full_w - 16) / 2
        client_info_card(PAGE_MARGIN, col, name1, client.get("dob1", ""), client.get("ssn1", "XXXX"))
        client_info_card(PAGE_MARGIN + col + 16, col, name2,
                         client.get("dob2", ""), client.get("ssn2", "XXXX"))
    else:
        client_info_card(PAGE_MARGIN, full_w, name1,
                         client.get("dob1", ""), client.get("ssn1", "XXXX"))

    cur_y = info_y - info_h - 20

    # ─── Reusable group renderer ──────────────────────────────────────────────
    def render_group_header(x, y, w, title, total, *,
                            hdr_fill=GRAY_50, label_fill=GRAY_700, total_fill=NAVY,
                            border=GRAY_200):
        h = 26
        c.setFillColor(hdr_fill)
        c.setStrokeColor(border)
        c.setLineWidth(0.6)
        c.roundRect(x, y - h, w, h, 4, fill=1, stroke=1)
        c.setFillColor(label_fill)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(x + 12, y - 17, title.upper())
        c.setFillColor(total_fill)
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(x + w - 12, y - 17, fmt(total))
        return y - h

    def acct_card(x, y, w, h, acct_type, last4, balance, accent=BLUE_LIGHT):
        draw_card(c, x, y, w, h, accent=accent)
        c.setFillColor(GRAY_900)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(x + 12, y + h - 18, acct_type or "Account")
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica", 7.5)
        c.drawString(x + 12, y + h - 30, f"•••• {last4 or '----'}")
        c.setFillColor(GRAY_900)
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(x + w - 12, y + 12, fmt(balance))

    # ─── Retirement Accounts ──────────────────────────────────────────────────
    ret_accounts = client.get("retirement_accounts", [])
    ret1 = [(i, a) for i, a in enumerate(ret_accounts) if a.get("owner") == "client1"]
    ret2 = [(i, a) for i, a in enumerate(ret_accounts) if a.get("owner") == "client2"]

    if ret1 or ret2:
        draw_section_title(c, PAGE_MARGIN, cur_y, full_w, "Retirement Accounts")
        cur_y -= 22

        if ret2 and name2:
            col_w = (full_w - 18) / 2

            # Left: Client 1 retirement
            y_after_l = render_group_header(PAGE_MARGIN, cur_y, col_w,
                                            f"{name1} retirement", calc["ret1_total"])
            # Right: Client 2 retirement
            y_after_r = render_group_header(PAGE_MARGIN + col_w + 18, cur_y, col_w,
                                            f"{name2} retirement", calc["ret2_total"])

            card_h = 36
            gap = 6
            left_y = y_after_l - 8
            for idx, (i, a) in enumerate(ret1):
                bal = float(balances.get(f"ret_{i}", 0))
                acct_card(PAGE_MARGIN, left_y - card_h, col_w, card_h,
                          a.get("type"), a.get("last4"), bal, accent=BLUE_LIGHT)
                left_y -= card_h + gap

            right_y = y_after_r - 8
            for idx, (i, a) in enumerate(ret2):
                bal = float(balances.get(f"ret_{i}", 0))
                acct_card(PAGE_MARGIN + col_w + 18, right_y - card_h, col_w, card_h,
                          a.get("type"), a.get("last4"), bal, accent=BLUE_LIGHT)
                right_y -= card_h + gap

            cur_y = min(left_y, right_y)
        else:
            # Single column — 2 cards per row
            y_after = render_group_header(PAGE_MARGIN, cur_y, full_w,
                                          f"{name1} retirement", calc["ret1_total"])
            card_h = 36
            gap = 6
            ry = y_after - 8
            per_row = 2
            col_w_single = (full_w - (per_row - 1) * 10) / per_row
            for idx, (i, a) in enumerate(ret1):
                row = idx // per_row
                cidx = idx % per_row
                x = PAGE_MARGIN + cidx * (col_w_single + 10)
                y = ry - row * (card_h + gap) - card_h
                bal = float(balances.get(f"ret_{i}", 0))
                acct_card(x, y, col_w_single, card_h,
                          a.get("type"), a.get("last4"), bal, accent=BLUE_LIGHT)
            rows_used = max(1, (len(ret1) + per_row - 1) // per_row)
            cur_y = ry - rows_used * (card_h + gap)

    # ─── Non-Retirement Accounts ──────────────────────────────────────────────
    nret_accounts = client.get("non_retirement_accounts", [])
    if nret_accounts:
        cur_y -= 10
        draw_section_title(c, PAGE_MARGIN, cur_y, full_w, "Non-Retirement Accounts")
        cur_y -= 20

        y_after = render_group_header(PAGE_MARGIN, cur_y, full_w,
                                      "Brokerage & Cash", calc["non_ret_total"])
        cur_y = y_after - 8
        card_h = 38
        per_row = 3
        col_w_nr = (full_w - (per_row - 1) * 10) / per_row
        for j, a in enumerate(nret_accounts):
            row = j // per_row
            cidx = j % per_row
            x = PAGE_MARGIN + cidx * (col_w_nr + 10)
            y = cur_y - row * (card_h + 8) - card_h
            bal = float(balances.get(f"nret_{j}", 0))
            acct_card(x, y, col_w_nr, card_h, a.get("type"), a.get("last4"), bal,
                      accent=GREEN_LIGHT)
        rows_used = max(1, (len(nret_accounts) + per_row - 1) // per_row)
        cur_y -= rows_used * (card_h + 8)

    # ─── Trust / Property ─────────────────────────────────────────────────────
    trust_addr = (client.get("trust") or {}).get("address", "").strip()
    trust_val = float(balances.get("trust_value", 0))
    if trust_addr or trust_val:
        cur_y -= 10
        draw_section_title(c, PAGE_MARGIN, cur_y, full_w, "Trust / Property")
        cur_y -= 20

        trust_h = 60
        ty = cur_y - trust_h
        draw_card(c, PAGE_MARGIN, ty, full_w, trust_h, accent=GOLD, fill=GRAY_50)
        # Left: label + address
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(PAGE_MARGIN + 16, ty + trust_h - 20, "PRIMARY RESIDENCE / TRUST")
        c.setFillColor(GRAY_900)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(PAGE_MARGIN + 16, ty + trust_h - 38, trust_addr or "Property")
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica", 8.5)
        c.drawString(PAGE_MARGIN + 16, ty + 14, "Source: Zillow Zestimate")
        # Right: large value
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawRightString(PAGE_MARGIN + full_w - 16, ty + trust_h - 20, "ESTIMATED VALUE")
        c.setFillColor(GRAY_900)
        # Trust value at 20pt (down from 22) keeps the right edge well inside
        # the card so 7-digit values never get clipped at the card boundary.
        c.setFont("Helvetica-Bold", 20)
        c.drawRightString(PAGE_MARGIN + full_w - 16, ty + 18, fmt(trust_val))
        cur_y = ty

    # ─── Grand Total (featured navy block) ────────────────────────────────────
    cur_y -= 18
    gt_h = 80
    c.setFillColor(NAVY)
    c.roundRect(PAGE_MARGIN, cur_y - gt_h, full_w, gt_h, 10, fill=1, stroke=0)
    c.setFillColor(NAVY_DARK)
    c.rect(PAGE_MARGIN, cur_y - gt_h, 4, gt_h, fill=1, stroke=0)
    # Subtle gold accent rule
    c.setFillColor(GOLD)
    c.rect(PAGE_MARGIN + 4, cur_y - gt_h, full_w - 4, 1.2, fill=1, stroke=0)

    c.setFillColor(NAVY_PALE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(PAGE_MARGIN + 22, cur_y - 24, "GRAND TOTAL NET WORTH")
    c.setFillColor(WHITE)
    # Grand total at 30pt (down from 34) keeps even 8-digit totals like
    # $12,345,678 from approaching the composition column on the right.
    c.setFont("Helvetica-Bold", 30)
    c.drawString(PAGE_MARGIN + 22, cur_y - 60, fmt(calc["grand_total"]))

    # Breakdown stack on the right
    ret_combined = calc["ret1_total"] + calc["ret2_total"]
    breakdown_parts = []
    if ret_combined:
        breakdown_parts.append(("Retirement", ret_combined))
    if calc["non_ret_total"]:
        breakdown_parts.append(("Non-Retirement", calc["non_ret_total"]))
    if trust_addr and trust_val:
        breakdown_parts.append(("Trust / Property", trust_val))

    bd_x = PAGE_MARGIN + full_w - 18
    bd_y = cur_y - 24
    c.setFillColor(NAVY_PALE)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(bd_x, bd_y, "COMPOSITION")
    line_h = 14
    for idx, (label, val) in enumerate(breakdown_parts):
        y_line = bd_y - 14 - idx * line_h
        c.setFillColor(NAVY_TINT)
        c.setFont("Helvetica", 9)
        c.drawRightString(bd_x - 90, y_line, label)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawRightString(bd_x, y_line, fmt(val))
    cur_y -= gt_h

    # ─── Liabilities (visually separated, distinct accent) ────────────────────
    liabs = client.get("liabilities", [])
    liab_h = 44
    per_row = 2
    rows_used = max(1, (len(liabs) + per_row - 1) // per_row) if liabs else 0

    # Footer line sits at y = 38. Required height of the full liabilities block
    # (top spacing + section title + group header + card rows + note + bottom buffer).
    liabs_block_h = 16 + 18 + 26 + 8 + rows_used * (liab_h + 8) + 14 + 14
    overflow_to_page_2 = bool(liabs) and (cur_y - liabs_block_h < 50)

    if overflow_to_page_2:
        # Finish page 1 with proper pagination label, then start a fresh page.
        draw_footer(c, W, "Page 1 of 2  ·  Net Worth Summary")
        c.showPage()
        draw_header(c, W, H,
                    title="Liabilities Summary", name=name, quarter=quarter,
                    date_str=data["generated_at"], prepared_by=prepared_by,
                    page_label="Page 2 of 2")
        cur_y = H - 122
        draw_section_title(c, PAGE_MARGIN, cur_y, full_w,
                           "Liabilities", eyebrow="Tracked separately — not deducted from net worth")
        cur_y -= 22
    elif liabs:
        cur_y -= 16
        draw_section_title(c, PAGE_MARGIN, cur_y, full_w,
                           "Liabilities", eyebrow="Tracked separately — not deducted from net worth")
        cur_y -= 18

    if liabs:
        y_after = render_group_header(PAGE_MARGIN, cur_y, full_w,
                                      "Outstanding Liabilities", calc["liabilities_total"],
                                      hdr_fill=RED_PALE, label_fill=RED, total_fill=RED,
                                      border=RED_PALE)
        cur_y = y_after - 8

        col_w_l = (full_w - (per_row - 1) * 10) / per_row
        for j, liab in enumerate(liabs):
            row = j // per_row
            cidx = j % per_row
            x = PAGE_MARGIN + cidx * (col_w_l + 10)
            y = cur_y - row * (liab_h + 8) - liab_h
            bal = float(balances.get(f"liab_{j}", 0))
            draw_card(c, x, y, col_w_l, liab_h, accent=RED)
            c.setFillColor(GRAY_900)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x + 14, y + liab_h - 18, liab.get("type", "Liability"))
            c.setFillColor(GRAY_500)
            c.setFont("Helvetica", 8.5)
            rate = liab.get("rate", 0) or 0
            c.drawString(x + 14, y + liab_h - 32,
                         f"•••• {liab.get('last4', '----')}   ·   {rate}% APR")
            c.setFillColor(RED)
            c.setFont("Helvetica-Bold", 13)
            c.drawRightString(x + col_w_l - 14, y + 14, fmt(bal))
        cur_y -= rows_used * (liab_h + 8)

        cur_y -= 14
        c.setFillColor(GRAY_500)
        c.setFont("Helvetica-Oblique", 8.5)
        c.drawString(PAGE_MARGIN, cur_y,
            "Liabilities are tracked separately and not deducted from net worth.")

    if overflow_to_page_2:
        draw_footer(c, W, "Page 2 of 2  ·  Liabilities Summary")
    else:
        draw_footer(c, W, "Confidential  ·  Total Net Worth")
    c.showPage()
    c.save()
