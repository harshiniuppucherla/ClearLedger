# ClearLedger — AI Finance Controller

ClearLedger is an AI-assisted financial reconciliation and audit platform designed to help businesses identify transaction exceptions, investigate discrepancies, prepare dispute messages, and maintain financial close audit records.

## 🚀 Features

* 📊 Financial reconciliation dashboard
* 🔍 Automatic exception detection
* 🤖 AI-assisted exception investigation
* 💳 Transaction reconciliation
* 📝 Evidence-backed dispute draft generation
* 📁 Upload and process financial data
* 🧾 Financial close audit reports
* 🔎 Search audit reports by date
* 📥 Download audit and dispute records
* 🧪 Demo data for testing different reconciliation scenarios

## 🏗️ Project Structure

```text
ClearLedger/
│
├── app.py
├── reconciliation.py
├── ai_controller.py
├── requirements.txt
├── README.md
└── .gitignore
```

### `app.py`

Main Streamlit application containing the user interface and application workflow.

### `reconciliation.py`

Handles financial data validation, normalization, reconciliation, exception detection, and audit report generation.Contains sample/demo financial data used for testing and demonstrating the application.

### `ai_controller.py`

Handles AI-assisted exception investigation and evidence-backed dispute draft generation.

## 🛠️ Tech Stack

* Python
* Streamlit
* Pandas
* Numpy
* Altair
* OpenPyXL
* AI-assisted financial analysis

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/harshiniuppucherla/ClearLedger
cd ClearLedger
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## ▶️ Run Locally

Start the Streamlit application:

```bash
streamlit run app.py
```

The application will open in your browser.

## 📌 Workflow

```text
Financial Data
      ↓
Upload / Demo Data
      ↓
Data Validation
      ↓
Reconciliation
      ↓
Exception Detection
      ↓
AI Investigation
      ↓
Dispute Generation
      ↓
Review / Hold
      ↓
Financial Close Audit
```

## 🎯 Use Cases

ClearLedger can be used to assist finance teams with:

* Payment reconciliation
* Bank-to-ledger reconciliation
* Identifying transaction mismatches
* Investigating financial exceptions
* Preparing dispute documentation
* Maintaining audit evidence
* Financial close monitoring

## 🔐 Security

Do not commit API keys, passwords, credentials, or other secrets to GitHub.

For deployment, sensitive configuration should be stored using the deployment platform's secret-management functionality.

## ☁️ Deployment

ClearLedger can be deployed using Streamlit Community Cloud.

The main application entry point is:

```text
app.py
```

## 👩‍💻 Author
HARSHINI UPPUCHERLA
