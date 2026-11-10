# CA Consulting Management Dashboard

A lightweight, local management workspace built with **Streamlit** for Chartered Accountants and financial consultants. This application provides real-time client tracking, core financial metrics, and follow-up schedules from a single interface.

<iframe width="560" height="315" src="https://www.youtube.com/embed/OEZ5bCCjgPM?si=ZdMrlmGThFXqzXVc" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## 📊 Features

### 1. Key Performance Indicators (KPIs)
*   **Total Customers:** Tracks the total number of onboarding clients.
*   **Total Revenue Collected:** Displays aggregate revenue from paid invoices.
*   **Pending Amount:** Highlights outstanding receivables.
*   **Status Tally:** Live counters for Paid Clients, Pending Clients, and Upcoming Follow-ups.

### 2. Sidebar Navigation
*   **Dashboard:** Main operational center tracking active KPIs and recent logs.
*   **Add Customer:** Digital onboarding form to register new client profiles.
*   **Customer Database:** Searchable directory containing all historical records.
*   **Analytics:** Dedicated panels mapping business health and financial insights.
*   **Follow-up Reminders:** Calendar-linked timeline tracking client engagement deadlines.
*   **Settings:** Access panels for profile updates and system configurations.

### 3. Recent Customers Ledger
*   **Service Logs:** Displays client details matched with explicit assignments (e.g., Financial Planning, GST Return Filing, Company Incorporation).
*   **Status Tags:** Visually labels the payment and progress state of individual jobs.
*   **Timeline Metrics:** Links clear target calendar dates to proactive reminder markers.

### 4. Interactive Data Visualizations
*   **Payment Split Breakdown:** Integrates dynamic chart elements to illustrate the percentage ratio of completed collections against pending accounts receivable.

---

## 🛠️ Tech Stack
*   **Framework:** Streamlit (Local Host UI)
*   **Core Logic:** Python 3.8+
*   **Data Processing:** Pandas, NumPy
*   **Charts:** Plotly / Matplotlib

---

## 🚀 Getting Started

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com
   cd ca-dashboard
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Execution
Launch the interface locally via your terminal application:
```bash
streamlit run app.py
```
Once deployed, open your web browser and navigate to: **`http://localhost:8501`**
