import os
import uuid
import pyodbc # type: ignore
import logging
import traceback
import time
import requests # type: ignore
import webbrowser
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, session, url_for # type: ignore
from flask_cors import CORS # type: ignore
from werkzeug.utils import secure_filename # type: ignore
from threading import Timer, Lock
 
app = Flask(__name__)
app.secret_key = 'supersecretkey'
# Logging
logging.basicConfig(
    filename='error.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
 
# Configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'txt', 'docx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CORS(app)
 
last_ping = time.time()
lock = Lock()
 
# def auto_close_old_tickets():
#     try:
#         conn = get_db_connection()
#         cur = conn.cursor()
 
#         # Calculate date 7 days ago
#         threshold_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
 
#         # Update tickets older than 7 days with Open/In Progress status
#         cur.execute("""
#         UPDATE tickets
#         SET status = 'Closed', closed_date = ?
#         WHERE (status = 'On Hold (ARM Team)' OR status = 'On Hold (SAAIT TEAM)')
#         AND TRY_CAST(date_logged AS DATE) <= ?
#         """, (datetime.now().strftime('%Y-%m-%d'), threshold_date))
 
#         conn.commit()
#         cur.close()
#         conn.close()
#         print("✅ Auto-closed tickets older than 7 days.")
#     except Exception as e:
#         print("❌ Failed to auto-close tickets:", e)
       
# def heartbeat_monitor():
#     while True:
#         time.sleep(10)
#         with lock:
#             if time.time() - last_ping > 15:
#                 print("❌ Browser disconnected. Shutting down...")
#                 os._exit(0)  # force kill Flask
 
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")
 
 
import time, pyodbc, logging

# SQL Server connection with retry logic
def get_db_connection(retries=3, delay=2):
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=saaitserver1.database.windows.net;"
        "DATABASE=saaitsqldb;"
        "UID=ticketadmin;"
        "PWD=Saait@tickets123;"
    )
    for attempt in range(1, retries + 1):
        try:
            logging.info(f"🔗 Attempting DB connection (try {attempt}/{retries})...")
            conn = pyodbc.connect(conn_str, timeout=5)  # 5s timeout
            logging.info("✅ Database connection established")
            return conn
        except pyodbc.OperationalError as e:
            logging.warning(f"⚠️ OperationalError on attempt {attempt}: {e}")
            if attempt < retries:
                time.sleep(delay)  # wait before retry
            else:
                logging.exception("❌ Could not connect to SQL Server after retries")
                raise
        except Exception as e:
            logging.exception("❌ Unexpected error while connecting to SQL Server")
            raise

 
# Email notification helper
def send_ticket_notification(data, mode="create"):
    url = 'https://prod-23.centralindia.logic.azure.com:443/workflows/3b1f78d329a049a4a2ce4d557bc4754d/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=-D5A54qmb6aj9wPzekbVp2psSyYdfnTSQwembUKUZsk'  # 🔁 Replace with your actual Logic App URL
 
    def get_email(name):
        mapping = {
            "ABRAR" : "AbrarKhan@saait.co",
            "Naved" : "NavedS@saait.co",
            "Sanobar" : "Sanobar@saait.co",
            "Rafey" : "Rafey@saait.co",
            "Omair" : "Omair@saait.co",
            "Shahid" : "Shahid@saait.co",
            "Maaz": "maazt@saait.co",
            "Tanveer" : "support@saait.co",
            "Sarfraz" : "ss@saait.co",
            "Ajay" : "ajay.parab@armholding.ae",
            "Afroz" : "afroz.kazi@armholding.ae",
            "Joyson" : "joyson.dmello@armholding.ae",
            "Bryan" : "bryan.tribiana@armholding.ae",
            "Mario" : "mario.francis@armholding.ae",
            "Jayesh" : "jayesh.ladwa@armholding.ae",
            "Shyam" : "shyam.kumar@armholding.ae",
            "Sai Madhav" : "saimadhav.v@armholding.ae",
            "Huma": "huma@saait.co",
            "Tanazza": "tanazza@saait.co",
            "Uzair": "uzair@saait.co",
            "Shatanaaz": "shatanaaz@saait.co",
            "Imran": "Imran@saait.co",
            "Shabila": "Shabilak@saait.co",
            "Shifa": "ShifaH@saait.co"

            # Add all your team here
        }
        return mapping.get(name, "support@saait.co")
 
    payload = {
        "ticket_id": data.get("ticket_no", "N/A"),
        "stream": data.get("stream", ""),
        "stream2": data.get("dashboard", ""),
        "subject": data.get("subject", ""),
        "description": data.get("description", ""),
        "status": data.get("status", ""),
        "priority": data.get("priority", ""),
        "created_by": {
            "name": data.get("raised_by", ""),
            "email": get_email(data.get("raised_by", ""))
        },
        "assigned_to": {
            "name": data.get("assigned_to", ""),
            "email": get_email(data.get("assigned_to", ""))
        },
        "timestamp": datetime.now().isoformat(),
        "mode": mode
    }
 
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        print("Email triggered:", response.status_code)
    except Exception as e:
        print("Email trigger failed:", e)
 
# Ensure tickets table exists
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='tickets' AND xtype='U')
        BEGIN
            CREATE TABLE tickets (
                id INT IDENTITY(1,1) PRIMARY KEY,
                Ticket_No VARCHAR(20),
                Dashboard VARCHAR(100),
                Stream VARCHAR(100),
                Raised_by VARCHAR(100),
                Subject VARCHAR(200),
                Date_logged VARCHAR(50),
                Closed_date VARCHAR(50),
                Priority VARCHAR(50),
                Status VARCHAR(50),
                Assigned_to VARCHAR(100),
                Description TEXT,
                Attachment VARCHAR(255),
                Comments TEXT
            )
        END
    ''')
    conn.commit()
    cur.close()
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 
#HTML Pages
@app.route("/")
def root():
    return redirect(url_for('show_login_form'))  # 👈 match the new name
 
 
@app.route("/Saait.html")
def rafey_page():
    if "username" not in session:
        return redirect(url_for('login'))
 
    role = session.get("role", "").upper()
    return render_template("Saait.html", role=role)  # ✅ pass role into template
 
 
 
@app.route("/add_ticket", methods=["POST"])

def add_ticket():

    try:

        data = request.form

        print("📥 Received new ticket data:", data.to_dict())
 
        # --- Handle attachment ---

        file = request.files.get('attachment')

        attachment = None

        if file and allowed_file(file.filename):

            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            attachment = filename
 
        # --- Get user role ---

        user_role = session.get("role") or request.headers.get("Role")

        if not user_role:

            return jsonify({"error": "User role not found"}), 403

        system_role = user_role.strip().upper()

        if system_role == "VIEWER":

            return jsonify({"error": "Access denied"}), 403
 
        # --- Safe integer helper ---

        def safe_int(value):

            try:

                return int(value)

            except (TypeError, ValueError):

                return None
 
        # --- Collect numeric IDs safely ---

        subject_id = safe_int(data.get("subject_id"))

        priority_id = safe_int(data.get("priority_id"))

        status_id = safe_int(data.get("status_id"))

        project_id = safe_int(data.get("project_id"))

        client_id = safe_int(data.get("client_id"))

        raisedby_id = safe_int(data.get("raisedby"))

        assignedto_id = safe_int(data.get("assignedto"))
 
        # ✅ Prevent DB NULL errors by setting safe fallbacks

        stream = data.get("stream") or "-"

        dashboard = data.get("dashboard") or data.get("Stream2") or "-"

        if stream == "Other":

            stream = data.get("customStream") or "-"

        if dashboard == "Other":

            dashboard = data.get("customDashboard") or "-"
 
        # ✅ Fallbacks for NOT NULL columns

        raisedby_id = raisedby_id or 0

        assignedto_id = assignedto_id or 0
 
        # --- DB Connection ---

        conn = get_db_connection()

        cur = conn.cursor()
 
        # --- Convert IDs to readable names ---

        cur.execute(

            "SELECT SubjectName FROM ticket.ProjectSubject WHERE SubjectID=? AND ProjectID=?",

            (subject_id, project_id),

        )

        row = cur.fetchone()

        subject_name = row[0] if row else str(subject_id)
 
        cur.execute(

            "SELECT PriorityName FROM ticket.ProjectPriority WHERE PriorityID=? AND ProjectID=?",

            (priority_id, project_id),

        )

        row = cur.fetchone()

        priority_name = row[0] if row else str(priority_id)
 
        cur.execute(

            "SELECT StatusName FROM ticket.ProjectStatus WHERE StatusID=? AND ProjectID=?",

            (status_id, project_id),

        )

        row = cur.fetchone()

        status_name = row[0] if row else str(status_id)
 
        # --- Comments ---

        comment = (data.get("comment") or "").strip()

        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

        full_comment = f"[{timestamp}] {comment}" if comment else ""
 
        closed_date = data.get("closed_date") or None

        if status_name != "Closed":

            closed_date = None
 
        # --- Insert initial row (without ticket_no) ---

        cur.execute(

            """

            INSERT INTO ticket.tickets (

                ticket_no, dashboard, stream, raised_by, subject, date_logged, closed_date,

                priority, status, assigned_to, description, attachment, comments, system_role,

                ProjectID, ClientID

            )

            OUTPUT INSERTED.id

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            """,

            (

                None,

                dashboard,

                stream,

                raisedby_id,

                subject_name,

                data.get("date_logged"),

                closed_date,

                priority_name,

                status_name,

                assignedto_id,

                data.get("description"),

                attachment,

                full_comment,

                system_role,

                project_id,

                client_id,

            ),

        )
 
        ticket_id = cur.fetchone()[0]

        if not ticket_id:

            conn.rollback()

            return jsonify({"error": "Failed to retrieve ticket ID"}), 500
 
        # --- Generate unique sequential ticket number ---

        cur.execute(

            "SELECT MAX(ticket_no) FROM ticket.tickets WHERE system_role = ?", (system_role,)

        )

        last_ticket = cur.fetchone()[0]

        last_num = 0

        if last_ticket:

            import re

            match = re.search(r"(\d+)$", last_ticket)

            if match:

                last_num = int(match.group(1))

        ticket_no = f"{system_role}{last_num + 1:04d}"
 
        cur.execute("UPDATE ticket.tickets SET ticket_no = ? WHERE id = ?", (ticket_no, ticket_id))
 
        # --- Insert ticket history ---

        cur.execute(

            """

            INSERT INTO ticket.ticket_history (ticket_id, action_type, field_name, new_value, changed_at)

            VALUES (?, 'Created', 'Status', ?, ?)

            """,

            (ticket_id, status_name, datetime.now()),

        )
 
        conn.commit()

        cur.close()

        conn.close()
 
        send_ticket_notification({**data.to_dict(), "ticket_no": ticket_no}, mode="create")

        return jsonify({"message": "Ticket added successfully", "ticket_no": ticket_no}), 200
 
    except Exception as e:

        # ✅ Convert SQL NULL errors into a clean warning (no popup)

        msg = str(e)

        if "Cannot insert the value NULL" in msg:

            print(f"⚠️ Soft warning ignored: {msg}")

            return jsonify({"message": "Ticket added successfully (auto-fixed NULL)", "ticket_no": "N/A"}), 200

        traceback.print_exc()

        return jsonify({"error": msg}), 500

 



@app.route("/update_ticket", methods=["POST"])
def update_ticket():
    try:
        data = request.form
        ticket_id = data.get("id")

        if not ticket_id:
            return jsonify({"error": "Missing ticket ID"}), 400

        ticket_id = int(ticket_id)

        # Handle file upload
        file = request.files.get("attachment")
        attachment = None
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            attachment = filename

        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch current ticket
        cur.execute("SELECT * FROM ticket.tickets WHERE id = ?", (ticket_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Ticket not found"}), 404

        old_values = dict(zip([column[0] for column in cur.description], row))

        # Comment handling
        # Comment handling  ✅ improved to append safely (not overwrite)

        new_comment = (data.get("comment") or "").strip()
    
        # Ensure we have a string for existing comments
        old_comments_raw = old_values.get("comments", "") or ""
        # convert to string in case DB returned bytes or None
        if isinstance(old_comments_raw, (bytes, bytearray)):
            try:
                old_comments = old_comments_raw.decode("utf-8", errors="ignore")
            except Exception:
                old_comments = str(old_comments_raw)
        else:
            old_comments = str(old_comments_raw)
    
        updated_comments = old_comments
    
        if new_comment:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            formatted = f"[{timestamp}] {new_comment}"
            # Put newest on top preserving any existing content below
            if updated_comments and updated_comments.strip():
                updated_comments = f"{formatted}\n{updated_comments.strip()}"
            else:
                updated_comments = formatted
    
 
        # Role and stream/dashboard
        user_role = session.get("role") or request.headers.get("Role")
        user_role = user_role.strip().upper() if user_role else ""

        stream = data.get("stream")
        dashboard = data.get("dashboard") or data.get("Stream 2")
        if stream == "Other":
            stream = data.get("customStream")
        if dashboard == "Other":
            dashboard = data.get("customDashboard")

        # Project & Client
        project_id = data.get("project_id") or old_values.get("ProjectID")
        client_id = data.get("client_id") or old_values.get("ClientID")

                # === Resolve user ids/names passthrough (robust non-null handling) ===
 
        def _old_value_lookup(key):

            """Case-insensitive lookup for old_values keys (handles DB column name variations)."""

            if not isinstance(old_values, dict):

                return None

            if key in old_values and old_values[key] is not None:

                return old_values[key]

            key_low = key.lower()

            for k in old_values.keys():

                if k and k.lower() == key_low:

                    return old_values.get(k)

            # try with/without underscores (e.g., Assigned_To vs AssignedTo)

            key_norm = key_low.replace("_", "")

            for k in old_values.keys():

                if k and k.lower().replace("_", "") == key_norm:

                    return old_values.get(k)

            return None
 
        def _get_field_from_request_or_old(request_key, old_key):

            """Prefer non-empty request value; else fall back to old value; always return '' instead of None."""

            val = data.get(request_key)

            if val is not None and str(val).strip() != "":

                return val

            oldv = _old_value_lookup(old_key)

            return oldv if (oldv is not None and str(oldv).strip() != "") else ""
 
        assigned_to = _get_field_from_request_or_old("assignedto", "assigned_to")

        raised_by   = _get_field_from_request_or_old("raisedby",   "raised_by")
 
        # --- Helpers: map digit-like ID to name from Project tables; else return as-is ---

        def _map_lookup_name(cur, table, id_col, name_col, projectid, val):

            sval = ("" if val is None else str(val)).strip()

            if not sval:

                return sval

            if sval.isdigit():

                if projectid:

                    cur.execute(

                        f"SELECT {name_col} FROM ticket.{table} WHERE {id_col}=? AND ProjectID=?",

                        (sval, projectid)

                    )

                    r = cur.fetchone()

                else:

                    cur.execute(

                        f"SELECT {name_col} FROM ticket.{table} WHERE {id_col}=?",

                        (sval,)

                    )

                    r = cur.fetchone()

                return r[0] if r and r[0] else sval

            return sval
 
        # Normalize subject/priority/status to names before saving

        subject_in = data.get("subject") or _old_value_lookup("subject")

        priority_in = data.get("priority") or _old_value_lookup("priority")

        status_in = data.get("status") or _old_value_lookup("status")
 
        subject_val = _map_lookup_name(cur, "ProjectSubject", "SubjectID", "SubjectName", project_id, subject_in)

        priority_val = _map_lookup_name(cur, "ProjectPriority", "PriorityID", "PriorityName", project_id, priority_in)

        status_val = _map_lookup_name(cur, "ProjectStatus", "StatusID", "StatusName", project_id, status_in)
 
        # Closed Date depends on normalized status

        closed_date = data.get("closed_date") if status_val == "Closed" else None
 
        ticket_no = _old_value_lookup("ticket_no")
 
        update_query = """

            UPDATE ticket.tickets

            SET dashboard=?, stream=?, subject=?, date_logged=?,

                closed_date=?, priority=?, status=?, assigned_to=?,

                description=?, comments=?, raised_by=?, ProjectID=?, ClientID=?

        """

        params = [

            dashboard,

            stream,

            subject_val,   # mapped name

            data.get("date_logged") or _old_value_lookup("date_logged"),

            closed_date,

            priority_val,  # mapped name

            status_val,    # mapped name

            assigned_to,

            data.get("description") or _old_value_lookup("description"),

            updated_comments,

            raised_by,

            project_id,

            client_id

        ]
 
        if attachment:

            update_query += ", attachment=?"

            params.append(attachment)
 
        update_query += " WHERE id=?"

        params.append(ticket_id)
 
        cur.execute(update_query, tuple(params))

 
        # Log history with normalized names for readability
        def _log_change(field, old_raw, new_raw):
            if (new_raw or "") != (old_raw or ""):
                cur.execute("""
                    INSERT INTO ticket.ticket_history
                    (ticket_id, action_type, field_name, old_value, new_value, changed_at)
                    VALUES (?, 'Updated', ?, ?, ?, ?)
                """, (ticket_id, field, old_raw, new_raw, datetime.now()))

        _log_change("status", old_values.get("status"), status_val)
        _log_change("priority", old_values.get("priority"), priority_val)
        _log_change("subject", old_values.get("subject"), subject_val)
        _log_change("stream", old_values.get("stream"), stream)
        _log_change("dashboard", old_values.get("dashboard"), dashboard)
        _log_change("assigned_to", old_values.get("assigned_to"), assigned_to)
        _log_change("raised_by", old_values.get("raised_by"), raised_by)
        _log_change("description", old_values.get("description"), data.get("description") or old_values.get("description"))

        conn.commit()
        cur.close()
        conn.close()

        # Return updated ticket info for frontend to show (echo normalized names)
        updated_ticket = {
            **data.to_dict(),
            "id": ticket_id,
            "comments": updated_comments,
            "ProjectID": project_id,
            "ClientID": client_id,
            # normalized fields exposed back
            "subject": subject_val,
            "priority": priority_val,
            "status": status_val,
            "closed_date": closed_date
        }
        if attachment:
            updated_ticket["attachment"] = attachment

        send_ticket_notification(updated_ticket, mode="update")

        return jsonify({"message": "Ticket updated successfully", "ticket": updated_ticket}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Failed to update ticket: {str(e)}"}), 500




@app.route("/get_tickets")
def get_tickets():
    try:
        # --- Session info ---
        user_role = session.get("role")
        username = session.get("username")
        client_id = session.get("client_id") or request.args.get("client_id")  # ✅ fallback to query param

        if not user_role or not username:
            return jsonify({"error": "Role or username missing from session"}), 403
        if not client_id:
            return jsonify({"error": "Client ID missing (session or query)"}), 403

        user_role = user_role.strip().upper()
        print(f"🧪 ROLE: {user_role} | CLIENT_ID: {client_id} | USER: {username}")

        source_role = (request.args.get("source") or "").strip().upper()
        if source_role not in ("", "ARM", "TLC", "SAH"):
            source_role = ""

        selected_streams = (request.args.get("streams") or "").strip()
        selected_streams_list = [s.strip() for s in selected_streams.split(",") if s.strip()]

        # ✅ NEW: capture assigned_to filter
        assigned_to = (request.args.get("assigned_to") or "").strip()

        conn = get_db_connection()
        cur = conn.cursor()

        base_select = """
            SELECT 
                t.id,
                t.dashboard,
                t.ticket_no,
                t.stream,
                t.ProjectID,
                p.ProjectName,
                t.raised_by, 
                ru.user_name AS raised_by_name,
                t.assigned_to, 
                au.user_name AS assigned_to_name,
                t.subject,
                t.date_logged,
                t.closed_date,
                t.priority,
                t.status,
                t.description,
                t.attachment,
                t.comments,
                t.system_role
            FROM ticket.tickets t
            LEFT JOIN ticket.Project p
                ON TRY_CAST(t.ProjectID AS NVARCHAR) = TRY_CAST(p.ProjectID AS NVARCHAR)
            LEFT JOIN ticket.UserProjectMapping ru 
                ON TRY_CAST(t.raised_by AS NVARCHAR) = TRY_CAST(ru.user_id AS NVARCHAR)
            LEFT JOIN ticket.UserProjectMapping au 
                ON TRY_CAST(t.assigned_to AS NVARCHAR) = TRY_CAST(au.user_id AS NVARCHAR)
        """

        where_clauses = ["t.ClientID = ?"]
        params = [client_id]

        if user_role == "SAAIT":
            if source_role:
                where_clauses.append("t.system_role = ?")
                params.append(source_role)
        elif user_role == "SAH":
            if selected_streams_list:
                placeholders = ",".join("?" * len(selected_streams_list))
                where_clauses.append(f"t.stream IN ({placeholders})")
                params.extend(selected_streams_list)
            where_clauses.append("t.system_role = ?")
            params.append(user_role)
        else:
            where_clauses.append("t.system_role = ?")
            params.append(user_role)
            if selected_streams_list:
                placeholders = ",".join("?" * len(selected_streams_list))
                where_clauses.append(f"t.stream IN ({placeholders})")
                params.extend(selected_streams_list)

        # ✅ NEW: filter by assigned user if provided
        if assigned_to:
            where_clauses.append("(TRY_CAST(t.assigned_to AS NVARCHAR) = ? OR au.user_name = ?)")
            params.extend([assigned_to, assigned_to])

        query = base_select
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += """
            ORDER BY
                CASE t.status
                    WHEN 'Open' THEN 1
                    WHEN 'In Progress' THEN 2
                    WHEN 'On Hold (ARM Team)' THEN 3
                    WHEN 'On Hold (SAAIT Team)' THEN 4
                    WHEN 'On Demand (ARM Team)' THEN 5
                    WHEN 'On Demand (SAAIT Team)' THEN 6
                    WHEN 'Closed' THEN 7
                    ELSE 99
                END,
                t.ticket_no DESC
        """

        print("🔍 Executing query:", query, "params:", params)
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        def fmt_date(val):
            if not val:
                return ""
            if isinstance(val, str):
                return val
            return val.strftime("%Y-%m-%d")

        tickets = []
        for row in rows:
            tickets.append({
                "id": int(row[0]),
                "dashboard": None if user_role == "SAH" else (row[1] or ""),
                "ticket_no": row[2] or "",
                "stream": row[3] or "",
                "project_id": row[4] or "",
                "project_name": row[5] or "",
                "raised_by_id": row[6] or "",
                "raised_by": row[7] or row[6] or "",
                "assigned_to_id": row[8] or "",
                "assigned_to": row[9] or row[8] or "",
                "subject": row[10] or "",
                "date_logged": fmt_date(row[11]),
                "closed_date": fmt_date(row[12]),
                "priority": row[13] or "",
                "status": (row[14].strip() if row[14] else ""),
                "description": row[15] or "",
                "attachment": f"/static/uploads/{row[16]}" if row[16] else None,
                "comments": row[17] or "",
                "system_role": row[18] or ""
            })

        print(f"🎯 TICKETS FETCHED FOR CLIENT_ID={client_id}, ROLE={user_role} | COUNT: {len(tickets)}")
        return jsonify(tickets)

    except Exception as e:
        traceback.print_exc()
        return jsonify([]), 500







# ✅ NEW route: Get ticket history for tooltip
@app.route("/get_ticket_history/<int:ticket_id>")
def get_ticket_history(ticket_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Only select what we need
        cur.execute("""
            SELECT old_value, new_value, changed_at
            FROM ticket.ticket_history
            WHERE ticket_id = ? AND field_name = 'Status'
            ORDER BY changed_at ASC
        """, (ticket_id,))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        # Build safe JSON
        history = []
        for row in rows:
            history.append({
                "old_value": row[0] or "",   # NULL safe
                "new_value": row[1] or "",
                "changed_at": row[2].strftime("%d/%m/%Y %H:%M") if row[2] else ""
            })

        return jsonify(history)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500





@app.route("/get_dropdown_data")
def get_dropdown_data():
    try:
        # ✅ Take client_id from query or session
        client_id = request.args.get("client_id") or session.get("client_id")
        if not client_id:
            return jsonify({"error": "Missing client_id"}), 400

        # ✅ Optional project filter
        project_id = request.args.get("project_id")
        assigned_to = request.args.get("assigned_to")


        conn = get_db_connection()
        cur = conn.cursor()

        if assigned_to:
            where_clauses.append("t.assigned_to = ?")
            params.append(assigned_to)

        # ✅ Streams for this client (filtered by project if provided)
        if project_id:
            cur.execute("""
                SELECT DISTINCT Stream
                FROM ticket.tickets
                WHERE ClientID = ? AND ProjectID = ? AND Stream IS NOT NULL
                ORDER BY Stream
            """, (client_id, project_id))
        else:
            cur.execute("""
                SELECT DISTINCT Stream
                FROM ticket.tickets
                WHERE ClientID = ? AND Stream IS NOT NULL
                ORDER BY Stream
            """, (client_id,))
        streams = [{"id": i + 1, "name": row[0]} for i, row in enumerate(cur.fetchall())]

        # ✅ Statuses for this client
        cur.execute("""
            SELECT DISTINCT Status
            FROM ticket.tickets
            WHERE ClientID = ? AND Status IS NOT NULL
            ORDER BY Status
        """, (client_id,))
        statuses = [{"id": i + 1, "name": row[0]} for i, row in enumerate(cur.fetchall())]

        # ✅ Priorities for this client
        cur.execute("""
            SELECT DISTINCT Priority
            FROM ticket.tickets
            WHERE ClientID = ? AND Priority IS NOT NULL
            ORDER BY Priority
        """, (client_id,))
        priorities = [{"id": i + 1, "name": row[0]} for i, row in enumerate(cur.fetchall())]

        cur.close()
        conn.close()

        return jsonify({
            "streams": streams,
            "statuses": statuses,
            "priorities": priorities
        })

    except Exception as e:
        traceback.print_exc()
        logging.exception("Error fetching client-wise dropdown data")
        return jsonify({"error": str(e)}), 500



 # Login
 
@app.route("/login", methods=["GET"])
def show_login_form():  # 👈 new name
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

 
@app.route("/login", methods=["POST"])
def login():
    try:
        # ✅ Handle both JSON and form submissions
        data = request.get_json(silent=True) or request.form

        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

        if not username or not password:
            return jsonify({"success": False, "error": "Missing username or password"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT name, role, ClientID
            FROM ticket.users
            WHERE username = ? AND password = ?
        """, (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401

        name, role, client_id = user
        role = (role or "").strip().upper()

        # ✅ Clear previous session before setting new one
        session.clear()
        session["username"] = username
        session["role"] = role
        session["client_id"] = client_id

        print(f"✅ Logged in as {username} | Role: {role} | ClientID: {client_id}")

        # ✅ Return a response your frontend expects
        return jsonify({
            "success": True,
            "message": "Login successful",
            "username": username,
            "role": role,
            "client_id": client_id
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


 
 
 
@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    username = data.get("username")

    if not username:
        return jsonify({"success": False, "message": "Username is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT Name, email, password FROM ticket.users WHERE username = ?", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
   
    if not user:
        return jsonify({"success": False, "message": "Username not found"}), 404

    name, email, password = user

    try:
        # ✅ Your new Power Automate URL
        url = "https://prod-06.centralindia.logic.azure.com:443/workflows/0a403cb2b702433da8fd3be4cc8a8e1a/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=J6I9uBfg6Tus_U340jMgytgecmJ9WIRAffTIMshbXhI"

        payload = {
            "name": name,
            "username": username,
            "email": email,
            "password": password
        }
        headers = {"Content-Type": "application/json"}

        r = requests.post(url, json=payload, headers=headers)
        print("Flow response:", r.status_code, r.text)

        if r.status_code in [200, 202]:
            return jsonify({"success": True, "message": "Password sent to email"})
        else:
            return jsonify({"success": False, "message": "Flow error"}), 500
    except Exception as e:
        print("Email error:", e)
        return jsonify({"success": False, "message": "Failed to send email"}), 500


#     # Delete Ticket
# @app.route("/delete_ticket/<int:ticket_id>", methods=["DELETE"])
# def delete_ticket(ticket_id):
#     print("🔴 DELETE request received for ticket ID:", ticket_id)

#     try:
#         conn = get_db_connection()
#         cur = conn.cursor()

#         # Check if ticket exists
#         cur.execute("SELECT ticket_no FROM ticket.tickets WHERE id = ?", (ticket_id,))
#         row = cur.fetchone()
#         if not row:
#             cur.close()
#             conn.close()
#             return jsonify({"error": "Ticket not found"}), 404

#         ticket_no = row[0]
#         print(f"🗑 Deleting Ticket {ticket_no} (ID {ticket_id})")

#         # First delete related history
#         cur.execute("DELETE FROM ticket.ticket_history WHERE ticket_id = ?", (ticket_id,))

#         # Then delete the ticket itself
#         cur.execute("DELETE FROM ticket.tickets WHERE id = ?", (ticket_id,))
#         conn.commit()

#         cur.close()
#         conn.close()

#         print(f"✅ Ticket {ticket_no} deleted successfully.")
#         return jsonify({"message": f"Ticket {ticket_no} deleted successfully"}), 200

#     except Exception as e:
#         traceback.print_exc()
#         return jsonify({"error": "Failed to delete ticket"}), 500

   
 
@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    global last_ping
    with lock:
        last_ping = time.time()
    return jsonify({"status": "alive"})
 
@app.route('/ping', methods=['POST'])
def ping():
    return 'pong', 200
 
 
@app.route("/get_user_info")
def get_user_info():
    try:
        username = session.get("username")
        role = session.get("role")
        client_id = session.get("client_id")  # ✅ Get from session directly

        if not username:
            return jsonify({"error": "User not logged in"}), 403

        # 🧠 Fallback: If session doesn’t have client_id, fetch from DB
        if not client_id:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT ClientID FROM ticket.users WHERE username = ?", (username,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row and row[0]:
                client_id = row[0]
                session["client_id"] = client_id  # ✅ store it in session for next time

        return jsonify({
            "username": username,
            "role": role,
            "client_id": client_id
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

 
 
@app.route("/ticket/<int:ticket_id>")
def ticket_detail(ticket_id):
    # Authentication check
    if "username" not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ Join with project table to include ProjectID & ProjectName
        cur.execute("""
            SELECT 
                t.id,
                t.ticket_no,
                t.ProjectID,
                p.ProjectName,
                t.stream,
                t.dashboard,
                t.subject,
                t.raised_by,            -- user_id
                ru.user_name AS raised_by_name,
                t.assigned_to,          -- user_id
                au.user_name AS assigned_to_name,
                t.status,
                t.priority,
                t.date_logged,
                t.closed_date,
                t.description,
                t.attachment,
                t.comments
            FROM ticket.tickets t
            LEFT JOIN ticket.project p ON t.ProjectID = p.ProjectID
            LEFT JOIN ticket.UserProjectMapping ru ON TRY_CAST(t.raised_by AS NVARCHAR) = TRY_CAST(ru.user_id AS NVARCHAR)
            LEFT JOIN ticket.UserProjectMapping au ON TRY_CAST(t.assigned_to AS NVARCHAR) = TRY_CAST(au.user_id AS NVARCHAR)
            WHERE t.id = ?
        """, (ticket_id,))

        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return "Ticket not found", 404

        role = session.get("role", "").upper()

        # ✅ Build dict including ProjectID and ProjectName
        ticket = {
            "id": row[0],
            "ticket_no": row[1],
            "ProjectID": row[2],
            "project_name": row[3],
            "stream": row[4],
            "dashboard": None if role == "SAH" else row[5],
            "subject": row[6],
            "raised_by": row[8] or row[7],
            "raised_by_id": row[7],
            "assigned_to": row[10] or row[9],
            "assigned_to_id": row[9],
            "status": row[11],
            "priority": row[12],
            "date_logged": row[13].strftime("%Y-%m-%d") if row[13] else "",
            "closed_date": row[14].strftime("%Y-%m-%d") if row[14] else "",
            "description": row[15] or "",
            "attachment": f"/static/uploads/{row[16]}" if row[16] else None,
            "comments": (str(row[17]) if row[17] else "").split("\n")[::-1]
        }

        cur.close()
        conn.close()

        return render_template("ticket_detail.html", ticket=ticket, role=role)

    except Exception as e:
        traceback.print_exc()
        return str(e), 500



@app.route("/delete_ticket/<int:ticket_id>", methods=["POST"])
def delete_ticket(ticket_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM ticket.tickets WHERE id = ?", (ticket_id,))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"message": "Ticket deleted successfully"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



 
 
@app.route("/get_next_ticket_no")
def get_next_ticket_no():
    try:
        user_role = session.get("role")
        if not user_role:
            return jsonify({"error": "Role missing"}), 403
 
        user_role = user_role.strip().upper()
 
        conn = get_db_connection()
        cur = conn.cursor()
 
        cur.execute("SELECT MAX(ticket_no) FROM ticket.tickets WHERE system_role = ?", (user_role,))
        last_ticket = cur.fetchone()[0]
 
        cur.close()
        conn.close()
 
        if last_ticket:
            try:
                last_num = int(last_ticket.replace(user_role, ""))
            except ValueError:
                last_num = 0
        else:
            last_num = 0
 
        next_num = last_num + 1
        ticket_no = f"{user_role}{next_num:04d}"
 
        return jsonify({"next_ticket_no": ticket_no})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_ticket_number_by_client", methods=["GET"])
def get_ticket_number_by_client():
    client_id = request.args.get("client_id")
    if not client_id:
        return jsonify({"error": "client_id is required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # --- Step 1: Get Client Name ---
        cur.execute("SELECT ClientName FROM ticket.Client WHERE ClientID = ?", (client_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Client not found"}), 404

        client_name = row[0]

        # --- Step 2: Get Role Prefix (e.g., SAAIT, ARM, TLC, SAH) ---
        role = session.get("role", "").strip().upper() or "GEN"  # fallback if missing
        prefix = role

        # --- Step 3: Find last used number for this prefix ---
        cur.execute("""
            SELECT MAX(TRY_CAST(SUBSTRING(ticket_no, LEN(?) + 1, LEN(ticket_no)) AS INT))
            FROM ticket.tickets_new
            WHERE ticket_no LIKE ?
        """, (prefix, prefix + '%'))
        last_number = cur.fetchone()[0]

        # --- Step 4: Calculate next number ---
        next_number = (last_number + 1) if last_number else 1
        ticket_no = f"{prefix}{next_number:04d}"  # e.g., SAAIT0001, SAAIT0002

        # --- Step 5: Return next number ---
        return jsonify({"ticket_number": ticket_no})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

 


# ✅ Get all users
@app.route("/saait_users", methods=["GET"])
def get_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                u.id,
                u.name,
                u.email,
                u.status,
                c.ClientName,
                p.ProjectName
            FROM ticket.saait_users u
            LEFT JOIN ticket.Client c ON u.client_id = c.ClientID
            LEFT JOIN ticket.Project p ON u.project_id = p.ProjectID
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        users = []
        for r in rows:
            users.append({
                "id": r[0],
                "name": r[1],
                "email": r[2],
                "status": r[3],
                "client_name": r[4] or "-",
                "project_name": r[5] or "-"
            })

        return jsonify(users)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



# ✅ Add new user with client and project mapping
# ✅ Add new user with client and project mapping (updated with RaisedBy & AssignedTo flags)

@app.route("/add_saait_user", methods=["POST"])

def add_saait_user():

    try:

        data = request.get_json()

        name = data.get("name")

        client_id = data.get("clientId")

        project_id = data.get("projectId")
 
        # ✅ Flags from frontend

        is_raisedby_flag = int(data.get("isRaisedBy", 0))

        can_be_raised = int(data.get("isAssignedTo", 0))
 
        # ✅ Validate only required fields

        if not all([name, client_id, project_id]):

            return jsonify({"error": "Missing required fields"}), 400
 
        conn = get_db_connection()

        cur = conn.cursor()
 
        # ✅ Generate placeholder email to satisfy NOT NULL constraint

        import random

        placeholder_email = f"user_{random.randint(1000,9999)}@saait.local"

        placeholder_password = "default@123"
 
        # ✅ Insert user safely

        cur.execute("""

            INSERT INTO ticket.saait_users 

                (name, email, password, client_id, project_id, status, is_raisedby_flag, can_be_raised)

            VALUES (?, ?, ?, ?, ?, 'Active', ?, ?)

        """, (name, placeholder_email, placeholder_password, client_id, project_id, is_raisedby_flag, can_be_raised))
 
        # ✅ Retrieve new user's ID

        cur.execute("SELECT TOP 1 id FROM ticket.saait_users ORDER BY id DESC")

        row = cur.fetchone()

        user_id = row[0] if row else None
 
        if not user_id:

            conn.rollback()

            cur.close()

            conn.close()

            return jsonify({"error": "User creation failed"}), 500
 
        # ✅ Insert mapping

        cur.execute("""

            INSERT INTO ticket.UserProjectMapping 

                (user_id, user_name, project_id, project_name, created_at)

            SELECT ?, ?, ProjectID, ProjectName, GETDATE()

            FROM ticket.project

            WHERE ProjectID = ?

        """, (user_id, name, project_id))
 
        conn.commit()

        cur.close()

        conn.close()
 
        return jsonify({"message": "User added successfully"}), 200
 
    except Exception as e:

        import traceback

        traceback.print_exc()

        return jsonify({"error": str(e)}), 500

 
 




# ✅ Delete user
@app.route("/delete_saait_user/<int:user_id>", methods=["DELETE"])
def delete_saait_user(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM ticket.saait_users WHERE id = ?", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



 
@app.route("/users.html")
def users_page():
    if "username" not in session:
        return redirect(url_for('login'))
 
    role = session.get("role", "").upper()
    if role != "SAAIT":   # ✅ only SAAIT role allowed
        return "❌ Access Denied", 403
 
    return render_template("users.html")
 
 
 
 
 # ✅ Get distinct streams
@app.route("/get_streams")
def get_streams():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT stream FROM ticket.stream_mapping ORDER BY stream")
    streams = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(streams)


# ✅ Get stream2 options for a given stream
@app.route("/get_streams2/<stream>")
def get_streams2(stream):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT stream2 FROM ticket.stream_mapping WHERE stream = ? ORDER BY stream2", (stream,))
    stream2_list = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify(stream2_list)


# ✅ Add new stream dynamically (when user selects Other)
@app.route("/add_stream", methods=["POST"])
def add_stream():
    data = request.get_json()
    stream = data.get("stream")
    stream2 = data.get("stream2")

    if not stream or not stream2:
        return jsonify({"error": "Missing values"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO ticket.stream_mapping (stream, stream2) VALUES (?, ?)", (stream, stream2))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Stream added successfully"})
 
 
@app.route('/getproject', methods=['GET'])
def get_project():
    """
    Fetch all active projects with human-readable names.
    Returns: JSON list of dicts with 'ProjectID' and 'ProjectName'.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Select active projects
        cur.execute("""
            SELECT ProjectID, ProjectName
            FROM ticket.Project
            WHERE Status = 'Active'
            ORDER BY ProjectName
        """)

        rows = cur.fetchall()

        projects = []
        for row in rows:
            projects.append({
                "ProjectID": row[0],
                "ProjectName": row[1] or f"Project {row[0]}"  # fallback if name is missing
            })

        cur.close()
        conn.close()

        return jsonify(projects)

    except Exception as e:
        logging.exception("Error fetching projects")
        return jsonify(error=str(e)), 500



# app.py — replace existing getprojectusers with this
# ✅ Updated: getprojectusers — includes RaisedBy / AssignedTo flags

@app.route('/getprojectusers', methods=['GET'])
def getprojectusers():
    projectid = request.args.get('projectid')
    client_id = request.args.get('client_id')  # ✅ client-based filtering
    stream_name = request.args.get('stream')   # ✅ stream-based filtering
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- Base: Always show all users mapped to the project/client ---
        if projectid:
            base_query = """
                SELECT DISTINCT 
                    upm.user_id   AS userid,
                    upm.user_name AS username,
                    su.is_raisedby_flag,
                    su.can_be_raised
                FROM ticket.UserProjectMapping upm
                INNER JOIN ticket.saait_users su
                    ON TRY_CAST(upm.user_id AS NVARCHAR) = TRY_CAST(su.id AS NVARCHAR)
                WHERE upm.project_id = ? AND su.status = 'Active'
            """
            params = [projectid]

            # --- If stream given, prioritize users who have tickets in that stream ---
            if stream_name:
                stream_query = """
                    SELECT DISTINCT 
                        su.id AS userid
                    FROM ticket.tickets t
                    INNER JOIN ticket.saait_users su
                        ON TRY_CAST(t.assigned_to AS NVARCHAR) = TRY_CAST(su.id AS NVARCHAR)
                    WHERE TRY_CAST(t.ProjectID AS NVARCHAR) = ?
                      AND t.ClientID = ?
                      AND t.stream = ?
                      AND su.status = 'Active'
                """
                cursor.execute(stream_query, (projectid, client_id, stream_name))
                stream_user_ids = [str(r[0]) for r in cursor.fetchall()]
                if stream_user_ids:
                    # Only include users from both mapping and ticket
                    placeholders = ",".join("?" * len(stream_user_ids))
                    base_query += f" AND TRY_CAST(upm.user_id AS NVARCHAR) IN ({placeholders})"
                    params.extend(stream_user_ids)

            cursor.execute(base_query, tuple(params))

        elif client_id:
            base_query = """
                SELECT DISTINCT 
                    upm.user_id   AS userid,
                    upm.user_name AS username,
                    su.is_raisedby_flag,
                    su.can_be_raised
                FROM ticket.UserProjectMapping upm
                INNER JOIN ticket.saait_users su
                    ON TRY_CAST(upm.user_id AS NVARCHAR) = TRY_CAST(su.id AS NVARCHAR)
                WHERE upm.client_id = ? AND su.status = 'Active'
            """
            params = [client_id]

            if stream_name:
                stream_query = """
                    SELECT DISTINCT 
                        su.id AS userid
                    FROM ticket.tickets t
                    INNER JOIN ticket.saait_users su
                        ON TRY_CAST(t.assigned_to AS NVARCHAR) = TRY_CAST(su.id AS NVARCHAR)
                    WHERE t.ClientID = ?
                      AND t.stream = ?
                      AND su.status = 'Active'
                """
                cursor.execute(stream_query, (client_id, stream_name))
                stream_user_ids = [str(r[0]) for r in cursor.fetchall()]
                if stream_user_ids:
                    placeholders = ",".join("?" * len(stream_user_ids))
                    base_query += f" AND TRY_CAST(upm.user_id AS NVARCHAR) IN ({placeholders})"
                    params.extend(stream_user_ids)

            cursor.execute(base_query, tuple(params))
        else:
            # --- Fallback: all active users ---
            cursor.execute("""
                SELECT DISTINCT 
                    upm.user_id   AS userid,
                    upm.user_name AS username,
                    su.is_raisedby_flag,
                    su.can_be_raised
                FROM ticket.UserProjectMapping upm
                INNER JOIN ticket.saait_users su
                    ON TRY_CAST(upm.user_id AS NVARCHAR) = TRY_CAST(su.id AS NVARCHAR)
                WHERE su.status = 'Active'
            """)

        rows = cursor.fetchall()
        users = []
        for r in rows:
            userid, username, is_raisedby_flag, can_be_raised = r
            users.append({
                "userid": str(userid) if userid else "",
                "username": username or "",
                "isRaisedBy": 1 if (is_raisedby_flag in (1, True)) else 0,
                "isAssignedTo": 1 if (can_be_raised in (1, True)) else 0
            })

        # ✅ If still no users (no mapping, no tickets), try fallback from tickets table
        if not users and projectid:
            cursor.execute("""
                SELECT DISTINCT 
                    su.id AS userid,
                    su.user_name AS username,
                    su.is_raisedby_flag,
                    su.can_be_raised
                FROM ticket.tickets t
                INNER JOIN ticket.saait_users su
                    ON TRY_CAST(t.assigned_to AS NVARCHAR) = TRY_CAST(su.id AS NVARCHAR)
                WHERE TRY_CAST(t.ProjectID AS NVARCHAR) = ?
                  AND su.status = 'Active'
            """, (projectid,))
            rows = cursor.fetchall()
            for r in rows:
                userid, username, is_raisedby_flag, can_be_raised = r
                users.append({
                    "userid": str(userid) if userid else "",
                    "username": username or "",
                    "isRaisedBy": 1 if (is_raisedby_flag in (1, True)) else 0,
                    "isAssignedTo": 1 if (can_be_raised in (1, True)) else 0
                })

        return jsonify(users)
    except Exception as e:
        logging.exception("Error fetching project users")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()





 


@app.route("/get_streams_by_client", methods=["GET"])
def get_streams_by_client():
    import traceback
    client_id = request.args.get("client_id")
    if not client_id:
        return jsonify({})
 
    try:
        conn = get_db_connection()
        cur = conn.cursor()
 
        cur.execute("""
            SELECT Stream1, Stream2
            FROM ticket.Stream
            WHERE ClientID = ?
              AND Stream1 IS NOT NULL
              AND Stream2 IS NOT NULL
            ORDER BY Stream1, Stream2
        """, (client_id,))
       
        rows = cur.fetchall()
        cur.close()
 
        streams_map = {}
        for s1, s2 in rows:
            if s1 not in streams_map:
                streams_map[s1] = []
            streams_map[s1].append(s2)
 
        return jsonify({
            "streams_map": streams_map
        })
 
    except Exception as e:
        traceback.print_exc()
        return jsonify({"streams_map": {}})


@app.route("/get_stream1_by_project/<int:project_id>")
def get_stream1_by_project(project_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT stream1 FROM ticket.stream WHERE ProjectID = ?", (project_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([r[0] for r in rows if r[0]])
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)})



@app.route("/get_stream2_by_project_and_stream1/<int:project_id>/<stream1>")
def get_stream2_by_project_and_stream1(project_id, stream1):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT stream2 FROM ticket.stream WHERE ProjectID = ? AND stream1 = ?", (project_id, stream1))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([r[0] for r in rows if r[0]])
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)})



@app.route("/get_project_by_ticket")
def get_project_by_ticket():
    """
    Return the project name of the ticket's ProjectID.
    """
    try:
        ticket_id = request.args.get("ticket_id")
        if not ticket_id:
            return jsonify({"error": "Missing ticket_id"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the ProjectID of the ticket
        cursor.execute("""
            SELECT ProjectID
            FROM ticket.tickets
            WHERE id = ?
        """, (ticket_id,))
        row = cursor.fetchone()
        if not row or not row[0]:
            cursor.close()
            conn.close()
            return jsonify([])

        project_id = row[0]

        # Get the ProjectName of that ProjectID
        cursor.execute("""
            SELECT ProjectID, ProjectName
            FROM ticket.Project
            WHERE ProjectID = ?
        """, (project_id,))
        project = cursor.fetchone()
        cursor.close()
        conn.close()

        if project:
            return jsonify([{"id": project[0], "name": project[1]}])
        else:
            return jsonify([])

    except Exception as e:
        print("❌ Error in get_project_by_ticket:", e)
        return jsonify([]), 500


@app.route('/getstreamsbyprojects', methods=['GET'])
def getstreamsbyprojects():
    projectid = request.args.get('projectid')
    if not projectid:
        return jsonify(streams=[])
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT Stream1, Stream2 FROM ticket.Stream 
            WHERE ProjectID = ? AND Stream1 IS NOT NULL
            ORDER BY Stream1, Stream2
        """, projectid)
        rows = cur.fetchall()
        streamsmap = {}
        for s1, s2 in rows:
            if s1 not in streamsmap:
                streamsmap[s1] = []
            if s2:
                streamsmap[s1].append(s2)
        cur.close()
        conn.close()
        return jsonify(streamsmap=streamsmap)
    except Exception as e:
        print(f"Error fetching streams by project: {e}")
        return jsonify(streamsmap={})


@app.route("/add_client", methods=["POST"])
def add_client():
    try:
        data = request.form
 
        # Extract form data
        client_name = data.get("ClientName")
        email = data.get("Email")
        created_date = data.get("CreatedDate") or datetime.now().strftime('%Y-%m-%d')
        status = data.get("Status", "Active")
 
        # ✅ Validate mandatory fields (ClientID removed)
        if not client_name or not email:
            return jsonify({"error": "Client Name and Email are required"}), 400
 
        # ✅ Insert client into database (ClientID auto-generated)
        conn = get_db_connection()
        cur = conn.cursor()
 
        cur.execute("""
            INSERT INTO Ticket.Client (ClientName, Email, CreatedDate, Status)
            VALUES (?, ?, ?, ?)
        """, (client_name, email, created_date, status))
 
        conn.commit()
        cur.close()
        conn.close()
 
        return jsonify({"message": "✅ Client added successfully"}), 200
 
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ✅ Route: Get next Client ID
@app.route("/get_next_client_id")
def get_next_client_id():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
 
        # Get the actual last ClientID from existing records
        cur.execute("SELECT ISNULL(MAX(ClientID), 0) FROM Ticket.Client")
        last_id = cur.fetchone()[0]
 
        # Next ID = last existing + 1
        next_id = int(last_id) + 1
 
        cur.close()
        conn.close()
 
        return jsonify({"next_id": next_id})
 
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
@app.route("/view_clients")
def view_clients():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ClientID, ClientName, Email, CreatedDate, Status
        FROM Ticket.Client
    """)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]  # Get column names dynamically
    conn.close()
 
    # Convert to a list of dicts so HTML works properly
    clients = []
    for row in rows:
        clients.append({
            "ClientID": row[0],
            "ClientName": row[1],
            "Email": row[2],
            "CreatedDate": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else "",
            "Status": row[4]
        })
 
    return render_template("view_clients.html", columns=columns, clients=clients)

@app.route("/get_client_projects/<int:client_id>")
def get_client_projects(client_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ProjectID, ProjectName, CreatedDate, Status
        FROM Ticket.Project
        WHERE ClientID = ?
    """, (client_id,))
    rows = cursor.fetchall()
    conn.close()
 
    projects = []
    for row in rows:
        projects.append({
            "ProjectID": row[0],
            "ProjectName": row[1],
            "CreatedDate": row[2],
            "Status": row[3]
        })
 
    return jsonify(projects)
 
 

# # Used for View Clients screen (show all clients even if they have no projects)
# @app.route("/get_clients_view")
# def get_clients_view():
#     conn = get_db_connection()
#     cursor = conn.cursor()
 
#     cursor.execute("""
#         SELECT
#             c.ClientID,
#             c.ClientName,
#             c.Email,
#             c.CreatedDate,
#             c.Status
#         FROM ticket.client c
#         LEFT JOIN ticket.project p
#             ON c.ClientID = p.ClientID
#         GROUP BY
#             c.ClientID,
#             c.ClientName,
#             c.Email,
#             c.CreatedDate,
#             c.Status
#         ORDER BY c.CreatedDate DESC
#     """)
 
#     rows = cursor.fetchall()
#     conn.close()
 
#     clients = []
#     for row in rows:
#         clients.append({
#             "ClientID": row[0],
#             "ClientName": row[1],
#             "Email": row[2],
#             "CreatedDate": row[3].strftime("%Y-%m-%d") if row[3] else None,
#             "Status": row[4]
#         })
 
#     return jsonify(clients)

# @app.route("/update_client/<int:client_id>", methods=["POST"])
# def update_client(client_id):
#     client_name = request.form.get("ClientName")
#     created_date = request.form.get("CreatedDate")
#     status = request.form.get("Status")
 
#     conn = get_db_connection()
#     cursor = conn.cursor()
 
#     if created_date:
#         query = "UPDATE Ticket.Client SET ClientName=?, CreatedDate=?, Status=? WHERE ClientID=?"
#         cursor.execute(query, (client_name, created_date, status, client_id))
#     else:
#         query = "UPDATE Ticket.Client SET ClientName=?, Status=? WHERE ClientID=?"
#         cursor.execute(query, (client_name, status, client_id))
 
#     conn.commit()
#     conn.close()
#     return jsonify({"message": "Client updated successfully!"})


@app.route("/update_client/<int:client_id>", methods=["POST"])
def update_client(client_id):
    try:
        client_name = request.form.get("ClientName")
        created_date = request.form.get("CreatedDate")
        status = request.form.get("Status") or "Active"  # ✅ default fallback
 
        conn = get_db_connection()
        cursor = conn.cursor()
 
        if created_date:
            query = """
                UPDATE Ticket.Client
                SET ClientName = ?, CreatedDate = ?, Status = ?
                WHERE ClientID = ?
            """
            cursor.execute(query, (client_name, created_date, status, client_id))
        else:
            query = """
                UPDATE Ticket.Client
                SET ClientName = ?, Status = ?
                WHERE ClientID = ?
            """
            cursor.execute(query, (client_name, status, client_id))
 
        conn.commit()
        cursor.close()
        conn.close()
 
        return jsonify({"message": "Client updated successfully!"})
 
    except Exception as e:
        print("❌ Error updating client:", e)
        return jsonify({"error": str(e)}), 500
 
 
 
 
 
 
 
@app.route("/view_client_projects", methods=["GET"])
def show_client_projects():
    client_id = request.args.get("client_id")
 
    if not client_id:
        return "Client ID is required!", 400
 
    try:
        client_id = int(client_id)
    except ValueError:
        return "Invalid Client ID", 400
 
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
 
        # ✅ Use schema-qualified table name
        cursor.execute("""
            SELECT ProjectID, ProjectName, Status, CreatedDate
            FROM ticket.Project
            WHERE ClientID = ?
            and deletestatus='Not Deleted'
        """, (client_id,))
 
        projects = cursor.fetchall()
        conn.close()
 
        # ✅ Format project data
        project_list = []
        for p in projects:
            created_date = p[3]
            if isinstance(created_date, str):
                formatted_date = created_date
            elif created_date is None:
                formatted_date = ""
            else:
                formatted_date = created_date.strftime("%Y-%m-%d")
 
            project_list.append({
                "ProjectID": p[0],
                "ProjectName": p[1],
                "Status": p[2],
                "CreatedDate": formatted_date
            })
 
        return render_template("view_client_projects.html", projects=project_list, client_id=client_id)
 
    except Exception as e:
        print("Error:", str(e))
        return f"An error occurred: {str(e)}", 500


@app.route("/delete_client/<int:client_id>", methods=["DELETE"])
def delete_client(client_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
 
        # ✅ Check if client has linked projects
        cursor.execute("SELECT COUNT(*) FROM Ticket.Project WHERE ClientID = ?", (client_id,))
        project_count = cursor.fetchone()[0]
 
        if project_count > 0:
            conn.close()
            return jsonify({
                "success": False,
                "message": "Cannot delete client. There are active projects linked to this client."
            })
 
        # ✅ Safe to delete client
        cursor.execute("DELETE FROM Ticket.Client WHERE ClientID = ?", (client_id,))
        conn.commit()
        conn.close()
 
        return jsonify({"success": True, "message": "Client deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
 

# Add near other routes in app.py

@app.route("/getpriority", methods=["GET"])
def get_priority():
    projectid = request.args.get("projectid")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if projectid:
            cur.execute("""
                SELECT DISTINCT PriorityName 
                FROM ticket.ProjectPriority 
                WHERE ProjectID = ? AND PriorityName IS NOT NULL
                ORDER BY PriorityName
            """, (projectid,))
        else:
            cur.execute("""
                SELECT DISTINCT PriorityName 
                FROM ticket.ProjectPriority 
                WHERE PriorityName IS NOT NULL
                ORDER BY PriorityName
            """)
        rows = cur.fetchall()
        priorities = [{"name": r[0]} for r in rows]
        return jsonify(priorities)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/getsubject", methods=["GET"])
def get_subject():
    projectid = request.args.get("projectid")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if projectid:
            # Filter subjects by projectid if provided
            cur.execute("""
                SELECT DISTINCT SubjectName 
                FROM ticket.ProjectSubject 
                WHERE ProjectID = ? AND SubjectName IS NOT NULL
                ORDER BY SubjectName
            """, (projectid,))
        else:
            # Return all subjects if no projectid provided
            cur.execute("""
                SELECT DISTINCT SubjectName 
                FROM ticket.ProjectSubject 
                WHERE SubjectName IS NOT NULL
                ORDER BY SubjectName
            """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        subjects = [{"name": r[0]} for r in rows]
        return jsonify(subjects)
    except Exception as e:
        logging.exception("Error fetching subjects")
        return jsonify(error=str(e)), 500


 
@app.route("/getstatus", methods=["GET"])
def get_status():
    projectid = request.args.get("projectid")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if projectid:
            cur.execute("""
                SELECT DISTINCT StatusName 
                FROM ticket.ProjectStatus 
                WHERE ProjectID = ? AND StatusName IS NOT NULL
                ORDER BY StatusName
            """, (projectid,))
        else:
            cur.execute("""
                SELECT DISTINCT StatusName 
                FROM ticket.ProjectStatus 
                WHERE StatusName IS NOT NULL
                ORDER BY StatusName
            """)
        rows = cur.fetchall()
        statuses = [{"name": r[0]} for r in rows]
        return jsonify(statuses)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Used for Add Ticket dropdown (only clients with at least one project)
@app.route("/get_clients")
def get_clients_dropdown():
    conn = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT DISTINCT
            c.ClientID,
            c.ClientName,
            c.Email,
            c.CreatedDate,
            c.Status
        FROM ticket.client c
        INNER JOIN ticket.project p
            ON c.ClientID = p.ClientID
        ORDER BY c.CreatedDate DESC
    """)
 
    rows = cursor.fetchall()
    conn.close()
 
    clients = []
    for row in rows:
        clients.append({
            "ClientID": row[0],
            "ClientName": row[1],
            "Email": row[2],
            "CreatedDate": row[3].strftime("%Y-%m-%d") if row[3] else None,
            "Status": row[4]
        })
 
    return jsonify(clients)

# @app.route("/get_projects", methods=["GET"])
# def get_projects():
#     try:
#         conn = get_db_connection()
#         cur = conn.cursor()
 
#         cur.execute("""
#             SELECT p.ProjectID, p.ProjectName, p.ClientID, c.ClientName, p.CreatedDate, p.Status
#             FROM Ticket.Project p
#             LEFT JOIN Ticket.Client c ON p.ClientID = c.ClientID
#             where p.deletestatus='Not Deleted'
#             ORDER BY p.ProjectID ASC
#         """)
       
#         rows = cur.fetchall()
#         conn.close()
 
#         projects = [
#             {
#                 "ProjectID": row[0],
#                 "ProjectName": row[1],
#                 "ClientID": row[2],
#                 "ClientName": row[3],
#                 "CreatedDate": row[4].strftime("%Y-%m-%d") if row[4] else "",
#                 "Status": row[5]
#             }
#             for row in rows
#         ]
 
#         return jsonify(projects)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
 
@app.route("/add_project", methods=["POST"])
def add_project():
    try:
        data = request.form
        project_name = data.get("ProjectName").strip()
        client_id = data.get("ClientID")
        created_date = data.get("CreatedDate")
        status = data.get("Status")
 
        conn = get_db_connection()
        cursor = conn.cursor()
 
        # Check for duplicate project for the same client
        cursor.execute("""
            SELECT COUNT(*) FROM Ticket.Project
            WHERE ProjectName = ? AND ClientID = ?
        """, (project_name, client_id))
        count = cursor.fetchone()[0]
 
        if count > 0:
            return jsonify({"success": False, "message": "Project with this name already exists for this client!"})
 
        # Insert if not duplicate
        cursor.execute("""
            INSERT INTO Ticket.Project (ProjectName, ClientID, CreatedDate, Status)
            VALUES (?, ?, ?, ?)
        """, (project_name, client_id, created_date, status))
 
        conn.commit()
        conn.close()
 
        return jsonify({"success": True, "message": "Project created successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
 
@app.route("/get_next_project_id")
def get_next_project_id():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
 
        # ✅ Get next Project ID
        cursor.execute("SELECT ISNULL(MAX(ProjectID), 0) + 1 FROM Ticket.Project")
        next_id = cursor.fetchone()[0]
 
        cursor.close()
        conn.close()
 
        return jsonify({"success": True, "next_id": next_id})
    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "message": str(e)})

@app.route("/get_project_by_id")
def get_project_by_id():
    project_id = request.args.get("project_id")
    if not project_id:
        return jsonify({"success": False, "message": "Missing project_id"}), 400
 
    conn = get_db_connection()
    cur = conn.cursor()
 
    # Join project with client to get ClientName
    query = """
        SELECT p.ProjectID, p.ClientID, c.ClientName, p.ProjectName, p.CreatedDate, p.Status
        FROM ticket.project p
        LEFT JOIN ticket.client c ON p.ClientID = c.ClientID
        WHERE p.ProjectID = ?
        and p.deletestatus='Not Deleted'
    """
    cur.execute(query, (project_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
 
    if not row:
        return jsonify({"success": False, "message": "Project not found"}), 404
 
    project = {
        "ProjectID": row[0],
        "ClientID": row[1],
        "ClientName": row[2],
        "ProjectName": row[3],
        "CreatedDate": str(row[4]),
        "Status": row[5]
    }
 
    return jsonify({"success": True, "project": project})
 
 
 

# @app.route("/get_project_by_id")
# def get_project_by_id():
#     project_id = request.args.get("project_id")
#     if not project_id:
#         return jsonify({"success": False, "message": "Missing project_id"}), 400
 
#     conn = get_db_connection()
#     cur = conn.cursor()
 
#     # Join project with client to get ClientName
#     query = """
#         SELECT p.ProjectID, p.ClientID, c.ClientName, p.ProjectName, p.CreatedDate, p.Status
#         FROM ticket.project p
#         LEFT JOIN ticket.client c ON p.ClientID = c.ClientID
#         WHERE p.ProjectID = ?
#         and p.deletestatus='Not Delete'
#     """
#     cur.execute(query, (project_id,))
#     row = cur.fetchone()
#     cur.close()
#     conn.close()
 
#     if not row:
#         return jsonify({"success": False, "message": "Project not found"}), 404
 
#     project = {
#         "ProjectID": row[0],
#         "ClientID": row[1],
#         "ClientName": row[2],
#         "ProjectName": row[3],
#         "CreatedDate": str(row[4]),
#         "Status": row[5]
#     }
 
#     return jsonify({"success": True, "project": project})
 
@app.route("/edit_project", methods=["POST"])
def edit_project():
    try:
        project_id = request.form.get("ProjectID")
        project_name = request.form.get("ProjectName")
        client_id = request.form.get("ClientID")
        created_date = request.form.get("CreatedDate")
        status = request.form.get("Status")
 
        if not project_id:
            return jsonify({"success": False, "message": "Missing ProjectID"})
 
        conn = get_db_connection()
        cursor = conn.cursor()
 
        query = """
            UPDATE Ticket.Project
            SET ProjectName = ?, ClientID = ?, CreatedDate = ?, Status = ?
            WHERE ProjectID = ?
        """
        cursor.execute(query, (project_name, client_id, created_date, status, project_id))
        conn.commit()
 
        cursor.close()
        conn.close()
 
        return jsonify({"success": True, "message": "Project updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
 
@app.route("/add_stream1", methods=["POST"])
def add_stream1():
    data = request.json
    project_id = data.get("project_id")
    stream1 = data.get("stream1")
    created_date = data.get("created_date")
    client_id = data.get("client_id")
 
    if not all([project_id, stream1, created_date, client_id]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
 
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO TICKET.STREAM (ProjectID, Stream1, Stream2, CreatedDate, ClientID)
            VALUES (?, ?, NULL, ?, ?)
        """, project_id, stream1, created_date, client_id)
        conn.commit()
        return jsonify({"success": True, "message": "Stream1 added successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()
 
# ✅ Add Stream 2
@app.route("/add_stream2", methods=["POST"])
def add_stream2():
    data = request.json
    project_id = data.get("project_id")
    stream1_id = data.get("stream1_id")
    stream2 = data.get("stream2")
    created_date = data.get("created_date")
    client_id = data.get("client_id")
 
    if not all([project_id, stream1_id, stream2, created_date, client_id]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
 
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get Stream1 value for the selected Stream1 ID
        cursor.execute("SELECT Stream1 FROM TICKET.STREAM WHERE StreamID=?", stream1_id)
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Stream1 not found"}), 404
        stream1_value = row[0]
 
        cursor.execute("""
            INSERT INTO TICKET.STREAM (ProjectID, Stream1, Stream2, CreatedDate, ClientID)
            VALUES (?, ?, ?, ?, ?)
        """, project_id, stream1_value, stream2, created_date, client_id)
        conn.commit()
        return jsonify({"success": True, "message": "Stream2 added successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

# ✅ Get Stream1 for a project

# @app.route("/get_stream1/<int:project_id>")

# def get_stream1(project_id):

#     try:

#         conn = get_db_connection()

#         cursor = conn.cursor()

#         cursor.execute("SELECT StreamID, Stream1 FROM TICKET.STREAM WHERE ProjectID=? AND Stream2 IS NULL", project_id)

#         streams = [{"StreamID": row[0], "Stream1": row[1]} for row in cursor.fetchall()]

#         return jsonify(streams)

#     except Exception as e:

#         return jsonify({"success": False, "message": str(e)})

#     finally:

#         conn.close()


 
 
# ✅ Get Stream2 for a project
# ✅ Get Stream2 for a project
# @app.route("/get_stream2/<project_id>")
# def get_stream2(project_id):
#     conn = get_db_connection()
#     cur = conn.cursor()
#     # If ProjectID in SQL is INT, convert to int safely, otherwise use string
#     try:
#         project_id_int = int(project_id)
#         cur.execute("SELECT Stream2Name FROM ticket.Stream2 WHERE ProjectID=?", (project_id_int,))
#     except ValueError:
#         # fallback if project_id is string
#         cur.execute("SELECT Stream2Name FROM ticket.Stream2 WHERE ProjectID=?", (project_id,))
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#     return jsonify([r[0] for r in rows])

# ✅ Get Stream1 for a project
@app.route("/get_stream1/<int:project_id>")
def get_stream1(project_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT StreamID, Stream1 FROM TICKET.STREAM WHERE ProjectID=? AND Stream2 IS NULL", project_id)
        streams = [{"StreamID": row[0], "Stream1": row[1]} for row in cursor.fetchall()]
        return jsonify(streams)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()
 

@app.route("/get_stream2/<int:project_id>")
def get_stream2(project_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT StreamID, Stream1, Stream2
            FROM TICKET.STREAM
            WHERE ProjectID=? AND Stream2 IS NOT NULL
        """, project_id)
        streams = [{"StreamID": row[0], "Stream1": row[1], "Stream2": row[2]} for row in cursor.fetchall()]
        return jsonify(streams)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close() 
 
# Delete a stream (either Stream1 or Stream2)
@app.route("/delete_stream", methods=["DELETE"])
def delete_stream():
    try:
        stream_id = request.args.get("StreamID")
        if not stream_id:
            return jsonify({"success": False, "message": "Missing StreamID"}), 400
 
        conn = get_db_connection()
        cur = conn.cursor()
 
        # Delete from ticket.stream table
        cur.execute("DELETE FROM [ticket].[stream] WHERE StreamID = ?", (stream_id,))
        conn.commit()
        conn.close()
 
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
 
 
@app.route("/get_active_clients", methods=["GET"])
def get_active_clients():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Only fetch clients with Status = 'Active'
        cur.execute("""
            SELECT ClientID, ClientName
            FROM Ticket.Client
                        WHERE Status = 'Active'

            ORDER BY ClientName
        """)
        rows = cur.fetchall()
        conn.close()
 
        clients = [{"ClientID": row[0], "ClientName": row[1]} for row in rows]
        return jsonify(clients)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Get project info for header ===
@app.route("/get_project_info")
def get_project_info():
    project_id = request.args.get("project_id")
    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400
 
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.ProjectID, p.ProjectName, c.ClientName
        FROM ticket.Project p
        LEFT JOIN ticket.Client c ON p.ClientID = c.ClientID
        WHERE p.ProjectID = ?
    """, project_id)
    row = cursor.fetchone()
    conn.close()
 
    if row:
        return jsonify({
            "ProjectID": row.ProjectID,
            "ProjectName": row.ProjectName,
            "ClientName": row.ClientName
        })
    else:
        return jsonify({"error": "Project not found"}), 404
 
# === Render manage_subject page ===
@app.route("/manage_subject.html")
def manage_subject_page():
    project_id = request.args.get("project_id")
    return render_template("manage_subject.html", project_id=project_id)

 
@app.route("/get_subjects")
def get_subjects():
    project_id = request.args.get("project_id")
    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400
 
    conn = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT SubjectID, SubjectName, CreatedDate
        FROM ticket.ProjectSubject
        WHERE ProjectID = ?
        ORDER BY SubjectID ASC
    """, (project_id,))  # ✅ tuple param is important
 
    rows = cursor.fetchall()
    conn.close()
 
    subjects = []  # ✅ correctly aligned (no extra indent)
    for row in rows:
        subjects.append({
            "SubjectID": row[0],
            "SubjectName": row[1],
            "CreatedDate": row[2].strftime("%Y-%m-%d") if row[2] else ""
        })
 
    return jsonify(subjects)

# === Add a new subject ===
@app.route("/add_subject", methods=["POST"])
def add_subject():
    project_id = request.form.get("ProjectID")
    subject_name = request.form.get("SubjectName")
 
    if not project_id or not subject_name:
        return jsonify({"success": False, "message": "Project ID and Subject Name are required"}), 400
 
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if the subject already exists for this project
        cursor.execute("""
            SELECT COUNT(*)
            FROM ticket.ProjectSubject
            WHERE ProjectID = ? AND SubjectName = ?
        """, (project_id, subject_name))
        count = cursor.fetchone()[0]
 
        if count > 0:
            return jsonify({"success": False, "message": "Subject already exists for this project"})
 
        # Insert new subject if it does not exist
        cursor.execute("""
            INSERT INTO ticket.ProjectSubject (ProjectID, SubjectName, CreatedDate)
            VALUES (?, ?, ?)
        """, (project_id, subject_name, datetime.now()))
        conn.commit()
        return jsonify({"success": True, "message": "Subject added successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()
 
# === Delete a subject ===
@app.route("/delete_subject", methods=["DELETE"])
def delete_subject():
    subject_id = request.args.get("subject_id")
    if not subject_id:
        return jsonify({"success": False, "message": "Subject ID is required"}), 400
 
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM ticket.ProjectSubject WHERE SubjectID = ?", subject_id)
        conn.commit()
        return jsonify({"success": True, "message": "Subject deleted successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()
  
 
@app.route("/get_project_info_status")
def get_project_info_status():
    project_id = request.args.get("project_id")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.ProjectID, p.ProjectName, c.ClientName
        FROM ticket.Project p
        JOIN ticket.Client c ON p.ClientID = c.ClientID
        WHERE p.ProjectID = ?
    """, project_id)
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Project not found"})
    return jsonify({"ProjectID": row.ProjectID, "ProjectName": row.ProjectName, "ClientName": row.ClientName})
 
 
# === STATUS ===
@app.route("/Status.html")
def status_page():
    project_id = request.args.get("project_id")
    return render_template("Status.html", project_id=project_id)
 
@app.route("/get_statuses")
def get_statuses():
    project_id = request.args.get("project_id")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT StatusName, StatusID FROM ticket.ProjectStatus WHERE ProjectID=?", project_id)
    rows = cur.fetchall()
    conn.close()
    return jsonify([{"StatusID": r.StatusID, "StatusName": r.StatusName} for r in rows])
 
@app.route("/add_status", methods=["POST"])
def add_status():
    project_id = request.form.get("ProjectID")
    status_name = request.form.get("StatusName")
 
    if not project_id or not status_name:
        return jsonify({"success": False, "message": "Project ID and Status Name are required"}), 400
 
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if the status already exists for this project
        cur.execute("""
            SELECT COUNT(*)
            FROM ticket.ProjectStatus
            WHERE ProjectID = ? AND StatusName = ?
        """, (project_id, status_name))
        count = cur.fetchone()[0]
 
        if count > 0:
            return jsonify({"success": False, "message": "Status already exists for this project"})
 
        # Insert new status if it does not exist
        cur.execute("""
            INSERT INTO ticket.ProjectStatus (ProjectID, StatusName, CreatedDate)
            VALUES (?, ?, ?)
        """, (project_id, status_name, datetime.now()))
        conn.commit()
        return jsonify({"success": True, "message": "Status added successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()
 
 
@app.route("/delete_status", methods=["DELETE"])
def delete_status():
    status_id = request.args.get("status_id")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ticket.ProjectStatus WHERE StatusID=?", status_id)
        conn.commit()
        return jsonify({"success": True, "message": "Deleted successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()


@app.route("/add_priority", methods=["POST"])
def add_priority():
    project_id = request.form.get("ProjectID")
    priority_name = request.form.get("PriorityName")
   
    if not project_id or not priority_name:
        return jsonify({"success": False, "message": "Project ID and Priority Name are required"})
   
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if the priority already exists for this project
        cur.execute("""
            SELECT COUNT(*) FROM ticket.ProjectPriority
            WHERE ProjectID = ? AND PriorityName = ?
        """, (project_id, priority_name))
        exists = cur.fetchone()[0]
 
        if exists:
            return jsonify({"success": False, "message": "Priority already exists for this project"})
       
        # Insert new priority
        cur.execute("""
            INSERT INTO ticket.ProjectPriority (ProjectID, PriorityName, CreatedDate)
            VALUES (?, ?, ?)
        """, (project_id, priority_name, datetime.now()))
        conn.commit()
        return jsonify({"success": True, "message": "Priority added successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()
 
@app.route("/get_priorities")
def get_priorities():
    project_id = request.args.get("project_id")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT PriorityID, PriorityName FROM ticket.ProjectPriority WHERE ProjectID=?", project_id)
    rows = cur.fetchall()
    conn.close()
    return jsonify([{"PriorityID": r.PriorityID, "PriorityName": r.PriorityName} for r in rows])
 
@app.route("/delete_priority", methods=["DELETE"])
def delete_priority():
    priority_id = request.args.get("priority_id")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ticket.ProjectPriority WHERE PriorityID=?", priority_id)
        conn.commit()
        return jsonify({"success": True, "message": "Deleted successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()
 
@app.route("/get_project_info_priority")
def get_project_info_priority():
    project_id = request.args.get("project_id")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.ProjectID, p.ProjectName, c.ClientName
        FROM ticket.Project p
        JOIN ticket.Client c ON p.ClientID = c.ClientID
        WHERE p.ProjectID = ?
    """, project_id)
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Project not found"})
    return jsonify({"ProjectID": row.ProjectID, "ProjectName": row.ProjectName, "ClientName": row.ClientName})
 
 
 
 
 
 
# === PRIORITY ===
@app.route("/priority.html")
def priority_page():
    project_id = request.args.get("project_id")
    return render_template("Priority.html", project_id=project_id)
 


@app.route("/delete_project", methods=["DELETE"])
def delete_project():
    try:
        project_id = request.args.get("ProjectID")
        if not project_id:
            return jsonify({"success": False, "message": "ProjectID is missing!"})
 
        conn = get_db_connection()
        cursor = conn.cursor()
 
        # Delete tickets first
        cursor.execute("DELETE FROM ticket.tickets_new WHERE project_id = ?", (project_id,))
 
        # Delete dependent streams
        cursor.execute("DELETE FROM Ticket.Stream WHERE ProjectID = ?", (project_id,))
 
        # Then delete the project
        cursor.execute("DELETE FROM Ticket.Project WHERE ProjectID = ?", (project_id,))
 
        conn.commit()
        cursor.close()
        conn.close()
 
        return jsonify({"success": True, "message": "Project and related data deleted successfully!"})
 
    except Exception as e:
        print("Error deleting project:", e)
        return jsonify({"success": False, "message": str(e)})
 


@app.route("/view_stream")
def view_stream():
    return render_template("view_stream.html")
 
@app.route("/view_projects")
def view_projects():
    return render_template("view_projects.html") 


@app.route('/getprojectsbyclient', methods=['GET'])
def getprojectsbyclient():
    try:
        client_id = request.args.get("clientid")  # Note: param must match JS fetch (`clientid`)
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ProjectID AS id, ProjectName AS name
            FROM ticket.project
            WHERE ClientID = ? AND Status = 'Active'
            ORDER BY ProjectName
        """, (client_id,))

        rows = cursor.fetchall()
        projects = [{"id": row[0], "name": row[1]} for row in rows]

        cursor.close()
        conn.close()
        return jsonify(projects)

    except Exception as e:
        print("Error fetching projects:", e)
        return jsonify([])

@app.route("/get_projects", methods=["GET"])
def get_projects():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
 
        cur.execute("""
            SELECT p.ProjectID, p.ProjectName, p.ClientID, c.ClientName, p.CreatedDate, p.Status
            FROM Ticket.Project p
            LEFT JOIN Ticket.Client c ON p.ClientID = c.ClientID
            where p.deletestatus='Not Deleted'
            ORDER BY p.ProjectID ASC
        """)
       
        rows = cur.fetchall()
        conn.close()
 
        projects = [
            {
                "ProjectID": row[0],
                "ProjectName": row[1],
                "ClientID": row[2],
                "ClientName": row[3],
                "CreatedDate": row[4].strftime("%Y-%m-%d") if row[4] else "",
                "Status": row[5]
            }
            for row in rows
        ]
 
        return jsonify(projects)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 

@app.route("/soft_delete_client/<int:client_id>", methods=["POST"])
def soft_delete_client(client_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
 
        # ✅ Update DeleteStatus instead of deleting record
        cursor.execute("""
            UPDATE ticket.client
            SET DeleteStatus = 'Deleted'
            WHERE ClientID = ?
        """, (client_id,))
 
        conn.commit()
        conn.close()
 
        return jsonify({"success": True, "message": "Client marked as deleted."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/soft_delete_project/<int:project_id>", methods=["POST"])
def soft_delete_project(project_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
 
        # ✅ Update DeleteStatus instead of deleting record
        cursor.execute("""
            UPDATE ticket.project
            SET DeleteStatus = 'Deleted'
            WHERE ProjectID = ?
        """, (project_id,))
 
        conn.commit()
        conn.close()
 
        return jsonify({"success": True, "message": "Project marked as deleted."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# Used for View Clients screen (show all clients even if they have no projects)
@app.route("/get_clients_view")
def get_clients_view():
    conn = get_db_connection()
    cursor = conn.cursor()
 
    cursor.execute("""
        SELECT
            c.ClientID,
            c.ClientName,
            c.Email,
            c.CreatedDate,
            c.Status
        FROM ticket.client c
        LEFT JOIN ticket.project p
            ON c.ClientID = p.ClientID
        WHERE c.DeleteStatus = 'Not Deleted'         -- ✅ only show active (not deleted) clients
        GROUP BY
            c.ClientID,
            c.ClientName,
            c.Email,
            c.CreatedDate,
            c.Status
        ORDER BY c.CreatedDate DESC
    """)
 
    rows = cursor.fetchall()
    conn.close()
 
    clients = []
    for row in rows:
        clients.append({
            "ClientID": row[0],
            "ClientName": row[1],
            "Email": row[2],
            "CreatedDate": row[3].strftime("%Y-%m-%d") if row[3] else None,
            "Status": row[4]
        })
 
    return jsonify(clients)
 
 



@app.route("/get_projects_by_client")
def get_projects_by_client():
    
    try:
        client_id = request.args.get("client_id")
        conn = get_db_connection()
        cursor = conn.cursor()
 
        cursor.execute("""
            SELECT ProjectID AS id, ProjectName AS name
            FROM ticket.Project
            WHERE ClientID = ? 
            and status = 'Active'

        """, (client_id,))  # ✅ Use ? instead of %s
 
        # Fetch all projects
        rows = cursor.fetchall()
 
        # ✅ Convert result to list of dicts manually (since cursor is not dictionary=True)
        projects = [
            {"id": row[0], "name": row[1]} for row in rows
        ]
 
        cursor.close()
        conn.close()
 
        return jsonify(projects)
 
    except Exception as e:
        print("Error fetching projects:", e)
        return jsonify([])
 
# Run initialization
init_db()
 
if __name__ == "__main__":
    Timer(1.5, open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
 
 
 
 
 