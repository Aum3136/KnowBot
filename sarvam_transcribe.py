import requests
import os
import io
from dotenv import load_dotenv
import google.generativeai as genai
from pydub import AudioSegment
import struct

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))



def add_wav_header(pcm_bytes: bytes, sample_rate: int = 48000, channels: int = 1, bit_depth: int = 16) -> bytes:
    """Add WAV header to raw PCM bytes."""
    data_size = len(pcm_bytes)
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        data_size + 36,      # file size - 8
        b'WAVE',
        b'fmt ',
        16,                  # chunk size
        1,                   # PCM format
        channels,
        sample_rate,
        sample_rate * channels * bit_depth // 8,  # byte rate
        channels * bit_depth // 8,                # block align
        bit_depth,
        b'data',
        data_size
    )
    return header + pcm_bytes

def transcribe_chunk(audio_bytes: bytes, language: str = "en-IN") -> str:
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": SARVAM_API_KEY}

    if audio_bytes[:4] == b'RIFF':
        print(f"[SARVAM] Chunk has WAV header — sending directly ({len(audio_bytes)} bytes)")
        wav_bytes = audio_bytes
    else:
        print(f"[SARVAM] Raw PCM — adding WAV header at 48kHz ({len(audio_bytes)} bytes)")
        wav_bytes = add_wav_header(audio_bytes, sample_rate=48000, channels=1, bit_depth=16)

    try:
        audio_io = io.BytesIO(wav_bytes)
        audio_seg = AudioSegment.from_wav(audio_io)
        audio_seg = audio_seg.set_frame_rate(16000).set_channels(1)
        out_io = io.BytesIO()
        audio_seg.export(out_io, format="wav")
        wav_bytes = out_io.getvalue()
        print(f"[SARVAM] Resampled to 16kHz — {len(wav_bytes)} bytes")
    except Exception as e:
        print(f"[SARVAM] Resample failed, using original: {e}")

    files = {"file": ("chunk.wav", wav_bytes, "audio/wav")}
    data = {
        "language_code": language,
        "model": "saarika:v2.5",
        "with_timestamps": False
    }

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        if response.status_code == 200:
            transcript = response.json().get("transcript", "")
            print(f"[SARVAM] Transcript: '{transcript}'")
            return transcript
        else:
            print(f"[SARVAM] Error {response.status_code}: {response.text}")
            return ""
    except Exception as e:
        print(f"[SARVAM] Request failed: {e}")
        return ""


def transcribe_file(audio_path: str, language: str = "en-IN") -> str:
    ext = os.path.splitext(audio_path)[1].lower()
    print(f"[SARVAM FILE] Processing {ext} file — chunking into 25s pieces...")
    
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": SARVAM_API_KEY}
    
    if ext == ".wav":
        return _transcribe_wav_chunked(audio_path, url, headers, language)
    else:
        return _transcribe_nonwav_chunked(audio_path, url, headers, language, ext)


def _transcribe_wav_chunked(audio_path: str, url: str, headers: dict, language: str) -> str:
    """Split WAV into 25s chunks using built-in wave module. No ffmpeg needed."""
    import wave as wave_module

    print("[SARVAM FILE] WAV detected — splitting with wave module...")
    full_transcript = []

    with wave_module.open(audio_path, 'rb') as wav:
        sample_rate  = wav.getframerate()
        channels     = wav.getnchannels()
        sampwidth    = wav.getsampwidth()
        total_frames = wav.getnframes()
        duration     = total_frames / sample_rate
        print(f"[SARVAM FILE] Duration: {duration:.1f}s | Sample rate: {sample_rate}Hz | Channels: {channels}")

        chunk_frames = sample_rate * 25  # 25 seconds per chunk
        chunk_num = 0

        while True:
            frames = wav.readframes(chunk_frames)
            if not frames:
                break

            chunk_num += 1
            print(f"[SARVAM FILE] Transcribing WAV chunk {chunk_num}...")

            chunk_buffer = io.BytesIO()
            with wave_module.open(chunk_buffer, 'wb') as chunk_wav:
                chunk_wav.setnchannels(channels)
                chunk_wav.setsampwidth(sampwidth)
                chunk_wav.setframerate(sample_rate)
                chunk_wav.writeframes(frames)

            chunk_bytes = chunk_buffer.getvalue()
            files = {"file": (f"chunk_{chunk_num}.wav", chunk_bytes, "audio/wav")}
            data  = {"language_code": language, "model": "saarika:v2.5", "with_timestamps": False}

            response = requests.post(url, headers=headers, files=files, data=data)

            if response.status_code == 200:
                text = response.json().get("transcript", "")
                print(f"[SARVAM FILE] Chunk {chunk_num}: '{text[:60]}'")
                if text.strip():
                    full_transcript.append(text)
            else:
                print(f"[SARVAM FILE] Chunk {chunk_num} error: {response.status_code} — {response.text}")

    result = " ".join(full_transcript)
    print(f"[SARVAM FILE] Done — {len(full_transcript)} chunks — {len(result)} chars total")
    return result


def _transcribe_nonwav_chunked(audio_path: str, url: str, headers: dict, language: str, ext: str) -> str:
    """
    Split MP3/M4A/OGG into 25s chunks by estimating byte boundaries.
    Uses only mutagen for duration — no ffmpeg needed.
    """
    mime_map = {
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".ogg": "audio/ogg",
    }
    mimetype = mime_map.get(ext, "audio/mpeg")

    # Get duration using mutagen (no ffmpeg needed)
    try:
        from mutagen import File as MutagenFile
        audio_info = MutagenFile(audio_path)
        duration = audio_info.info.length
        print(f"[SARVAM FILE] {ext} duration: {duration:.1f}s")
    except Exception as e:
        print(f"[SARVAM FILE] Could not read duration: {e} — sending as single file")
        # Fallback: send as single file
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, mimetype)}
            data = {"language_code": language, "model": "saarika:v2.5", "with_timestamps": False}
            response = requests.post(url, headers=headers, files=files, data=data)
        if response.status_code == 200:
            return response.json().get("transcript", "")
        return ""

    # If under 28s send directly — no need to chunk
    if duration <= 28:
        print(f"[SARVAM FILE] Under 28s — sending directly")
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, mimetype)}
            data = {"language_code": language, "model": "saarika:v2.5", "with_timestamps": False}
            response = requests.post(url, headers=headers, files=files, data=data)
        if response.status_code == 200:
            transcript = response.json().get("transcript", "")
            print(f"[SARVAM FILE] Transcript: '{transcript[:100]}'")
            return transcript
        else:
            print(f"[SARVAM FILE] Error {response.status_code}: {response.text}")
            return ""

    # Over 28s — split by byte estimation
    with open(audio_path, "rb") as f:
        all_bytes = f.read()

    total_bytes = len(all_bytes)
    bytes_per_second = total_bytes / duration
    chunk_size = int(bytes_per_second * 25)  # 25 seconds worth of bytes

    full_transcript = []
    chunk_num = 0
    offset = 0

    while offset < total_bytes:
        chunk_num += 1
        chunk = all_bytes[offset:offset + chunk_size]
        offset += chunk_size

        print(f"[SARVAM FILE] Chunk {chunk_num}: {len(chunk)} bytes")

        files = {"file": (f"chunk_{chunk_num}{ext}", chunk, mimetype)}
        data  = {"language_code": language, "model": "saarika:v2.5", "with_timestamps": False}

        response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code == 200:
            text = response.json().get("transcript", "")
            print(f"[SARVAM FILE] Chunk {chunk_num}: '{text[:60]}'")
            if text.strip():
                full_transcript.append(text)
        else:
            print(f"[SARVAM FILE] Chunk {chunk_num} error {response.status_code}: {response.text}")

    result = " ".join(full_transcript)
    print(f"[SARVAM FILE] Done — {len(full_transcript)} chunks — {len(result)} chars total")
    return result

def generate_meeting_notes(transcript: str, meeting_type: str = "internal") -> dict:
    """
    Takes full transcript and generates structured meeting notes using Gemini.
    Returns a dictionary with all sections.
    """
    if not transcript.strip():
        return {"error": "Empty transcript — nothing to summarize."}

    # Different prompts for different meeting types
    context = {
        "internal": "This is an internal team meeting at an IT company.",
        "remote":   "This is a remote meeting with distributed team members.",
        "client":   "This is a client call. Focus on commitments and deliverables."
    }.get(meeting_type, "This is a business meeting.")

    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
{context}

You are an expert meeting notes assistant. Analyze this transcript and generate structured meeting notes.

Return your response in this EXACT format:

SUMMARY:
[2-3 sentence overview of what was discussed]

KEY DECISIONS:
- [Decision 1]
- [Decision 2]

ACTION ITEMS:
- [Person name if mentioned]: [Task] by [deadline if mentioned]
- [Person name if mentioned]: [Task] by [deadline if mentioned]

OPEN QUESTIONS:
- [Any unresolved questions or topics]

NEXT STEPS:
[What happens after this meeting]

TRANSCRIPT:
{transcript}
"""

    try:
        response = model.generate_content(prompt)
        raw_notes = response.text

        # Parse into sections
        sections = {
            "raw": raw_notes,
            "summary": extract_section(raw_notes, "SUMMARY"),
            "decisions": extract_section(raw_notes, "KEY DECISIONS"),
            "action_items": extract_section(raw_notes, "ACTION ITEMS"),
            "open_questions": extract_section(raw_notes, "OPEN QUESTIONS"),
            "next_steps": extract_section(raw_notes, "NEXT STEPS")
        }
        return sections

    except Exception as e:
        return {"error": f"Notes generation failed: {str(e)}"}

def extract_section(text: str, section_name: str) -> str:
    """Helper to extract a specific section from the notes."""
    try:
        lines = text.split('\n')
        capturing = False
        result = []

        for line in lines:
            if section_name + ":" in line:
                capturing = True
                continue
            elif any(s + ":" in line for s in [
                "SUMMARY", "KEY DECISIONS", "ACTION ITEMS",
                "OPEN QUESTIONS", "NEXT STEPS"
            ]) and capturing:
                break
            elif capturing and line.strip():
                result.append(line)

        return '\n'.join(result).strip()
    except:
        return ""