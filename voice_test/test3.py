import requests
import os
import wave
import tempfile
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SARVAM_API_KEY")

def record_audio(duration=120, sample_rate=16000):
    """Record audio from microphone."""
    try:
        import pyaudio
        print(f"Recording for {duration} seconds... SPEAK NOW!")
        print("(Say something in English or Hindi)")

        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=1024
        )

        frames = []
        for i in range(0, int(sample_rate / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)
            # Show progress every second
            if i % int(sample_rate / 1024) == 0:
                seconds_left = duration - (i // int(sample_rate / 1024))
                print(f"  {seconds_left} seconds remaining...")

        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save to wav file
        output_path = "test_audio.wav"
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))

        print(f"\nRecording saved to {output_path}")
        return output_path

    except ImportError:
        print("pyaudio not installed. Install it with:")
        print("  pip install pyaudio")
        print("  OR on Windows: pipwin install pyaudio")
        return None

def transcribe_audio(audio_path, language="en-IN"):
    """Send audio to Sarvam API."""
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": API_KEY}

    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        data = {
            "language_code": language,
            "model": "saarika:v2.5",
            "with_timestamps": False
        }
        print("\nSending to Sarvam API...")
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code == 200:
        transcript = response.json().get("transcript", "")
        print(f"\n{'='*50}")
        print("TRANSCRIPT:")
        print(transcript)
        print('='*50)
        return transcript
    else:
        print(f"ERROR {response.status_code}: {response.text}")
        return None

def generate_quick_notes(transcript):
    """Quick test of Gemini summarization."""
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
You are a meeting notes assistant.
Given this transcript, extract:
1. SUMMARY (2-3 sentences)
2. ACTION ITEMS (bullet points)
3. KEY DECISIONS

Transcript:
{transcript}
"""
    response = model.generate_content(prompt)
    print(f"\n{'='*50}")
    print("MEETING NOTES:")
    print(response.text)
    print('='*50)
    return response.text

# ── MAIN POC FLOW ──
print("=== SARVAM REAL-TIME TRANSCRIPTION POC ===\n")

# Step 1: Record
audio_file = record_audio(duration=10)

if audio_file:
    # Step 2: Transcribe with Sarvam
    transcript = transcribe_audio(audio_file, language="en-IN")

    if transcript:
        # Step 3: Generate notes with Gemini
        print("\nGenerating meeting notes...")
        notes = generate_quick_notes(transcript)
        print("\nPOC COMPLETE! Everything works.")
        print("Ready to integrate into KnowBot.")
    else:
        print("Transcription failed. Check your API key.")
else:
    print("Recording failed. Check your microphone.")
