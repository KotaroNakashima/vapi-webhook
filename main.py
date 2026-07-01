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

    intent = data.get("intent", "")
    summary = data.get("summary", "")
    name = data.get("name", "")
    party_size = data.get("party_size", "")
    reservation_date = data.get("reservation_date", "")
    reservation_time = data.get("reservation_time", "")
    caller_number = data.get("caller_number")

    try:
        sms_sid = None

        if intent == "reservation" and caller_number:
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

            sms_sid = sms.sid

        resend.Emails.send({
            "from": "Sakura Omakase <onboarding@resend.dev>",
            "to": [OWNER_EMAIL],
            "subject": f"Sakura Omakase NYC - {intent}",
            "text": f"""
New reservation request

Name: {name}
Party Size: {party_size}
Date: {reservation_date}
Time: {reservation_time}
Phone: {caller_number}

Summary:
{summary}
""",
        })

        return {
            "success": True,
            "message": "Request submitted successfully.",
        }

    except Exception as e:
        print(e)

        return {
            "success": False,
            "message": str(e),
        }
