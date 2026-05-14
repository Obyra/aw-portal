from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import math

# Brand colors
BLUE = HexColor("#1B4F8C")
BLUE_LIGHT = HexColor("#2E6DB4")
GREEN = HexColor("#2D7A3A")
GREEN_LIGHT = HexColor("#3A9E4A")
RED = HexColor("#B22222")
RED_LIGHT = HexColor("#CC3333")
GRAY = HexColor("#F2F2F2")
GRAY_MED = HexColor("#CCCCCC")
DARK = HexColor("#1A1A1A")
WHITE = colors.white

def fmt(n):
    return f"${n:,.0f}"

def full_name(client):
    n1 = client.get("name1", "").strip()
    n2 = client.get("name2", "").strip()
    last = client.get("last_name", "").strip()
    if n2:
        return f"{n1} & {n2} {last}".strip()
    return f"{n1} {last}".strip()

def draw_circle(c, x, y, r, fill_color, stroke_color=None, stroke_width=2):
    c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(stroke_width)
        c.circle(x, y, r, fill=1, stroke=1)
    else:
        c.circle(x, y, r, fill=1, stroke=0)

def draw_arrow(c, x1, y1, x2, y2, color, label=None):
    c.setStrokeColor(color)
    c.setLineWidth(2.5)
    c.line(x1, y1, x2, y2)
    # Arrowhead
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 8
    c.setFillColor(color)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - size * math.cos(angle - 0.4), y2 - size * math.sin(angle - 0.4))
    p.lineTo(x2 - size * math.cos(angle + 0.4), y2 - size * math.sin(angle + 0.4))
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def generate_sacs_pdf(buf, data):
    c = canvas.Canvas(buf, pagesize=letter)
    W, H = letter
    calc = data["calc"]
    client = data["client"]
    quarter = data["quarter"]

    name = full_name(client)

    # ─── Header ───────────────────────────────────────────────
    c.setFillColor(BLUE)
    c.rect(0, H - 70, W, 70, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, H - 40, "Simple Automated Cash Flow System")
    c.setFont("Helvetica", 11)
    c.drawString(40, H - 58, f"{name}  |  {quarter}  |  {data['generated_at']}")
    # Logo area
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(W - 40, H - 45, "WINDBROOK")
    c.setFont("Helvetica", 9)
    c.drawRightString(W - 40, H - 58, "SOLUTIONS")

    # ─── Page 1: Cashflow Diagram ─────────────────────────────
    cy = H - 180  # center Y for diagram

    # INFLOW circle (green, left)
    ix, iy, ir = 140, cy, 80
    draw_circle(c, ix, iy, ir, GREEN_LIGHT, GREEN, 3)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(ix, iy + 18, "INFLOW")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(ix, iy, fmt(calc["inflow"]))
    c.setFont("Helvetica", 9)
    c.drawCentredString(ix, iy - 16, "/ month")

    # Arrow: Inflow → Outflow
    draw_arrow(c, ix + ir, iy, 300 - 80, iy, RED)
    c.setFillColor(RED)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString((ix + ir + 300 - 80) / 2, iy + 8, "MONTHLY EXPENSES")

    # OUTFLOW circle (red, center)
    ox, oy, or_ = 300, cy, 80
    draw_circle(c, ox, oy, or_, RED_LIGHT, RED, 3)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(ox, oy + 18, "OUTFLOW")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(ox, oy, fmt(calc["outflow"]))
    c.setFont("Helvetica", 9)
    c.drawCentredString(ox, oy - 16, "/ month")

    # X on outflow arrow
    c.setFillColor(RED)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString((ix + ir + 300 - 80) / 2, iy - 14, "✕")

    # Arrow: Inflow → Private Reserve (blue, going right from inflow over outflow)
    prx, pry = 520, cy
    # Draw curved connection: from top of inflow, arc over to private reserve
    c.setStrokeColor(BLUE_LIGHT)
    c.setLineWidth(2.5)
    c.bezier(ix + ir, iy + 30, ix + ir + 60, iy + 120, prx - 60, pry + 120, prx - 90, pry + 40)
    # Arrow tip
    draw_arrow(c, prx - 92, pry + 38, prx - 88, pry + 10, BLUE_LIGHT)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(300, iy + 105, f"EXCESS: {fmt(calc['excess'])} / mo")

    # PRIVATE RESERVE box (blue, right)
    pr_w, pr_h = 160, 120
    px = prx - pr_w / 2
    py = pry - pr_h / 2
    c.setFillColor(BLUE)
    c.roundRect(px, py, pr_w, pr_h, 12, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(prx, py + pr_h - 18, "PRIVATE RESERVE")
    c.setFont("Helvetica", 8)
    c.drawCentredString(prx, py + pr_h - 32, "High-Yield Savings")
    c.setLineWidth(1)
    c.setStrokeColor(WHITE)
    c.line(px + 15, py + pr_h - 38, px + pr_w - 15, py + pr_h - 38)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(prx, py + pr_h - 52, "Current Balance")
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(prx, py + pr_h - 70, fmt(calc["private_reserve_balance"]))
    c.setFont("Helvetica", 8)
    c.drawCentredString(prx, py + pr_h - 85, f"Target: {fmt(calc['private_reserve_target'])}")

    # ─── Page 1 caption (under diagram) ───────────────────────
    cap_y = cy - 130
    c.setFillColor(DARK)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(W / 2, cap_y,
        f"Monthly excess of {fmt(calc['excess'])} flows from Inflow into the Private Reserve.")

    # ─── Footer (page 1) ─────────────────────────────────────
    c.setFillColor(BLUE)
    c.rect(0, 0, W, 28, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 8)
    c.drawCentredString(W / 2, 14, "Windbrook Solutions  |  Confidential  |  For Client Use Only")
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, 4, "Page 1 of 2 — Cash Flow Diagram")

    c.showPage()

    # ───────────────────────────────────────────────────────────
    # ─── PAGE 2: Reserve, Investment, Target ──────────────────
    # ───────────────────────────────────────────────────────────
    c.setFillColor(BLUE)
    c.rect(0, H - 70, W, 70, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, H - 40, "Reserve & Investment Summary")
    c.setFont("Helvetica", 11)
    c.drawString(40, H - 58, f"{name}  |  {quarter}  |  {data['generated_at']}")
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(W - 40, H - 45, "WINDBROOK")
    c.setFont("Helvetica", 9)
    c.drawRightString(W - 40, H - 58, "SOLUTIONS")

    # Three big stacked cards
    def draw_metric_card(y, label, value, sublabel, accent=BLUE):
        card_x = 60
        card_w = W - 120
        card_h = 110
        # Card body
        c.setFillColor(WHITE)
        c.setStrokeColor(HexColor("#E2E5EA"))
        c.setLineWidth(1.2)
        c.roundRect(card_x, y, card_w, card_h, 14, fill=1, stroke=1)
        # Left accent stripe
        c.setFillColor(accent)
        p = c.beginPath()
        p.moveTo(card_x + 14, y)
        p.lineTo(card_x, y)
        p.lineTo(card_x, y + card_h)
        p.lineTo(card_x + 14, y + card_h)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        # Label
        c.setFillColor(HexColor("#6B7280"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(card_x + 32, y + card_h - 26, label.upper())
        # Value
        c.setFillColor(accent)
        c.setFont("Helvetica-Bold", 36)
        c.drawString(card_x + 32, y + 38, value)
        # Sublabel
        c.setFillColor(DARK)
        c.setFont("Helvetica", 10)
        c.drawString(card_x + 32, y + 18, sublabel)

    top_y = H - 220
    gap = 130
    draw_metric_card(
        top_y,
        "Private Reserve — Current Balance",
        fmt(calc["private_reserve_balance"]),
        "High-yield savings account",
        BLUE
    )
    draw_metric_card(
        top_y - gap,
        "Investment Account — Charles Schwab",
        fmt(calc["schwab_balance"]),
        "Brokerage balance reported this quarter",
        BLUE_LIGHT
    )
    draw_metric_card(
        top_y - 2 * gap,
        "Private Reserve Target",
        fmt(calc["private_reserve_target"]),
        f"6 × monthly outflow ({fmt(calc['outflow'])}) + insurance deductibles",
        GREEN
    )

    # Progress hint: how close PR balance is to target
    target = calc["private_reserve_target"] or 1
    pct = min(calc["private_reserve_balance"] / target, 1.0)
    bar_x, bar_y, bar_w, bar_h = 60, top_y - 2 * gap - 50, W - 120, 14
    c.setFillColor(HexColor("#E2E5EA"))
    c.roundRect(bar_x, bar_y, bar_w, bar_h, 7, fill=1, stroke=0)
    c.setFillColor(BLUE)
    c.roundRect(bar_x, bar_y, bar_w * pct, bar_h, 7, fill=1, stroke=0)
    c.setFillColor(DARK)
    c.setFont("Helvetica", 9)
    c.drawString(bar_x, bar_y + bar_h + 8, f"Reserve funded: {int(pct * 100)}% of target")

    # ─── Footer (page 2) ─────────────────────────────────────
    c.setFillColor(BLUE)
    c.rect(0, 0, W, 28, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 8)
    c.drawCentredString(W / 2, 14, "Windbrook Solutions  |  Confidential  |  For Client Use Only")
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, 4, "Page 2 of 2 — Reserve & Investment Summary")

    c.showPage()
    c.save()


def generate_tcc_pdf(buf, data):
    c = canvas.Canvas(buf, pagesize=letter)
    W, H = letter
    calc = data["calc"]
    client = data["client"]
    balances = data["balances"]
    quarter = data["quarter"]

    name = full_name(client)

    # ─── Header ───────────────────────────────────────────────
    c.setFillColor(BLUE)
    c.rect(0, H - 70, W, 70, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, H - 40, "Total Client Chart")
    c.setFont("Helvetica", 11)
    c.drawString(40, H - 58, f"{name}  |  {quarter}  |  {data['generated_at']}")
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(W - 40, H - 45, "WINDBROOK")
    c.setFont("Helvetica", 9)
    c.drawRightString(W - 40, H - 58, "SOLUTIONS")

    # ─── Client info bubbles ──────────────────────────────────
    def draw_client_bubble(cx, cy, name, dob, age, ssn):
        c.setFillColor(GREEN)
        c.circle(cx, cy, 42, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(cx, cy + 16, name)
        c.setFont("Helvetica", 8)
        c.drawCentredString(cx, cy + 3, f"DOB: {dob}")
        c.drawCentredString(cx, cy - 10, f"Age: {age}")
        c.drawCentredString(cx, cy - 23, f"SSN: XXX-XX-{ssn}")

    def calc_age(dob_str):
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            today = datetime.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except:
            return "N/A"

    from datetime import datetime
    c1y = H - 140
    draw_client_bubble(130, c1y, client.get("name1", "Client 1"),
                       client.get("dob1", ""), calc_age(client.get("dob1", "")), client.get("ssn1", "XXXX"))
    if client.get("name2"):
        draw_client_bubble(W - 130, c1y, client.get("name2", "Client 2"),
                           client.get("dob2", ""), calc_age(client.get("dob2", "")), client.get("ssn2", "XXXX"))

    # ─── Retirement accounts ──────────────────────────────────
    ret_accounts = client.get("retirement_accounts", [])
    ret_y = H - 230

    def draw_account_bubble(cx, cy, acct_type, last4, balance, r=38):
        c.setFillColor(BLUE_LIGHT)
        c.circle(cx, cy, r, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(cx, cy + 14, acct_type)
        c.setFont("Helvetica", 7)
        c.drawCentredString(cx, cy + 3, f"••••{last4}")
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(cx, cy - 10, fmt(balance))

    # Split by client1 / client2
    ret1 = [(i, a) for i, a in enumerate(ret_accounts) if a["owner"] == "client1"]
    ret2 = [(i, a) for i, a in enumerate(ret_accounts) if a["owner"] == "client2"]

    # Client 1 retirement (left side)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(30, ret_y + 10, f"{client.get('name1','')} — Retirement")
    spacing = 100
    start_x = 75
    for j, (i, a) in enumerate(ret1):
        bal = float(balances.get(f"ret_{i}", 0))
        draw_account_bubble(start_x + j * spacing, ret_y - 30, a["type"], a["last4"], bal)

    # Client 2 retirement (right side)
    if ret2:
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(W / 2 + 20, ret_y + 10, f"{client.get('name2','')} — Retirement")
        start_x2 = W / 2 + 65
        for j, (i, a) in enumerate(ret2):
            bal = float(balances.get(f"ret_{i}", 0))
            draw_account_bubble(start_x2 + j * spacing, ret_y - 30, a["type"], a["last4"], bal)

    # Divider
    div_y = ret_y - 90
    c.setStrokeColor(GRAY_MED)
    c.setLineWidth(1)
    c.line(30, div_y, W - 30, div_y)

    # ─── Summary boxes (retirement totals) ────────────────────
    def draw_summary_box(x, y, w, h, label, value):
        c.setFillColor(GRAY)
        c.roundRect(x, y, w, h, 6, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + w / 2, y + h - 14, label)
        c.setFillColor(BLUE)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(x + w / 2, y + 8, fmt(value))

    sb_y = div_y - 42
    draw_summary_box(30, sb_y, 160, 38, f"{client.get('name1','')} Retirement Total", calc["ret1_total"])
    if ret2:
        draw_summary_box(W / 2 - 80, sb_y, 160, 38, f"{client.get('name2','')} Retirement Total", calc["ret2_total"])

    # ─── Non-retirement accounts ──────────────────────────────
    nret_y = sb_y - 60
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(30, nret_y + 10, "Non-Retirement Accounts")

    nret_accounts = client.get("non_retirement_accounts", [])
    start_x = 75
    for j, a in enumerate(nret_accounts):
        bal = float(balances.get(f"nret_{j}", 0))
        draw_account_bubble(start_x + j * spacing, nret_y - 30, a["type"], a["last4"], bal, r=40)

    # Trust bubble (center)
    trust_x = W / 2
    trust_y = nret_y - 30
    trust_val = float(balances.get("trust_value", 0))
    c.setFillColor(HexColor("#6B8F71"))
    c.circle(trust_x, trust_y, 48, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(trust_x, trust_y + 18, "TRUST")
    c.setFont("Helvetica", 7)
    addr = client.get("trust", {}).get("address", "")
    c.drawCentredString(trust_x, trust_y + 5, addr[:28])
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(trust_x, trust_y - 10, fmt(trust_val))
    c.setFont("Helvetica", 7)
    c.drawCentredString(trust_x, trust_y - 22, "Zillow Zestimate")

    # Non-ret summary
    sb_y2 = nret_y - 90
    draw_summary_box(30, sb_y2, 160, 38, "Non-Retirement Total", calc["non_ret_total"])
    draw_summary_box(W - 190, sb_y2, 160, 38, "GRAND TOTAL", calc["grand_total"])

    # ─── Liabilities ──────────────────────────────────────────
    liab_y = sb_y2 - 55
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(30, liab_y + 5, "Liabilities")
    c.setStrokeColor(GRAY_MED)
    c.line(30, liab_y, W - 30, liab_y)

    liabs = client.get("liabilities", [])
    for j, liab in enumerate(liabs):
        bal = float(balances.get(f"liab_{j}", 0))
        lx = 30 + j * 190
        ly = liab_y - 50
        c.setFillColor(HexColor("#8B0000"))
        c.roundRect(lx, ly, 170, 42, 6, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(lx + 10, ly + 28, liab["type"])
        c.setFont("Helvetica", 8)
        c.drawString(lx + 10, ly + 16, f"Rate: {liab.get('rate', 0)}%  ••••{liab.get('last4','')}")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(lx + 10, ly + 4, fmt(bal))

    # Liabilities total
    draw_summary_box(W - 190, liab_y - 56, 160, 38, "Liabilities Total", calc["liabilities_total"])

    # ─── Footer ───────────────────────────────────────────────
    c.setFillColor(BLUE)
    c.rect(0, 0, W, 28, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 8)
    c.drawCentredString(W / 2, 10, "Windbrook Solutions  |  Confidential  |  For Client Use Only")

    c.showPage()
    c.save()
