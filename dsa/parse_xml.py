"""
dsa/parse_xml.py

Task 1: Data Parsing
---------------------
Parses the modified_sms_v2.xml file (MTN MoMo SMS backup export) and converts
each <sms> record into a structured JSON object (a Python dict).

The raw XML only gives us generic SMS metadata (address, date, body, etc.) —
the actual transaction details (type, amount, sender/receiver, fee, balance,
transaction ID) are embedded as free text inside the `body` attribute, so
this parser classifies each message by keyword and extracts fields with
regular expressions.

Usage:
    python dsa/parse_xml.py [path/to/modified_sms_v2.xml] [path/to/output.json]

Defaults to data/modified_sms_v2.xml -> data/transactions.json
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _to_amount(raw: str) -> float:
    """Convert a string like '1,000' or '2000' into a float."""
    if raw is None:
        return None
    cleaned = raw.replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def classify_and_extract(body: str) -> dict:
    """
    Classify an SMS body into a transaction type and pull out the fields
    relevant to that type. Returns a dict of extracted fields; unmatched
    fields are left as None so every record has a consistent shape.
    """
    fields = {
        "transaction_type": "unknown",
        "amount": None,
        "fee": None,
        "new_balance": None,
        "sender": None,
        "receiver": None,
        "phone_number": None,
        "transaction_id": None,
        "transaction_time": None,
    }

    text = body or ""
    lower = text.lower()

    # --- One-Time Password messages (not a transaction) ---
    if "one-time password" in lower:
        fields["transaction_type"] = "otp"
        match = re.search(r"password is\s*:?\s*(\d+)", text)
        if match:
            fields["transaction_id"] = match.group(1)
        return fields

    # --- Data bundle / airtime bundle purchase ("Yello!Umaze kugura ...") ---
    if lower.startswith("yello") and "kugura" in lower:
        fields["transaction_type"] = "bundle_purchase"
        match = re.search(r"igura\s+([\d,]+)\s*RWF", text, re.IGNORECASE)
        if match:
            fields["amount"] = _to_amount(match.group(1))
        return fields

    # --- Reversal (two observed phrasings) ---
    if "reversal has been initiated" in lower or "has been reversed" in lower:
        fields["transaction_type"] = "reversal"
        match = re.search(r"transaction to ([A-Za-z .]+?)\s*\((\d+)\)\s*with\s*([\d,]+)\s*RWF", text)
        if match:
            fields["receiver"] = match.group(1).strip()
            fields["phone_number"] = match.group(2)
            fields["amount"] = _to_amount(match.group(3))
        m_bal = re.search(r"new balance is\s*([\d,]+)\s*RWF", text, re.IGNORECASE)
        if m_bal:
            fields["new_balance"] = _to_amount(m_bal.group(1))
        m_time = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if m_time:
            fields["transaction_time"] = m_time.group(1)
        return fields

    # --- Failed transaction ---
    if "failed at" in lower:
        fields["transaction_type"] = "failed"
        m_amt = re.search(r"amount\s+([\d,]+)\s*RWF\s+for\s+(.+?)\s+with message", text, re.IGNORECASE)
        if m_amt:
            fields["amount"] = _to_amount(m_amt.group(1))
            fields["receiver"] = m_amt.group(2).strip()
        m_time = re.search(r"failed at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if m_time:
            fields["transaction_time"] = m_time.group(1)
        return fields

    # --- Tabular-style deposit ("1) 2024-08-23 DEPOSIT RWF 25000 Receiver: ...") ---
    if "deposit" in lower and "receiver:" in lower:
        fields["transaction_type"] = "deposit"
        m_amt = re.search(r"DEPOSIT\s+RWF\s+([\d,]+)", text, re.IGNORECASE)
        if m_amt:
            fields["amount"] = _to_amount(m_amt.group(1))
        m_recv = re.search(r"Receiver:\s*(\S+)", text)
        if m_recv:
            fields["phone_number"] = m_recv.group(1)
        m_time = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if m_time:
            fields["transaction_time"] = m_time.group(1)
        return fields

    # --- Bank-account-initiated transfer ("You have transferred X RWF to ... from your mobile money account ... imbank.bank") ---
    if lower.startswith("you have transferred"):
        fields["transaction_type"] = "bank_transfer"
        m_amt = re.search(r"transferred\s+([\d,]+)\s*RWF\s+to\s+(.+?)\s*\((\d+)\)", text, re.IGNORECASE)
        if m_amt:
            fields["amount"] = _to_amount(m_amt.group(1))
            fields["receiver"] = m_amt.group(2).strip()
            fields["phone_number"] = m_amt.group(3)
        m_time = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if m_time:
            fields["transaction_time"] = m_time.group(1)
        return fields

    # --- Withdrawal via agent ---
    if "withdrawn" in lower and "agent" in lower:
        fields["transaction_type"] = "withdrawal"
        m_sender = re.match(r"You ([A-Za-z .]+?)\s*\(", text)
        if m_sender:
            fields["sender"] = m_sender.group(1).strip()
        m_amt = re.search(r"withdrawn\s+([\d,]+)\s*RWF", text)
        if m_amt:
            fields["amount"] = _to_amount(m_amt.group(1))
        m_bal = re.search(r"new balance:\s*([\d,]+)\s*RWF", text, re.IGNORECASE)
        if m_bal:
            fields["new_balance"] = _to_amount(m_bal.group(1))
        m_time = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if m_time:
            fields["transaction_time"] = m_time.group(1)
        return fields

    # --- Bank deposit ---
    if "bank deposit" in lower:
        fields["transaction_type"] = "deposit"
        m_amt = re.search(r"bank deposit of\s+([\d,]+)\s*RWF", text, re.IGNORECASE)
        if m_amt:
            fields["amount"] = _to_amount(m_amt.group(1))
        m_bal = re.search(r"NEW BALANCE\s*:?\s*([\d,]+)\s*RWF", text, re.IGNORECASE)
        if m_bal:
            fields["new_balance"] = _to_amount(m_bal.group(1))
        m_time = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if m_time:
            fields["transaction_time"] = m_time.group(1)
        return fields

    # --- Received money from someone ---
    if lower.startswith("you have received") or "you have received" in lower:
        fields["transaction_type"] = "received"
        m_amt = re.search(r"received\s+([\d,]+)\s*RWF\s+from\s+(.+?)\s*\(", text, re.IGNORECASE)
        if m_amt:
            fields["amount"] = _to_amount(m_amt.group(1))
            fields["sender"] = m_amt.group(2).strip()
        m_bal = re.search(r"new balance\s*:?\s*([\d,]+)\s*RWF", text, re.IGNORECASE)
        if m_bal:
            fields["new_balance"] = _to_amount(m_bal.group(1))
        m_time = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if m_time:
            fields["transaction_time"] = m_time.group(1)
        return fields

    # --- Payment (to a person, merchant, or airtime) ---
    if "payment of" in lower:
        fields["transaction_type"] = "airtime" if "airtime" in lower else "payment"
        m_tx = re.search(r"TxId:\s*(\d+)", text)
        if m_tx:
            fields["transaction_id"] = m_tx.group(1)
        m_amt = re.search(r"payment of\s+([\d,]+)\s*RWF\s+to\s+(.+?)\s+has been completed", text, re.IGNORECASE)
        if m_amt:
            fields["amount"] = _to_amount(m_amt.group(1))
            fields["receiver"] = m_amt.group(2).strip()
        m_bal = re.search(r"new balance:\s*([\d,]+)\s*RWF", text, re.IGNORECASE)
        if m_bal:
            fields["new_balance"] = _to_amount(m_bal.group(1))
        m_fee = re.search(r"Fee was\s+([\d,]+)\s*RWF", text, re.IGNORECASE)
        if m_fee:
            fields["fee"] = _to_amount(m_fee.group(1))
        m_time = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if m_time:
            fields["transaction_time"] = m_time.group(1)
        return fields

    # --- Peer transfer ("*165*S*<amount> RWF transferred to ...") ---
    if "transferred to" in lower:
        fields["transaction_type"] = "transfer"
        m_amt = re.search(r"([\d,]+)\s*RWF\s+transferred\s+to\s+(.+?)\s*\((\d+)\)", text, re.IGNORECASE)
        if m_amt:
            fields["amount"] = _to_amount(m_amt.group(1))
            fields["receiver"] = m_amt.group(2).strip()
            fields["phone_number"] = m_amt.group(3)
        m_fee = re.search(r"Fee was:?\s*([\d,]+)\s*RWF", text, re.IGNORECASE)
        if m_fee:
            fields["fee"] = _to_amount(m_fee.group(1))
        m_bal = re.search(r"New balance:\s*([\d,]+)\s*RWF", text, re.IGNORECASE)
        if m_bal:
            fields["new_balance"] = _to_amount(m_bal.group(1))
        m_time = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if m_time:
            fields["transaction_time"] = m_time.group(1)
        return fields

    # --- Direct third-party transaction ("A transaction of X RWF by COMPANY...") ---
    if "transaction of" in lower:
        fields["transaction_type"] = "third_party_transaction"
        m_amt = re.search(r"transaction of\s+([\d,]+)\s*RWF\s+by\s+(.+?)\s+on your MOMO", text, re.IGNORECASE)
        if m_amt:
            fields["amount"] = _to_amount(m_amt.group(1))
            fields["receiver"] = m_amt.group(2).strip()
        m_time = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
        if m_time:
            fields["transaction_time"] = m_time.group(1)
        return fields

    return fields  # falls through as "unknown" with raw body preserved by caller


def parse_xml(xml_path: str) -> list[dict]:
    """
    Parse the MoMo SMS XML export and return a list of transaction dicts.

    Each dict combines:
      - a stable integer `id` (1-indexed, used as the API resource ID)
      - the raw SMS metadata (address, date, readable_date, body, etc.)
      - the fields extracted from the body text (transaction_type, amount, ...)
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    transactions = []
    for idx, sms in enumerate(root.findall("sms"), start=1):
        body = sms.get("body", "")
        extracted = classify_and_extract(body)

        record = {
            "id": idx,
            "address": sms.get("address"),
            "date_raw": sms.get("date"),
            "readable_date": sms.get("readable_date"),
            "body": body,
            **extracted,
        }
        transactions.append(record)

    return transactions


def main():
    xml_path = sys.argv[1] if len(sys.argv) > 1 else "data/modified_sms_v2.xml"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "data/transactions.json"

    transactions = parse_xml(xml_path)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2, ensure_ascii=False)

    print(f"Parsed {len(transactions)} SMS records from {xml_path}")
    print(f"Wrote JSON output to {out_path}")

    # Quick breakdown so you can eyeball classification coverage
    counts = {}
    for t in transactions:
        counts[t["transaction_type"]] = counts.get(t["transaction_type"], 0) + 1
    print("\nTransaction type breakdown:")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:<25} {v}")


if __name__ == "__main__":
    main()