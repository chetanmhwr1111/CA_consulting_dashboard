"""
utils.py - Utility helpers: Excel export & email reminders
"""

import io
import smtplib
import email
import email.mime
import email.mime.multipart
import email.mime.text
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd


# ─────────────────────────────────────────────
#  Excel Export
# ─────────────────────────────────────────────

EXPORT_COLUMNS = {
    "customer_name":     "Customer Name",
    "mobile_number":     "Mobile Number",
    "email_address":     "Email Address",
    "company_name":      "Company Name",
    "service_category":  "Service Category",
    "service_description": "Service Description",
    "consultation_date": "Consultation Date",
    "fee_amount":        "Fee Amount (₹)",
    "payment_status":    "Payment Status",
    "payment_date":      "Payment Date",
    "follow_up_date":    "Follow-up Date",
    "remarks":           "Remarks",
    "created_at":        "Record Created At",
}


def records_to_dataframe(records: list[dict]) -> pd.DataFrame:
    """Convert list of row dicts to a clean DataFrame."""
    if not records:
        return pd.DataFrame(columns=list(EXPORT_COLUMNS.values()))
    df = pd.DataFrame(records)
    # Keep only export columns that exist
    cols = [c for c in EXPORT_COLUMNS if c in df.columns]
    df = df[cols].rename(columns=EXPORT_COLUMNS)
    return df


def export_to_excel(records: list[dict]) -> bytes:
    """Return Excel file as bytes ready for st.download_button."""
    df = records_to_dataframe(records)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Customers")
        # Auto-fit column widths
        ws = writer.sheets["Customers"]
        for col in ws.columns:
            max_len = max(
                (len(str(cell.value)) if cell.value is not None else 0)
                for cell in col
            )
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)
    return output.getvalue()


# ─────────────────────────────────────────────
#  Follow-up Reminders
# ─────────────────────────────────────────────

def get_followup_due_customers(records: list[dict], days_ahead: int = 7) -> list[dict]:
    """
    Return customers whose follow_up_date falls within today + days_ahead.
    Buckets: 'today', '3_days', '7_days'
    """
    today = datetime.today().date()
    due = []
    for r in records:
        fu = r.get("follow_up_date", "")
        if not fu:
            continue
        try:
            fu_date = datetime.strptime(fu, "%Y-%m-%d").date()
        except ValueError:
            continue
        delta = (fu_date - today).days
        if delta < 0:
            bucket = "overdue"
        elif delta == 0:
            bucket = "today"
        elif delta <= 3:
            bucket = "3_days"
        elif delta <= 7:
            bucket = "7_days"
        else:
            continue
        due.append({**r, "_days_left": delta, "_bucket": bucket})
    due.sort(key=lambda x: x["_days_left"])
    return due


def send_followup_email(
    smtp_host: str,
    smtp_port: int,
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    customer_name: str,
    service_category: str,
    follow_up_date: str,
    ca_name: str = "Your CA",
) -> tuple[bool, str]:
    """
    Send a follow-up reminder email.
    Returns (success: bool, message: str).
    """
    subject = f"📅 Follow-up Reminder – {customer_name} | {service_category}"
    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto">
      <div style="background:#1a1f3c;padding:20px;border-radius:8px 8px 0 0">
        <h2 style="color:#fff;margin:0">CA Consulting – Follow-up Reminder</h2>
      </div>
      <div style="background:#f9f9f9;padding:24px;border:1px solid #e0e0e0;border-radius:0 0 8px 8px">
        <p>Dear <strong>{ca_name}</strong>,</p>
        <p>This is a reminder that a follow-up is scheduled for the following client:</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0">
          <tr style="background:#eef2ff">
            <td style="padding:10px;border:1px solid #ddd;font-weight:bold">Customer Name</td>
            <td style="padding:10px;border:1px solid #ddd">{customer_name}</td>
          </tr>
          <tr>
            <td style="padding:10px;border:1px solid #ddd;font-weight:bold">Service</td>
            <td style="padding:10px;border:1px solid #ddd">{service_category}</td>
          </tr>
          <tr style="background:#eef2ff">
            <td style="padding:10px;border:1px solid #ddd;font-weight:bold">Follow-up Date</td>
            <td style="padding:10px;border:1px solid #ddd"><strong>{follow_up_date}</strong></td>
          </tr>
          <tr>
            <td style="padding:10px;border:1px solid #ddd;font-weight:bold">Client Email</td>
            <td style="padding:10px;border:1px solid #ddd">{recipient_email}</td>
          </tr>
        </table>
        <p style="color:#666;font-size:13px">Please take the necessary action before the due date.</p>
        <p style="margin-top:24px">Regards,<br><strong>CA Consulting Dashboard</strong></p>
      </div>
    </body></html>
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return True, "Email sent successfully."
    except Exception as exc:
        return False, str(exc)


# ─────────────────────────────────────────────
#  Formatting Helpers
# ─────────────────────────────────────────────

def fmt_inr(amount: float) -> str:
    """Format a number as Indian Rupees string."""
    try:
        return f"₹{amount:,.0f}"
    except Exception:
        return f"₹{amount}"


def days_label(days: int) -> str:
    if days < 0:
        return f"Overdue by {abs(days)} day(s)"
    if days == 0:
        return "Due Today"
    return f"In {days} day(s)"


def status_badge(status: str) -> str:
    """Return an HTML badge string for payment status."""
    color = "#16a34a" if status == "Paid" else "#dc2626"
    bg = "#dcfce7" if status == "Paid" else "#fee2e2"
    return (
        f'<span style="background:{bg};color:{color};padding:3px 10px;'
        f'border-radius:12px;font-size:12px;font-weight:600">{status}</span>'
    )
