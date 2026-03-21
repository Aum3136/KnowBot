import os
import whisper
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
model = ChatGoogleGenerativeAI(model='gemini-2.5-flash',api_key=os.getenv("GEMINI_API_KEY"))

def transcribe_meeting(audio_path):
    try:
        # Load Whisper model (base = fast, runs on CPU, free)
        model = whisper.load_model("base")
        print("Transcribing audio...")
        result = model.transcribe(audio_path)
        transcript = result["text"]
        return transcript
    except Exception as e:
        return f"Transcription error: {str(e)}"

def summarize_transcript(transcript):
    try:
        gemini = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
You are an expert meeting assistant for an IT company.
Analyze this meeting transcript and provide:

1. MEETING SUMMARY (3-4 sentences)
2. KEY DECISIONS MADE
3. ACTION ITEMS (with owner if mentioned)
4. FOLLOW-UP REQUIRED

Transcript:
{transcript}
"""
        response = gemini.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Summarization error: {str(e)}"