"""
app.py  –  CA Consulting Management Dashboard (Streamlit)
Run:  streamlit run app.py

v1.1 changes
  • Auto-contrast text  – get_contrast_color() computes #fff or #000 from any bg
  • Theme system        – 5 presets + fully custom colour picker (live preview)
  • Auto-rerun          – st.rerun() after every save/update/delete/theme-change
  • Auto-refresh        – optional meta-refresh (configurable interval in Settings)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

import database as db
import utils

# ─────────────────────────────────────────────────────────
#  Page config
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CA Consulting Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────
#  Auto-contrast utilities
# ─────────────────────────────────────────────────────────
def get_contrast_color(hex_color: str) -> str:
    """Return #ffffff or #000000 — whichever gives best readability on hex_color."""
    h = hex_color.lstrip('#')
    if len(h) != 6:
        return '#ffffff'
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255   # W3C perceived-luminance
    return '#000000' if luminance > 0.55 else '#ffffff'


def rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert hex → rgba(r,g,b,a) string."""
    h = hex_color.lstrip('#')
    if len(h) != 6:
        return f'rgba(99,102,241,{alpha})'
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


# ─────────────────────────────────────────────────────────
#  Theme presets
# ─────────────────────────────────────────────────────────
THEME_PRESETS: dict[str, dict | None] = {
    "🌑 Dark Navy":   dict(kpi_bg="#1e293b", sb0="#0f172a", sb1="#1e293b",
                           a1="#6366f1", a2="#10b981", a3="#f59e0b",
                           a4="#3b82f6", a5="#ef4444", a6="#8b5cf6"),
    "🟣 Deep Purple": dict(kpi_bg="#2e1065", sb0="#1e1b4b", sb1="#2e1065",
                           a1="#a78bfa", a2="#34d399", a3="#fbbf24",
                           a4="#60a5fa", a5="#f87171", a6="#c084fc"),
    "🌊 Ocean Teal":  dict(kpi_bg="#0c4a6e", sb0="#0a2540", sb1="#0c4a6e",
                           a1="#38bdf8", a2="#34d399", a3="#fbbf24",
                           a4="#818cf8", a5="#f87171", a6="#a78bfa"),
    "🌲 Forest":      dict(kpi_bg="#14532d", sb0="#052e16", sb1="#14532d",
                           a1="#4ade80", a2="#fbbf24", a3="#fb923c",
                           a4="#60a5fa", a5="#f87171", a6="#c084fc"),
    "🌅 Warm Slate":  dict(kpi_bg="#292524", sb0="#1c1917", sb1="#292524",
                           a1="#fb923c", a2="#4ade80", a3="#fbbf24",
                           a4="#60a5fa", a5="#f87171", a6="#a78bfa"),
    "☀️ Custom":      None,   # populated at runtime from colour pickers
}
_DEFAULT_THEME = list(THEME_PRESETS.values())[0]


def get_theme() -> dict:
    return st.session_state.get("active_theme", _DEFAULT_THEME)


# ─────────────────────────────────────────────────────────
#  Dynamic CSS — all text colours auto-computed from bg
# ─────────────────────────────────────────────────────────
def inject_css() -> None:
    t   = get_theme()
    bg  = t["kpi_bg"]
    fg  = get_contrast_color(bg)          # ← white or black, chosen automatically
    lbl = rgba(fg, 0.65)
    sub = rgba(fg, 0.45)
    a1  = t["a1"]

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;}}

[data-testid="stSidebar"]{{
    background:linear-gradient(180deg,{t['sb0']} 0%,{t['sb1']} 100%);
}}
[data-testid="stSidebar"] *{{color:#e2e8f0 !important;}}
[data-testid="stSidebar"] .stRadio label{{font-size:15px !important;}}
[data-testid="stAppViewContainer"]{{background:#f1f5f9;}}

/* KPI card — text is always readable regardless of background */
.kpi-card{{
    background:{bg};border-radius:14px;padding:20px 24px;
    box-shadow:0 4px 20px rgba(0,0,0,.15);
    border-left:4px solid var(--accent);transition:transform .2s;
}}
.kpi-card:hover{{transform:translateY(-3px);}}
.kpi-label{{font-size:13px;color:{lbl};font-weight:500;margin-bottom:6px;}}
.kpi-value{{font-size:28px;font-weight:700;letter-spacing:-.5px;color:{fg};}}
.kpi-sub  {{font-size:12px;color:{sub};margin-top:4px;}}

.section-header{{
    font-size:20px;font-weight:700;color:#1e293b;
    padding-bottom:8px;border-bottom:3px solid {a1};margin-bottom:18px;
}}
[data-testid="stDataFrame"]{{border-radius:10px;overflow:hidden;}}

.badge-red   {{background:#fee2e2;color:#dc2626;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;}}
.badge-orange{{background:#ffedd5;color:#ea580c;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;}}
.badge-yellow{{background:#fef9c3;color:#ca8a04;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;}}
.badge-green {{background:#dcfce7;color:#16a34a;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;}}
.msg-success {{background:#dcfce7;color:#166534;padding:12px 18px;border-radius:10px;font-weight:500;}}
.msg-error   {{background:#fee2e2;color:#991b1b;padding:12px 18px;border-radius:10px;font-weight:500;}}
.form-card   {{background:#fff;border-radius:14px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,.08);}}
.js-plotly-plot{{border-radius:12px !important;}}

/* Live swatch shown in Settings colour picker */
.color-swatch{{
    display:inline-flex;align-items:center;justify-content:center;
    gap:8px;padding:10px 18px;border-radius:10px;
    font-weight:600;font-size:14px;margin-top:6px;
    width:100%;box-shadow:0 2px 8px rgba(0,0,0,.15);
}}
</style>
""", unsafe_allow_html=True)


inject_css()

# ─────────────────────────────────────────────────────────
#  Auto-refresh meta tag (configured in Settings)
# ─────────────────────────────────────────────────────────
if st.session_state.get("auto_refresh_enabled", False):
    ivl = st.session_state.get("auto_refresh_secs", 60)
    st.markdown(f'<meta http-equiv="refresh" content="{ivl}">', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
#  DB init & constants
# ─────────────────────────────────────────────────────────
db.init_db()

SERVICE_CATEGORIES = [
    "Income Tax Filing", "GST Registration", "GST Return Filing",
    "Company Incorporation", "ROC Compliance", "Audit Services",
    "Financial Planning", "Investment Advisory", "Loan Consultation", "Other",
]

# ─────────────────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="text-align:center;padding:16px 0 24px">
    <div style="font-size:36px">📊</div>
    <div style="font-size:18px;font-weight:700;color:#e2e8f0;margin-top:6px">CA Consulting</div>
    <div style="font-size:12px;color:#64748b;margin-top:2px">Management Dashboard</div>
</div>""", unsafe_allow_html=True)

    page = st.radio("Navigation", [
        "🏠 Dashboard", "➕ Add Customer", "👥 Customer Database",
        "📈 Analytics", "📅 Follow-up Reminders", "⚙️ Settings",
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown(
        f"<div style='font-size:11px;color:#475569;text-align:center'>"
        f"Last refreshed: {datetime.now().strftime('%d %b %Y %H:%M')}</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────
#  KPI card — text auto-contrasted against theme background
# ─────────────────────────────────────────────────────────
def kpi_card(label: str, value: str, sub: str = "", accent: str = "#6366f1") -> None:
    bg    = get_theme()["kpi_bg"]
    fg    = get_contrast_color(bg)
    lbl_c = rgba(fg, 0.65)
    sub_c = rgba(fg, 0.45)
    st.markdown(
        f"""<div class="kpi-card" style="--accent:{accent}">
            <div class="kpi-label" style="color:{lbl_c}">{label}</div>
            <div class="kpi-value" style="color:{fg}">{value}</div>
            {"<div class='kpi-sub' style='color:"+sub_c+"'>"+sub+"</div>" if sub else ""}
        </div>""",
        unsafe_allow_html=True,
    )


def accent_map() -> dict[str, str]:
    """KPI accent colours sourced from the active theme."""
    t = get_theme()
    return {
        "Total Customers":     t["a1"],
        "Total Revenue":       t["a2"],
        "Pending Amount":      t["a3"],
        "Paid Clients":        t["a4"],
        "Pending Clients":     t["a5"],
        "Upcoming Follow-ups": t["a6"],
    }


# ─────────────────────────────────────────────────────────
#  PAGE: Dashboard
# ─────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.markdown('<div class="section-header">🏠 Dashboard Overview</div>', unsafe_allow_html=True)
    stats = db.get_dashboard_stats()
    AM    = accent_map()

    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Total Customers",         str(stats["total_customers"]),       "All registered clients",    AM["Total Customers"])
    with c2: kpi_card("Total Revenue Collected",  utils.fmt_inr(stats["total_revenue"]), "From paid invoices",     AM["Total Revenue"])
    with c3: kpi_card("Pending Amount",           utils.fmt_inr(stats["pending_amount"]), "Awaiting payment",     AM["Pending Amount"])

    st.markdown("<div style='margin-top:16px'/>", unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3)
    with c4: kpi_card("Paid Clients",         str(stats["paid_count"]),        "Payments received",         AM["Paid Clients"])
    with c5: kpi_card("Pending Clients",      str(stats["pending_count"]),     "Payments outstanding",      AM["Pending Clients"])
    with c6: kpi_card("Upcoming Follow-ups",  str(stats["upcoming_followups"]), "Scheduled from today",     AM["Upcoming Follow-ups"])

    st.markdown("<div style='margin-top:28px'/>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown('<div class="section-header">🕐 Recent Customers</div>', unsafe_allow_html=True)
        records = db.get_all_customers()
        if records:
            df_r = pd.DataFrame(records[:10])
            sc   = [c for c in ["customer_name","service_category","fee_amount","payment_status","follow_up_date"] if c in df_r.columns]
            st.dataframe(df_r[sc].rename(columns={
                "customer_name":"Customer","service_category":"Service",
                "fee_amount":"Fee (₹)","payment_status":"Status","follow_up_date":"Follow-up",
            }), use_container_width=True, hide_index=True)
        else:
            st.info("No customers yet. Add your first customer from '➕ Add Customer'.")

    with col_right:
        st.markdown('<div class="section-header">💳 Payment Split</div>', unsafe_allow_html=True)
        t = get_theme()
        if stats["paid_count"] + stats["pending_count"] > 0:
            fig_pie = go.Figure(data=[go.Pie(
                labels=["Paid","Pending"], values=[stats["paid_count"],stats["pending_count"]],
                hole=0.55, marker_colors=[t["a2"], t["a5"]], textinfo="percent+label",
            )])
            fig_pie.update_layout(margin=dict(t=10,b=10,l=10,r=10),
                paper_bgcolor="rgba(0,0,0,0)", showlegend=False, height=260)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No data yet.")

    due = utils.get_followup_due_customers(db.get_all_customers(), days_ahead=7)
    if due:
        st.markdown('<div class="section-header" style="margin-top:28px">⚠️ Upcoming Follow-ups (Next 7 Days)</div>', unsafe_allow_html=True)
        for r in due:
            badge = {"overdue":"badge-red","today":"badge-red","3_days":"badge-orange","7_days":"badge-yellow"}.get(r["_bucket"],"badge-green")
            st.markdown(
                f"""<div style="background:#fff;border-radius:10px;padding:14px 18px;margin-bottom:10px;
                    box-shadow:0 1px 6px rgba(0,0,0,.07);border-left:4px solid {get_theme()['a1']};
                    display:flex;justify-content:space-between;align-items:center">
                    <div><strong>{r['customer_name']}</strong>
                    <span style="color:#64748b;font-size:13px;margin-left:10px">{r['service_category']}</span></div>
                    <div><span class="{badge}">{utils.days_label(r['_days_left'])}</span>
                    <span style="color:#94a3b8;font-size:12px;margin-left:10px">{r['follow_up_date']}</span></div>
                </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
#  PAGE: Add Customer
# ─────────────────────────────────────────────────────────
elif page == "➕ Add Customer":
    st.markdown('<div class="section-header">➕ Add New Customer</div>', unsafe_allow_html=True)

    edit_id   = st.session_state.get("edit_customer_id")
    edit_data = db.get_customer_by_id(edit_id) if edit_id else None

    def v(field, default=""):
        return edit_data.get(field, default) if edit_data else default

    def parse_date(val):
        if val and isinstance(val, str):
            try: return datetime.strptime(val, "%Y-%m-%d").date()
            except: pass
        return None

    if edit_data:
        st.info(f"✏️ Editing record for **{edit_data['customer_name']}** (ID: {edit_id})")

    with st.form("customer_form", clear_on_submit=True):
        st.markdown("#### 👤 Customer Information")
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name *", value=v("customer_name"))
            email_address = st.text_input("Email Address *", value=v("email_address"))
        with col2:
            mobile_number = st.text_input("Mobile Number *", value=v("mobile_number"))
            company_name  = st.text_input("Company Name",    value=v("company_name"))

        st.markdown("#### 🗂️ Service Details")
        col3, col4 = st.columns(2)
        with col3:
            svc_idx          = SERVICE_CATEGORIES.index(v("service_category")) if v("service_category") in SERVICE_CATEGORIES else 0
            service_category = st.selectbox("Service Category *", SERVICE_CATEGORIES, index=svc_idx)
            consultation_date= st.date_input("Consultation Date", value=parse_date(v("consultation_date")) or date.today())
        with col4:
            service_description = st.text_area("Service Description", value=v("service_description"), height=100)

        st.markdown("#### 💰 Payment Details")
        col5, col6, col7 = st.columns(3)
        with col5:
            fee_amount = st.number_input("Fee Amount (₹) *", min_value=0.0, step=100.0, value=float(v("fee_amount", 0.0)))
        with col6:
            pay_opts       = ["Pending","Paid"]
            pay_idx        = pay_opts.index(v("payment_status")) if v("payment_status") in pay_opts else 0
            payment_status = st.selectbox("Payment Status", pay_opts, index=pay_idx)
        with col7:
            payment_date = st.date_input("Payment Date", value=parse_date(v("payment_date")) if v("payment_date") else None)

        st.markdown("#### 📅 Follow-up & Remarks")
        col8, col9 = st.columns(2)
        with col8:
            follow_up_date = st.date_input("Follow-up Date", value=parse_date(v("follow_up_date")) if v("follow_up_date") else None)
        with col9:
            remarks = st.text_area("Remarks", value=v("remarks"), height=100)

        submitted = st.form_submit_button(
            "💾 Update Customer" if edit_data else "✅ Save Customer",
            use_container_width=True, type="primary",
        )

        if submitted:
            errors = []
            if not customer_name.strip(): errors.append("Customer Name is required.")
            if not mobile_number.strip(): errors.append("Mobile Number is required.")
            if not email_address.strip(): errors.append("Email Address is required.")

            if errors:
                for e in errors: st.error(e)
            else:
                payload = dict(
                    customer_name=customer_name.strip(), mobile_number=mobile_number.strip(),
                    email_address=email_address.strip(), company_name=company_name.strip(),
                    service_category=service_category, service_description=service_description.strip(),
                    consultation_date=str(consultation_date), fee_amount=fee_amount,
                    payment_status=payment_status,
                    payment_date=str(payment_date) if payment_date else "",
                    follow_up_date=str(follow_up_date) if follow_up_date else "",
                    remarks=remarks.strip(),
                )
                if edit_data:
                    db.update_customer(edit_id, payload)
                    st.session_state.pop("edit_customer_id", None)
                    st.success(f"✅ Customer **{customer_name}** updated successfully!")
                else:
                    new_id = db.add_customer(payload)
                    st.success(f"✅ Customer **{customer_name}** added! (ID: {new_id})")
                st.rerun()   # ← auto-rerun: clears form & reflects new data immediately


# ─────────────────────────────────────────────────────────
#  PAGE: Customer Database
# ─────────────────────────────────────────────────────────
elif page == "👥 Customer Database":
    st.markdown('<div class="section-header">👥 Customer Database</div>', unsafe_allow_html=True)

    # Widgets outside any form → every change auto-triggers a Streamlit rerun
    col_s, col_f1, col_f2 = st.columns([3, 2, 2])
    with col_s:
        search_q = st.text_input("🔍 Search by name, email, company, service…", placeholder="Type to search")
    with col_f1:
        filter_service = st.selectbox("Filter by Service", ["All"] + SERVICE_CATEGORIES)
    with col_f2:
        filter_status  = st.selectbox("Filter by Payment Status", ["All", "Paid", "Pending"])

    records = db.search_customers(search_q) if search_q else db.get_all_customers()
    if filter_service != "All": records = [r for r in records if r["service_category"] == filter_service]
    if filter_status  != "All": records = [r for r in records if r["payment_status"]   == filter_status]

    col_info, col_btn = st.columns([4, 1])
    with col_info:
        st.markdown(f"**{len(records)}** record(s) found")
    with col_btn:
        if records:
            st.download_button("📥 Export Excel",
                data=utils.export_to_excel(records),
                file_name=f"ca_customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)

    if records:
        df = pd.DataFrame(records)
        dc = [c for c in ["id","customer_name","mobile_number","email_address",
              "company_name","service_category","fee_amount","payment_status","follow_up_date"] if c in df.columns]
        st.dataframe(df[dc].rename(columns={
            "id":"ID","customer_name":"Customer Name","mobile_number":"Mobile",
            "email_address":"Email","company_name":"Company","service_category":"Service",
            "fee_amount":"Fee (₹)","payment_status":"Status","follow_up_date":"Follow-up",
        }), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### ✏️ Edit or Delete a Record")
        col_e1, col_e2, col_e3 = st.columns([2, 1, 1])
        with col_e1:
            ids   = [r["id"] for r in records]
            names = [f"#{r['id']} – {r['customer_name']}" for r in records]
            sel   = st.selectbox("Select customer", names)
            sel_id= ids[names.index(sel)]
        with col_e2:
            if st.button("✏️ Edit", use_container_width=True):
                st.session_state["edit_customer_id"] = sel_id
                st.info("Switch to '➕ Add Customer' to edit.")
        with col_e3:
            if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
                db.delete_customer(sel_id)
                st.success(f"Deleted record #{sel_id}")
                st.rerun()   # ← table refreshes instantly
    else:
        st.info("No records match your filters.")


# ─────────────────────────────────────────────────────────
#  PAGE: Analytics
# ─────────────────────────────────────────────────────────
elif page == "📈 Analytics":
    st.markdown('<div class="section-header">📈 Revenue & Service Analytics</div>', unsafe_allow_html=True)
    service_data = db.get_service_revenue()
    monthly_data = db.get_monthly_revenue()
    all_records  = db.get_all_customers()
    t = get_theme()

    if not all_records:
        st.info("No data yet. Add customers to see analytics.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Revenue by Service Category")
            if service_data:
                df_svc  = pd.DataFrame(service_data)
                fig_bar = px.bar(df_svc, x="service_category",
                    y=["paid_revenue","pending_revenue"],
                    labels={"value":"Amount (₹)","variable":"Status","service_category":"Service"},
                    color_discrete_map={"paid_revenue": t["a2"], "pending_revenue": t["a5"]},
                    barmode="stack", text_auto=True)
                fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_tickangle=-30, legend=dict(title="",orientation="h",y=1.12),
                    margin=dict(t=30,b=60), height=350)
                fig_bar.update_traces(texttemplate="₹%{y:,.0f}", textposition="inside")
                st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.markdown("##### Client Count by Service")
            if service_data:
                df_svc    = pd.DataFrame(service_data)
                fig_donut = px.pie(df_svc, names="service_category", values="count", hole=0.5,
                    color_discrete_sequence=px.colors.qualitative.Vivid)
                fig_donut.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=20,b=20), height=350, legend=dict(font=dict(size=11)))
                st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("##### Monthly Revenue Trend")
        if monthly_data:
            df_monthly = pd.DataFrame(monthly_data)
            fig_line   = px.area(df_monthly, x="month", y="revenue", markers=True,
                labels={"month":"Month","revenue":"Revenue (₹)"},
                color_discrete_sequence=[t["a1"]])
            fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor="#e2e8f0"),
                margin=dict(t=20,b=20), height=300)
            fig_line.update_traces(fill="tozeroy", fillcolor=rgba(t["a1"], 0.15))
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Add consultation dates to see monthly trends.")

        st.markdown("##### Service-wise Revenue Summary")
        if service_data:
            df_tbl = pd.DataFrame(service_data).rename(columns={
                "service_category":"Service","count":"Clients",
                "revenue":"Total (₹)","paid_revenue":"Paid (₹)","pending_revenue":"Pending (₹)",
            })
            for col in ["Total (₹)","Paid (₹)","Pending (₹)"]:
                df_tbl[col] = df_tbl[col].map(lambda x: f"₹{x:,.0f}")
            st.dataframe(df_tbl, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────
#  PAGE: Follow-up Reminders
# ─────────────────────────────────────────────────────────
elif page == "📅 Follow-up Reminders":
    st.markdown('<div class="section-header">📅 Follow-up Reminders</div>', unsafe_allow_html=True)
    all_records = db.get_all_customers()
    due = utils.get_followup_due_customers(all_records, days_ahead=30)

    if not due:
        st.success("🎉 No follow-ups due in the next 30 days.")
    else:
        bucket_labels = {
            "overdue": ("🔴 Overdue",          "badge-red"),
            "today":   ("🔴 Due Today",         "badge-red"),
            "3_days":  ("🟠 Due in 1–3 Days",   "badge-orange"),
            "7_days":  ("🟡 Due in 4–7 Days",   "badge-yellow"),
        }
        from collections import defaultdict
        grouped = defaultdict(list)
        for r in due: grouped[r["_bucket"]].append(r)

        for bk in ["overdue","today","3_days","7_days"]:
            items = grouped.get(bk, [])
            if not items: continue
            label, badge = bucket_labels[bk]
            st.markdown(f"### {label}")
            for r in items:
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    with c1: st.markdown(f"**{r['customer_name']}**  \n*{r['company_name'] or '–'}*")
                    with c2: st.markdown(f"📧 {r['email_address']}  \n📱 {r['mobile_number']}")
                    with c3: st.markdown(f"🗂️ {r['service_category']}  \n📅 {r['follow_up_date']}")
                    with c4: st.markdown(f'<span class="{badge}">{utils.days_label(r["_days_left"])}</span>', unsafe_allow_html=True)
                st.markdown("---")

    st.markdown('<div class="section-header" style="margin-top:28px">📧 Send Email Reminders</div>', unsafe_allow_html=True)
    smtp_cfg = st.session_state.get("smtp_config", {})
    if not smtp_cfg:
        st.warning("⚙️ Configure email settings in the **Settings** page first.")
    else:
        if not due:
            st.info("No upcoming follow-ups to send reminders for.")
        else:
            options       = [f"#{r['id']} – {r['customer_name']} ({r['follow_up_date']})" for r in due]
            selected_opts = st.multiselect("Select customers", options, default=options[:1])
            if st.button("📨 Send Selected Reminders", type="primary"):
                for opt in selected_opts:
                    rid = int(opt.split("–")[0].replace("#","").strip())
                    rec = next((r for r in due if r["id"] == rid), None)
                    if rec:
                        ok, msg = utils.send_followup_email(
                            smtp_host=smtp_cfg["host"], smtp_port=smtp_cfg["port"],
                            sender_email=smtp_cfg["email"], sender_password=smtp_cfg["password"],
                            recipient_email=smtp_cfg["email"],
                            customer_name=rec["customer_name"], service_category=rec["service_category"],
                            follow_up_date=rec["follow_up_date"], ca_name=smtp_cfg.get("ca_name","CA"),
                        )
                        if ok: st.success(f"✅ Reminder sent for {rec['customer_name']}")
                        else:  st.error(f"❌ Failed for {rec['customer_name']}: {msg}")


# ─────────────────────────────────────────────────────────
#  PAGE: Settings
# ─────────────────────────────────────────────────────────
elif page == "⚙️ Settings":
    st.markdown('<div class="section-header">⚙️ Settings</div>', unsafe_allow_html=True)

    # ── 🎨 Colour Theme ──────────────────────────────────────────────────────
    st.markdown("#### 🎨 Colour Theme")
    st.caption("Text contrast is computed automatically — no manual colour pairing needed.")

    preset_names = list(THEME_PRESETS.keys())
    cur_preset   = st.session_state.get("selected_preset_name", preset_names[0])
    sel_preset   = st.selectbox("Theme Preset", preset_names,
                                index=preset_names.index(cur_preset) if cur_preset in preset_names else 0)

    if sel_preset == "☀️ Custom":
        st.markdown("**Pick your colours — auto-contrast text previews update live as you choose:**")
        col_cp1, col_cp2 = st.columns(2)

        with col_cp1:
            st.markdown("**KPI Card Background**")
            bg_pick = st.color_picker("Background colour", value=st.session_state.get("custom_bg", "#1e293b"), key="cp_bg")
            fg_pick = get_contrast_color(bg_pick)   # ← computed on every widget change
            st.markdown(
                f'<div class="color-swatch" style="background:{bg_pick};color:{fg_pick}">'
                f'Auto text → {fg_pick} &nbsp;|&nbsp; BG: {bg_pick}</div>',
                unsafe_allow_html=True,
            )

        with col_cp2:
            st.markdown("**Primary Accent / Border colour**")
            ac_pick = st.color_picker("Accent colour", value=st.session_state.get("custom_accent", "#6366f1"), key="cp_accent")
            fg_ac   = get_contrast_color(ac_pick)   # ← computed on every widget change
            st.markdown(
                f'<div class="color-swatch" style="background:{ac_pick};color:{fg_ac}">'
                f'Auto text → {fg_ac} &nbsp;|&nbsp; Accent: {ac_pick}</div>',
                unsafe_allow_html=True,
            )

        if st.button("✅ Apply Custom Theme", type="primary"):
            st.session_state["active_theme"] = dict(
                kpi_bg=bg_pick, sb0="#1c1917", sb1=bg_pick,
                a1=ac_pick, a2="#10b981", a3="#f59e0b",
                a4="#3b82f6", a5="#ef4444", a6="#8b5cf6",
            )
            st.session_state["selected_preset_name"] = "☀️ Custom"
            st.session_state["custom_bg"]     = bg_pick
            st.session_state["custom_accent"] = ac_pick
            st.rerun()   # ← theme applied instantly across whole app

    else:
        preview = THEME_PRESETS[sel_preset]
        if preview:
            fg_prev = get_contrast_color(preview["kpi_bg"])
            st.markdown(
                f'<div class="color-swatch" style="background:{preview["kpi_bg"]};'
                f'color:{fg_prev};border-left:6px solid {preview["a1"]}">'
                f'Preview — auto text: {fg_prev} &nbsp;|&nbsp; BG: {preview["kpi_bg"]}</div>',
                unsafe_allow_html=True,
            )
        if st.button("✅ Apply Theme", type="primary"):
            st.session_state["active_theme"]         = THEME_PRESETS[sel_preset]
            st.session_state["selected_preset_name"] = sel_preset
            st.rerun()   # ← whole app re-renders with new theme immediately

    st.markdown("---")

    # ── 🔄 Auto-Refresh ──────────────────────────────────────────────────────
    st.markdown("#### 🔄 Auto-Refresh")
    st.caption("Keeps Dashboard KPIs current without manual page reload.")

    col_ar1, col_ar2 = st.columns([1, 2])
    with col_ar1:
        ar_enabled = st.toggle("Enable Auto-Refresh",
                               value=st.session_state.get("auto_refresh_enabled", False))
    with col_ar2:
        ar_secs = st.slider("Refresh interval (seconds)", 15, 300,
                            value=st.session_state.get("auto_refresh_secs", 60),
                            step=15, disabled=not ar_enabled)

    if st.button("💾 Save Auto-Refresh Settings"):
        st.session_state["auto_refresh_enabled"] = ar_enabled
        st.session_state["auto_refresh_secs"]    = ar_secs
        status = f"every {ar_secs}s" if ar_enabled else "disabled"
        st.success(f"✅ Auto-refresh {status}.")
        st.rerun()

    st.markdown("---")

    # ── 📧 Email / SMTP ───────────────────────────────────────────────────────
    st.markdown("#### 📧 Email / SMTP Configuration")
    st.markdown("> For Gmail use an **App Password** — not your regular password.")

    cfg = st.session_state.get("smtp_config", {})
    with st.form("smtp_form"):
        ca_name    = st.text_input("Your Name / CA Firm Name", value=cfg.get("ca_name",""))
        smtp_email = st.text_input("Sender Email Address",     value=cfg.get("email",""))
        smtp_pwd   = st.text_input("App Password",             value=cfg.get("password",""), type="password")
        smtp_host  = st.text_input("SMTP Host",                value=cfg.get("host","smtp.gmail.com"))
        smtp_port  = st.number_input("SMTP Port",              value=int(cfg.get("port",465)), step=1)
        if st.form_submit_button("💾 Save Email Settings", type="primary"):
            st.session_state["smtp_config"] = dict(
                ca_name=ca_name, email=smtp_email, password=smtp_pwd,
                host=smtp_host, port=smtp_port,
            )
            st.success("✅ Email settings saved for this session.")

    st.markdown("---")

    # ── 🗄️ Database ───────────────────────────────────────────────────────────
    st.markdown("#### 🗄️ Database Management")
    col_db1, col_db2 = st.columns(2)
    with col_db1:
        all_r = db.get_all_customers()
        if all_r:
            st.download_button("📥 Download Full Backup (Excel)",
                data=utils.export_to_excel(all_r),
                file_name=f"ca_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        else:
            st.info("No data to export yet.")
    with col_db2:
        st.markdown("<div style='background:#fff3cd;color:#856404;padding:12px;border-radius:8px;font-size:13px'>"
                    "⚠️ Database: <code>ca_consulting.db</code> — stored in the app folder.</div>",
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### ℹ️ About")
    st.markdown("""
| Field | Value |
|---|---|
| **App** | CA Consulting Management Dashboard |
| **Version** | 1.1.0 |
| **Stack** | Streamlit · SQLite · Plotly · Pandas |
| **Database** | `ca_consulting.db` (local SQLite) |
| **New in 1.1** | Auto-contrast text · 5 theme presets · Live colour picker · Auto-refresh · Auto-rerun on every save/change |
""")
