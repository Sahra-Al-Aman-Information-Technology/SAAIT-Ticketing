from flask import Blueprint, request, jsonify
import sqlite3

ticket_bp = Blueprint('ticket_bp', __name__)

def get_db_connection():
    conn = sqlite3.connect('tickets.db')
    conn.row_factory = sqlite3.Row
    return conn

@ticket_bp.route('/tickets', methods=['GET'])
def get_tickets():
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM tickets').fetchall()
    conn.close()
    return jsonify([dict(ticket) for ticket in tickets])

@ticket_bp.route('/tickets', methods=['POST'])
def add_ticket():
    data = request.json
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO tickets (
            dashboard_name, ticket_no, stream, raised_by, subject,
            date_logged, closed_date, priority, status,
            assigned_to, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['dashboard_name'], data['ticket_no'], data['stream'], data['raised_by'],
        data['subject'], data['date_logged'], data.get('closed_date', ''),
        data['priority'], data['status'], data['assigned_to'], data['description']
    ))
    conn.commit()
    conn.close()
    return jsonify({"message": "Ticket added"}), 201
