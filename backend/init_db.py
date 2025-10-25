import sqlite3

conn = sqlite3.connect('tickets.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dashboard_name TEXT,
    ticket_no TEXT,
    stream TEXT,
    raised_by TEXT,
    subject TEXT,
    date_logged TEXT,
    closed_date TEXT,
    priority TEXT,
    status TEXT,
    assigned_to TEXT,
    description TEXT
)
''')

conn.commit()
conn.close()
print("Database initialized.")
