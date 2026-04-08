"""
FlowMingo — AML Intelligence Platform
Backend API  (Flask + SQLite)
Run:  python app.py
Then open:  http://localhost:5000
"""

import sqlite3, os, json, random, string, uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g, send_from_directory, render_template

app = Flask(__name__, static_folder="static", template_folder="templates")
DB_PATH = os.path.join(os.path.dirname(__file__), "flowmingo.db")

# ─────────────────────────────────────────────
#  DATABASE HELPERS
# ─────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db: db.close()

def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv  = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid

# ─────────────────────────────────────────────
#  SCHEMA — runs on first launch
# ─────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ref         TEXT    UNIQUE NOT NULL,
    ts          TEXT    NOT NULL,          -- ISO-8601 datetime
    from_acc    TEXT    NOT NULL,
    to_acc      TEXT    NOT NULL,
    bank_from   TEXT    NOT NULL DEFAULT '',
    bank_to     TEXT    NOT NULL DEFAULT '',
    amount      REAL    NOT NULL,
    mode        TEXT    NOT NULL DEFAULT 'NEFT',
    typology    TEXT    NOT NULL DEFAULT 'normal',
    risk_score  INTEGER NOT NULL DEFAULT 0,
    status      TEXT    NOT NULL DEFAULT 'review',
    is_manual   INTEGER NOT NULL DEFAULT 0,  -- 1 = user-filed complaint
    notes       TEXT    DEFAULT ''
);

CREATE TABLE IF NOT EXISTS complaints (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ref           TEXT    UNIQUE NOT NULL,
    ts            TEXT    NOT NULL,
    my_acc        TEXT    NOT NULL,
    susp_acc      TEXT    NOT NULL,
    my_bank       TEXT    NOT NULL DEFAULT '',
    susp_bank     TEXT    NOT NULL DEFAULT '',
    mode          TEXT    NOT NULL DEFAULT 'NEFT',
    amount        REAL    NOT NULL,
    txn_count     INTEGER DEFAULT 1,
    txn_ref       TEXT    DEFAULT '',
    txn_date      TEXT    DEFAULT '',
    txn_time      TEXT    DEFAULT '',
    typology      TEXT    NOT NULL,
    description   TEXT    DEFAULT '',
    officer_name  TEXT    DEFAULT '',
    officer_id    TEXT    DEFAULT '',
    priority      TEXT    DEFAULT 'high',
    risk_score    INTEGER NOT NULL DEFAULT 0,
    status        TEXT    NOT NULL DEFAULT 'open',  -- open / under_review / closed
    str_ref       TEXT    DEFAULT ''
);

CREATE TABLE IF NOT EXISTS alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL,
    txn_ref     TEXT    NOT NULL,
    from_acc    TEXT    NOT NULL,
    to_acc      TEXT    NOT NULL,
    amount      REAL    NOT NULL,
    typology    TEXT    NOT NULL,
    risk_score  INTEGER NOT NULL,
    severity    TEXT    NOT NULL DEFAULT 'high',  -- high / medium / low
    resolved    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS audit_log (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       TEXT NOT NULL,
    action   TEXT NOT NULL,
    entity   TEXT NOT NULL,   -- 'transaction' | 'complaint' | 'alert'
    ref      TEXT NOT NULL,
    detail   TEXT DEFAULT ''
);
"""

def init_db():
    with app.app_context():
        db = sqlite3.connect(DB_PATH)
        db.executescript(SCHEMA)
        db.commit()
        # Seed if empty
        cur = db.execute("SELECT COUNT(*) FROM transactions")
        if cur.fetchone()[0] == 0:
            _seed(db)
        db.close()

# ─────────────────────────────────────────────
#  SEED DATA
# ─────────────────────────────────────────────
BANKS    = ["Union Bank of India","SBI","HDFC Bank","ICICI Bank","Axis Bank","Kotak Mahindra","PNB","Bank of Baroda"]
MODES    = ["RTGS","NEFT","IMPS","UPI","SWIFT","Cheque"]
TYPOS    = ["smurfing","round-tripping","layering","normal","dormant"]
STATUSES = ["flagged","review","cleared"]

def _rand_acc(): return "ACC" + "".join(random.choices(string.digits, k=5))
def _rand_ref(): return "UTR" + datetime.now().strftime("%Y%m%d") + "".join(random.choices(string.digits, k=6))
def _str_ref():  return "STR/" + str(datetime.now().year) + "/" + "".join(random.choices(string.digits, k=5))

def _make_txn(db, overrides=None):
    overrides = overrides or {}
    typo   = overrides.get("typology", random.choice(TYPOS))
    risk   = overrides.get("risk_score", _calc_risk(typo))
    amt    = overrides.get("amount", random.randint(5000,49999) if typo=="smurfing" else random.randint(50000,2000000))
    status = "flagged" if risk > 85 else ("review" if risk > 55 else "cleared")
    ts     = (datetime.now() - timedelta(seconds=random.randint(0,86400))).isoformat(timespec="seconds")
    row = dict(
        ref       = _rand_ref(),
        ts        = ts,
        from_acc  = _rand_acc(),
        to_acc    = _rand_acc(),
        bank_from = random.choice(BANKS),
        bank_to   = random.choice(BANKS),
        amount    = amt,
        mode      = random.choice(MODES),
        typology  = typo,
        risk_score= risk,
        status    = status,
        is_manual = 0,
        notes     = "",
    )
    row.update(overrides)
    db.execute("""INSERT OR IGNORE INTO transactions
        (ref,ts,from_acc,to_acc,bank_from,bank_to,amount,mode,typology,risk_score,status,is_manual,notes)
        VALUES (:ref,:ts,:from_acc,:to_acc,:bank_from,:bank_to,:amount,:mode,:typology,:risk_score,:status,:is_manual,:notes)""", row)
    if row["risk_score"] > 70:
        sev = "high" if row["risk_score"]>85 else "medium"
        db.execute("""INSERT INTO alerts (ts,txn_ref,from_acc,to_acc,amount,typology,risk_score,severity)
            VALUES (?,?,?,?,?,?,?,?)""",
            (row["ts"],row["ref"],row["from_acc"],row["to_acc"],row["amount"],row["typology"],row["risk_score"],sev))

def _calc_risk(typo):
    if typo == "smurfing":      return random.randint(70,99)
    if typo == "layering":      return random.randint(75,99)
    if typo == "round-tripping":return random.randint(60,95)
    if typo == "dormant":       return random.randint(50,80)
    return random.randint(5,45)

def _seed(db):
    for _ in range(50):
        _make_txn(db)
    db.commit()

# ─────────────────────────────────────────────
#  UTILITY
# ─────────────────────────────────────────────
def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

# ─────────────────────────────────────────────
#  FRONTEND SERVING
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("templates", "index.html")

# ─────────────────────────────────────────────
#  API — STATS
# ─────────────────────────────────────────────
@app.route("/api/stats")
def api_stats():
    db = get_db()
    total       = db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    flagged     = db.execute("SELECT COUNT(*) FROM transactions WHERE status='flagged'").fetchone()[0]
    smurfing    = db.execute("SELECT COUNT(*) FROM transactions WHERE typology='smurfing'").fetchone()[0]
    layering    = db.execute("SELECT COUNT(*) FROM transactions WHERE typology='layering'").fetchone()[0]
    round_trip  = db.execute("SELECT COUNT(*) FROM transactions WHERE typology='round-tripping'").fetchone()[0]
    normal      = db.execute("SELECT COUNT(*) FROM transactions WHERE typology='normal'").fetchone()[0]
    volume      = db.execute("SELECT COALESCE(SUM(amount),0) FROM transactions").fetchone()[0]
    complaints  = db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    open_alerts = db.execute("SELECT COUNT(*) FROM alerts WHERE resolved=0").fetchone()[0]
    accounts    = db.execute("SELECT COUNT(DISTINCT from_acc)+COUNT(DISTINCT to_acc) FROM transactions").fetchone()[0]
    return jsonify({
        "total_transactions": total,
        "flagged":            flagged,
        "smurfing":           smurfing,
        "layering":           layering,
        "round_tripping":     round_trip,
        "normal":             normal,
        "total_volume":       volume,
        "complaints_filed":   complaints,
        "open_alerts":        open_alerts,
        "monitored_accounts": accounts,
    })

# ─────────────────────────────────────────────
#  API — TRANSACTIONS
# ─────────────────────────────────────────────
@app.route("/api/transactions")
def api_transactions():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 15))
    q        = request.args.get("q", "").strip()
    typology = request.args.get("typology", "")
    status   = request.args.get("status", "")
    order    = request.args.get("order", "desc")   # asc | desc

    conditions, params = [], []
    if q:
        conditions.append("(ref LIKE ? OR from_acc LIKE ? OR to_acc LIKE ?)")
        like = f"%{q}%"
        params += [like, like, like]
    if typology:
        conditions.append("typology = ?"); params.append(typology)
    if status:
        conditions.append("status = ?"); params.append(status)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    order_sql = "DESC" if order == "desc" else "ASC"

    total_count = get_db().execute(f"SELECT COUNT(*) FROM transactions {where}", params).fetchone()[0]
    rows = query(
        f"SELECT * FROM transactions {where} ORDER BY ts {order_sql} LIMIT ? OFFSET ?",
        params + [per_page, (page-1)*per_page]
    )
    return jsonify({
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "records": rows_to_list(rows)
    })

@app.route("/api/transactions/<ref>")
def api_transaction_detail(ref):
    row = query("SELECT * FROM transactions WHERE ref=?", (ref,), one=True)
    if not row: return jsonify({"error": "Not found"}), 404
    return jsonify(row_to_dict(row))

@app.route("/api/transactions/<ref>/status", methods=["PATCH"])
def api_update_txn_status(ref):
    data = request.get_json()
    new_status = data.get("status")
    if new_status not in ("flagged","review","cleared"):
        return jsonify({"error":"Invalid status"}), 400
    execute("UPDATE transactions SET status=? WHERE ref=?", (new_status, ref))
    execute("INSERT INTO audit_log (ts,action,entity,ref,detail) VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(), f"status_changed_to_{new_status}", "transaction", ref, ""))
    return jsonify({"success": True, "ref": ref, "status": new_status})

@app.route("/api/transactions/simulate", methods=["POST"])
def api_simulate():
    """Generate 1-5 random transactions (used by frontend live ticker)."""
    count = int(request.get_json(silent=True, force=True).get("count", 1) if request.data else 1)
    count = min(count, 5)
    new_rows = []
    db = get_db()
    for _ in range(count):
        _make_txn(db)
    db.commit()
    rows = query("SELECT * FROM transactions ORDER BY ts DESC LIMIT ?", (count,))
    return jsonify(rows_to_list(rows))

# ─────────────────────────────────────────────
#  API — COMPLAINTS
# ─────────────────────────────────────────────
@app.route("/api/complaints", methods=["GET"])
def api_get_complaints():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 15))
    q        = request.args.get("q", "").strip()
    status   = request.args.get("status", "")

    conditions, params = [], []
    if q:
        conditions.append("(ref LIKE ? OR my_acc LIKE ? OR susp_acc LIKE ?)")
        like = f"%{q}%"
        params += [like, like, like]
    if status:
        conditions.append("status = ?"); params.append(status)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    total_count = get_db().execute(f"SELECT COUNT(*) FROM complaints {where}", params).fetchone()[0]
    rows = query(
        f"SELECT * FROM complaints {where} ORDER BY ts DESC LIMIT ? OFFSET ?",
        params + [per_page, (page-1)*per_page]
    )
    return jsonify({"total": total_count, "page": page, "per_page": per_page, "records": rows_to_list(rows)})

@app.route("/api/complaints", methods=["POST"])
def api_file_complaint():
    d = request.get_json()
    if not d:
        return jsonify({"error": "No JSON body"}), 400

    required = ["my_acc","susp_acc","amount","typology"]
    for f in required:
        if not d.get(f):
            return jsonify({"error": f"Missing field: {f}"}), 400

    typo       = d["typology"]
    risk       = _calc_risk(typo)
    ref        = "COMPLAINT-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6].upper()
    str_ref    = _str_ref()
    ts         = datetime.now().isoformat(timespec="seconds")

    execute("""INSERT INTO complaints
        (ref,ts,my_acc,susp_acc,my_bank,susp_bank,mode,amount,txn_count,txn_ref,txn_date,txn_time,
         typology,description,officer_name,officer_id,priority,risk_score,status,str_ref)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        ref, ts,
        d["my_acc"], d["susp_acc"],
        d.get("my_bank",""), d.get("susp_bank",""),
        d.get("mode","NEFT"),
        float(d["amount"]),
        int(d.get("txn_count",1)),
        d.get("txn_ref",""),
        d.get("txn_date",""),
        d.get("txn_time",""),
        typo,
        d.get("description",""),
        d.get("officer_name",""),
        d.get("officer_id",""),
        d.get("priority","high"),
        risk,
        "open",
        str_ref,
    ))

    # Mirror complaint as a transaction record
    txn_ref = _rand_ref()
    execute("""INSERT OR IGNORE INTO transactions
        (ref,ts,from_acc,to_acc,bank_from,bank_to,amount,mode,typology,risk_score,status,is_manual,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        txn_ref, ts,
        d["my_acc"], d["susp_acc"],
        d.get("my_bank",""), d.get("susp_bank",""),
        float(d["amount"]),
        d.get("mode","NEFT"),
        typo, risk,
        "flagged" if risk>70 else "review",
        1,
        f"Filed via complaint {ref}",
    ))

    if risk > 60:
        sev = "high" if risk>85 else "medium"
        execute("""INSERT INTO alerts (ts,txn_ref,from_acc,to_acc,amount,typology,risk_score,severity)
            VALUES (?,?,?,?,?,?,?,?)""",
            (ts, txn_ref, d["my_acc"], d["susp_acc"], float(d["amount"]), typo, risk, sev))

    execute("INSERT INTO audit_log (ts,action,entity,ref,detail) VALUES (?,?,?,?,?)",
            (ts,"complaint_filed","complaint",ref,f"by {d.get('officer_name','unknown')}"))

    return jsonify({"success": True, "ref": ref, "str_ref": str_ref, "risk_score": risk}), 201

@app.route("/api/complaints/<ref>")
def api_complaint_detail(ref):
    row = query("SELECT * FROM complaints WHERE ref=?", (ref,), one=True)
    if not row: return jsonify({"error":"Not found"}), 404
    return jsonify(row_to_dict(row))

@app.route("/api/complaints/<ref>/status", methods=["PATCH"])
def api_update_complaint_status(ref):
    data = request.get_json()
    new_status = data.get("status")
    if new_status not in ("open","under_review","closed"):
        return jsonify({"error":"Invalid status"}), 400
    execute("UPDATE complaints SET status=? WHERE ref=?", (new_status, ref))
    execute("INSERT INTO audit_log (ts,action,entity,ref,detail) VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(), f"complaint_{new_status}", "complaint", ref, ""))
    return jsonify({"success": True})

# ─────────────────────────────────────────────
#  API — ALERTS
# ─────────────────────────────────────────────
@app.route("/api/alerts")
def api_alerts():
    limit    = int(request.args.get("limit", 30))
    resolved = request.args.get("resolved", "0")
    rows = query(
        "SELECT * FROM alerts WHERE resolved=? ORDER BY ts DESC LIMIT ?",
        (int(resolved), limit)
    )
    return jsonify(rows_to_list(rows))

@app.route("/api/alerts/<int:alert_id>/resolve", methods=["PATCH"])
def api_resolve_alert(alert_id):
    execute("UPDATE alerts SET resolved=1 WHERE id=?", (alert_id,))
    execute("INSERT INTO audit_log (ts,action,entity,ref,detail) VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(),"alert_resolved","alert",str(alert_id),""))
    return jsonify({"success": True})

# ─────────────────────────────────────────────
#  API — STR REPORT (PDF-ready text)
# ─────────────────────────────────────────────
@app.route("/api/str/<ref>")
def api_str_report(ref):
    """Returns a structured STR report dict for a complaint ref."""
    row = query("SELECT * FROM complaints WHERE ref=?", (ref,), one=True)
    if not row: return jsonify({"error":"Not found"}), 404
    r = row_to_dict(row)
    now = datetime.now()
    report = {
        "report_ref":   r["str_ref"] or _str_ref(),
        "complaint_ref":r["ref"],
        "filed_date":   now.strftime("%d-%b-%Y"),
        "filed_time":   now.strftime("%H:%M:%S"),
        "bank":         r["my_bank"] or "Union Bank of India",
        "branch":       "Mumbai Main",
        "filed_by":     r["officer_name"] or "FlowMingo AML System",
        "officer_id":   r["officer_id"] or "—",
        "subject_acc":  r["susp_acc"],
        "subject_bank": r["susp_bank"],
        "reporting_acc":r["my_acc"],
        "reporting_bank":r["my_bank"],
        "amount":       r["amount"],
        "typology":     r["typology"].upper(),
        "risk_score":   r["risk_score"],
        "priority":     r["priority"].upper(),
        "txn_mode":     r["mode"],
        "txn_date":     r["txn_date"] or r["ts"][:10],
        "txn_ref":      r["txn_ref"] or "—",
        "description":  r["description"],
        "pmla_compliant": True,
        "status":       "READY FOR FIU-IND SUBMISSION",
    }
    return jsonify(report)

# ─────────────────────────────────────────────
#  API — AUDIT LOG
# ─────────────────────────────────────────────
@app.route("/api/audit")
def api_audit():
    limit = int(request.args.get("limit", 50))
    rows  = query("SELECT * FROM audit_log ORDER BY ts DESC LIMIT ?", (limit,))
    return jsonify(rows_to_list(rows))

# ─────────────────────────────────────────────
#  API — EXPORT (CSV text)
# ─────────────────────────────────────────────
@app.route("/api/export/transactions")
def api_export_txn():
    from flask import Response
    rows = query("SELECT * FROM transactions ORDER BY ts DESC")
    lines = ["ref,ts,from_acc,to_acc,bank_from,bank_to,amount,mode,typology,risk_score,status,is_manual"]
    for r in rows:
        lines.append(f'{r["ref"]},{r["ts"]},{r["from_acc"]},{r["to_acc"]},{r["bank_from"]},{r["bank_to"]},{r["amount"]},{r["mode"]},{r["typology"]},{r["risk_score"]},{r["status"]},{r["is_manual"]}')
    return Response("\n".join(lines), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=flowmingo_transactions.csv"})

@app.route("/api/export/complaints")
def api_export_complaints():
    from flask import Response
    rows = query("SELECT * FROM complaints ORDER BY ts DESC")
    lines = ["ref,ts,my_acc,susp_acc,my_bank,susp_bank,amount,mode,typology,risk_score,priority,status,str_ref,officer_name"]
    for r in rows:
        lines.append(f'{r["ref"]},{r["ts"]},{r["my_acc"]},{r["susp_acc"]},{r["my_bank"]},{r["susp_bank"]},{r["amount"]},{r["mode"]},{r["typology"]},{r["risk_score"]},{r["priority"]},{r["status"]},{r["str_ref"]},{r["officer_name"]}')
    return Response("\n".join(lines), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=flowmingo_complaints.csv"})

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("\n🦩  FlowMingo AML Backend running → http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
