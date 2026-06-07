import os

import resend
from fastapi import FastAPI, Request
from twilio.rest import Client

app = FastAPI()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "kiimigu4@gmail.com")

resend.api_key = RESEND_API_KEY


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/vapi")
async def vapi_webhook(request: Request):
    data = await request.json()

    intent = data.get("intent", "unknown")
    summary = data.get("summary", "")
    caller_number = data.get("caller_number")

    if not caller_number:
        return {
            "success": False,
            "error": "Missing caller_number",
            "received": data,
        }

    sms_body = """Thank you for contacting Sakura Omakase NYC.

Reserve your table here:
https://www.opentable.com/xxxx

We look forward to welcoming you."""

    try:
        sms_sid = None

        if intent == "reservation":
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            sms = client.messages.create(
                body=sms_body,
                from_=TWILIO_PHONE_NUMBER,
                to=caller_number,
            )
            sms_sid = sms.sid

        email_subject = f"Sakura Omakase NYC Inquiry: {intent}"

        email_body = f"""
New guest request received.

Intent:
{intent}

Summary:
{summary}

Caller Number:
{caller_number}
"""

        print("Sending owner email via Resend...")

        resend.Emails.send({
            "from": "Sakura Omakase <onboarding@resend.dev>",
            "to": [OWNER_EMAIL],
            "subject": email_subject,
            "text": email_body,
        })

        print("Owner email sent successfully via Resend")

        return {
            "success": True,
            "intent": intent,
            "sms_sent": intent == "reservation",
            "sms_sid": sms_sid,
            "owner_notified": True,
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "success": False,
            "error": str(e),
        }

