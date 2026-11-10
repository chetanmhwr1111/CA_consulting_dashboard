"""
database.py - SQLite database operations for CA Consulting Dashboard
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "ca_consulting.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            mobile_number TEXT NOT NULL,
            email_address TEXT NOT NULL,
            company_name TEXT,
            service_category TEXT NOT NULL,
            service_description TEXT,
            consultation_date TEXT,
            fee_amount REAL DEFAULT 0.0,
            payment_status TEXT DEFAULT 'Pending',
            payment_date TEXT,
            follow_up_date TEXT,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_customer(data: dict) -> int:
    """Insert a new customer record. Returns the new row id."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO customers (
            customer_name, mobile_number, email_address, company_name,
            service_category, service_description, consultation_date,
            fee_amount, payment_status, payment_date, follow_up_date,
            remarks, created_at, updated_at
        ) VALUES (
            :customer_name, :mobile_number, :email_address, :company_name,
            :service_category, :service_description, :consultation_date,
            :fee_amount, :payment_status, :payment_date, :follow_up_date,
            :remarks, :created_at, :updated_at
        )
    """, {**data, "created_at": now, "updated_at": now})
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_all_customers() -> list[dict]:
    """Fetch all customer records ordered by creation date desc."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_customer_by_id(customer_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_customer(customer_id: int, data: dict):
    """Update an existing customer record."""
    conn = get_connection()
    cursor = conn.cursor()
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["id"] = customer_id
    cursor.execute("""
        UPDATE customers SET
            customer_name     = :customer_name,
            mobile_number     = :mobile_number,
            email_address     = :email_address,
            company_name      = :company_name,
            service_category  = :service_category,
            service_description = :service_description,
            consultation_date = :consultation_date,
            fee_amount        = :fee_amount,
            payment_status    = :payment_status,
            payment_date      = :payment_date,
            follow_up_date    = :follow_up_date,
            remarks           = :remarks,
            updated_at        = :updated_at
        WHERE id = :id
    """, data)
    conn.commit()
    conn.close()


def delete_customer(customer_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()


def search_customers(query: str) -> list[dict]:
    """Full-text search across name, email, company, service."""
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{query}%"
    cursor.execute("""
        SELECT * FROM customers
        WHERE customer_name LIKE ?
           OR email_address LIKE ?
           OR company_name  LIKE ?
           OR service_category LIKE ?
           OR mobile_number LIKE ?
        ORDER BY created_at DESC
    """, (like, like, like, like, like))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_dashboard_stats() -> dict:
    """Return aggregated stats for the KPI cards."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM customers")
    total_customers = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COALESCE(SUM(fee_amount),0) as total FROM customers WHERE payment_status='Paid'"
    )
    total_revenue = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COALESCE(SUM(fee_amount),0) as total FROM customers WHERE payment_status='Pending'"
    )
    pending_amount = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM customers WHERE payment_status='Paid'"
    )
    paid_count = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM customers WHERE payment_status='Pending'"
    )
    pending_count = cursor.fetchone()["cnt"]

    today = datetime.today().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM customers
        WHERE follow_up_date >= ? AND follow_up_date != ''
    """, (today,))
    upcoming_followups = cursor.fetchone()["cnt"]

    conn.close()
    return {
        "total_customers": total_customers,
        "total_revenue": total_revenue,
        "pending_amount": pending_amount,
        "paid_count": paid_count,
        "pending_count": pending_count,
        "upcoming_followups": upcoming_followups,
    }


def get_service_revenue() -> list[dict]:
    """Revenue breakdown by service category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT service_category,
               COUNT(*) as count,
               COALESCE(SUM(fee_amount),0) as revenue,
               COALESCE(SUM(CASE WHEN payment_status='Paid' THEN fee_amount ELSE 0 END),0) as paid_revenue,
               COALESCE(SUM(CASE WHEN payment_status='Pending' THEN fee_amount ELSE 0 END),0) as pending_revenue
        FROM customers
        GROUP BY service_category
        ORDER BY revenue DESC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_upcoming_followups(days: int = 7) -> list[dict]:
    """Customers whose follow-up date is within the next N days."""
    from datetime import timedelta
    today = datetime.today()
    end_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM customers
        WHERE follow_up_date BETWEEN ? AND ?
        ORDER BY follow_up_date ASC
    """, (today_str, end_date))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_monthly_revenue() -> list[dict]:
    """Monthly revenue trend."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%Y-%m', consultation_date) as month,
               COALESCE(SUM(fee_amount),0) as revenue,
               COUNT(*) as count
        FROM customers
        WHERE consultation_date != '' AND consultation_date IS NOT NULL
        GROUP BY month
        ORDER BY month ASC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
