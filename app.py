import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

from reconciliation import (
    REQUIRED_COLUMNS,
    generate_demo_data,
    validate_and_normalize,
    read_uploaded_file,
    run_reconciliation,
    build_audit_report,
)

from ai_controller import (
    investigate_exception,
    generate_dispute_draft,
)


st.set_page_config(
    page_title="ClearLedger",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .stApp {
        background: #f8f9fc;
        color: #202033;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
        max-width: 1500px;
    }

    h1, h2, h3 {
        color: #211B38 !important;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #eee9ff 0%,
            #e8e1ff 55%,
            #ded5ff 100%
        );
        border-right: 1px solid #d3c8f7;
    }

    .brand {
        padding: 8px 10px 20px 10px;
    }

    .brand-icon {
        width: 42px;
        height: 42px;
        background: #6d4aff;
        color: white;
        border-radius: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 21px;
        font-weight: 800;
        margin-right: 10px;
        vertical-align: middle;
    }

    .brand-name {
        display: inline-block;
        vertical-align: middle;
        font-size: 21px;
        font-weight: 800;
        color: #211b38;
    }

    .brand-subtitle {
        margin-left: 54px;
        margin-top: -6px;
        font-size: 11px;
        color: #766d91;
    }

    .hero {
        background: linear-gradient(
            135deg,
            #f2efff 0%,
            #faf9ff 60%,
            #ffffff 100%
        );
        border: 1px solid #e2dcf7;
        border-radius: 20px;
        padding: 25px 28px;
        margin-bottom: 22px;
    }

    .hero-title {
        font-size: 30px;
        font-weight: 800;
        color: #211b38;
        margin-bottom: 5px;
    }

    .hero-text {
        color: #716a80;
        font-size: 14px;
        line-height: 1.6;
    }

    .metric-card {
        background: white;
        border: 1px solid #e7e4ee;
        border-radius: 16px;
        padding: 18px;
        min-height: 115px;
        box-shadow: 0 5px 18px rgba(40, 31, 75, 0.05);
    }

    .metric-label {
        color: #7b748c;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .metric-value {
        color: #211b38;
        font-size: 27px;
        font-weight: 800;
    }

    .metric-caption {
        color: #8a839a;
        font-size: 11px;
        margin-top: 5px;
    }

    .status-green {
        background: #ecfdf3;
        color: #087443;
        border: 1px solid #b7e8cb;
        border-radius: 12px;
        padding: 12px 15px;
        font-weight: 700;
    }

    .status-orange {
        background: #fff8e7;
        color: #a56a00;
        border: 1px solid #f2d899;
        border-radius: 12px;
        padding: 12px 15px;
        font-weight: 700;
    }

    .status-red {
        background: #fff0f1;
        color: #b4232c;
        border: 1px solid #f3c2c6;
        border-radius: 12px;
        padding: 12px 15px;
        font-weight: 700;
    }

    .case-header {
        background: white;
        border: 1px solid #e5e1ee;
        border-radius: 14px;
        padding: 17px;
        margin-top: 12px;
        margin-bottom: 12px;
    }

    .ai-card {
        background: #faf8ff;
        border: 1px solid #ddd4ff;
        border-radius: 16px;
        padding: 22px;
        line-height: 1.45;
        color: #383248;
        white-space: normal;
        overflow-wrap: anywhere;
        word-break: normal;
    }

    .ai-heading {
        color: #211b38;
        font-weight: 800;
        margin-top: 12px;
        margin-bottom: 4px;
    }

    .ai-heading:first-child {
        margin-top: 0;
    }

    .ai-line {
        margin: 2px 0;
        overflow-wrap: anywhere;
    }

    .info-card {
        background: white;
        border: 1px solid #e5e1ee;
        border-radius: 14px;
        padding: 18px;
    }

    .dispute-card {
        background: #ffffff;
        border: 1px solid #ddd4ff;
        border-radius: 16px;
        padding: 22px;
        line-height: 1.55;
        color: #383248;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        word-break: normal;
        max-height: none;
        overflow: visible;
    }

    .dispute-heading {
        color: #211b38;
        font-weight: 800;
        margin-top: 12px;
        margin-bottom: 5px;
    }

    .dispute-heading:first-child {
        margin-top: 0;
    }

    .dispute-line {
        margin: 3px 0;
        overflow-wrap: anywhere;
    }

    [data-testid="stFileUploader"] {
        border: 1.5px dashed #bbaef0;
        border-radius: 15px;
        background: #faf9ff;
    }

    .stButton > button {
        border-radius: 10px;
        min-height: 42px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


DEFAULTS = {
    "page": "Dashboard",
    "demo_enabled": False,
    "razorpay_df": None,
    "bank_df": None,
    "ledger_df": None,
    "results": None,
    "investigations": {},
    "dispute_drafts": {},
    "audit_df": None,
    "last_run": None,
    "uploaded_files_audit": [],
    "uploaded_file_signatures": set(),
    "reviewed_disputes": [],
    "hold_disputes": [],
    "audit_reports": [],
    "upload_validation": {
        "razorpay": False,
        "bank": False,
        "ledger": False,
    },
}


for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def clear_financial_data():
    st.session_state.razorpay_df = None
    st.session_state.bank_df = None
    st.session_state.ledger_df = None
    st.session_state.results = None
    st.session_state.investigations = {}
    st.session_state.dispute_drafts = {}
    st.session_state.audit_df = None
    st.session_state.last_run = None

    st.session_state.upload_validation = {
        "razorpay": False,
        "bank": False,
        "ledger": False,
    }

    # Remove all Demo Data audit reports when Demo Data is disabled.
    # Uploaded-data audit reports are preserved.
    st.session_state.audit_reports = [
        audit_record
        for audit_record in st.session_state.audit_reports
        if audit_record.get("data_source") != "demo"
    ]


def load_demo_data():
    (
        st.session_state.razorpay_df,
        st.session_state.bank_df,
        st.session_state.ledger_df,
    ) = generate_demo_data()

    st.session_state.upload_validation = {
        "razorpay": True,
        "bank": True,
        "ledger": True,
    }

    st.session_state.results = None
    st.session_state.investigations = {}
    st.session_state.dispute_drafts = {}
    st.session_state.audit_df = None
    st.session_state.last_run = None


def record_uploaded_file(
    source,
    uploaded_file,
):
    if uploaded_file is None:
        return

    signature = (
        source,
        uploaded_file.name,
        uploaded_file.size,
    )

    if signature in st.session_state.uploaded_file_signatures:
        return

    st.session_state.uploaded_file_signatures.add(
        signature
    )

    st.session_state.uploaded_files_audit.append(
        {
            "Timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "Source": source.title(),
            "File Name": uploaded_file.name,
            "File Type": (
                uploaded_file.name
                .split(".")[-1]
                .upper()
            ),
            "File Size": f"{uploaded_file.size:,} bytes",
        }
    )


def hero(title, subtitle):
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-title">{title}</div>
            <div class="hero-text">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric(label, value, caption=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def data_available():
    return (
        st.session_state.razorpay_df is not None
        and st.session_state.bank_df is not None
        and st.session_state.ledger_df is not None
        and st.session_state.upload_validation.get(
            "razorpay",
            False,
        )
        and st.session_state.upload_validation.get(
            "bank",
            False,
        )
        and st.session_state.upload_validation.get(
            "ledger",
            False,
        )
    )


def format_ai_investigation(text):
    if not text:
        return "No AI explanation was returned."

    text = str(text).strip()

    headings = [
        "ROOT CAUSE",
        "EVIDENCE",
        "FINANCIAL INTERPRETATION",
        "CONFIDENCE",
        "RECOMMENDED ACTION",
    ]

    for heading in headings:
        text = text.replace(
            f"\n{heading}\n",
            f"\n|||{heading}|||\n",
        )

        if text.startswith(heading + "\n"):
            text = text.replace(
                heading + "\n",
                f"|||{heading}|||\n",
                1,
            )

    sections = text.split("|||")
    html_parts = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        if section.endswith("|||"):
            heading = section[:-3].strip()

            if heading in headings:
                html_parts.append(
                    f'<div class="ai-heading">{heading}</div>'
                )
                continue

        lines = section.splitlines()

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if line in headings:
                html_parts.append(
                    f'<div class="ai-heading">{line}</div>'
                )
            else:
                html_parts.append(
                    f'<div class="ai-line">{line}</div>'
                )

    return "".join(html_parts)


def format_dispute_draft(text):
    if not text:
        return "No dispute draft was returned."

    text = str(text).strip()

    headings = [
        "SUBJECT",
        "CASE IDENTIFICATION",
        "DISCREPANCY",
        "VERIFIED EVIDENCE",
        "FINANCIAL IMPACT",
        "REQUEST FOR INVESTIGATION",
        "REQUEST FOR SUPPORTING DOCUMENTATION",
        "NEXT STEPS",
        "CLOSING",
    ]

    for heading in headings:
        text = text.replace(
            f"\n{heading}\n",
            f"\n|||{heading}|||\n",
        )

        if text.startswith(heading + "\n"):
            text = text.replace(
                heading + "\n",
                f"|||{heading}|||\n",
                1,
            )

    sections = text.split("|||")
    html_parts = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        if section.endswith("|||"):
            heading = section[:-3].strip()

            if heading in headings:
                html_parts.append(
                    f'<div class="dispute-heading">{heading}</div>'
                )
                continue

        lines = section.splitlines()

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if line in headings:
                html_parts.append(
                    f'<div class="dispute-heading">{line}</div>'
                )
            else:
                html_parts.append(
                    f'<div class="dispute-line">{line}</div>'
                )

    return "".join(html_parts)


with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            <span class="brand-icon">◈</span>
            <span class="brand-name">ClearLedger</span>
            <div class="brand-subtitle">AI Finance Controller</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    pages = [
        "Dashboard",
        "Upload & Close",
        "Exceptions",
        "Disputes & Audits",
    ]

    selected_page = st.radio(
        "Navigation",
        pages,
        index=pages.index(st.session_state.page),
        label_visibility="collapsed",
    )

    st.session_state.page = selected_page

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        "<div style='font-size:11px;color:#716987;font-weight:700;margin-bottom:8px;'>DATA ENVIRONMENT</div>",
        unsafe_allow_html=True,
    )

    demo_enabled = st.checkbox(
        "Demo Data",
        value=st.session_state.demo_enabled,
        key="demo_checkbox",
    )

    if demo_enabled != st.session_state.demo_enabled:

        st.session_state.demo_enabled = demo_enabled

        if demo_enabled:
            load_demo_data()
        else:
            clear_financial_data()

        st.rerun()

    if st.session_state.demo_enabled:

        st.success("Demo dataset active")

        if data_available():
            st.caption(
                f"{len(st.session_state.razorpay_df)} payment records loaded"
            )

    else:
        st.info("Upload your financial files to begin.")

    st.markdown("---")

    if st.session_state.results is not None:

        r = st.session_state.results

        st.markdown(
            "<div style='font-size:11px;color:#716987;font-weight:700;margin-bottom:8px;'>CURRENT CLOSE</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            f"Records: {r['total_records']}"
        )

        st.caption(
            f"Matched: {r['matched']}"
        )

        st.caption(
            f"Exceptions: {r['exceptions']}"
        )

        st.caption(
            f"Needs review: {r['needs_review']}"
        )


page = st.session_state.page


if page == "Dashboard":

    hero(
        "Finance Control Center",
        "Reconcile payment settlements, bank credits and merchant ledger records "
        "into a controlled financial close.",
    )

    if st.session_state.results is None:

        st.subheader("Ready for financial close")

        cols = st.columns(3)

        with cols[0]:
            metric(
                "Financial Sources",
                "3",
                "Razorpay, bank and ledger",
            )

        with cols[1]:
            metric(
                "Reconciliation",
                "Ready",
                "Deterministic financial checks",
            )

        with cols[2]:
            metric(
                "AI Controller",
                "Ready",
                "Evidence-based investigation",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if data_available():

            st.success(
                "All three financial sources are loaded. "
                "Open Upload & Close to execute the financial close."
            )

        else:

            st.info(
                "No financial close has been executed. "
                "Enable Demo Data or upload all three financial sources."
            )

    else:

        r = st.session_state.results

        st.subheader("Financial Close")

        cols = st.columns(5)

        with cols[0]:
            metric(
                "Records",
                f"{r['total_records']:,}",
                "Processed",
            )

        with cols[1]:
            metric(
                "Matched",
                f"{r['matched']:,}",
                "Exact financial matches",
            )

        with cols[2]:
            metric(
                "Exceptions",
                f"{r['exceptions']:,}",
                "Detected exceptions",
            )

        with cols[3]:
            metric(
                "Auto Resolved",
                f"{r['auto_resolved']:,}",
                "Rule-based resolution",
            )

        with cols[4]:
            metric(
                "Needs Review",
                f"{r['needs_review']:,}",
                "Human attention",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("Reconciliation Outcome")

        exceptions_df = r["exceptions_df"]

        if exceptions_df.empty:

            st.info("No exception categories were detected.")

        else:

            exception_chart_df = (
                exceptions_df[
                    "exception_type"
                ]
                .value_counts()
                .rename_axis("Exception Type")
                .reset_index(name="Records")
            )

            exception_colors = {
                "MISSING SETTLEMENT": "#ef5350",
                "FEE DISCREPANCY": "#ff9800",
                "TAX-LINE DISCREPANCY": "#9c6ade",
                "ROUNDING DIFFERENCE": "#26a69a",
                "CHARGEBACK ADJUSTMENT": "#42a5f5",
                "LEDGER MISMATCH": "#ec407a",
                "DUPLICATE": "#7e57c2",
                "SETTLEMENT DISCREPANCY": "#ab47bc",
            }

            all_exception_types = sorted(
                exception_chart_df[
                    "Exception Type"
                ].tolist()
            )

            color_range = [
                exception_colors.get(
                    exception_type,
                    "#7657F5",
                )
                for exception_type in all_exception_types
            ]

            chart = (
                alt.Chart(
                    exception_chart_df
                )
                .mark_bar(
                    cornerRadiusTopLeft=5,
                    cornerRadiusTopRight=5,
                )
                .encode(
                    x=alt.X(
                        "Exception Type:N",
                        sort=all_exception_types,
                        axis=alt.Axis(
                            labelAngle=-30,
                            title=None,
                        ),
                    ),
                    y=alt.Y(
                        "Records:Q",
                        title="Records",
                        scale=alt.Scale(
                            nice=True,
                            zero=True,
                        ),
                    ),
                    color=alt.Color(
                        "Exception Type:N",
                        scale=alt.Scale(
                            domain=all_exception_types,
                            range=color_range,
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "Exception Type:N",
                            title="Exception",
                        ),
                        alt.Tooltip(
                            "Records:Q",
                            title="Records",
                        ),
                    ],
                )
                .properties(
                    height=390,
                )
            )

            st.altair_chart(
                chart,
                use_container_width=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        cols = st.columns(3)

        with cols[0]:
            metric(
                "Match Rate",
                f"{r['match_rate']:.1f}%",
                "Exact matches",
            )

        with cols[1]:
            metric(
                "Exception Rate",
                f"{r['exception_rate']:.1f}%",
                "Records with exceptions",
            )

        with cols[2]:
            metric(
                "Straight Through",
                f"{r['straight_through_rate']:.1f}%",
                "Matched plus auto resolved",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if r["unresolved"] == 0:

            st.markdown(
                '<div class="status-green">Financial close complete. No unresolved exceptions remain.</div>',
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                f'<div class="status-orange">Financial close requires review. {r["unresolved"]} exception(s) require human attention.</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("Close Summary")

        summary = pd.DataFrame(
            {
                "Metric": [
                    "Records processed",
                    "Exact matches",
                    "Exceptions",
                    "Automatically resolved",
                    "Needs review",
                    "Unresolved",
                    "Amount reconciled",
                    "Amount in dispute",
                ],
                "Value": [
                    r["total_records"],
                    r["matched"],
                    r["exceptions"],
                    r["auto_resolved"],
                    r["needs_review"],
                    r["unresolved"],
                    f"₹{r['amount_reconciled']:,.2f}",
                    f"₹{r['amount_in_dispute']:,.2f}",
                ],
            }
        )

        st.dataframe(
            summary,
            hide_index=True,
            use_container_width=True,
        )


elif page == "Upload & Close":

    hero(
        "Upload & Financial Close",
        "Load the three financial sources, validate their structure and execute "
        "the reconciliation engine.",
    )

    if st.session_state.demo_enabled:

        st.subheader("Demo financial sources")

        cols = st.columns(3)

        with cols[0]:
            metric(
                "Razorpay",
                len(st.session_state.razorpay_df),
                "records loaded",
            )

        with cols[1]:
            metric(
                "Bank",
                len(st.session_state.bank_df),
                "records loaded",
            )

        with cols[2]:
            metric(
                "Ledger",
                len(st.session_state.ledger_df),
                "records loaded",
            )

        st.info(
            "Demo Data is currently enabled. Turn it off from the sidebar "
            "to upload your own CSV,PDF or Excel files."
        )

    else:

        st.subheader("Financial Sources")

        c1, c2, c3 = st.columns(3)

        with c1:

            razorpay_file = st.file_uploader(
                "Razorpay Settlement File",
                type=["csv", "pdf", "xlsx", "xls"],
                key="razorpay_upload",
            )

            if razorpay_file is not None:

                try:

                    raw = read_uploaded_file(
                        razorpay_file
                    )

                    normalized, missing, discarded = (
                        validate_and_normalize(
                            raw,
                            "razorpay",
                        )
                    )

                    if missing:

                        st.session_state.razorpay_df = None
                        st.session_state.upload_validation[
                            "razorpay"
                        ] = False

                        st.error(
                            "Razorpay file is missing required information: "
                            + ", ".join(missing)
                            + ". Please check the file and upload it again."
                        )

                    elif normalized.empty:

                        st.session_state.razorpay_df = None
                        st.session_state.upload_validation[
                            "razorpay"
                        ] = False

                        st.error(
                            "Razorpay file contains no usable financial records. "
                            "Please check the file and upload it again."
                        )

                    else:

                        st.session_state.razorpay_df = normalized

                        st.session_state.upload_validation[
                            "razorpay"
                        ] = True

                        record_uploaded_file(
                            "razorpay",
                            razorpay_file,
                        )

                        st.success(
                            f"Razorpay loaded: {len(normalized)} records"
                        )

                        if discarded:

                            st.caption(
                                "Unsupported columns ignored: "
                                + ", ".join(discarded)
                            )

                except Exception as e:

                    st.session_state.razorpay_df = None
                    st.session_state.upload_validation[
                        "razorpay"
                    ] = False

                    st.error(
                        "Razorpay file could not be validated. "
                        "Please check the file and upload it again. "
                        f"Details: {e}"
                    )

        with c2:

            bank_file = st.file_uploader(
                "Bank Statement File",
                type=["csv", "pdf", "xlsx", "xls"],
                key="bank_upload",
            )

            if bank_file is not None:

                try:

                    raw = read_uploaded_file(
                        bank_file
                    )

                    normalized, missing, discarded = (
                        validate_and_normalize(
                            raw,
                            "bank",
                        )
                    )

                    if missing:

                        st.session_state.bank_df = None
                        st.session_state.upload_validation[
                            "bank"
                        ] = False

                        st.error(
                            "Bank statement is missing required information: "
                            + ", ".join(missing)
                            + ". Please check the file and upload it again."
                        )

                    elif normalized.empty:

                        st.session_state.bank_df = None
                        st.session_state.upload_validation[
                            "bank"
                        ] = False

                        st.error(
                            "Bank statement contains no usable financial records. "
                            "Please check the file and upload it again."
                        )

                    else:

                        st.session_state.bank_df = normalized

                        st.session_state.upload_validation[
                            "bank"
                        ] = True

                        record_uploaded_file(
                            "bank",
                            bank_file,
                        )

                        st.success(
                            f"Bank statement loaded: {len(normalized)} records"
                        )

                        if discarded:

                            st.caption(
                                "Unsupported columns ignored: "
                                + ", ".join(discarded)
                            )

                except Exception as e:

                    st.session_state.bank_df = None
                    st.session_state.upload_validation[
                        "bank"
                    ] = False

                    st.error(
                        "Bank statement could not be validated. "
                        "Please check the file and upload it again. "
                        f"Details: {e}"
                    )

        with c3:

            ledger_file = st.file_uploader(
                "Merchant Ledger File",
                type=["csv", "pdf", "xlsx", "xls"],
                key="ledger_upload",
            )

            if ledger_file is not None:

                try:

                    raw = read_uploaded_file(
                        ledger_file
                    )

                    normalized, missing, discarded = (
                        validate_and_normalize(
                            raw,
                            "ledger",
                        )
                    )

                    if missing:

                        st.session_state.ledger_df = None
                        st.session_state.upload_validation[
                            "ledger"
                        ] = False

                        st.error(
                            "Ledger is missing required information: "
                            + ", ".join(missing)
                            + ". Please check the file and upload it again."
                        )

                    elif normalized.empty:

                        st.session_state.ledger_df = None
                        st.session_state.upload_validation[
                            "ledger"
                        ] = False

                        st.error(
                            "Ledger contains no usable financial records. "
                            "Please check the file and upload it again."
                        )

                    else:

                        st.session_state.ledger_df = normalized

                        st.session_state.upload_validation[
                            "ledger"
                        ] = True

                        record_uploaded_file(
                            "ledger",
                            ledger_file,
                        )

                        st.success(
                            f"Ledger loaded: {len(normalized)} records"
                        )

                        if discarded:

                            st.caption(
                                "Unsupported columns ignored: "
                                + ", ".join(discarded)
                            )

                except Exception as e:

                    st.session_state.ledger_df = None
                    st.session_state.upload_validation[
                        "ledger"
                    ] = False

                    st.error(
                        "Ledger could not be validated. "
                        "Please check the file and upload it again. "
                        f"Details: {e}"
                    )

    st.markdown("---")

    st.subheader("Execute Financial Close")

    if st.session_state.demo_enabled:

        st.success(
            "All three demo financial sources are ready."
        )

    elif not data_available():

        invalid_sources = []

        if not st.session_state.upload_validation.get(
            "razorpay",
            False,
        ):
            invalid_sources.append("Razorpay")

        if not st.session_state.upload_validation.get(
            "bank",
            False,
        ):
            invalid_sources.append("Bank")

        if not st.session_state.upload_validation.get(
            "ledger",
            False,
        ):
            invalid_sources.append("Ledger")

        if invalid_sources:

            st.warning(
                "Financial close is blocked. "
                "Please check and re-upload the following source(s): "
                + ", ".join(invalid_sources)
                + "."
            )

        else:

            st.warning(
                "All three sources are required before the financial close can run."
            )

    else:

        st.success(
            "All three financial sources are validated and ready."
        )

    if st.button(
        "Run Financial Close",
        type="primary",
        use_container_width=True,
        disabled=not data_available(),
    ):

        if not data_available():

            st.error(
                "Financial close was not executed because one or more uploaded "
                "files are incomplete or invalid. Please check the files and "
                "upload them again."
            )

        else:

            with st.spinner(
                "Running reconciliation and generating the audit trail..."
            ):

                try:

                    results = run_reconciliation(
                        st.session_state.razorpay_df,
                        st.session_state.bank_df,
                        st.session_state.ledger_df,
                    )

                    close_time = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    audit_df = build_audit_report(
                        results
                    )

                    st.session_state.results = results

                    st.session_state.audit_df = audit_df

                    st.session_state.last_run = close_time

                    # Store the audit with an explicit data source.
                    #
                    # Demo Data:
                    #   Store it as "demo" so that only demo audits are shown
                    #   while Demo Data is enabled.
                    #
                    # Uploaded Data:
                    #   Store it as "uploaded" so that only uploaded audits are
                    #   shown when Demo Data is disabled.
                    audit_source = (
                        "demo"
                        if st.session_state.demo_enabled
                        else "uploaded"
                    )

                    st.session_state.audit_reports.append(
                        {
                            "close_time": close_time,
                            "audit_df": audit_df.copy(),
                            "data_source": audit_source,
                        }
                    )

                    st.session_state.investigations = {}
                    st.session_state.dispute_drafts = {}

                    st.success(
                        "Financial close completed successfully."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Financial close failed safely. "
                        f"No financial result was saved. Details: {e}"
                    )


elif page == "Exceptions":

    hero(
        "Exception Control",
        "Review every reconciliation break, inspect the underlying evidence "
        "and request an AI explanation when required.",
    )

    if st.session_state.results is None:

        st.info(
            "Run a financial close before reviewing exceptions."
        )

    else:

        exceptions_df = (
            st.session_state.results["exceptions_df"]
        )

        if exceptions_df.empty:

            st.markdown(
                '<div class="status-green">No reconciliation exceptions were detected.</div>',
                unsafe_allow_html=True,
            )

        else:

            c1, c2, c3 = st.columns(3)

            with c1:
                metric(
                    "Total Exceptions",
                    len(exceptions_df),
                    "Detected by reconciliation",
                )

            with c2:
                metric(
                    "AI Investigations",
                    len(st.session_state.investigations),
                    "Completed",
                )

            with c3:
                metric(
                    "Needs Review",
                    int(
                        (
                            exceptions_df["resolution"]
                            == "NEEDS_REVIEW"
                        ).sum()
                    ),
                    "Human attention",
                )

            st.markdown("<br>", unsafe_allow_html=True)

            display_columns = [
                "case_id",
                "exception_type",
                "payment_id",
                "order_id",
                "expected",
                "actual",
                "difference",
                "resolution",
            ]

            display_df = exceptions_df[
                display_columns
            ].copy()

            display_df.columns = [
                "Case",
                "Exception",
                "Payment",
                "Order",
                "Expected",
                "Actual",
                "Difference",
                "Resolution",
            ]

            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)

            case_options = exceptions_df[
                "case_id"
            ].tolist()

            selected_case = st.selectbox(
                "Select an exception",
                case_options,
                key="exception_case_selector",
            )

            case = exceptions_df[
                exceptions_df["case_id"] == selected_case
            ].iloc[0].to_dict()

            st.markdown(
                f"""
                <div class="case-header">
                    <strong>{case["case_id"]}</strong>
                    <br>
                    <span style="color:#766F82;">
                        {case["exception_type"]}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                metric(
                    "Expected",
                    f"₹{case['expected']:,.2f}",
                )

            with c2:
                metric(
                    "Actual",
                    f"₹{case['actual']:,.2f}",
                )

            with c3:
                metric(
                    "Difference",
                    f"₹{case['difference']:,.2f}",
                )

            with c4:
                metric(
                    "Resolution",
                    case["resolution"],
                )

            st.markdown("<br>", unsafe_allow_html=True)

            st.subheader("Verified Evidence")

            evidence_fields = [
                ("Case", "case_id"),
                ("Payment ID", "payment_id"),
                ("Order ID", "order_id"),
                ("Expected settlement", "expected"),
                ("Bank credit", "actual"),
                ("Difference", "difference"),
                ("Expected fee", "expected_fee"),
                ("Actual fee", "actual_fee"),
                ("Expected GST", "expected_gst"),
                ("Actual GST", "actual_gst"),
                ("Ledger amount", "ledger_amount"),
                ("Chargeback amount", "chargeback_amount"),
                ("Bank record count", "duplicate_count"),
            ]

            evidence_rows = []

            for label, field in evidence_fields:

                value = case.get(field)

                if value is None:
                    continue

                if pd.isna(value):
                    continue

                if isinstance(value, float):
                    value = f"₹{value:,.2f}"

                evidence_rows.append(
                    {
                        "Evidence Item": label,
                        "Verified Value": value,
                    }
                )

            evidence_df = pd.DataFrame(
                evidence_rows
            )

            st.dataframe(
                evidence_df,
                hide_index=True,
                use_container_width=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)

            if selected_case in st.session_state.investigations:

                st.subheader("AI Investigation")

                investigation = (
                    st.session_state.investigations[
                        selected_case
                    ]
                )

                st.markdown(
                    f"""
                    <div class="ai-card">
                        {format_ai_investigation(investigation)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    """
                    <div style="
                        margin-top:10px;
                        padding:10px 14px;
                        border-radius:10px;
                        background:#fff8e7;
                        border:1px solid #f2d899;
                        color:#7a5a00;
                        font-size:12px;
                        font-weight:600;
                    ">
                        AI is used only to help understand and explain the verified evidence.
                        It is not used for financial calculations, financial records,
                        or financial decision-making. Python reconciliation remains the
                        source of truth for all financial purposes.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                if st.button(
                    "Investigate Exception with AI",
                    type="primary",
                    use_container_width=True,
                ):

                    with st.spinner(
                        "AI controller is reviewing the verified evidence..."
                    ):

                        investigation = investigate_exception(
                            case
                        )

                        st.session_state.investigations[
                            selected_case
                        ] = investigation

                        st.rerun()


elif page == "Disputes & Audits":

    hero(
        "Disputes & Audit Trail",
        "Create evidence-backed escalation drafts and review the complete "
        "financial close audit record.",
    )

    # Allow the Audit Report tab to remain accessible even when the current
    # financial data has been replaced or is no longer loaded.
    has_current_results = (
        st.session_state.results is not None
    )

    # IMPORTANT:
    # Only consider audit reports belonging to the currently selected
    # environment.
    #
    # Demo Data ON  -> only demo audit reports
    # Demo Data OFF -> only uploaded audit reports
    current_audit_source = (
        "demo"
        if st.session_state.demo_enabled
        else "uploaded"
    )

    visible_audit_reports = [
        audit_record
        for audit_record in st.session_state.audit_reports
        if audit_record.get("data_source") == current_audit_source
    ]

    has_historical_audits = (
        len(visible_audit_reports) > 0
    )

    if not has_current_results and not has_historical_audits:

        st.info(
            "Run a financial close before opening disputes and audits."
        )

    else:

        exceptions_df = (
            st.session_state.results["exceptions_df"]
            if has_current_results
            else pd.DataFrame()
        )

        tab1, tab2 = st.tabs(
            [
                "Dispute Evidence Builder",
                "Audit Report",
            ]
        )

        with tab1:

            if not has_current_results:

                st.info(
                    "Run a financial close before preparing a dispute."
                )

            elif exceptions_df.empty:

                st.success(
                    "There are no exceptions requiring dispute preparation."
                )

            else:

                selected_case = st.selectbox(
                    "Choose case",
                    exceptions_df["case_id"].tolist(),
                    key="dispute_case",
                )

                case = exceptions_df[
                    exceptions_df["case_id"] == selected_case
                ].iloc[0].to_dict()

                st.subheader(
                    f"Case {case['case_id']}"
                )

                c1, c2, c3 = st.columns(3)

                with c1:
                    metric(
                        "Issue",
                        case["exception_type"],
                    )

                with c2:
                    metric(
                        "Expected",
                        f"₹{case['expected']:,.2f}",
                    )

                with c3:
                    metric(
                        "Difference",
                        f"₹{case['difference']:,.2f}",
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                st.subheader("Evidence Pack")

                evidence_rows = [
                    [
                        "Payment ID",
                        case.get("payment_id", ""),
                    ],
                    [
                        "Order ID",
                        case.get("order_id", ""),
                    ],
                    [
                        "Expected amount",
                        f"₹{case['expected']:,.2f}",
                    ],
                    [
                        "Actual amount",
                        f"₹{case['actual']:,.2f}",
                    ],
                    [
                        "Difference",
                        f"₹{case['difference']:,.2f}",
                    ],
                    [
                        "Expected fee",
                        f"₹{case.get('expected_fee', 0):,.2f}",
                    ],
                    [
                        "Actual fee",
                        f"₹{case.get('actual_fee', 0):,.2f}",
                    ],
                    [
                        "Expected GST",
                        f"₹{case.get('expected_gst', 0):,.2f}",
                    ],
                    [
                        "Actual GST",
                        f"₹{case.get('actual_gst', 0):,.2f}",
                    ],
                    [
                        "Chargeback",
                        f"₹{case.get('chargeback_amount', 0):,.2f}",
                    ],
                ]

                evidence_df = pd.DataFrame(
                    evidence_rows,
                    columns=[
                        "Evidence",
                        "Value",
                    ],
                )

                st.dataframe(
                    evidence_df,
                    hide_index=True,
                    use_container_width=True,
                )

                if selected_case in st.session_state.dispute_drafts:

                    st.subheader(
                        "Human Approval Draft"
                    )

                    draft = st.session_state.dispute_drafts[
                        selected_case
                    ]

                    st.markdown(
                        f"""
                        <div class="dispute-card">
                            {format_dispute_draft(draft)}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("<br>", unsafe_allow_html=True)

                    editable_message = st.text_area(
                        "Editable dispute message",
                        draft,
                        height=500,
                        key=f"editable_dispute_{selected_case}",
                    )

                    st.markdown("<br>", unsafe_allow_html=True)

                    review_col, hold_col = st.columns(2)

                    with review_col:

                        if st.button(
                            "Review",
                            type="primary",
                            use_container_width=True,
                            key=f"review_{selected_case}",
                        ):

                            review_record = {
                                "Case": selected_case,
                                "Exception Type": case[
                                    "exception_type"
                                ],
                                "Timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "Message": editable_message,
                            }

                            st.session_state.reviewed_disputes = [
                                record
                                for record in st.session_state.reviewed_disputes
                                if record["Case"] != selected_case
                            ]

                            st.session_state.hold_disputes = [
                                record
                                for record in st.session_state.hold_disputes
                                if record["Case"] != selected_case
                            ]

                            st.session_state.reviewed_disputes.append(
                                review_record
                            )

                            st.success(
                                f"{selected_case} has been stored under Reviewed."
                            )

                    with hold_col:

                        if st.button(
                            "Hold",
                            use_container_width=True,
                            key=f"hold_{selected_case}",
                        ):

                            hold_record = {
                                "Case": selected_case,
                                "Exception Type": case[
                                    "exception_type"
                                ],
                                "Timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "Message": editable_message,
                            }

                            st.session_state.hold_disputes = [
                                record
                                for record in st.session_state.hold_disputes
                                if record["Case"] != selected_case
                            ]

                            st.session_state.reviewed_disputes = [
                                record
                                for record in st.session_state.reviewed_disputes
                                if record["Case"] != selected_case
                            ]

                            st.session_state.hold_disputes.append(
                                hold_record
                            )

                            st.warning(
                                f"{selected_case} has been stored under Hold."
                            )

                    st.markdown("<br>", unsafe_allow_html=True)

                    st.subheader("Reviewed")

                    reviewed_records = [
                        record
                        for record in st.session_state.reviewed_disputes
                        if record["Case"] == selected_case
                    ]

                    if reviewed_records:

                        for index, record in enumerate(
                            reviewed_records
                        ):

                            st.caption(
                                f"Case: {record['Case']} | "
                                f"Exception Type: {record['Exception Type']}"
                            )

                            st.download_button(
                                "Download Reviewed Message",
                                record["Message"],
                                file_name=(
                                    f"clearledger_{selected_case}_"
                                    f"reviewed.txt"
                                ),
                                mime="text/plain",
                                use_container_width=True,
                                key=(
                                    f"download_reviewed_"
                                    f"{selected_case}_{index}"
                                ),
                            )

                    else:

                        st.info(
                            "No reviewed message has been stored for this case."
                        )

                    st.markdown("<br>", unsafe_allow_html=True)

                    st.subheader("Hold")

                    hold_records = [
                        record
                        for record in st.session_state.hold_disputes
                        if record["Case"] == selected_case
                    ]

                    if hold_records:

                        for index, record in enumerate(
                            hold_records
                        ):

                            st.caption(
                                f"Case: {record['Case']} | "
                                f"Exception Type: {record['Exception Type']}"
                            )

                            st.download_button(
                                "Download Held Message",
                                record["Message"],
                                file_name=(
                                    f"clearledger_{selected_case}_"
                                    f"hold.txt"
                                ),
                                mime="text/plain",
                                use_container_width=True,
                                key=(
                                    f"download_hold_"
                                    f"{selected_case}_{index}"
                                ),
                            )

                    else:

                        st.info(
                            "No held message has been stored for this case."
                        )

                else:

                    if st.button(
                        "Generate Evidence Backed Dispute Draft",
                        type="primary",
                        use_container_width=True,
                    ):

                        with st.spinner(
                            "Preparing the professional dispute draft..."
                        ):

                            draft = generate_dispute_draft(
                                case
                            )

                            st.session_state.dispute_drafts[
                                selected_case
                            ] = draft

                            st.rerun()

        with tab2:

            st.subheader("Financial Close Audit History")

            if st.session_state.demo_enabled:

                st.caption(
                    "Showing Demo Data audit reports only."
                )

            else:

                st.caption(
                    "Showing uploaded financial-data audit reports only."
                )

            audit_search_date = st.date_input(
                "Search Audit by Date",
                value=None,
                key="audit_search_date",
            )

            filtered_audit_reports = visible_audit_reports

            if audit_search_date is not None:

                searched_date = audit_search_date.strftime(
                    "%Y-%m-%d"
                )

                filtered_audit_reports = [
                    audit_record
                    for audit_record in visible_audit_reports
                    if audit_record["close_time"].startswith(
                        searched_date
                    )
                ]

            if not filtered_audit_reports:

                if audit_search_date is not None:

                    if st.session_state.demo_enabled:

                        st.info(
                            f"No Demo Data audit reports were found for "
                            f"{audit_search_date.strftime('%Y-%m-%d')}."
                        )

                    else:

                        st.info(
                            f"No uploaded-data audit reports were found for "
                            f"{audit_search_date.strftime('%Y-%m-%d')}."
                        )

                else:

                    if st.session_state.demo_enabled:

                        st.info(
                            "No Demo Data financial close audit reports are available yet."
                        )

                    else:

                        st.info(
                            "No uploaded financial-data close audit reports are available yet."
                        )

            else:

                for index, audit_record in enumerate(
                    reversed(filtered_audit_reports)
                ):

                    close_time = audit_record[
                        "close_time"
                    ]

                    historical_audit_df = audit_record[
                        "audit_df"
                    ]

                    data_source_label = (
                        "Demo Data"
                        if audit_record.get("data_source") == "demo"
                        else "Uploaded Data"
                    )

                    st.markdown(
                        f"""
                        <div class="case-header">
                            <strong>Financial Close Audit — {data_source_label}</strong>
                            <br>
                            <span style="color:#766F82;">
                                Financial Close Date & Time: {close_time}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.dataframe(
                        historical_audit_df,
                        hide_index=True,
                        use_container_width=True,
                    )

                    csv = historical_audit_df.to_csv(
                        index=False
                    ).encode("utf-8")

                    safe_timestamp = close_time.replace(
                        ":",
                        "-"
                    ).replace(
                        " ",
                        "_",
                    )

                    source_filename = (
                        "demo"
                        if audit_record.get("data_source") == "demo"
                        else "uploaded"
                    )

                    st.download_button(
                        "Download Audit CSV",
                        csv,
                        file_name=(
                            f"clearledger_{source_filename}_"
                            f"financial_audit_{safe_timestamp}.csv"
                        ),
                        mime="text/csv",
                        use_container_width=True,
                        key=f"download_historical_audit_{index}",
                    )

                    if index < len(
                        filtered_audit_reports
                    ) - 1:

                        st.markdown(
                            "<hr>",
                            unsafe_allow_html=True,
                        )

            if (
                st.session_state.results is not None
                and st.session_state.audit_df is not None
                and not visible_audit_reports
            ):

                audit_df = (
                    st.session_state.audit_df
                )

                r = st.session_state.results

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    metric(
                        "Records",
                        r["total_records"],
                    )

                with c2:
                    metric(
                        "Matched",
                        r["matched"],
                    )

                with c3:
                    metric(
                        "Exceptions",
                        r["exceptions"],
                    )

                with c4:
                    metric(
                        "Close Time",
                        st.session_state.last_run or "-",
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                st.dataframe(
                    audit_df,
                    hide_index=True,
                    use_container_width=True,
                )

                csv = audit_df.to_csv(
                    index=False
                ).encode("utf-8")

                current_source_filename = (
                    "demo"
                    if st.session_state.demo_enabled
                    else "uploaded"
                )

                st.download_button(
                    "Download Audit CSV",
                    csv,
                    file_name=(
                        f"clearledger_{current_source_filename}_"
                        f"financial_audit.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                )
