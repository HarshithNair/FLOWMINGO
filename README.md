# 🦩 FlowMingo — AML Intelligence Platform

Full-stack Anti-Money Laundering dashboard with Flask backend + SQLite database.  
Built for PMLA 2002 compliance. Suitable as evidence for legal / jury presentation.

---

## 📁 Project Structure

```
flowmingo/
├── app.py               ← Flask backend (all API routes)
├── flowmingo.db         ← SQLite database (auto-created on first run)
├── requirements.txt     ← Python dependencies
├── templates/
│   └── index.html       ← Frontend (served by Flask)
└── README.md
```

---

## ⚡ Quick Start

### 1. Install Python (if not already installed)
Download from https://python.org — requires Python 3.9+

### 2. Install Flask
```bash
pip install flask
```

### 3. Run the server
```bash
cd flowmingo
python app.py
```

### 4. Open in browser
```
http://localhost:5000
```

That's it. The database is created automatically with 50 seed transactions.

---

## 🗄️ Database (flowmingo.db — SQLite)

Four tables — all data is **persistent across restarts**:

| Table | Purpose |
|-------|---------|
| `transactions` | All RTGS/NEFT/IMPS transfers, both auto-simulated and manual |
| `complaints` | Manually filed FIU-IND complaints with full officer details |
| `alerts` | Auto-generated risk alerts from GNN inference |
| `audit_log` | Every status change and action for legal evidence trail |

### View raw data (optional)
```bash
sqlite3 flowmingo.db
sqlite> .tables
sqlite> SELECT * FROM complaints;
sqlite> SELECT * FROM transactions WHERE status='flagged';
sqlite> .quit
```

---

## 🌐 REST API Reference

All endpoints return JSON. Base URL: `http://localhost:5000`

### Stats
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Dashboard KPIs (total txn, flagged, volume, etc.) |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions` | Paginated list. Params: `page`, `per_page`, `q`, `typology`, `status` |
| GET | `/api/transactions/:ref` | Single transaction detail |
| PATCH | `/api/transactions/:ref/status` | Update status. Body: `{"status":"flagged"\|"review"\|"cleared"}` |
| POST | `/api/transactions/simulate` | Generate random transactions. Body: `{"count":3}` |

### Complaints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/complaints` | Paginated list. Params: `page`, `per_page`, `q`, `status` |
| POST | `/api/complaints` | File a new complaint (see body below) |
| GET | `/api/complaints/:ref` | Single complaint detail |
| PATCH | `/api/complaints/:ref/status` | Update status. Body: `{"status":"open"\|"under_review"\|"closed"}` |

### STR Report
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/str/:complaint_ref` | Generate structured STR/CTR report for a complaint |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts` | Recent alerts. Params: `limit`, `resolved` |
| PATCH | `/api/alerts/:id/resolve` | Mark alert as resolved |

### Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/export/transactions` | Download all transactions as CSV |
| GET | `/api/export/complaints` | Download all complaints as CSV |

### Audit Log
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit` | Full audit trail. Param: `limit` |

---

## 📝 Filing a Complaint (POST /api/complaints)

```json
{
  "my_acc":       "ACC12345",
  "susp_acc":     "ACC67890",
  "my_bank":      "Union Bank of India",
  "susp_bank":    "HDFC Bank",
  "mode":         "RTGS",
  "amount":       500000,
  "txn_count":    3,
  "txn_ref":      "UTR20240409123456",
  "txn_date":     "2024-04-09",
  "txn_time":     "14:30:00",
  "typology":     "smurfing",
  "description":  "Multiple sub-threshold transfers observed...",
  "officer_name": "Rahul Sharma",
  "officer_id":   "UBI/AML/001",
  "priority":     "high"
}
```

**Typology values:** `smurfing` | `round-tripping` | `layering` | `normal` | `dormant`  
**Priority values:** `low` | `medium` | `high` | `critical`

**Response:**
```json
{
  "success": true,
  "ref": "COMPLAINT-20240409-A1B2C3",
  "str_ref": "STR/2024/83721",
  "risk_score": 92
}
```

---

## ⚖️ Legal / Jury Evidence Use

The platform is designed so every action is traceable:

1. **Complaints table** — stores officer name, officer ID, timestamp, STR reference, full description
2. **Audit log** — every flag/clear/status-change is logged with timestamp
3. **STR Reports** — generated via `GET /api/str/:ref`, include all PMLA-required fields
4. **CSV Export** — download complete transaction or complaint history for court submission
5. **Database file** — `flowmingo.db` is a standard SQLite file, openable in any DB browser for independent verification

### To present to a jury:
- Run the server, open http://localhost:5000 on a projector
- Navigate to **RECORDS → COMPLAINTS** tab to show all filed complaints
- Click any complaint → **GENERATE STR** to show the FIU-IND report
- Use **⬇ EXPORT CSV** to produce court-admissible spreadsheet records
- The `audit_log` table provides a tamper-evident action trail

---

## 🔧 Configuration

Edit the top of `app.py` to change:
- `DB_PATH` — where the SQLite file is stored
- Port — change `port=5000` in the last line
- Seed count — change `range(50)` in `_seed()` for more initial data

---

## 📦 Dependencies

- Python 3.9+
- Flask (only external dependency)
- SQLite3 (built into Python — no install needed)
