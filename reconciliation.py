import pandas as pd
import numpy as np
import io


REQUIRED_COLUMNS = {

    "razorpay": [
        "payment_id",
        "order_id",
        "amount",
        "fee",
        "GST",
        "settlement_amount",
        "status",
    ],

    "bank": [
        "transaction_id",
        "date",
        "UTR",
        "credit",
        "debit",
        "description",
    ],

    "ledger": [
        "order_id",
        "invoice_amount",
        "customer",
        "invoice_date",
        "status",
    ],
}


def read_uploaded_file(
    uploaded_file,
):

    if uploaded_file is None:
        raise ValueError(
            "No file supplied."
        )

    file_name = str(
        uploaded_file.name
    ).lower()

    uploaded_file.seek(0)

    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if file_name.endswith(
        ".xlsx"
    ) or file_name.endswith(
        ".xls"
    ):

        return pd.read_excel(
            uploaded_file
        )

    if file_name.endswith(
        ".pdf"
    ):

        return read_pdf_file(
            uploaded_file
        )

    raise ValueError(
        "Unsupported file format. "
        "Please upload a CSV,PDF or Excel file."
    )


def read_pdf_file(
    uploaded_file,
):

    uploaded_file.seek(0)

    try:

        import pdfplumber

    except ImportError:

        raise ImportError(
            "PDF reading requires pdfplumber. "
            "Install it with: pip install pdfplumber"
        )

    tables = []

    with pdfplumber.open(
        uploaded_file
    ) as pdf:

        for page in pdf.pages:

            page_tables = (
                page.extract_tables()
            )

            for table in page_tables:

                if not table:
                    continue

                cleaned_table = []

                for row in table:

                    if row is None:
                        continue

                    cleaned_row = [
                        (
                            str(value).strip()
                            if value is not None
                            else ""
                        )
                        for value in row
                    ]

                    if any(
                        value != ""
                        for value in cleaned_row
                    ):
                        cleaned_table.append(
                            cleaned_row
                        )

                if len(cleaned_table) >= 2:
                    tables.append(
                        cleaned_table
                    )

    if not tables:

        raise ValueError(
            "No readable table was found in the PDF. "
            "The PDF should contain a structured financial table."
        )

    frames = []

    for table in tables:

        header = table[0]

        data = table[1:]

        frame = pd.DataFrame(
            data,
            columns=header,
        )

        frames.append(frame)

    if not frames:

        raise ValueError(
            "Unable to extract financial records from PDF."
        )

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    combined.columns = [
        str(column).strip()
        for column in combined.columns
    ]

    return combined


def validate_and_normalize(
    df,
    source,
):

    if source not in REQUIRED_COLUMNS:
        raise ValueError(
            f"Unknown source: {source}"
        )

    if df is None:
        raise ValueError(
            f"No data supplied for {source}"
        )

    normalized = df.copy()

    normalized.columns = [
        str(column).strip()
        for column in normalized.columns
    ]

    required = REQUIRED_COLUMNS[source]

    missing = [
        column
        for column in required
        if column not in normalized.columns
    ]

    supported = [
        column
        for column in normalized.columns
        if column in required
    ]

    discarded = [
        column
        for column in normalized.columns
        if column not in required
    ]

    normalized = normalized[
        supported
    ].copy()

    if missing:
        return (
            normalized,
            missing,
            discarded,
        )

    numeric_by_source = {

        "razorpay": [
            "amount",
            "fee",
            "GST",
            "settlement_amount",
        ],

        "bank": [
            "credit",
            "debit",
        ],

        "ledger": [
            "invoice_amount",
        ],
    }

    for column in numeric_by_source[source]:

        normalized[column] = pd.to_numeric(
            normalized[column],
            errors="coerce",
        ).fillna(0.0)

    for column in normalized.columns:

        if column not in numeric_by_source[source]:

            normalized[column] = (
                normalized[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    return (
        normalized,
        [],
        discarded,
    )


def generate_demo_data():

    rng = np.random.default_rng(42)

    total_records = 80

    records = []

    for i in range(
        1,
        total_records + 1,
    ):

        payment_id = f"PAY-{i:04d}"
        order_id = f"ORD-{i:04d}"

        amount = float(
            rng.choice(
                [
                    1250,
                    2500,
                    5000,
                    10000,
                    15000,
                    25000,
                    50000,
                ]
            )
        )

        fee = round(
            amount * 0.02,
            2,
        )

        gst = round(
            fee * 0.18,
            2,
        )

        settlement = round(
            amount - fee - gst,
            2,
        )

        records.append(
            {
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": amount,
                "fee": fee,
                "GST": gst,
                "settlement_amount": settlement,
                "status": "SUCCESS",
            }
        )

    razorpay = pd.DataFrame(
        records
    )

    bank_records = []

    for _, row in razorpay.iterrows():

        bank_records.append(
            {
                "transaction_id": (
                    f"TXN-{row['payment_id']}"
                ),
                "date": "2026-09-04",
                "UTR": (
                    f"UTR{row['payment_id']}"
                ),
                "credit": float(
                    row["settlement_amount"]
                ),
                "debit": 0.0,
                "description": (
                    f"Razorpay "
                    f"{row['payment_id']}"
                ),
            }
        )

    bank = pd.DataFrame(
        bank_records
    )

    ledger_records = []

    for _, row in razorpay.iterrows():

        ledger_records.append(
            {
                "order_id": row["order_id"],
                "invoice_amount": float(
                    row["amount"]
                ),
                "customer": (
                    f"Customer "
                    f"{row['order_id'][-4:]}"
                ),
                "invoice_date": "2026-09-04",
                "status": "PAID",
            }
        )

    ledger = pd.DataFrame(
        ledger_records
    )

    # =====================================================
    # DEMO DESIGN
    #
    # 60 records remain fully matched.
    # 20 records contain different exception scenarios.
    #
    # 1 to 60   = matched
    # 61 to 64  = missing settlement
    # 65 to 68  = fee discrepancy
    # 69 to 72  = GST discrepancy
    # 73 to 76  = rounding difference
    # 77 to 78  = chargeback
    # 79 to 80  = ledger mismatch
    # =====================================================

    for i in range(
        61,
        65,
    ):

        idx = i - 1

        bank.loc[
            idx,
            "credit",
        ] = 0.0

    for i in range(
        65,
        69,
    ):

        idx = i - 1

        razorpay.loc[
            idx,
            "fee",
        ] = round(
            razorpay.loc[
                idx,
                "fee",
            ] + 250,
            2,
        )

        razorpay.loc[
            idx,
            "settlement_amount",
        ] = round(
            razorpay.loc[
                idx,
                "amount",
            ]
            - razorpay.loc[
                idx,
                "fee",
            ]
            - razorpay.loc[
                idx,
                "GST",
            ],
            2,
        )

    for i in range(
        69,
        73,
    ):

        idx = i - 1

        razorpay.loc[
            idx,
            "GST",
        ] = round(
            razorpay.loc[
                idx,
                "GST",
            ] + 45,
            2,
        )

        razorpay.loc[
            idx,
            "settlement_amount",
        ] = round(
            razorpay.loc[
                idx,
                "amount",
            ]
            - razorpay.loc[
                idx,
                "fee",
            ]
            - razorpay.loc[
                idx,
                "GST",
            ],
            2,
        )

    for i in range(
        73,
        77,
    ):

        idx = i - 1

        bank.loc[
            idx,
            "credit",
        ] = round(
            bank.loc[
                idx,
                "credit",
            ] + 0.01,
            2,
        )

    for i in range(
        77,
        79,
    ):

        idx = i - 1

        bank.loc[
            idx,
            "credit",
        ] = round(
            bank.loc[
                idx,
                "credit",
            ] - 1000.0,
            2,
        )

    duplicate_rows = bank.iloc[
        78:80
    ].copy()

    bank = pd.concat(
        [
            bank,
            duplicate_rows,
        ],
        ignore_index=True,
    )

    for i in range(
        79,
        81,
    ):

        idx = i - 1

        ledger.loc[
            idx,
            "invoice_amount",
        ] = round(
            ledger.loc[
                idx,
                "invoice_amount",
            ] - 500,
            2,
        )

    return (
        razorpay,
        bank,
        ledger,
    )


def run_reconciliation(
    razorpay,
    bank,
    ledger,
):

    rp = razorpay.copy()
    bk = bank.copy()
    lg = ledger.copy()

    exceptions = []
    audit_rows = []

    total_records = len(rp)

    matched = 0
    auto_resolved = 0
    needs_review = 0

    amount_reconciled = 0.0
    amount_in_dispute = 0.0

    bank_by_payment = {}

    payment_ids = rp[
        "payment_id"
    ].astype(str).tolist()

    for _, row in bk.iterrows():

        description = str(
            row["description"]
        )

        for payment_id in payment_ids:

            if payment_id in description:

                bank_by_payment.setdefault(
                    payment_id,
                    [],
                ).append(row)

    for _, payment in rp.iterrows():

        payment_id = str(
            payment["payment_id"]
        )

        order_id = str(
            payment["order_id"]
        )

        amount = float(
            payment["amount"]
        )

        fee = float(
            payment["fee"]
        )

        gst = float(
            payment["GST"]
        )

        expected_settlement = round(
            amount - fee - gst,
            2,
        )

        bank_rows = (
            bank_by_payment.get(
                payment_id,
                [],
            )
        )

        bank_credit = round(
            sum(
                float(row["credit"])
                for row in bank_rows
            ),
            2,
        )

        ledger_rows = lg[
            lg["order_id"] == order_id
        ]

        if not ledger_rows.empty:

            ledger_amount = float(
                ledger_rows.iloc[0][
                    "invoice_amount"
                ]
            )

        else:

            ledger_amount = 0.0

        duplicate_count = len(
            bank_rows
        )

        difference = round(
            expected_settlement
            - bank_credit,
            2,
        )

        expected_fee = round(
            amount * 0.02,
            2,
        )

        expected_gst = round(
            expected_fee * 0.18,
            2,
        )

        exception_type = "MATCHED"
        resolution = "MATCHED"
        chargeback_amount = 0.0

        if bank_credit == 0:

            exception_type = (
                "MISSING SETTLEMENT"
            )

            resolution = "NEEDS_REVIEW"

        elif duplicate_count > 1:

            exception_type = "DUPLICATE"

            resolution = "NEEDS_REVIEW"

        elif abs(
            fee - expected_fee
        ) > 0.01:

            exception_type = (
                "FEE DISCREPANCY"
            )

            fee_difference = round(
                fee - expected_fee,
                2,
            )

            if abs(
                difference
                - fee_difference
            ) <= 0.02:

                resolution = (
                    "AUTO_RESOLVED"
                )

            else:

                resolution = (
                    "NEEDS_REVIEW"
                )

        elif abs(
            gst - expected_gst
        ) > 0.01:

            exception_type = (
                "TAX-LINE DISCREPANCY"
            )

            gst_difference = round(
                gst - expected_gst,
                2,
            )

            if abs(
                difference
                - gst_difference
            ) <= 0.02:

                resolution = (
                    "AUTO_RESOLVED"
                )

            else:

                resolution = (
                    "NEEDS_REVIEW"
                )

        elif abs(
            amount - ledger_amount
        ) > 0.01:

            exception_type = (
                "LEDGER MISMATCH"
            )

            resolution = (
                "NEEDS_REVIEW"
            )

        elif (
            999.99
            <= difference
            <= 1000.01
        ):

            exception_type = (
                "CHARGEBACK ADJUSTMENT"
            )

            resolution = (
                "AUTO_RESOLVED"
            )

            chargeback_amount = 1000.0

        elif (
            abs(difference) > 0
            and abs(difference) <= 0.02
        ):

            exception_type = (
                "ROUNDING DIFFERENCE"
            )

            resolution = (
                "AUTO_RESOLVED"
            )

        elif abs(difference) <= 0.02:

            exception_type = "MATCHED"

            resolution = "MATCHED"

        else:

            exception_type = (
                "SETTLEMENT DISCREPANCY"
            )

            resolution = (
                "NEEDS_REVIEW"
            )

        if resolution == "MATCHED":

            matched += 1

            amount_reconciled += (
                expected_settlement
            )

        elif resolution == "AUTO_RESOLVED":

            auto_resolved += 1

            amount_reconciled += (
                expected_settlement
            )

        else:

            needs_review += 1

            amount_in_dispute += abs(
                difference
            )

        if exception_type != "MATCHED":

            case_id = (
                f"CL-{len(exceptions) + 1:04d}"
            )

            exceptions.append(
                {
                    "case_id": case_id,
                    "exception_type": (
                        exception_type
                    ),
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "expected": (
                        expected_settlement
                    ),
                    "actual": bank_credit,
                    "difference": difference,
                    "resolution": resolution,
                    "expected_fee": (
                        expected_fee
                    ),
                    "actual_fee": fee,
                    "expected_gst": (
                        expected_gst
                    ),
                    "actual_gst": gst,
                    "bank_credit": (
                        bank_credit
                    ),
                    "ledger_amount": (
                        ledger_amount
                    ),
                    "chargeback_amount": (
                        chargeback_amount
                    ),
                    "duplicate_count": (
                        duplicate_count
                    ),
                    "razorpay_amount": (
                        amount
                    ),
                    "settlement_amount": (
                        expected_settlement
                    ),
                }
            )

        audit_rows.append(
            {
                "payment_id": payment_id,
                "order_id": order_id,
                "expected_settlement": (
                    expected_settlement
                ),
                "bank_credit": bank_credit,
                "difference": difference,
                "exception_type": (
                    exception_type
                ),
                "resolution": resolution,
            }
        )

    exceptions_df = pd.DataFrame(
        exceptions
    )

    audit_df = pd.DataFrame(
        audit_rows
    )

    exception_count = len(
        exceptions_df
    )

    unresolved = needs_review

    if total_records:

        match_rate = (
            matched
            / total_records
            * 100
        )

        exception_rate = (
            exception_count
            / total_records
            * 100
        )

        straight_through_rate = (
            (
                matched
                + auto_resolved
            )
            / total_records
            * 100
        )

    else:

        match_rate = 0.0
        exception_rate = 0.0
        straight_through_rate = 0.0

    return {
        "total_records": total_records,
        "matched": matched,
        "exceptions": exception_count,
        "auto_resolved": auto_resolved,
        "needs_review": needs_review,
        "unresolved": unresolved,
        "match_rate": match_rate,
        "exception_rate": exception_rate,
        "straight_through_rate": (
            straight_through_rate
        ),
        "amount_reconciled": round(
            amount_reconciled,
            2,
        ),
        "amount_in_dispute": round(
            amount_in_dispute,
            2,
        ),
        "exceptions_df": exceptions_df,
        "audit_df": audit_df,
    }


def build_audit_report(
    results
):

    if results is None:

        return pd.DataFrame()

    return results[
        "audit_df"
    ].copy()

