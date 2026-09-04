import os
import json
import re
from typing import Dict, Any
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PRIMARY_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)

FALLBACK_MODEL = os.getenv(
    "GROQ_FALLBACK_MODEL",
    "openai/gpt-oss-20b",
)


if GROQ_API_KEY:

    client = Groq(
        api_key=GROQ_API_KEY
    )

    GROQ_AVAILABLE = True

else:

    client = None

    GROQ_AVAILABLE = False


SYSTEM_PROMPT = """

You are ClearLedger AI, an AI finance controller.

You investigate reconciliation exceptions using only verified evidence

provided by the Python reconciliation engine.

Python is the source of truth for financial calculations.

Never invent transaction IDs.

Never invent payment IDs.

Never invent order IDs.

Never invent amounts.

Never invent dates.

Never invent references.

Never change financial calculations.

Never claim fraud without evidence.

Never claim certainty when the evidence is insufficient.

Clearly distinguish what the evidence proves from what is only likely.

Your response must be clean, professional and easy for a finance controller

to read.

Do not use Markdown formatting.

Do not use asterisks.

Do not use backticks.

Do not use bullet symbols.

Do not use decorative symbols.

Use simple section headings followed by numbered or short paragraphs.

If the evidence is insufficient, explicitly state:

Root cause not conclusively established from available evidence.

"""


def clean_ai_text(text: str) -> str:

    if not text:

        return "No AI explanation was returned."

    text = str(text)

    text = text.replace(
        "**",
        "",
    )

    text = text.replace(
        "__",
        "",
    )

    text = text.replace(
        "`",
        "",
    )

    text = text.replace(
        "•",
        "",
    )

    text = text.replace(
        "▪",
        "",
    )

    text = text.replace(
        "◦",
        "",
    )

    text = re.sub(
        r"^\s*[-*]\s+",
        "",
        text,
        flags=re.MULTILINE,
    )

    return text.strip()


def _ask_groq(
    prompt: str,
    system_prompt: str = None,
    max_tokens: int = 1400,
) -> str:

    if not GROQ_AVAILABLE:

        return (
            "AI investigation is unavailable because the Groq API key "
            "has not been configured. The financial reconciliation "
            "results remain available."
        )

    active_system_prompt = (
        system_prompt
        if system_prompt is not None
        else SYSTEM_PROMPT
    )

    def call_model(
        model_name: str
    ):

        return client.chat.completions.create(

            model=model_name,

            messages=[

                {
                    "role": "system",
                    "content": active_system_prompt,
                },

                {
                    "role": "user",
                    "content": prompt,
                },

            ],

            temperature=0.1,

            max_completion_tokens=max_tokens,
            include_reasoning=False,

        )

    primary_error = None

    try:

        response = call_model(
            PRIMARY_MODEL
        )

        return clean_ai_text(
            response.choices[0].message.content
        )

    except Exception as error:

        primary_error = error

    try:

        response = call_model(
            FALLBACK_MODEL
        )

        return clean_ai_text(
            response.choices[0].message.content
        )

    except Exception as fallback_error:

        return (
            "AI investigation is temporarily unavailable.\n\n"

            "The deterministic financial reconciliation has still "
            "been completed successfully.\n\n"

            f"Primary model error: {primary_error}\n"

            f"Fallback model error: {fallback_error}"
        )


def build_case_evidence(
    case: Dict[str, Any]
) -> Dict[str, Any]:

    fields = [

        "case_id",
        "exception_type",
        "payment_id",
        "order_id",
        "transaction_id",
        "expected",
        "actual",
        "difference",
        "expected_amount",
        "actual_amount",
        "razorpay_amount",
        "settlement_amount",
        "bank_credit",
        "fee",
        "expected_fee",
        "actual_fee",
        "gst",
        "expected_gst",
        "actual_gst",
        "ledger_amount",
        "chargeback_amount",
        "duplicate_count",
        "status",
        "resolution",

    ]

    evidence = {}

    for field in fields:

        value = case.get(field)

        if value is not None:

            evidence[field] = value

    return evidence


def investigate_exception(
    case: Dict[str, Any]
) -> str:

    evidence = build_case_evidence(
        case
    )

    prompt = f"""

Investigate the following verified ClearLedger reconciliation exception.

VERIFIED CASE DATA

{json.dumps(

    evidence,

    indent=2,

    default=str

)}

Write the response using exactly these sections:

ROOT CAUSE

State the most likely explanation based only on the evidence.

If the evidence does not prove the cause, say:

Root cause not conclusively established from available evidence.

EVIDENCE

Explain the specific verified values that support the conclusion.

Use numbered lines.display each financial amount clearly on its own line with proper spacing and alignment, rather than placing multiple amounts continuously in the same sentence, while keeping the numbered evidence format neat and easy to read.

FINANCIAL INTERPRETATION

Explain the financial impact for a finance controller.

CONFIDENCE

State High, Medium or Low.

RECOMMENDED ACTION

Give practical next steps for the finance team.

Formatting requirements:

Always place the ₹ symbol immediately before every financial amount displayed.

Generate the complete message from beginning to end without stopping, truncating, or leaving any section unfinished.

Keep each section compact.

Do not insert unnecessary blank lines.

Use one blank line only between major sections.

Do not use Markdown.

Do not use asterisks.

Do not use backticks.

Do not use bullet symbols.

Do not invent information.

"""

    return _ask_groq(

        prompt,

        max_tokens=1400,

    )


def generate_dispute_draft(
    case: Dict[str, Any]
) -> str:

    evidence = build_case_evidence(
        case
    )

    prompt = f"""

Prepare a professional finance dispute or escalation message using only

the verified evidence below.

VERIFIED EVIDENCE

{json.dumps(

    evidence,

    indent=2,

    default=str

)}

Create a structured, ready-to-send finance escalation message.

Use exactly these sections and headings:

SUBJECT

Provide a concise subject describing the reconciliation issue and case ID.

CASE IDENTIFICATION

State the case ID, exception type, payment ID and order ID when available.

DISCREPANCY

Clearly explain the difference between the expected and actual values.

VERIFIED EVIDENCE

Present the important verified financial evidence using numbered lines.

Include expected amount, actual amount, difference, fee, GST, ledger amount,

chargeback or duplicate information when available and relevant.

FINANCIAL IMPACT

Explain the financial impact based only on the verified evidence.

REQUEST FOR INVESTIGATION

Clearly request investigation of the discrepancy and confirmation of the

underlying settlement or transaction status.

REQUEST FOR SUPPORTING DOCUMENTATION

Request the relevant settlement report, transaction reference, adjustment

documentation or other supporting records needed to resolve the case.

NEXT STEPS

Provide concise practical next steps for the recipient and finance team.

CLOSING

End with a professional request for confirmation and resolution.

Important requirements:

Generate the complete dispute message from beginning to end without stopping, truncating, or leaving any section unfinished.

Do not claim fraud.

Do not accuse the counterparty of an error unless the evidence proves it.

Do not invent dates, references, transaction IDs, payment IDs, order IDs,

amounts or documentation.

Always place the ₹ symbol immediately before every financial amount displayed.

Use only the verified evidence supplied above.

Do not use Markdown.

Do not use asterisks.

Do not use backticks.

Do not use bullet symbols.

Do not add unnecessary blank lines.

Use one blank line only between major sections.

Make the result professional, concise and ready for human approval.

"""

    return _ask_groq(

        prompt,

        max_tokens=1600,

    )


def summarize_exception(
    case: Dict[str, Any]
) -> str:

    evidence = build_case_evidence(
        case
    )

    prompt = f"""

Summarize this reconciliation exception for a finance controller.

VERIFIED EVIDENCE

{json.dumps(

    evidence,

    indent=2,

    default=str

)}

Keep the summary below 80 words.

Explain what happened, the most likely reason and whether further

investigation is required.

Do not invent facts.

Do not use Markdown.

Do not use asterisks.

Do not use backticks.

Do not use bullet symbols.

"""

    return _ask_groq(

        prompt,

        max_tokens=250,

    )


def test_groq_connection():

    if not GROQ_AVAILABLE:

        return {

            "success": False,

            "message": "GROQ_API_KEY is missing.",

            "model": PRIMARY_MODEL,

        }

    try:

        response = client.chat.completions.create(

            model=PRIMARY_MODEL,

            messages=[

                {

                    "role": "user",

                    "content": (
                        "Reply with exactly: "
                        "ClearLedger AI connected."
                    ),

                }

            ],

            temperature=0,

            max_completion_tokens=30,
            include_reasoning=False,

        )

        return {

            "success": True,

            "message": (
                response.choices[0]
                .message
                .content
                .strip()
            ),

            "model": PRIMARY_MODEL,

        }

    except Exception as error:

        return {

            "success": False,

            "message": str(error),

            "model": PRIMARY_MODEL,

        }