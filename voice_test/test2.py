import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SARVAM_API_KEY")

def transcribe_file(audio_path, language="hi-IN"):
    """
    Send an audio file to Sarvam and get transcript back.
    Supported languages:
      hi-IN = Hindi
      en-IN = English (Indian accent)
      gu-IN = Gujarati
      mr-IN = Marathi
      bn-IN = Bengali
      kn-IN = Kannada
      ml-IN = Malayalam
      od-IN = Odia
      pa-IN = Punjabi
      ta-IN = Tamil
      te-IN = Telugu
    """
    url = "https://api.sarvam.ai/speech-to-text"

    headers = {
        "api-subscription-key": API_KEY
    }

    with open(audio_path, "rb") as audio_file:
        files = {
            "file": (os.path.basename(audio_path), audio_file, "audio/wav")
        }
        data = {
            "language_code": language,
            "model": "saarika:v2.5",        # Sarvam's latest model
            "with_timestamps": False,
            "with_diarization": False      # set True to detect who spoke
        }

        print(f"Sending {audio_path} to Sarvam API...")
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        transcript = result.get("transcript", "")
        print(f"\nTRANSCRIPT:\n{transcript}")
        return transcript
    else:
        print(f"ERROR: {response.status_code}")
        print(f"Details: {response.text}")
        return None

# Test with any audio file you have
# Change this path to any .wav or .mp3 file on your computer
AUDIO_FILE = r"D:\Aum\KnowBot\voice_test\harvard.wav"

if os.path.exists(AUDIO_FILE):
    transcribe_file(AUDIO_FILE, language="en-IN")
else:
    print(f"Audio file '{AUDIO_FILE}' not found.")
    print("Run poc_test3_record.py first to record a test audio.")