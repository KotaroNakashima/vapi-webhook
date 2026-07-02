import os
import traceback

import requests
import resend
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from twilio.rest import Client

app = FastAPI()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "kiimigu4@gmail.com")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

resend.api_key = RESEND_API_KEY


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/vapi")
async def vapi_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}

    print("VAPI DATA:", data)

    name = data.get("name") or ""
    party_size = data.get("party_size") or ""
    reservation_date = data.get("reservation_date") or ""
    reservation_time = data.get("reservation_time") or ""
    caller_number = data.get("caller_number") or ""

    sms_status = "not_sent"
    email_status = "not_sent"
    errors = []

    # Send data to n8n
    if N8N_WEBHOOK_URL:
        try:
            requests.post(N8N_WEBHOOK_URL, json=data, timeout=10)
            print("N8N STATUS: sent")
        except Exception as e:
            errors.append(f"n8n error: {str(e)}")
            print("N8N ERROR:", str(e))

    # Send SMS to caller
    if caller_number:
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

            sms = client.messages.create(
                body="""Thank you for contacting Sakura Omakase NYC.

Your reservation request has been received.

Reserve your table here:
https://www.opentable.com/xxxx

We look forward to welcoming you.""",
                from_=TWILIO_PHONE_NUMBER,
                to=caller_number,
            )

            sms_status = "sent"
            print("SMS SID:", sms.sid)

        except Exception as e:
            sms_status = "failed"
            errors.append(f"SMS error: {str(e)}")
            print("SMS ERROR:", str(e))
            traceback.print_exc()

    # Send email to owner
    try:
        resend.Emails.send({
            "from": "Sakura Omakase <onboarding@resend.dev>",
            "to": [OWNER_EMAIL],
            "subject": "Sakura Omakase NYC - Reservation Request",
            "text": f"""
New reservation request

Name: {name}
Party Size: {party_size}
Date: {reservation_date}
Time: {reservation_time}
Phone: {caller_number}
""",
        })

        email_status = "sent"
        print("EMAIL STATUS: sent")

    except Exception as e:
        email_status = "failed"
        errors.append(f"Email error: {str(e)}")
        print("EMAIL ERROR:", str(e))
        traceback.print_exc()

    # Always return success to Vapi to avoid apology response
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "status": "submitted",
            "message": (
                "Reservation request submitted successfully. "
                "Tell the caller: Perfect. Your reservation request has been submitted. "
                "Our team will contact you if needed. We look forward to welcoming you."
            ),
            "sms_status": sms_status,
            "email_status": email_status,
            "errors": errors,
        },
    )
