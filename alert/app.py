from flask import Flask, send_file, request, abort
from twilio.rest import Client
import secrets
import time
import os
from dotenv import load_dotenv
load_dotenv('details.env')
NGROK_URL =  os.getenv("NGROK_URL")
account_sid= os.getenv("account_sid")
auth_token=os.getenv("auth_token")
client = Client(account_sid, auth_token)


PDF_PATH = "D:\Project_HeartAttackPrediction&AlertSystem\Survey Paper\Results_project_new.pdf"
TOKEN_EXPIRY_SECONDS = 300  # 5 minutes

# ----------------------------------------

app = Flask(__name__)

# In-memory token store (OK for local testing)
TOKENS = {}


@app.route("/pdf")
def serve_pdf():
    token = request.args.get("token")

    if not token or token not in TOKENS:
        abort(403)

    if TOKENS[token] < time.time():
        del TOKENS[token]
        abort(403)

    # one-time use
    del TOKENS[token]

    return send_file(
        PDF_PATH,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="report.pdf"
    )


@app.route("/")
# WhatsApp Sandbox is used for testing which is active for only 3 days
def send_notification():
    token = secrets.token_urlsafe(32)
    TOKENS[token] = time.time() + TOKEN_EXPIRY_SECONDS
    name = "John Doe"
    msg=f"Medical Alert: Abnormal heart activity detected. Please find the detailed report attached. Patient Name: {name}."
    pdf_url = f"{NGROK_URL}/pdf?token={token}"
    from_="whatsapp:"+os.getenv("from_number_whatsapp")
    to="whatsapp:"+os.getenv("to_number")
    message = client.messages.create(
    from_=from_,
    to=to,
    body=msg,
    media_url=[pdf_url]
)
    name = "John Doe"
    condition = "Heart Attack Detected"
    severity = "Very High"
    location = "123 Main St, Anytown, USA"
    twiml = f"""
    <Response>
        <Say voice="alice">
            This is an automated medical alert. Abnormal heart activity has been detected. The patient may be experiencing a cardiac emergency. 
            Name: {name}.
            Condition: {condition}.
            Severity: {severity}.
            Location: {location}.
            <break time="0.5s"/>
            Please seek immediate medical assistance.
        </Say>
    </Response>
    """
    call = client.calls.create(
        twiml=twiml,
        to=os.getenv("to_number"),
        from_=os.getenv("from_number"),
    )


    return {
        "status": "sent",
        "message_sid": message.sid
    }


if __name__ == "__main__":
    app.run(port=5000, debug=True)