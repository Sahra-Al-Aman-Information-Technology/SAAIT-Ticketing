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
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.environ.get('SQL_SERVER')};"
    f"DATABASE={os.environ.get('SQL_DATABASE')};"
    f"UID={os.environ.get('SQL_USER')};"
    f"PWD={os.environ.get('SQL_PASSWORD')};"
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
            "Sai Madhav" : "saimadhav.v@armholding.ae"
            # Add all your team here
        }
        return mapping.get(name, "support@saait.co")
 
    payload = {
        "ticket_id": data.get("ticket_no", "N/A"),
        "stream": data.get("stream", ""),
        "dashboard": data.get("dashboard", ""),
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
 
 
@app.route("/rafey.html")
def rafey_page():
    if "username" not in session:
        return redirect(url_for('login'))  # Redirect to /
    return render_template("rafey.html")
 
@app.route("/add_ticket", methods=["POST"])
def add_ticket():
    try:
        data = request.form
        file = request.files.get('attachment')
        attachment = None
 
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            attachment = filename
 
        # 🔒 Get and validate user role
        user_role = session.get("role")
        if not user_role:
            return jsonify({"error": "User role not found in session"}), 403
 
        user_role = user_role.strip().upper()
        if user_role == "VIEWER":
            return jsonify({"error": "Access denied"}), 403
 
        system_role = user_role  # 💡 Use this to tag the ticket
 
        # 🧪 Debug print
        print("🎫 Adding ticket for role:", system_role)
 
        # Comment handling
        comment = data.get('comment', '').strip()
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        full_comment = f"[{timestamp}] {comment}" if comment else ''
 
        # Closed date logic
        status = data.get('status')
        closed_date = data.get('closed_date')
        if status != 'Closed':
            closed_date = None
 
        # 🔄 Insert ticket (ticket_no will be updated later)
        conn = get_db_connection()
        cur = conn.cursor()
 
        cur.execute('''
            INSERT INTO ticket.tickets (
                ticket_no, dashboard, stream, raised_by, subject, date_logged, closed_date,
                priority, status, assigned_to, description, attachment, comments, system_role
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            None,  # ticket_no placeholder
            data.get('dashboard'),
            data.get('stream'),
            data.get('raised_by'),
            data.get('subject'),
            data.get('date_logged'),
            closed_date,
            data.get('priority'),
            data.get('status'),
            data.get('assigned_to'),
            data.get('description'),
            attachment,
            full_comment,
            system_role
        ))
 
        result = cur.fetchone()
        ticket_id = result[0] if result else None
 
        if ticket_id is None:
            return jsonify({"error": "Failed to retrieve ticket ID"}), 500
 
        # ✅ Generate ticket number based on last ticket_no for this role
        cur.execute("""
            SELECT MAX(ticket_no)
            FROM ticket.tickets
            WHERE system_role = ?
        """, (system_role,))
        last_ticket = cur.fetchone()[0]
 
        if last_ticket:
            try:
                last_num = int(last_ticket.replace(system_role, ""))
            except ValueError:
                last_num = 0
        else:
            last_num = 0
 
        next_num = last_num + 1
        ticket_no = f"{system_role}{next_num:04d}"
 
        # ✅ Update inserted row with new ticket_no
        cur.execute('UPDATE ticket.tickets SET ticket_no = ? WHERE id = ?', (ticket_no, ticket_id))
        conn.commit()
        cur.close()
 
        # 📧 Send email notification
        send_ticket_notification({
            **data.to_dict(),
            "ticket_no": ticket_no
        }, mode="create")
 
        return jsonify({"message": "Ticket added successfully", "ticket_no": ticket_no}), 200
 
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
 
 
 
# Update Ticket
@app.route("/update_ticket", methods=["POST"])
def update_ticket():
    try:
        data = request.form
        ticket_id = data.get('id')
 
        if not ticket_id:
            return jsonify({"error": "Missing ticket ID"}), 400
 
        ticket_id = int(ticket_id)
 
        # ✅ Handle file upload
        file = request.files.get('attachment')
        attachment = None
        if file and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            attachment = filename
 
        conn = get_db_connection()
        cur = conn.cursor()
 
        # ✅ Get existing comments
        cur.execute("SELECT comments FROM ticket.tickets WHERE id = ?", (ticket_id,))
        result = cur.fetchone()
        existing_comments = result[0] if result else ""
 
        # ✅ Append new comment with timestamp
        new_comment = data.get('comment', '').strip()
        updated_comments = existing_comments
        if new_comment:
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
            if existing_comments:
                updated_comments = f"{existing_comments}\n[{timestamp}] {new_comment}"
            else:
                updated_comments = f"[{timestamp}] {new_comment}"
 
        # ✅ Status / closed_date logic
        status = data.get('status', '').strip()
        closed_date = data.get('closed_date') if status == 'Closed' else None
 
        # ✅ Handle “Other” stream/dashboard
        stream = data.get('stream')
        if stream == "Other":
            stream = data.get('custom_stream')
 
        dashboard = data.get('dashboard')
        if dashboard == "Other":
            dashboard = data.get('custom_dashboard')
 
        # ✅ Handle “Other” assigned_to
        assigned_to = data.get('assigned_to')
        if assigned_to == "Other":
            assigned_to = data.get('custom_assigned_to')
 
        # ✅ Build update query (no ticket_no, no raised_by, no date_logged)
        update_query = '''
            UPDATE ticket.tickets SET
                dashboard=?, stream=?, subject=?,
                closed_date=?, priority=?, status=?, assigned_to=?,
                description=?, comments=?
        '''
        params = [
            dashboard,
            stream,
            data.get('subject'),
            closed_date,
            data.get('priority'),
            status,
            assigned_to,
            data.get('description'),
            updated_comments
        ]
 
        # ✅ Add attachment if uploaded
        if attachment:
            update_query += ', attachment=?'
            params.append(attachment)
 
        # ✅ Finalize query
        update_query += ' WHERE id=?'
        params.append(ticket_id)
 
        # Execute query
        cur.execute(update_query, tuple(params))
        conn.commit()
        cur.close()
        conn.close()
 
        # ✅ Send notification
        send_ticket_notification({
            **data.to_dict(),
            "id": ticket_id
        }, mode="update")
 
        return jsonify({"message": "Ticket updated successfully"}), 200
 
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to update ticket"}), 500
 
        # ✅ Add attachment if uploaded
        if attachment:
            update_query += ', attachment=?'
            params.append(attachment)
 
        # ✅ Finalize query
        update_query += ' WHERE id=?'
        params.append(ticket_id)
 
        # Execute
        cur.execute(update_query, tuple(params))
        conn.commit()
        cur.close()
        conn.close()
 
        # ✅ Send notification
        send_ticket_notification({
            **data.to_dict(),
            "id": ticket_id
        }, mode="update")
 
        return jsonify({"message": "Ticket updated successfully"}), 200
 
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to update ticket"}), 500
 
 
# ✅ NEW function: Get Tickets (Top-level route, NOT inside try/except)
@app.route("/get_tickets")
def get_tickets():
    try:
        user_role = session.get("role")
        if not user_role:
            return jsonify({"error": "Role missing from session"}), 403
 
        user_role = user_role.strip().upper()
        print("🧪 ROLE FROM SESSION in /get_tickets:", user_role)
 
        # NEW: check slicer param (?source=ARM|TLC)
        source_role = (request.args.get("source") or "").strip().upper()
        if source_role not in ("", "ARM", "TLC"):
            source_role = ""  # sanitize
 
        # Existing: check stream slicer
        selected_streams = (request.args.get("streams") or "").strip()
        selected_streams_list = [s.strip() for s in selected_streams.split(",") if s.strip()]
 
        conn = get_db_connection()
        cur = conn.cursor()
 
        base_select = """
            SELECT id, dashboard, ticket_no, stream, raised_by, subject, date_logged,
                   closed_date, priority, status, assigned_to, description, attachment, comments, system_role
            FROM ticket.tickets
        """
 
        where_clauses = []
        params = []
 
        if user_role == "SAAIT":
            # SAAIT can see all roles, but slicer (source) filters if chosen
            if source_role:
                where_clauses.append("system_role = ?")
                params.append(source_role)
        else:
            # Non-SAAIT locked to their own role
            where_clauses.append("system_role = ?")
            params.append(user_role)
 
        if selected_streams_list:
            placeholders = ",".join("?" * len(selected_streams_list))
            where_clauses.append(f"stream IN ({placeholders})")
            params.extend(selected_streams_list)
 
        query = base_select
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
 
        # ✅ Custom status ordering + ticket_no DESC inside each group
        query += """
            ORDER BY
                CASE status
                    WHEN 'Open' THEN 1
                    WHEN 'In Progress' THEN 2
                    WHEN 'On Hold (ARM Team)' THEN 3
                    WHEN 'On Hold (SAAIT Team)' THEN 4
                    WHEN 'On Demand (ARM Team)' THEN 5
                    WHEN 'On Demand (SAAIT Team)' THEN 6
                    WHEN 'Closed' THEN 7
                    ELSE 99
                END,
                ticket_no DESC
        """
 
        print("🔍 Executing query:", query, "params:", params)
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
 
        cur.close()
        conn.close()
 
        tickets = []
        for row in rows:
            attachment_url = f"/static/uploads/{row[12]}" if row[12] else None
            tickets.append({
                "id": row[0],
                "dashboard": row[1],
                "ticket_no": row[2],
                "stream": row[3],
                "raised_by": row[4],
                "subject": row[5],
                "date_logged": row[6],
                "closed_date": row[7],
                "priority": row[8],
                "status": row[9].strip() if row[9] else '',
                "assigned_to": row[10],
                "description": row[11],
                "attachment": attachment_url,
                "comments": row[13],
                "system_role": row[14]
            })
 
        print(f"🎯 TICKETS FETCHED FOR ROLE: {user_role} | Count: {len(tickets)}")
        return jsonify(tickets)
 
    except Exception as e:
        traceback.print_exc()
        return jsonify([]), 500
 
# Dropdown Data (if used)
@app.route("/get_dropdown_data")
def get_dropdown_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
 
        # Get distinct streams
        cur.execute("""
            SELECT DISTINCT Stream
            FROM ticket.tickets
            WHERE Stream IS NOT NULL
            ORDER BY Stream
        """)
        streams = [{"id": i+1, "name": row[0]} for i, row in enumerate(cur.fetchall())]
 
        # Get distinct dashboards
        cur.execute("""
            SELECT DISTINCT Dashboard, Stream
            FROM ticket.tickets
            WHERE Dashboard IS NOT NULL
            ORDER BY Dashboard
        """)
        dashboards = [
            {"id": i+1, "name": row[0], "stream": row[1]}
            for i, row in enumerate(cur.fetchall())
        ]
 
        cur.close()
        conn.close()
 
        return jsonify({
            "streams": streams,
            "dashboards": dashboards
        })
 
    except Exception as e:
        traceback.print_exc()
        logging.exception("Error message")
        return jsonify({"error": str(e)}), 500
   
 # Login
 
@app.route("/login", methods=["GET"])
def show_login_form():  # 👈 new name
    return render_template("login.html")
 
 
@app.route('/login', methods=['POST'])
 
def login():
 
    data = request.get_json()
 
    username = data.get("username")
 
    password = data.get("password")
 
    conn = get_db_connection()
 
    cur = conn.cursor()
 
    cur.execute("SELECT name, role FROM ticket.users WHERE username = ? AND password = ?", (username, password))
 
    user = cur.fetchone()
 
    cur.close()
 
    conn.close()
 
    if user:
        name, role = user
        role = role.strip().upper()
        session["username"] = username
        session["role"] = role
 
 
        # Optional: Store system_type as a separate session variable
 
        session["system_role"] = role
 
        print("✅ Logged in:", username)
 
        print("🧪 ROLE STORED IN SESSION:", session["role"])
 
        return jsonify({
 
            "success": True,
 
            "role": session["role"],
 
            "name": name
 
        })
 
    return jsonify({"success": False}), 401
 
 
 
 
 
# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('show_login_form'))    
 
 
 
# Forgot Password
@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    username = data.get("username")
 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, email, password FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
   
    if user:
        name, email, password = user
        # Trigger Power Automate email
        try:
            url = 'https://prod-06.centralindia.logic.azure.com:443/workflows/0a403cb2b702433da8fd3be4cc8a8e1a/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=J6I9uBfg6Tus_U340jMgytgecmJ9WIRAffTIMshbXhI'
            payload = {
                "name": name,
                "username": username,
                "email": email,
                "password": password
            }
            headers = {"Content-Type": "application/json"}
            r = requests.post(url, json=payload, headers=headers)
            print("Reset email sent:", r.status_code)
            return jsonify({"success": True})
        except Exception as e:
            print("Email error:", e)
            return jsonify({"success": False, "message": "Failed to send email"}), 500
    else:
        return jsonify({"success": False, "message": "Username not found"}), 404
# Delete Ticket
@app.route("/delete_ticket/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    print("🔴 DELETE request received for ticket ID:", ticket_id)
 
    try:
        conn = get_db_connection()
        cur = conn.cursor()
 
        # Check if ticket exists
        cur.execute("SELECT 1 FROM ticket.tickets WHERE id = ?", (ticket_id,))
        if not cur.fetchone():
            conn.close()
            return jsonify({"error": "Ticket not found"}), 404
 
        # Delete the ticket
        cur.execute("DELETE FROM ticket.tickets WHERE id = ?", (ticket_id,))
        conn.commit()
        cur.close()
        conn.close()
 
        print("✅ Ticket deleted.")
        return jsonify({"message": "Ticket deleted successfully"}), 200
 
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Failed to delete ticket"}), 500
   
 
   
 
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
    username = session.get("username")
    role = session.get("role")
    return jsonify({"username": username, "role": role})
 
 
 
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
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
# Run initialization
init_db()
 
if __name__ == "__main__":
    Timer(1.5, open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
 
 
 
 
 
