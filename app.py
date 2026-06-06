"""
Le & Zel — Wedding WhatsApp Sender
Simple Flask web app to trigger bulk WhatsApp sends from your phone.
"""

import csv
import json
import os
import time

from flask import Flask, jsonify, render_template
from twilio.rest import Client

app = Flask(__name__)

# ── Twilio credentials (from environment variables) ───────────────────────────
ACCOUNT_SID  = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN   = os.environ["TWILIO_AUTH_TOKEN"]
FROM_NUMBER  = os.environ.get("TWILIO_FROM_NUMBER", "+6589919363")

# ── CSV config ────────────────────────────────────────────────────────────────
CSV_FILE = os.environ.get("GUESTS_CSV_PATH", "/etc/secrets/guests.csv")

# ── Rate limiting ─────────────────────────────────────────────────────────────
DELAY_BETWEEN_SENDS = 0.2

# ── Template SIDs ─────────────────────────────────────────────────────────────
TEMPLATE_SIDS = {
    "reminder_2_week" : "HXd4eec64ed2b805119b4fb8a9cf4d6582",
    "reminder_1_week" : "HX85ce0adc53f8afcf3d351ae05f68b7f3",
    "reminder_1_day"  : "HXb79fb543dd50a24d6522a201bcbab763",
    "reminder_0_day"  : "HX3673955f7285c6cbf40999997b363fbf",
    "after"           : "HX7e1aaf2f76ac0bedb45fc757b9ddb7c4",
    "qr_media"        : "HX359f05d687494d2353a2bce6de42b232",
}


# ── Guest list ────────────────────────────────────────────────────────────────

def get_guests():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalise_phone(phone: str) -> str:
    phone = str(phone).strip()
    if not phone.startswith("+"):
        phone = f"+65{phone}"
    return phone


# ── Send helpers ──────────────────────────────────────────────────────────────

def send_reminder(client, guest, template_sid):
    phone = normalise_phone(guest["phone_number"])
    msg = client.messages.create(
        from_=f"whatsapp:{FROM_NUMBER}",
        to=f"whatsapp:{phone}",
        content_sid=template_sid,
    )
    return msg.sid, msg.status


def send_qr_media(client, guest):
    phone    = normalise_phone(guest["phone_number"])
    guest_id = str(guest["guest_id"]).strip()
    msg = client.messages.create(
        from_=f"whatsapp:{FROM_NUMBER}",
        to=f"whatsapp:{phone}",
        content_sid=TEMPLATE_SIDS["qr_media"],
        content_variables=json.dumps({"1": guest_id}),
    )
    return msg.sid, msg.status


# ── Core bulk-send logic ──────────────────────────────────────────────────────

def bulk_send(action: str):
    """
    Run a bulk send for the given action key.
    Returns a result dict with successes and failures.
    """
    guests  = get_guests()
    to_send = [g for g in guests if str(g.get("phone_number", "")).strip()]

    client     = Client(ACCOUNT_SID, AUTH_TOKEN)
    successful = []
    failed     = []

    for guest in to_send:
        name  = guest["full_name"].strip()
        phone = normalise_phone(guest["phone_number"])
        gid   = str(guest["guest_id"]).strip()

        try:
            if action == "qr_media":
                sid, status = send_qr_media(client, guest)
            else:
                sid, status = send_reminder(client, guest, TEMPLATE_SIDS[action])

            successful.append({"name": name, "phone": phone, "sid": sid, "status": status})
        except Exception as e:
            failed.append({"name": name, "phone": phone, "error": str(e)})

        time.sleep(DELAY_BETWEEN_SENDS)

    return {
        "action"    : action,
        "total"     : len(to_send),
        "successful": successful,
        "failed"    : failed,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/send/<action>", methods=["POST"])
def send(action: str):
    if action not in TEMPLATE_SIDS:
        return jsonify({"error": f"Unknown action: {action}"}), 400
    try:
        result = bulk_send(action)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/guests")
def guests():
    """Preview the loaded guest list."""
    try:
        all_guests = get_guests()
        with_phone = [g for g in all_guests if str(g.get("phone_number", "")).strip()]
        return jsonify({"total": len(all_guests), "with_phone": len(with_phone), "guests": with_phone})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
