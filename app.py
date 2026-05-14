from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import sqlite3
import json
import io
from datetime import datetime
from pdf_generator import generate_sacs_pdf, generate_tcc_pdf

app = Flask(__name__)
DB_PATH = "portal.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            quarter TEXT NOT NULL,
            report_data TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );
    """)
    conn.commit()
    # Seed a demo client if none exist
    cur = conn.execute("SELECT COUNT(*) FROM clients")
    if cur.fetchone()[0] == 0:
        demo = {
            "name1": "James", "name2": "Sarah", "last_name": "Patterson",
            "dob1": "1968-04-12", "dob2": "1971-09-23",
            "ssn1": "4821", "ssn2": "3094",
            "monthly_inflow": 15000,
            "monthly_outflow": 11000,
            "insurance_deductibles": 3500,
            "retirement_accounts": [
                {"owner": "client1", "type": "IRA", "last4": "2241"},
                {"owner": "client1", "type": "Roth IRA", "last4": "8832"},
                {"owner": "client2", "type": "401K", "last4": "5519"},
            ],
            "non_retirement_accounts": [
                {"type": "Schwab Brokerage", "last4": "7743"},
                {"type": "Joint Brokerage", "last4": "2201"},
            ],
            "trust": {"address": "1420 Peachtree Rd NE, Atlanta, GA"},
            "liabilities": [
                {"type": "Mortgage", "last4": "9921", "rate": 3.25},
                {"type": "Auto Loan", "last4": "4410", "rate": 5.99},
            ]
        }
        conn.execute("INSERT INTO clients (data) VALUES (?)", [json.dumps(demo)])
        conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    rows = conn.execute("SELECT id, data, updated_at FROM clients ORDER BY id").fetchall()
    clients = []
    for r in rows:
        d = json.loads(r["data"])
        last_report = conn.execute(
            "SELECT quarter, created_at FROM reports WHERE client_id=? ORDER BY id DESC LIMIT 1", [r["id"]]
        ).fetchone()
        clients.append({
            "id": r["id"],
            "full_name": f"{d.get('name1','')} & {d.get('name2','')} {d.get('last_name','')}".strip() if d.get('name2') else f"{d.get('name1','')} {d.get('last_name','')}",
            "last_report": last_report["quarter"] if last_report else None,
            "last_report_date": last_report["created_at"][:10] if last_report else None,
            "updated_at": r["updated_at"][:10]
        })
    conn.close()
    return render_template("index.html", clients=clients)

@app.route("/client/new", methods=["GET","POST"])
def new_client():
    if request.method == "POST":
        data = request.json
        conn = get_db()
        conn.execute("INSERT INTO clients (data) VALUES (?)", [json.dumps(data)])
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    return render_template("client_form.html", client=None, client_id=None)

@app.route("/client/<int:cid>/edit", methods=["GET","POST"])
def edit_client(cid):
    conn = get_db()
    if request.method == "POST":
        data = request.json
        conn.execute("UPDATE clients SET data=?, updated_at=datetime('now') WHERE id=?", [json.dumps(data), cid])
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    row = conn.execute("SELECT data FROM clients WHERE id=?", [cid]).fetchone()
    conn.close()
    client = json.loads(row["data"])
    return render_template("client_form.html", client=client, client_id=cid)

@app.route("/client/<int:cid>/report", methods=["GET","POST"])
def generate_report(cid):
    conn = get_db()
    row = conn.execute("SELECT data FROM clients WHERE id=?", [cid]).fetchone()
    client = json.loads(row["data"])

    if request.method == "POST":
        balances = request.json
        # Calculations
        inflow = float(client["monthly_inflow"])
        outflow = float(client["monthly_outflow"])
        excess = inflow - outflow
        private_reserve_target = (6 * outflow) + float(client.get("insurance_deductibles", 0))

        ret1_total = sum(float(balances.get(f"ret_{i}", 0)) for i, a in enumerate(client["retirement_accounts"]) if a["owner"] == "client1")
        ret2_total = sum(float(balances.get(f"ret_{i}", 0)) for i, a in enumerate(client["retirement_accounts"]) if a["owner"] == "client2")
        non_ret_total = sum(float(balances.get(f"nret_{i}", 0)) for i in range(len(client["non_retirement_accounts"])))
        trust_value = float(balances.get("trust_value", 0))
        grand_total = ret1_total + ret2_total + non_ret_total + trust_value
        liabilities_total = sum(float(balances.get(f"liab_{i}", 0)) for i in range(len(client.get("liabilities", []))))

        report_data = {
            "client": client,
            "balances": balances,
            "calc": {
                "inflow": inflow, "outflow": outflow, "excess": excess,
                "private_reserve_target": private_reserve_target,
                "ret1_total": ret1_total, "ret2_total": ret2_total,
                "non_ret_total": non_ret_total, "trust_value": trust_value,
                "grand_total": grand_total, "liabilities_total": liabilities_total,
                "private_reserve_balance": float(balances.get("private_reserve", 0)),
                "schwab_balance": float(balances.get("schwab_balance", 0)),
            },
            "quarter": balances.get("quarter", "Q1 2026"),
            "generated_at": datetime.now().strftime("%B %d, %Y")
        }

        cur = conn.execute("INSERT INTO reports (client_id, quarter, report_data) VALUES (?,?,?)",
                           [cid, report_data["quarter"], json.dumps(report_data)])
        report_id = cur.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "report_id": report_id, "calc": report_data["calc"]})

    # GET - load last balances for reference
    last = conn.execute("SELECT report_data FROM reports WHERE client_id=? ORDER BY id DESC LIMIT 1", [cid]).fetchone()
    last_balances = json.loads(last["report_data"])["balances"] if last else {}
    conn.close()
    return render_template("report_form.html", client=client, client_id=cid, last_balances=last_balances)

@app.route("/report/<int:rid>/pdf/<report_type>")
def download_pdf(rid, report_type):
    conn = get_db()
    row = conn.execute("SELECT report_data FROM reports WHERE id=?", [rid]).fetchone()
    conn.close()
    if not row:
        return "Report not found", 404
    report_data = json.loads(row["report_data"])
    buf = io.BytesIO()
    if report_type == "sacs":
        generate_sacs_pdf(buf, report_data)
        filename = f"SACS_{report_data['quarter'].replace(' ','_')}.pdf"
    else:
        generate_tcc_pdf(buf, report_data)
        filename = f"TCC_{report_data['quarter'].replace(' ','_')}.pdf"
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)

@app.route("/client/<int:cid>/reports")
def report_history(cid):
    conn = get_db()
    row = conn.execute("SELECT data FROM clients WHERE id=?", [cid]).fetchone()
    client = json.loads(row["data"])
    reports = conn.execute("SELECT id, quarter, created_at FROM reports WHERE client_id=? ORDER BY id DESC", [cid]).fetchall()
    conn.close()
    return render_template("history.html", client=client, client_id=cid, reports=reports)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
