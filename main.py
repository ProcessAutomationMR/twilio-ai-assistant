from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Webhook URLs (Replace these with actual Make Webhook URLs)
APPOINTMENT_WEBHOOK_URL = "https://hook.eu2.make.com/89y802twbjje331bwc8g8r65xsa57csa"
MESSAGE_WEBHOOK_URL = "https://hook.eu2.make.com/sxq5pwjhs7lsdfc0f5rg3fuq79ih5i7z"

@app.route("/voice", methods=['POST'])
def voice():
    """ Handles the incoming call and prompts the user """
    response = VoiceResponse()
    
    gather = Gather(input="speech", action="/handle_response", language="fr-FR", timeout=5)
    gather.say("Bonjour, je suis Julia. Souhaitez-vous prendre rendez-vous ou laisser un message?", voice="alice")
    
    response.append(gather)
    return Response(str(response), mimetype="text/xml")

@app.route("/handle_response", methods=['POST'])
def handle_response():
    """ Processes the user's response to determine next steps """
    response = VoiceResponse()
    user_input = request.form.get("SpeechResult", "").lower()

    if "rendez-vous" in user_input or "appointment" in user_input:
        gather = Gather(input="speech", action="/handle_appointment", language="fr-FR", timeout=5)
        gather.say("Quelle date et heure souhaitez-vous?", voice="alice")
        response.append(gather)

    elif "message" in user_input:
        response.say("Je vous écoute.", voice="alice")
        response.record(action="/handle_message", timeout=10, transcribe=True, transcribe_callback="/transcription_callback")

    else:
        response.say("Je n'ai pas compris, veuillez répéter.", voice="alice")
        response.redirect("/voice")

    return Response(str(response), mimetype="text/xml")

@app.route("/handle_appointment", methods=['POST'])
def handle_appointment():
    """ Sends the appointment details to the Make Webhook """
    appointment_time = request.form.get("SpeechResult", "").strip()
    
    try:
        iso_datetime = datetime.strptime(appointment_time, "%d %B %Y %H:%M").isoformat()
        requests.post(APPOINTMENT_WEBHOOK_URL, json={"appointment_time": iso_datetime})
    except ValueError:
        response = VoiceResponse()
        response.say("Je n'ai pas compris la date et l'heure. Veuillez réessayer.", voice="alice")
        response.redirect("/voice")
        return Response(str(response), mimetype="text/xml")

    response = VoiceResponse()
    response.say("Votre rendez-vous a été enregistré. Merci.", voice="alice")
    return Response(str(response), mimetype="text/xml")

@app.route("/handle_message", methods=['POST'])
def handle_message():
    """ Sends the recorded message to the Make Webhook """
    recording_url = request.form.get("RecordingUrl")

    requests.post(MESSAGE_WEBHOOK_URL, json={"recording_url": recording_url})

    response = VoiceResponse()
    response.say("Votre message a été enregistré. Merci.", voice="alice")
    return Response(str(response), mimetype="text/xml")

@app.route("/transcription_callback", methods=['POST'])
def transcription_callback():
    """ Handles transcription and sends it to Make Webhook """
    transcript = request.form.get("TranscriptionText", "")
    
    if transcript:
        requests.post(MESSAGE_WEBHOOK_URL, json={"message_text": transcript})

    return ("", 204)

if __name__ == "__main__":
    app.run(port=5000)
