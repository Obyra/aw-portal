from flask import (
    Flask, render_template, request, jsonify, send_file,
    redirect, url_for, session, abort,
)
import sqlite3
import json
import io
import os
import secrets
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from pdf_generator import generate_sacs_pdf, generate_tcc_pdf

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
DB_PATH = os.environ.get("DATABASE_PATH", "portal.db")

ROLES = ("admin", "planner", "assistant")


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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin','planner','assistant')),
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()

    # Seed demo client
    if conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0] == 0:
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
            ],
        }
        conn.execute("INSERT INTO clients (data) VALUES (?)", [json.dumps(demo)])
        conn.commit()

    # Seed default team users
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        default_pw = os.environ.get("DEFAULT_USER_PASSWORD", "TempPass2026!")
        users = [
            ("andrew",  "Andrew",  "admin"),
            ("rebecca", "Rebecca", "planner"),
            ("maryann", "Maryann", "assistant"),
        ]
        for u, name, role in users:
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?,?,?,?)",
                [u, generate_password_hash(default_pw), name, role],
            )
        conn.commit()
        print(f"[init_db] Seeded default users with temporary password: {default_pw}")
        for u, name, role in users:
            print(f"          {u:<10} ({role})")
        print("[init_db] Each user should change their password after first login.")

    conn.close()


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login", next=request.path))
            if session.get("role") not in roles:
                return render_template("forbidden.html"), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.context_processor
def inject_user():
    if "user_id" in session:
        return {
            "current_user": {
                "id": session["user_id"],
                "username": session["username"],
                "full_name": session["full_name"],
                "role": session["role"],
            }
        }
    return {"current_user": None}


# ─── Health check (public, no auth) ───────────────────────────────────────────

@app.route("/health")
def health():
    return "ok", 200


# ─── Auth routes ──────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""
        conn = get_db()
        row = conn.execute(
            "SELECT id, username, password_hash, full_name, role FROM users WHERE username=?",
            [username],
        ).fetchone()
        conn.close()
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["user_id"] = row["id"]
            session["username"] = row["username"]
            session["full_name"] = row["full_name"]
            session["role"] = row["role"]
            nxt = request.args.get("next") or url_for("index")
            return redirect(nxt)
        return render_template(
            "login.html", error="Invalid username or password.", username=username
        ), 401

    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("login.html", error=None, username="")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    msg = err = None
    if request.method == "POST":
        current = request.form.get("current_password") or ""
        new = request.form.get("new_password") or ""
        confirm = request.form.get("confirm_password") or ""
        conn = get_db()
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id=?", [session["user_id"]]
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], current):
            err = "Current password is incorrect."
        elif len(new) < 8:
            err = "New password must be at least 8 characters."
        elif new != confirm:
            err = "New password and confirmation do not match."
        else:
            conn.execute(
                "UPDATE users SET password_hash=? WHERE id=?",
                [generate_password_hash(new), session["user_id"]],
            )
            conn.commit()
            msg = "Password updated successfully."
        conn.close()
    return render_template("account.html", msg=msg, err=err)


# ─── Admin: user management ───────────────────────────────────────────────────

@app.route("/admin/users", methods=["GET", "POST"])
@role_required("admin")
def admin_users():
    conn = get_db()
    msg = err = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        full_name = (request.form.get("full_name") or "").strip()
        role = request.form.get("role") or "assistant"
        password = request.form.get("password") or ""
        if not username or not full_name:
            err = "Username and full name are required."
        elif len(password) < 8:
            err = "Password must be at least 8 characters."
        elif role not in ROLES:
            err = "Invalid role."
        elif conn.execute("SELECT 1 FROM users WHERE username=?", [username]).fetchone():
            err = f"Username '{username}' already exists."
        else:
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?,?,?,?)",
                [username, generate_password_hash(password), full_name, role],
            )
            conn.commit()
            msg = f"User '{username}' created."
    users = conn.execute(
        "SELECT id, username, full_name, role, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return render_template("admin_users.html", users=users, msg=msg, err=err)


@app.route("/admin/users/<int:uid>/delete", methods=["POST"])
@role_required("admin")
def admin_delete_user(uid):
    if uid == session["user_id"]:
        # Prevent self-deletion (would lock out the only admin)
        return redirect(url_for("admin_users"))
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", [uid])
    conn.commit()
    conn.close()
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:uid>/reset_password", methods=["POST"])
@role_required("admin")
def admin_reset_password(uid):
    new_pw = request.form.get("new_password") or ""
    if len(new_pw) < 8:
        return redirect(url_for("admin_users"))
    conn = get_db()
    conn.execute(
        "UPDATE users SET password_hash=? WHERE id=?",
        [generate_password_hash(new_pw), uid],
    )
    conn.commit()
    conn.close()
    return redirect(url_for("admin_users"))


# ─── Dashboard helpers ────────────────────────────────────────────────────────

STATUS_LABELS = {
    "completed": "Completed This Quarter",
    "pending":   "Report Pending",
    "missing":   "Missing Data",
    "none":      "No Report Generated",
}


def current_quarter_str(now=None):
    now = now or datetime.now()
    q = (now.month - 1) // 3 + 1
    return f"Q{q} {now.year}"


def client_full_name(d):
    n1 = (d.get("name1") or "").strip()
    n2 = (d.get("name2") or "").strip()
    last = (d.get("last_name") or "").strip()
    if n2:
        return f"{n1} & {n2} {last}".strip()
    return f"{n1} {last}".strip()


def is_missing_static_data(d):
    if not d.get("monthly_inflow") or not d.get("monthly_outflow"):
        return True
    has_accounts = bool(d.get("retirement_accounts")) or bool(d.get("non_retirement_accounts"))
    return not has_accounts


def client_status(d, last_quarter, cur_q):
    if is_missing_static_data(d):
        return "missing"
    if not last_quarter:
        return "none"
    if last_quarter == cur_q:
        return "completed"
    return "pending"


# ─── Client + report routes (all require login) ───────────────────────────────

@app.route("/")
@login_required
def index():
    conn = get_db()
    cur_q = current_quarter_str()

    rows = conn.execute("SELECT id, data, updated_at FROM clients ORDER BY id").fetchall()
    clients = []
    for r in rows:
        d = json.loads(r["data"])
        last_report = conn.execute(
            "SELECT quarter, created_at FROM reports WHERE client_id=? ORDER BY id DESC LIMIT 1",
            [r["id"]],
        ).fetchone()
        last_q = last_report["quarter"] if last_report else None
        status = client_status(d, last_q, cur_q)
        clients.append({
            "id": r["id"],
            "full_name": client_full_name(d),
            "last_report": last_q,
            "last_report_date": last_report["created_at"][:10] if last_report else None,
            "status": status,
            "status_label": STATUS_LABELS[status],
            "updated_at": r["updated_at"][:10],
        })

    recent_rows = conn.execute("""
        SELECT r.id, r.client_id, r.quarter, r.created_at, c.data AS client_data
        FROM reports r
        JOIN clients c ON c.id = r.client_id
        ORDER BY r.id DESC
        LIMIT 10
    """).fetchall()
    recent_reports = []
    for r in recent_rows:
        d = json.loads(r["client_data"])
        recent_reports.append({
            "id": r["id"],
            "client_id": r["client_id"],
            "client_name": client_full_name(d),
            "quarter": r["quarter"],
            "date": r["created_at"][:10],
            "is_current": r["quarter"] == cur_q,
        })

    counts = {
        "total":     len(clients),
        "completed": sum(1 for c in clients if c["status"] == "completed"),
        "pending":   sum(1 for c in clients if c["status"] in ("pending", "none")),
        "missing":   sum(1 for c in clients if c["status"] == "missing"),
    }

    conn.close()
    return render_template(
        "index.html",
        clients=clients,
        recent_reports=recent_reports,
        current_quarter=cur_q,
        counts=counts,
    )


@app.route("/client/new", methods=["GET", "POST"])
@login_required
def new_client():
    if request.method == "POST":
        data = request.json
        conn = get_db()
        conn.execute("INSERT INTO clients (data) VALUES (?)", [json.dumps(data)])
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    return render_template("client_form.html", client=None, client_id=None)


@app.route("/client/<int:cid>/edit", methods=["GET", "POST"])
@login_required
def edit_client(cid):
    conn = get_db()
    if request.method == "POST":
        data = request.json
        conn.execute(
            "UPDATE clients SET data=?, updated_at=datetime('now') WHERE id=?",
            [json.dumps(data), cid],
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    row = conn.execute("SELECT data FROM clients WHERE id=?", [cid]).fetchone()
    conn.close()
    client = json.loads(row["data"])
    return render_template("client_form.html", client=client, client_id=cid)


@app.route("/client/<int:cid>/report", methods=["GET", "POST"])
@login_required
def generate_report(cid):
    conn = get_db()
    row = conn.execute("SELECT data FROM clients WHERE id=?", [cid]).fetchone()
    client = json.loads(row["data"])

    if request.method == "POST":
        balances = request.json
        inflow = float(client["monthly_inflow"])
        outflow = float(client["monthly_outflow"])
        excess = inflow - outflow
        private_reserve_target = (6 * outflow) + float(client.get("insurance_deductibles", 0))

        ret1_total = sum(
            float(balances.get(f"ret_{i}", 0))
            for i, a in enumerate(client["retirement_accounts"])
            if a["owner"] == "client1"
        )
        ret2_total = sum(
            float(balances.get(f"ret_{i}", 0))
            for i, a in enumerate(client["retirement_accounts"])
            if a["owner"] == "client2"
        )
        non_ret_total = sum(
            float(balances.get(f"nret_{i}", 0))
            for i in range(len(client["non_retirement_accounts"]))
        )
        trust_value = float(balances.get("trust_value", 0))
        grand_total = ret1_total + ret2_total + non_ret_total + trust_value
        liabilities_total = sum(
            float(balances.get(f"liab_{i}", 0))
            for i in range(len(client.get("liabilities", [])))
        )

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
            "generated_at": datetime.now().strftime("%B %d, %Y"),
            "generated_by": session.get("full_name", "Unknown"),
            "prepared_by": (balances.get("prepared_by") or "").strip() or session.get("full_name", "Unknown"),
        }

        cur = conn.execute(
            "INSERT INTO reports (client_id, quarter, report_data) VALUES (?,?,?)",
            [cid, report_data["quarter"], json.dumps(report_data)],
        )
        report_id = cur.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "report_id": report_id, "calc": report_data["calc"]})

    last = conn.execute(
        "SELECT report_data FROM reports WHERE client_id=? ORDER BY id DESC LIMIT 1",
        [cid],
    ).fetchone()
    last_balances = json.loads(last["report_data"])["balances"] if last else {}
    conn.close()
    return render_template(
        "report_form.html", client=client, client_id=cid, last_balances=last_balances
    )


@app.route("/report/<int:rid>/pdf/<report_type>")
@login_required
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
@login_required
def report_history(cid):
    conn = get_db()
    row = conn.execute("SELECT data FROM clients WHERE id=?", [cid]).fetchone()
    client = json.loads(row["data"])
    reports = conn.execute(
        "SELECT id, quarter, created_at FROM reports WHERE client_id=? ORDER BY id DESC",
        [cid],
    ).fetchall()
    conn.close()
    return render_template("history.html", client=client, client_id=cid, reports=reports)


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
