# SmartScribe - single-file Flask application
# Converted from the supplied Colab notebook.
# Colab/ngrok startup commands have been removed.
# Do NOT put API keys, passwords, or ngrok tokens in this file.

import os
import subprocess
import shutil
import time
import threading
import hashlib
import uuid
import base64
import io
import re
import json
import sqlite3
import wave
import struct

import numpy as np
import cv2
import face_recognition

from datetime import datetime
from contextlib import contextmanager
from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import PyPDF2
from flask import make_response

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ==================== ORIGINAL NOTEBOOK CELL 2 ====================
# ==================== CELL 2: IMPORTS & DATABASE ====================
from contextlib import contextmanager



from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ==================== DATABASE SETUP ====================
DB_PATH = 'smartscribe.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS students (
                reg_no TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                image TEXT NOT NULL,
                face_encoding TEXT NOT NULL,
                voice_embedding TEXT,
                voice_wav_b64 TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
        for col in [('voice_embedding','TEXT'), ('voice_wav_b64','TEXT')]:
            try: c.execute(f'ALTER TABLE students ADD COLUMN {col[0]} {col[1]}')
            except: pass
        c.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                pdf TEXT NOT NULL,
                questions TEXT NOT NULL,
                duration_minutes INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
        try: c.execute('ALTER TABLE exams ADD COLUMN duration_minutes INTEGER DEFAULT 60')
        except: pass
        c.execute('''
            CREATE TABLE IF NOT EXISTS exam_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_no TEXT NOT NULL,
                student_name TEXT NOT NULL,
                exam_id TEXT NOT NULL,
                exam_name TEXT NOT NULL,
                answers TEXT NOT NULL,
                pdf_data BLOB,
                pdf_filename TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
        for col in [('student_name','TEXT DEFAULT ""'),('exam_name','TEXT DEFAULT ""'),
                    ('pdf_data','BLOB'),('pdf_filename','TEXT')]:
            try: c.execute(f'ALTER TABLE exam_submissions ADD COLUMN {col[0]} {col[1]}')
            except: pass
        print('✅ Database initialized')

init_db()


# ==================== ORIGINAL NOTEBOOK CELL 3 ====================
# ==================== CELL 3: FLASK APP & ALL CORE FUNCTIONS ====================

app = Flask(__name__)
app.secret_key = 'smartscribe_key'
CORS(app)

# ─── FACE HELPERS ─────────────────────────────────────────
def extract_face_features(image_data):
    """Extract exactly one face encoding from a base64 image."""
    try:
        if not image_data:
            return None
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]
        img_bytes = base64.b64decode(image_data, validate=True)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Use HOG for fast browser verification and require exactly one face.
        locations = face_recognition.face_locations(rgb_img, model='hog')
        if len(locations) == 0:
            print('Face extraction: no face detected')
            return None
        if len(locations) > 1:
            print(f'Face extraction: {len(locations)} faces detected')
            return None

        encs = face_recognition.face_encodings(rgb_img, known_face_locations=locations, num_jitters=2)
        if not encs:
            return None
        return encs[0].tolist()
    except Exception as e:
        print(f"Face extraction error: {e}")
        return None

# IMPORTANT: lower than the old 0.60 threshold.
# 0.45 is deliberately stricter to reduce false acceptance of another person.
FACE_MATCH_THRESHOLD = 0.45

def verify_face(registered_encoding, captured_image):
    try:
        if not registered_encoding:
            return False, "No registered face"
        cap_enc = extract_face_features(captured_image)
        if cap_enc is None:
            return False, "Show only one face clearly in the camera"

        reg = np.asarray(registered_encoding, dtype=np.float64)
        cap = np.asarray(cap_enc, dtype=np.float64)
        if reg.shape != cap.shape:
            return False, "Registered face data is invalid"

        dist = float(np.linalg.norm(reg - cap))
        print(f"Face distance: {dist:.4f} | threshold: {FACE_MATCH_THRESHOLD}")

        if dist <= FACE_MATCH_THRESHOLD:
            return True, f"Face verified (distance={dist:.3f})"
        return False, f"Face does not match (distance={dist:.3f})"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Face error: {e}"

# ─── WAV CONVERSION ────────────────────────────────────────
# Browser records as audio/webm (or audio/wav on some browsers).
# We convert anything to raw PCM using pydub+ffmpeg so MFCC works reliably.
def audio_b64_to_pcm_numpy(audio_b64: str, target_sr: int = 16000):
    """
    Convert browser-recorded audio (WebM/Opus/WAV/OGG/etc.)
    into mono 16 kHz PCM using FFmpeg.
    Returns (numpy float32 PCM, clean WAV base64).
    """
    try:
        if shutil.which("ffmpeg") is None:
            print("ERROR: FFmpeg not found in PATH")
            return None, None

        if audio_b64.startswith("data:") and "," in audio_b64:
            audio_b64 = audio_b64.split(",", 1)[1]

        raw_bytes = base64.b64decode(audio_b64)
        if not raw_bytes:
            print("ERROR: Empty audio data")
            return None, None

        print(f"Received audio: {len(raw_bytes)} bytes")

        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error",
             "-i", "pipe:0", "-ar", str(target_sr), "-ac", "1",
             "-sample_fmt", "s16", "-f", "wav", "pipe:1"],
            input=raw_bytes, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=True
        )

        wav_bytes = result.stdout
        if not wav_bytes:
            print("ERROR: FFmpeg produced empty WAV")
            return None, None

        print(f"FFmpeg converted audio to WAV: {len(wav_bytes)} bytes")

        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            frames = wf.readframes(wf.getnframes())

        pcm = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        wav_b64 = base64.b64encode(wav_bytes).decode("utf-8")

        print(f"Audio processed successfully: {len(pcm)} samples, {len(pcm)/target_sr:.2f} seconds")
        return pcm, wav_b64

    except subprocess.CalledProcessError as e:
        print("FFmpeg conversion error:")
        print(e.stderr.decode("utf-8", errors="ignore"))
        return None, None
    except Exception as e:
        print("audio_b64_to_pcm_numpy error:", e)
        return None, None

# ─── MFCC VOICE EMBEDDING ──────────────────────────────────
# Pure numpy: fast, no heavy ML library required.
# ─── IMPROVED VOICE VERIFICATION ───────────────────────────

def extract_mfcc_embedding(pcm, sr=16000, n_mfcc=20, n_fft=512, hop=160):
    """
    Create a more speaker-sensitive voice embedding.

    Uses:
    - MFCC mean
    - MFCC standard deviation
    - Delta MFCC mean
    - Delta MFCC standard deviation

    This is stronger than using only MFCC mean.
    """

    if pcm is None or len(pcm) < sr * 1.0:
        return None

    # Convert to float32
    pcm = np.asarray(pcm, dtype=np.float32)

    # Remove DC offset
    pcm = pcm - np.mean(pcm)

    # Normalize volume
    max_val = np.max(np.abs(pcm))
    if max_val > 0:
        pcm = pcm / max_val

    # Pre-emphasis
    pre = np.append(
        pcm[0],
        pcm[1:] - 0.97 * pcm[:-1]
    )

    # Framing
    frames = []

    for start in range(0, len(pre) - n_fft + 1, hop):
        frame = pre[start:start + n_fft]

        if len(frame) == n_fft:
            frames.append(
                frame * np.hamming(n_fft)
            )

    if len(frames) < 5:
        return None

    frames = np.asarray(frames, dtype=np.float32)

    # FFT
    spectrum = np.fft.rfft(frames, n=n_fft)
    magnitude = np.abs(spectrum)

    power = magnitude ** 2

    # ---------------------------------------------------------
    # MEL FILTER BANK
    # ---------------------------------------------------------

    n_mels = 40

    mel_min = 0
    mel_max = 2595 * np.log10(
        1 + (sr / 2) / 700
    )

    mel_points = np.linspace(
        mel_min,
        mel_max,
        n_mels + 2
    )

    hz_points = 700 * (
        10 ** (mel_points / 2595) - 1
    )

    bins = np.floor(
        (n_fft + 1) * hz_points / sr
    ).astype(int)

    filter_bank = np.zeros(
        (n_mels, n_fft // 2 + 1),
        dtype=np.float32
    )

    for m in range(1, n_mels + 1):

        left = bins[m - 1]
        center = bins[m]
        right = bins[m + 1]

        if center > left:
            for k in range(left, center):
                filter_bank[m - 1, k] = (
                    (k - left) /
                    (center - left)
                )

        if right > center:
            for k in range(center, right):
                filter_bank[m - 1, k] = (
                    (right - k) /
                    (right - center)
                )

    # Mel energy
    mel_energy = np.dot(
        power,
        filter_bank.T
    )

    mel_energy = np.maximum(
        mel_energy,
        1e-10
    )

    log_mel = np.log(mel_energy)

    # ---------------------------------------------------------
    # DCT → MFCC
    # ---------------------------------------------------------

    dct_matrix = np.cos(
        np.pi / n_mels *
        np.outer(
            np.arange(n_mfcc),
            np.arange(0.5, n_mels)
        )
    )

    mfcc = np.dot(
        log_mel,
        dct_matrix.T
    )

    # Ignore energy coefficient
    mfcc = mfcc[:, 1:]

    # ---------------------------------------------------------
    # DELTA MFCC
    # ---------------------------------------------------------

    if len(mfcc) > 2:

        delta = np.gradient(
            mfcc,
            axis=0
        )

    else:
        delta = np.zeros_like(mfcc)

    # ---------------------------------------------------------
    # BUILD STRONGER EMBEDDING
    # ---------------------------------------------------------

    mfcc_mean = np.mean(
        mfcc,
        axis=0
    )

    mfcc_std = np.std(
        mfcc,
        axis=0
    )

    delta_mean = np.mean(
        delta,
        axis=0
    )

    delta_std = np.std(
        delta,
        axis=0
    )

    embedding = np.concatenate([
        mfcc_mean,
        mfcc_std,
        delta_mean,
        delta_std
    ]).astype(np.float32)

    # ---------------------------------------------------------
    # NORMALIZE
    # ---------------------------------------------------------

    norm = np.linalg.norm(
        embedding
    )

    if norm <= 1e-8:
        return None

    embedding = embedding / norm

    return embedding


def compute_voice_embedding(audio_b64: str):

    """
    Convert browser audio → PCM → voice embedding.
    """

    pcm, wav_b64 = audio_b64_to_pcm_numpy(
        audio_b64
    )

    if pcm is None:
        return None, None

    # Check minimum useful duration
    duration = len(pcm) / 16000

    if duration < 1.0:
        print(
            f"Voice too short: {duration:.2f}s"
        )
        return None, None

    embedding = extract_mfcc_embedding(
        pcm,
        sr=16000
    )

    if embedding is None:
        print("Could not create voice embedding")
        return None, None

    print(
        f"Voice embedding created: "
        f"{len(embedding)} dimensions"
    )

    return embedding, wav_b64


def cosine_sim(a, b):

    a = np.asarray(
        a,
        dtype=np.float32
    )

    b = np.asarray(
        b,
        dtype=np.float32
    )

    # Safety check
    if len(a) != len(b):
        print(
            f"Embedding size mismatch: "
            f"{len(a)} vs {len(b)}"
        )
        return 0.0

    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)

    if a_norm <= 1e-8 or b_norm <= 1e-8:
        return 0.0

    a = a / a_norm
    b = b / b_norm

    return float(
        np.dot(a, b)
    )


# ------------------------------------------------------------
# VOICE VERIFICATION THRESHOLDS
# ------------------------------------------------------------

VOICE_LOGIN_THRESHOLD = 0.90
VOICE_MONITOR_THRESHOLD = 0.85


def verify_voice_embedding(
    registered_list,
    audio_b64: str
):

    """
    Compare student's current voice
    against registered voice.
    """

    if not registered_list:
        return (
            False,
            "No registered voice found",
            0.0
        )

    emb, _ = compute_voice_embedding(
        audio_b64
    )

    if emb is None:
        return (
            False,
            "Voice sample too short or unclear",
            0.0
        )

    try:

        registered = np.asarray(
            registered_list,
            dtype=np.float32
        )

        # Check embedding size
        if registered.shape != emb.shape:

            print(
                "Registered embedding shape:",
                registered.shape
            )

            print(
                "Current embedding shape:",
                emb.shape
            )

            return (
                False,
                "Voice registration is outdated. Please register your voice again.",
                0.0
            )

        similarity = cosine_sim(
            registered,
            emb
        )

        print(
            f"VOICE SIMILARITY = {similarity:.4f}"
        )

        print(
            f"VOICE THRESHOLD = {VOICE_LOGIN_THRESHOLD:.2f}"
        )

        if similarity >= VOICE_LOGIN_THRESHOLD:

            return (
                True,
                f"Voice verified (similarity={similarity:.2f})",
                similarity
            )

        return (
            False,
            f"Voice does not match "
            f"(similarity={similarity:.2f})",
            similarity
        )

    except Exception as e:

        print(
            "Voice verification error:",
            e
        )

        return (
            False,
            "Voice verification failed",
            0.0
        )

def compute_voice_embedding(audio_b64: str):
    """Returns (embedding_array_or_None, clean_wav_b64_or_None)"""
    pcm, wav_b64 = audio_b64_to_pcm_numpy(audio_b64)
    if pcm is None: return None, None
    emb = extract_mfcc_embedding(pcm)
    return emb, wav_b64

def cosine_sim(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    d = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / d) if d > 0 else 0.0

# Login threshold: strict. Monitor threshold: slightly looser.
# Raised thresholds for better speaker discrimination
VOICE_LOGIN_THRESHOLD   = 0.82   # must be clearly the same speaker
VOICE_MONITOR_THRESHOLD = 0.75   # during exam — slightly looser but still strict

def verify_voice_embedding(registered_list, audio_b64: str):
    emb, _ = compute_voice_embedding(audio_b64)
    if emb is None: return False, "Voice sample too short or silent", 0.0
    sim = cosine_sim(registered_list, emb.tolist())
    print(f"Voice cosine sim: {sim:.3f}")
    if sim >= VOICE_LOGIN_THRESHOLD:
        return True, "Voice verified", sim
    return False, f"Voice does not match (similarity={sim:.2f}, need {VOICE_LOGIN_THRESHOLD})", sim

# ─── PDF GENERATION ───────────────────────────────────────
def generate_exam_pdf(student_reg, student_name, exam_name, questions_answers):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    purple = colors.HexColor('#D082D9')
    story = [
        Paragraph('SmartScribe Exam Report',
            ParagraphStyle('T', parent=styles['Title'], fontSize=18, textColor=purple, spaceAfter=6, alignment=TA_CENTER)),
        HRFlowable(width='100%', thickness=2, color=purple, spaceAfter=10),
        Paragraph(f'<b>Student:</b> {student_name} ({student_reg})',
            ParagraphStyle('I', parent=styles['Normal'], fontSize=11, spaceAfter=4)),
        Paragraph(f'<b>Exam:</b> {exam_name}',
            ParagraphStyle('I2', parent=styles['Normal'], fontSize=11, spaceAfter=4)),
        Paragraph(f'<b>Date:</b> {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            ParagraphStyle('I3', parent=styles['Normal'], fontSize=11, spaceAfter=4)),
        Spacer(1, 0.4*cm),
        HRFlowable(width='100%', thickness=1, color=colors.lightgrey, spaceAfter=10),
    ]
    qs = ParagraphStyle('Q', parent=styles['Normal'], fontSize=12, textColor=purple,
        spaceBefore=12, spaceAfter=4, fontName='Helvetica-Bold')
    as_ = ParagraphStyle('A', parent=styles['Normal'], fontSize=11, spaceAfter=6, leftIndent=10)
    def esc(t): return str(t).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    for i, qa in enumerate(questions_answers, 1):
        story.append(Paragraph(f'Q{i}: {esc(qa.get("question",""))}', qs))
        story.append(Paragraph(f'Ans: {esc(qa.get("answer","") or "[No answer]")}', as_))
    doc.build(story)
    return buffer.getvalue()

# ─── PDF / QUESTION HELPERS ────────────────────────────────
def extract_text_from_pdf(pdf_base64):
    try:
        data = base64.b64decode(pdf_base64.split(',')[1])
        r = PyPDF2.PdfReader(io.BytesIO(data))
        return ''.join(p.extract_text() or '' for p in r.pages)
    except Exception as e:
        print(f"PDF Error: {e}"); return ''

def parse_questions_from_text(text):
    questions = []
    lines = [l.strip() for l in text.splitlines()]

    # Matches:
    # 1 what is photosynthesis
    # 2 what is chlorophyll
    # 3. what is bacteria
    # 4) list diseases
    question_pattern = re.compile(
        r'^\s*(\d+)\s*(?:[.)])?\s+(.+)$'
    )

    # Matches options such as:
    # a) Oxygen
    # b) Carbon dioxide
    option_pattern = re.compile(
        r'^\s*[a-dA-D]\s*[.)]\s*(.+)$'
    )

    current = ''

    for line in lines:

        if not line:
            continue

        # Check for a numbered question
        q_match = question_pattern.match(line)

        if q_match:
            if current:
                questions.append(current.strip())

            current = q_match.group(1) + '. ' + q_match.group(2).strip()
            continue

        # Check for an option
        opt_match = option_pattern.match(line)

        if opt_match:
            if current:
                current += ' ' + line.strip()
            continue

        # Continuation of current question
        if current:
            current += ' ' + line.strip()

    # Save last question
    if current:
        questions.append(current.strip())

    # Remove duplicates
    unique = []
    seen = set()

    for q in questions:
        if q not in seen:
            seen.add(q)
            unique.append(q)

    print("===================================")
    print("EXTRACTED QUESTIONS:", len(unique))

    for i, q in enumerate(unique, 1):
        print(f"{i}. {q}")

    print("===================================")

    return unique
def format_question_for_tts(q):
    pat = re.compile(r'(?:^|\s)([a-dA-D])\)\s*', re.IGNORECASE)
    matches = list(pat.finditer(q))
    if not matches: return q
    stem = q[:matches[0].start()].strip()
    result = stem
    for idx, m in enumerate(matches):
        letter = m.group(1).lower()
        start = m.end()
        end = matches[idx+1].start() if idx+1 < len(matches) else len(q)
        opt = q[start:end].strip().rstrip('.')
        result += f'. {letter}, {opt}'
    return result


# ==================== ORIGINAL NOTEBOOK CELL 4 ====================


COMMON_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Caveat:wght@600;700&display=swap');

:root {
  --purple-accent: #7C3AED;
  --purple-bright: #8B5CF6;
  --purple-soft: #F3E8FF;
  --purple-border: #E9D5FF;
  
  --blue-primary: #2563EB;
  --blue-bright: #3B82F6;
  --blue-soft: #EFF6FF;
  --blue-border: #BFDBFE;

  --teal-accent: #0D9488;
  --teal-bright: #14B8A6;
  --teal-soft: #CCFBF1;
  --teal-border: #99F6E4;

  --cyan-bright: #06B6D4;
  --navy-darkest: #0B0F19;
  --navy-deep: #111827;
  --navy-blue: #1E293B;

  --page-bg: #F8FAFC;
  --card-bg: #FFFFFF;

  --text-dark: #0F172A;
  --text-body: #334155;
  --text-muted: #64748B;
  --text-light: #94A3B8;

  --border-color: #E2E8F0;

  --success: #10B981;
  --success-bg: #ECFDF5;
  --success-border: #A7F3D0;

  --warning: #F59E0B;
  --warning-bg: #FFFBEB;
  --warning-border: #FDE68A;

  --danger: #EF4444;
  --danger-bg: #FEF2F2;
  --danger-border: #FCA5A5;

  --shadow-sm: 0 2px 8px rgba(124, 58, 237, 0.04);
  --shadow-md: 0 10px 30px rgba(124, 58, 237, 0.08);
  --shadow-lg: 0 20px 40px rgba(15, 23, 42, 0.12);
  --shadow-purple: 0 12px 28px rgba(124, 58, 237, 0.25);
  --shadow-teal: 0 12px 28px rgba(13, 148, 136, 0.25);

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 18px;
  --radius-xl: 24px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}

*:focus-visible {
  outline: 3px solid var(--purple-accent);
  outline-offset: 2px;
}

body {
  background-color: var(--navy-darkest);
  color: var(--text-dark);
  min-height: 100vh;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  position: relative;
  overflow-x: hidden;
}

a {
  color: var(--purple-accent);
  text-decoration: none;
  transition: all 0.2s ease;
}

/* SUBTLE ANIMATED BACKGROUND BLOBS */
.animated-bg-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  z-index: 0;
  pointer-events: none;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.22;
}

.blob-1 {
  width: 550px;
  height: 550px;
  background: radial-gradient(circle, #7C3AED 0%, #8B5CF6 100%);
  top: -120px;
  left: -120px;
  animation: floatBlob1 20s ease-in-out infinite;
}

.blob-2 {
  width: 650px;
  height: 650px;
  background: radial-gradient(circle, #2563EB 0%, #3B82F6 100%);
  bottom: -160px;
  right: -160px;
  animation: floatBlob2 24s ease-in-out infinite;
}

.blob-3 {
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, #0D9488 0%, #14B8A6 100%);
  top: 40%;
  left: 35%;
  animation: floatBlob3 22s ease-in-out infinite;
}

@keyframes floatBlob1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(80px, -50px) scale(1.12); }
}

@keyframes floatBlob2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-70px, 70px) scale(0.92); }
}

@keyframes floatBlob3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(60px, 80px) scale(1.1); }
}

/* GLOBAL ENTERPRISE LAYOUT */
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: linear-gradient(180deg, #0B0F19 0%, #111827 100%);
  position: relative;
  z-index: 1;
}

.top-header-bar {
  height: 76px;
  background: rgba(11, 15, 25, 0.95);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 110;
}

.top-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon-3d {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #7C3AED 0%, #2563EB 50%, #0D9488 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
  box-shadow: 0 4px 18px rgba(124, 58, 237, 0.45);
}

.brand-text h2 {
  font-size: 20px;
  font-weight: 800;
  color: #FFFFFF;
  letter-spacing: -0.5px;
  line-height: 1.1;
}

.brand-text p {
  font-size: 11px;
  color: #94A3B8;
  font-weight: 500;
}

.top-header-center {
  flex: 1;
  max-width: 440px;
  margin: 0 32px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input-wrapper svg {
  position: absolute;
  left: 16px;
  color: #64748B;
}

.search-input {
  width: 100%;
  padding: 10px 16px 10px 44px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 30px;
  color: #FFFFFF;
  font-size: 13px;
  outline: none;
  transition: all 0.2s ease;
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--purple-accent);
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.25);
}

.top-header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.slogan-handwritten {
  font-family: 'Caveat', cursive;
  font-size: 24px;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.5px;
}

.header-action-icon {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94A3B8;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.app-body {
  display: flex;
  flex: 1;
  padding: 24px 32px 32px;
  gap: 24px;
}

/* SIDEBAR */
.sidebar {
  width: 240px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 13px 20px;
  color: #94A3B8;
  text-decoration: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #FFFFFF;
}

.nav-link.active {
  background: linear-gradient(135deg, var(--purple-accent) 0%, var(--blue-primary) 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 18px rgba(124, 58, 237, 0.4);
}

.nav-link svg {
  stroke-width: 2;
}

.sidebar-promo-card {
  margin-top: auto;
  margin-bottom: 16px;
  background: linear-gradient(180deg, rgba(124, 58, 237, 0.15) 0%, rgba(13, 148, 136, 0.2) 100%);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: var(--radius-lg);
  padding: 20px 16px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.promo-quote {
  font-size: 12px;
  color: #C4B5FD;
  line-height: 1.5;
  font-weight: 600;
  font-style: italic;
}

.logout-link {
  color: #F87171 !important;
}

.logout-link:hover {
  background: rgba(239, 68, 68, 0.12) !important;
}

/* MAIN CONTENT CONTAINER PANEL */
.main-content-panel {
  flex: 1;
  background: var(--page-bg);
  border-radius: 28px;
  padding: 36px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
  min-height: calc(100vh - 130px);
}

/* DASHBOARD PANEL LAYOUT */
.dashboard-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
}

.dash-welcome {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-dark);
  letter-spacing: -0.6px;
}

.text-purple { color: var(--purple-accent); }
.text-blue { color: var(--blue-primary); }
.text-teal { color: var(--teal-accent); }

.dash-sub {
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 4px;
}

.header-quote-box {
  background: #FFFFFF;
  border-left: 3.5px solid var(--purple-accent);
  padding: 10px 16px;
  border-radius: 8px;
  box-shadow: var(--shadow-sm);
}

.header-quote-box p {
  font-size: 12px;
  font-style: italic;
  color: var(--text-muted);
  font-weight: 500;
}

/* PROCESS / PROGRESS UI STEPPER BAR */
.student-progress-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #FFFFFF;
  border-radius: var(--radius-xl);
  padding: 20px 32px;
  margin-bottom: 32px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  overflow-x: auto;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.step-num {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #F1F5F9;
  color: var(--text-muted);
  font-weight: 800;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #CBD5E1;
}

.step-item.active .step-num {
  background: linear-gradient(135deg, var(--purple-accent) 0%, var(--blue-primary) 100%);
  color: #FFFFFF;
  border: none;
  box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
}

.step-item.completed .step-num {
  background: var(--teal-accent);
  color: #FFFFFF;
  border: none;
}

.step-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-dark);
}

.step-line {
  flex: 1;
  min-width: 24px;
  max-width: 60px;
  height: 3px;
  background: #E2E8F0;
  border-radius: 2px;
  margin: 0 8px;
}

.step-line.active {
  background: linear-gradient(90deg, var(--purple-accent) 0%, var(--teal-accent) 100%);
}

/* METRICS GRID */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 24px;
  margin-bottom: 36px;
}

.metric-card {
  background: #FFFFFF;
  border-radius: var(--radius-lg);
  padding: 24px 28px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  overflow: hidden;
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s ease;
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.metric-icon-box {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.purple-icon { background: var(--purple-soft); color: var(--purple-accent); border: 1px solid var(--purple-border); }
.blue-icon { background: var(--blue-soft); color: var(--blue-primary); border: 1px solid var(--blue-border); }
.teal-icon { background: var(--teal-soft); color: var(--teal-accent); border: 1px solid var(--teal-border); }
.orange-icon { background: #FFFBEB; color: #F59E0B; border: 1px solid #FDE68A; }

.metric-content { flex: 1; }
.metric-label { font-size: 13px; font-weight: 600; color: var(--text-muted); }
.metric-number-row { display: flex; align-items: baseline; gap: 12px; margin-top: 4px; }
.metric-num { font-size: 34px; font-weight: 800; color: var(--text-dark); line-height: 1; letter-spacing: -1px; }
.metric-trend { font-size: 12px; font-weight: 700; color: var(--success); }

/* QUICK ACTIONS GRID */
.quick-actions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.quick-actions-header h3 {
  font-size: 18px;
  font-weight: 800;
  color: var(--text-dark);
}

.see-all-link {
  font-size: 13px;
  font-weight: 700;
  color: var(--purple-accent);
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.action-card {
  background: #FFFFFF;
  border-radius: var(--radius-lg);
  padding: 24px 20px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  position: relative;
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s ease, border-color 0.22s ease;
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 35px -10px rgba(124, 58, 237, 0.2);
  border-color: var(--purple-accent);
}

.action-icon-badge {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.bg-purple-subtle { background: var(--purple-soft); color: var(--purple-accent); border: 1px solid var(--purple-border); }
.bg-blue-subtle { background: var(--blue-soft); color: var(--blue-primary); border: 1px solid var(--blue-border); }
.bg-teal-subtle { background: var(--teal-soft); color: var(--teal-accent); border: 1px solid var(--teal-border); }
.bg-amber-subtle { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
.bg-rose-subtle { background: #FFF1F2; color: #E11D48; border: 1px solid #FECDD3; }

.action-card h4 {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-dark);
  margin-bottom: 4px;
}

.action-card p {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
  margin-bottom: 16px;
}

.action-circle-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  margin-left: auto;
  transition: transform 0.2s ease;
}

.action-card:hover .action-circle-btn {
  transform: translateX(3px);
}

.btn-purple { background: var(--purple-soft); color: var(--purple-accent); }
.btn-blue { background: var(--blue-soft); color: var(--blue-primary); }
.btn-teal { background: var(--teal-soft); color: var(--teal-accent); }
.btn-amber { background: #FFFBEB; color: #D97706; }
.btn-rose { background: #FFF1F2; color: #E11D48; }

/* ENTERPRISE FORM & BUTTON STYLES (ACCESSIBLE & HIGH CONTRAST) */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 28px;
  min-height: 48px;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  text-decoration: none;
  line-height: 1.2;
}

.btn-primary {
  background: linear-gradient(135deg, var(--purple-accent) 0%, var(--blue-primary) 100%);
  color: #FFFFFF;
  box-shadow: var(--shadow-purple);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #6D28D9 0%, #1D4ED8 100%);
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(124, 58, 237, 0.45);
  color: #FFFFFF;
}

.btn-teal {
  background: linear-gradient(135deg, var(--teal-accent) 0%, #059669 100%);
  color: #FFFFFF;
  box-shadow: var(--shadow-teal);
}

.btn-teal:hover {
  background: linear-gradient(135deg, #0F766E 0%, #047857 100%);
  transform: translateY(-2px);
  color: #FFFFFF;
}

.btn-secondary {
  background: #FFFFFF;
  color: var(--text-dark);
  border: 1.5px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.btn-secondary:hover {
  background: var(--page-bg);
  border-color: var(--purple-accent);
  color: var(--purple-accent);
  transform: translateY(-1px);
}

.btn-danger {
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.25);
}

.btn-danger:hover {
  background: #B91C1C;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.35);
  color: #FFFFFF;
}

.btn-sm { padding: 8px 16px; min-height: 36px; font-size: 13px; border-radius: var(--radius-sm); }
.btn-lg { padding: 16px 36px; min-height: 54px; font-size: 17px; border-radius: var(--radius-md); }

.card {
  background: #FFFFFF;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  padding: 32px;
  margin-bottom: 24px;
}

.form-group { margin-bottom: 22px; }
.form-group label { display: block; font-size: 14px; font-weight: 700; color: var(--text-dark); margin-bottom: 8px; }
.form-control {
  width: 100%;
  padding: 14px 18px;
  min-height: 48px;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 15px;
  color: var(--text-dark);
  background: #FFFFFF;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}
.form-control:focus {
  outline: none;
  border-color: var(--purple-accent);
  box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.2);
}

/* TABLES */
.table-container {
  background: #FFFFFF;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}
.table { width: 100%; border-collapse: collapse; text-align: left; }
.table th {
  background: #F8FAFC;
  padding: 16px 20px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}
.table td { padding: 16px 20px; font-size: 14px; border-bottom: 1px solid var(--border-color); color: var(--text-dark); }
.table tbody tr:last-child td { border-bottom: none; }
.table tbody tr:hover td { background-color: #F1F5F9; }

.badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; }
.badge-success { background: var(--success-bg); color: #047857; border: 1px solid var(--success-border); }
.badge-warning { background: var(--warning-bg); color: #B45309; border: 1px solid var(--warning-border); }
.badge-primary { background: var(--purple-soft); color: var(--purple-accent); border: 1px solid var(--purple-border); }

.empty-state { text-align: center; padding: 60px 20px; }
.empty-state-icon {
  width: 60px; height: 60px; background: var(--purple-soft); color: var(--purple-accent); border-radius: 50%;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; font-size: 26px;
}
.empty-state h3 { font-size: 18px; color: var(--text-dark); margin-bottom: 6px; }
.empty-state p { color: var(--text-muted); font-size: 14px; margin-bottom: 20px; }

@media (max-width: 900px) {
  .app-body { padding: 16px; flex-direction: column; }
  .sidebar { width: 100%; }
  .main-content-panel { padding: 20px; min-height: auto; }
}
"""

def render_admin_layout(active_page, title, subtitle, content_html):
    dash_act = 'active' if active_page == 'dashboard' else ''
    cstud_act = 'active' if active_page == 'create-student' else ''
    vstud_act = 'active' if active_page == 'view-students' else ''
    cexam_act = 'active' if active_page == 'create-exam' else ''
    vexam_act = 'active' if active_page == 'view-exams' else ''
    vsub_act = 'active' if active_page == 'view-submissions' else ''

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} — SmartScribe Enterprise</title>
        <style>{COMMON_CSS}</style>
    </head>
    <body>
    <div class="animated-bg-overlay">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
    </div>
    <div class="app-shell">
        <header class="top-header-bar">
            <div class="top-header-left">
                <div class="brand-logo-container">
                    <div class="logo-icon-3d">
                        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M12 6v8"/><path d="M8 10h8"/></svg>
                    </div>
                    <div class="brand-text">
                        <h2>SmartScribe</h2>
                        <p>AI Exam Assistant for Visually Impaired Students</p>
                    </div>
                </div>
            </div>
            <div class="top-header-center">
                <div class="search-input-wrapper">
                    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                    <input type="text" placeholder="Search students, exams..." class="search-input">
                </div>
            </div>
            <div class="top-header-right">
                <div class="slogan-handwritten">Education Without Limits</div>
                <div class="header-action-icon">
                    <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                </div>
            </div>
        </header>

        <div class="app-body">
            <aside class="sidebar" id="sidebar">
                <nav class="sidebar-nav">
                    <a href="/admin-dashboard" class="nav-link {dash_act}">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
                        Home
                    </a>
                    <a href="/view-students" class="nav-link {vstud_act}">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                        Students
                    </a>
                    <a href="/view-exams" class="nav-link {vexam_act}">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                        Exams
                    </a>
                    <a href="/view-submissions" class="nav-link {vsub_act}">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        Submissions
                    </a>
                </nav>

                <div class="sidebar-promo-card">
                    <div class="sidebar-promo-text">
                        <p class="promo-quote">"Same Education, Same Opportunities, A Brighter Tomorrow"</p>
                    </div>
                </div>

                <div class="sidebar-footer">
                    <a href="/" class="nav-link logout-link">
                        <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
                        Logout
                    </a>
                </div>
            </aside>

            <main class="main-content-panel">
                {content_html}
            </main>
        </div>
    </div>
    </body>
    </html>
    """)


from flask import render_template_string, request


@app.route('/')
def home():
    return render_template_string("""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>SmartScribe — Enterprise AI Examination Platform</title>
    <style>""" + COMMON_CSS + """
        .hero-bg {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 40px 20px;
            background: linear-gradient(180deg, #0B0F19 0%, #111827 100%);
            color: #FFFFFF;
            position: relative;
            z-index: 1;
        }
        .hero-container {
            max-width: 940px;
            width: 100%;
            text-align: center;
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 22px;
            background: rgba(124, 58, 237, 0.15);
            border: 1px solid rgba(139, 92, 246, 0.35);
            border-radius: 30px;
            color: #C4B5FD;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 24px;
        }
        .hero-title {
            font-size: 52px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -1.5px;
            margin-bottom: 16px;
            line-height: 1.1;
        }
        .hero-subtitle {
            font-size: 18px;
            color: #94A3B8;
            max-width: 660px;
            margin: 0 auto 52px;
            line-height: 1.6;
        }
        .role-selection {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 28px;
            margin-bottom: 40px;
        }
        .role-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: var(--radius-xl);
            padding: 40px 32px;
            text-align: left;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35);
            position: relative;
            overflow: hidden;
        }
        .role-card:hover {
            transform: translateY(-6px);
            border-color: var(--purple-accent);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 24px 48px rgba(124, 58, 237, 0.3);
        }
        .role-icon-box {
            width: 56px;
            height: 56px;
            border-radius: 16px;
            background: rgba(124, 58, 237, 0.2);
            color: #A78BFA;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
            border: 1px solid rgba(139, 92, 246, 0.35);
        }
        .role-card h3 {
            font-size: 22px;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 8px;
        }
        .role-card p {
            color: #94A3B8;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 24px;
        }
        .role-cta {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 700;
            color: #A78BFA;
        }
    </style></head><body>
    <div class="animated-bg-overlay">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
    </div>
    <div class="hero-bg">
        <div class="hero-container">
            <div class="hero-badge">
                <span>🛡️</span> Enterprise AI Biometric Examination Suite
            </div>
            <h1 class="hero-title">SmartScribe Platform</h1>
            <p class="hero-subtitle">Accessible, secure AI examination platform tailored for visually impaired students — with real-time speech interaction and dual face & voice biometric authentication.</p>
            
            <div class="role-selection">
                <div class="role-card" onclick="window.location.href='/admin-login'">
                    <div class="role-icon-box">
                        <svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    </div>
                    <h3>Administrator Portal</h3>
                    <p>Manage student profiles, upload PDF question papers, oversee exam sessions, and download answer sheet reports.</p>
                    <div class="role-cta">Sign In to Dashboard →</div>
                </div>
                <div class="role-card" onclick="window.location.href='/student-verification'">
                    <div class="role-icon-box" style="background:rgba(13,148,136,0.2); color:#2DD4BF; border-color:rgba(20,184,166,0.35);">
                        <svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
                    </div>
                    <h3>Student Verification</h3>
                    <p>Perform face & voice verification to launch your voice-guided examination suite.</p>
                    <div class="role-cta" style="color:#2DD4BF;">Start Verification →</div>
                </div>
            </div>
        </div>
    </div>
    </body></html>
    """)

@app.route('/admin-login')
def admin_login():
    return render_template_string("""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Admin Sign In - SmartScribe Enterprise</title>
    <style>""" + COMMON_CSS + """
        .auth-wrapper {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: linear-gradient(180deg, #0B0F19 0%, #111827 100%);
            position: relative;
            z-index: 1;
        }
        .auth-card {
            width: 100%;
            max-width: 440px;
            background: #FFFFFF;
            border-radius: var(--radius-xl);
            border: 1px solid var(--border-color);
            box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.4);
            padding: 40px;
        }
        .auth-header {
            text-align: center;
            margin-bottom: 32px;
        }
    </style></head><body>
    <div class="animated-bg-overlay">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
    </div>
    <div class="auth-wrapper">
        <div class="auth-card">
            <div class="auth-header">
                <div style="width:48px; height:48px; border-radius:14px; background:linear-gradient(135deg, var(--purple-accent) 0%, var(--blue-primary) 100%); color:white; display:flex; align-items:center; justify-content:center; margin:0 auto 16px; font-weight:800; font-size:20px; box-shadow:var(--shadow-purple);">S</div>
                <h2 style="font-size:24px;font-weight:800;color:var(--text-dark);">Admin Sign In</h2>
                <p style="font-size:13px;color:var(--text-muted);margin-top:4px;">Enter your enterprise credentials to access the console</p>
            </div>
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="u" placeholder="Enter username" class="form-control">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="p" placeholder="Enter password" class="form-control">
            </div>
            <button class="btn btn-primary" onclick="login()" style="width:100%;margin-top:8px;">Sign In to Console →</button>
            
            <div style="text-align:center;margin-top:24px;font-size:14px;color:var(--text-muted);">
                Don't have an account? <a href="/admin-register" style="font-weight:600;">Register here</a>
            </div>
            <div style="text-align:center;margin-top:16px;">
                <a href="/" style="font-size:13px;color:var(--text-muted);">← Back to Portal Home</a>
            </div>
        </div>
    </div>
    <script>
        function login(){
            fetch('/api/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},
                body:JSON.stringify({username:document.getElementById('u').value,password:document.getElementById('p').value})})
            .then(r=>r.json()).then(d=>{if(d.success)window.location.href='/admin-dashboard';else alert('Invalid credentials');});
        }
        document.addEventListener('keydown',e=>{if(e.key==='Enter')login();});
    </script></body></html>
    """)

@app.route('/admin-register')
def admin_register():
    return render_template_string("""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Admin Registration - SmartScribe Enterprise</title>
    <style>""" + COMMON_CSS + """
        .auth-wrapper {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            background: linear-gradient(180deg, #0B0F19 0%, #111827 100%);
            position: relative;
            z-index: 1;
        }
        .auth-card {
            width: 100%;
            max-width: 440px;
            background: #FFFFFF;
            border-radius: var(--radius-xl);
            border: 1px solid var(--border-color);
            box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.4);
            padding: 40px;
        }
    </style></head><body>
    <div class="animated-bg-overlay">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
    </div>
    <div class="auth-wrapper">
        <div class="auth-card">
            <div style="text-align:center;margin-bottom:32px;">
                <div style="width:48px; height:48px; border-radius:14px; background:linear-gradient(135deg, var(--purple-accent) 0%, var(--blue-primary) 100%); color:white; display:flex; align-items:center; justify-content:center; margin:0 auto 16px; font-weight:800; font-size:20px; box-shadow:var(--shadow-purple);">S</div>
                <h2 style="font-size:24px;font-weight:800;color:var(--text-dark);">Register Administrator</h2>
                <p style="font-size:13px;color:var(--text-muted);margin-top:4px;">Create a new admin account for the console</p>
            </div>
            <div class="form-group">
                <label>Username</label>
                <input type="text" id="u" placeholder="Choose a username" class="form-control">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="p" placeholder="Create a password" class="form-control">
            </div>
            <div class="form-group">
                <label>Confirm Password</label>
                <input type="password" id="c" placeholder="Confirm your password" class="form-control">
            </div>
            <button class="btn btn-primary" onclick="reg()" style="width:100%;margin-top:8px;">Create Account →</button>
            
            <div style="text-align:center;margin-top:24px;font-size:14px;color:var(--text-muted);">
                Already have an account? <a href="/admin-login" style="font-weight:600;">Sign in</a>
            </div>
            <div style="text-align:center;margin-top:16px;">
                <a href="/" style="font-size:13px;color:var(--text-muted);">← Back to Portal Home</a>
            </div>
        </div>
    </div>
    <script>
        function reg(){
            const u=document.getElementById('u').value,p=document.getElementById('p').value,c=document.getElementById('c').value;
            if(p!==c){alert('Passwords do not match');return;}
            fetch('/api/admin/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})})
            .then(r=>r.json()).then(d=>{if(d.success){alert('Registered! Please login.');window.location.href='/admin-login';}else alert(d.message);});
        }
    </script></body></html>
    """)

@app.route('/admin-dashboard')
def admin_dashboard():
    dashboard_body = """
    <div style="margin-bottom: 28px;">
        <h2 style="font-size: 26px; font-weight: 800; color: var(--text-dark); letter-spacing: -0.5px;">Welcome back 👋</h2>
        <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">Manage students, examinations and submissions from your enterprise dashboard.</p>
    </div>

    <!-- 3D METRIC CARDS -->
    <div class="metrics-grid">
        <div class="metric-card">
            <div style="position:absolute; top:0; left:0; width:4px; height:100%; background:var(--purple-accent);"></div>
            <div class="metric-icon-box purple-icon">
                <svg width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <div class="metric-content">
                <div class="metric-label">Registered Students</div>
                <div class="metric-number-row">
                    <div id="ts" class="metric-num">0</div>
                    <span class="metric-trend">↗ +0%</span>
                </div>
            </div>
        </div>

        <div class="metric-card">
            <div style="position:absolute; top:0; left:0; width:4px; height:100%; background:var(--blue-primary);"></div>
            <div class="metric-icon-box blue-icon">
                <svg width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
            </div>
            <div class="metric-content">
                <div class="metric-label">Total Examinations</div>
                <div class="metric-number-row">
                    <div id="te" class="metric-num">0</div>
                    <span class="metric-trend">↗ +0%</span>
                </div>
            </div>
        </div>

        <div class="metric-card">
            <div style="position:absolute; top:0; left:0; width:4px; height:100%; background:var(--teal-accent);"></div>
            <div class="metric-icon-box teal-icon">
                <svg width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </div>
            <div class="metric-content">
                <div class="metric-label">Answer Submissions</div>
                <div class="metric-number-row">
                    <div id="tsub" class="metric-num">0</div>
                    <span class="metric-trend">↗ +0%</span>
                </div>
            </div>
        </div>
    </div>

    <!-- QUICK ACTIONS WITH COLORFUL 3D BADGES -->
    <div class="quick-actions-header">
        <h3>Quick Actions</h3>
        <a href="/view-exams" class="see-all-link">Manage Exams →</a>
    </div>
    
    <div class="quick-actions-grid">
        <div class="action-card" onclick="window.location.href='/create-student'">
            <div class="action-icon-badge bg-purple-subtle">
                <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="17" y1="11" x2="23" y2="11"/></svg>
            </div>
            <h4>Add New Student</h4>
            <p>Register face & voice biometric profiles</p>
            <div class="action-circle-btn btn-purple">→</div>
        </div>

        <div class="action-card" onclick="window.location.href='/view-students'">
            <div class="action-icon-badge bg-teal-subtle">
                <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <h4>Student Directory</h4>
            <p>Browse and search student records</p>
            <div class="action-circle-btn btn-teal">→</div>
        </div>

        <div class="action-card" onclick="window.location.href='/create-exam'">
            <div class="action-icon-badge bg-blue-subtle">
                <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
            </div>
            <h4>Create New Exam</h4>
            <p>Upload PDF question papers for parsing</p>
            <div class="action-circle-btn btn-blue">→</div>
        </div>

        <div class="action-card" onclick="window.location.href='/view-exams'">
            <div class="action-icon-badge bg-amber-subtle">
                <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
            </div>
            <h4>View Active Exams</h4>
            <p>Preview question papers & settings</p>
            <div class="action-circle-btn btn-amber">→</div>
        </div>

        <div class="action-card" onclick="window.location.href='/view-submissions'">
            <div class="action-icon-badge bg-rose-subtle">
                <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </div>
            <h4>Review Submissions</h4>
            <p>Download generated answer sheet PDFs</p>
            <div class="action-circle-btn btn-rose">→</div>
        </div>
    </div>

    <script>
        fetch('/api/admin/stats').then(r=>r.json()).then(d=>{
            document.getElementById('ts').textContent=d.totalStudents;
            document.getElementById('te').textContent=d.totalExams;
            document.getElementById('tsub').textContent=d.totalSubmissions;
        });
    </script>
    """
    return render_admin_layout('dashboard', 'Overview Console', 'System analytics and operational shortcuts', dashboard_body)

@app.route('/view-submissions')
def view_submissions():
    with get_db() as conn:
        subs = conn.cursor().execute(
            "SELECT id,reg_no,student_name,exam_name,pdf_filename,submitted_at FROM exam_submissions ORDER BY submitted_at DESC"
        ).fetchall()
    rows = ''
    for s in subs:
        fname = s['pdf_filename'] or f"{s['student_name']}.{s['exam_name']}.pdf"
        rows += f"""<tr>
            <td style="font-weight:700; color:var(--text-dark);">{s['reg_no']}</td>
            <td style="font-weight:600;">{s['student_name']}</td>
            <td><span class="badge badge-primary">{s['exam_name']}</span></td>
            <td style="color:var(--text-muted);font-size:13px;">{s['submitted_at']}</td>
            <td>
                <a href="/api/admin/download-submission/{s['id']}" class="btn btn-sm btn-primary">⬇ Download PDF</a>
                <button onclick="deleteSubmission({s['id']})" class="btn btn-sm btn-danger" style="margin-left:6px;">🗑 Delete</button>
            </td>
        </tr>"""
    if not rows:
        rows = """<tr><td colspan="5">
            <div class="empty-state">
                <div class="empty-state-icon">
                    <svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                </div>
                <h3>No submissions yet</h3>
                <p>Student answer sheets will appear here once exams are completed.</p>
            </div>
        </td></tr>"""

    body = f"""
    <div class="table-container">
        <table class="table">
            <thead>
                <tr>
                    <th>Registration No</th>
                    <th>Student Name</th>
                    <th>Exam Name</th>
                    <th>Submitted At</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>

    <script>
    function deleteSubmission(id) {{
        if (!confirm('Delete this submitted answer sheet? This action cannot be undone.')) return;
        fetch('/api/admin/delete-submission/' + id, {{method:'POST'}})
            .then(r=>r.json())
            .then(d=>{{if(d.success){{alert('Submission deleted successfully.');location.reload();}}else{{alert(d.message||'Could not delete submission.');}}}})
            .catch(err=>alert('Delete failed: '+err));
    }}
    </script>
    """
    return render_admin_layout('view-submissions', 'Student Submissions', 'Review and manage submitted answer sheets.', body)

@app.route('/create-student')
def create_student():
    body = """
    <div style="max-width: 720px; margin: 0 auto;">
        <!-- PROCESS / PROGRESS UI STEPPER -->
        <div class="student-progress-bar">
            <div class="step-item active">
                <div class="step-num">01</div>
                <div class="step-label">Register</div>
            </div>
            <div class="step-line active"></div>
            <div class="step-item">
                <div class="step-num">02</div>
                <div class="step-label">Face Verification</div>
            </div>
            <div class="step-line"></div>
            <div class="step-item">
                <div class="step-num">03</div>
                <div class="step-label">Voice Verification</div>
            </div>
            <div class="step-line"></div>
            <div class="step-item">
                <div class="step-num">04</div>
                <div class="step-label">Start Exam</div>
            </div>
            <div class="step-line"></div>
            <div class="step-item">
                <div class="step-num">05</div>
                <div class="step-label">Submit</div>
            </div>
        </div>

        <div class="card">
            <h3 style="font-size:20px; font-weight:800; color:var(--text-dark); margin-bottom:24px;">Register New Student</h3>

            <!-- Section 1 -->
            <div class="form-group">
                <label>Registration Number</label>
                <input type="text" id="regNo" placeholder="e.g. 2024001" class="form-control">
            </div>
            <div class="form-group">
                <label>Full Name</label>
                <input type="text" id="studentName" placeholder="Enter student's full name" class="form-control">
            </div>

            <!-- Section 2: Face Photo -->
            <div class="form-group" style="margin-top:28px;">
                <label style="display:flex; align-items:center; gap:8px;">
                    <span>📷</span> Student Photo (Face Recognition)
                </label>
                <input type="file" id="studentImage" accept="image/*" onchange="previewImg(event)" class="form-control">
                <div style="text-align:center;">
                    <img id="imgPreview" style="max-width:180px; max-height:180px; display:none; margin:16px auto 0; border-radius:12px; border:3px solid var(--purple-accent); box-shadow:var(--shadow-md);">
                </div>
                <div style="font-size:12px; color:var(--warning); margin-top:8px; display:flex; align-items:center; gap:4px;">
                    ⚠️ Ensure the face is centered, well-lit, and clearly visible.
                </div>
            </div>

            <!-- Section 3: Voice Studio -->
            <div class="form-group" style="margin-top:28px;">
                <label style="display:flex; align-items:center; gap:8px;">
                    <span>🎙️</span> Voice Sample Registration
                </label>
                <div style="background:var(--purple-soft); border:2px dashed var(--purple-border); border-radius:var(--radius-lg); padding:24px; text-align:center;">
                    <p style="color:var(--text-muted); font-size:13px; margin-bottom:16px;">
                        Ask the student to speak clearly for <strong>5–8 seconds</strong>.<br>
                        <em>"My name is [Name] and my registration number is [Reg No]"</em>
                    </p>
                    <button class="btn btn-primary" id="recBtn" onclick="startRec()">🎙️ Start Recording</button>
                    <button class="btn btn-danger" id="stopBtn" onclick="stopRec()" style="display:none;">⏹ Stop Recording</button>
                    
                    <div id="voiceStatus" style="font-size:13px; color:var(--text-muted); margin-top:12px; min-height:20px;">Ready to listen</div>
                    <audio id="voicePlayback" controls style="display:none; width:100%; margin-top:14px; border-radius:8px;"></audio>
                    <div id="wavNotice" style="display:none; font-size:12px; color:var(--success); font-weight:600; margin-top:8px;">✓ Recording captured</div>
                </div>
            </div>

            <div style="display:flex; gap:12px; margin-top:32px;">
                <button class="btn btn-primary" onclick="registerStudent()" style="flex:1;">✅ Register Student</button>
                <button class="btn btn-secondary" onclick="window.location.href='/admin-dashboard'">Cancel</button>
            </div>
        </div>
    </div>

    <script>
    let imageData=null, voiceB64=null, mediaRecorder=null, audioChunks=[], autoStopTimer=null, recStream=null;

    function previewImg(event){
        const file=event.target.files[0];
        if(!file) return;
        const reader=new FileReader();
        reader.onload=e=>{
            document.getElementById('imgPreview').src=e.target.result;
            document.getElementById('imgPreview').style.display='block';
            imageData=e.target.result;
        };
        reader.readAsDataURL(file);
    }

    async function startRec(){
        audioChunks=[]; voiceB64=null;
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            try { mediaRecorder.stop(); } catch(e){}
        }
        if (recStream) {
            try { recStream.getTracks().forEach(t => t.stop()); } catch(e){}
            recStream = null;
        }
        document.getElementById('voicePlayback').style.display='none';
        document.getElementById('wavNotice').style.display='none';
        document.getElementById('recBtn').disabled = true;

        try{
            recStream = await navigator.mediaDevices.getUserMedia({audio:{sampleRate:16000,channelCount:1,echoCancellation:true}});
        }catch(e){
            alert('Microphone access denied: '+e.message);
            document.getElementById('recBtn').disabled = false;
            return;
        }
        const mime=MediaRecorder.isTypeSupported('audio/wav')?'audio/wav':
                   MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?'audio/webm;codecs=opus':'audio/webm';
        mediaRecorder=new MediaRecorder(recStream,{mimeType:mime});
        mediaRecorder.ondataavailable=e=>{ if(e.data && e.data.size > 0) audioChunks.push(e.data); };
        mediaRecorder.onstop=()=>{
            if (recStream) {
                try { recStream.getTracks().forEach(t => t.stop()); } catch(e){}
                recStream = null;
            }
            const blob=new Blob(audioChunks,{type:mime});
            if (blob.size > 0) {
                document.getElementById('voicePlayback').src=URL.createObjectURL(blob);
                document.getElementById('voicePlayback').style.display='block';
                const reader=new FileReader();
                reader.onload=e=>{
                    voiceB64=e.target.result.split(',')[1];
                    document.getElementById('voiceStatus').textContent='✓ Recording captured ('+(blob.size/1024).toFixed(1)+' KB). You can play it back.';
                    document.getElementById('wavNotice').style.display='block';
                };
                reader.readAsDataURL(blob);
            } else {
                document.getElementById('voiceStatus').textContent='❌ Recording empty. Please try again.';
            }
            document.getElementById('recBtn').style.display='inline-flex';
            document.getElementById('recBtn').disabled = false;
            document.getElementById('stopBtn').style.display='none';
        };
        mediaRecorder.start(100);
        document.getElementById('recBtn').style.display='none';
        document.getElementById('stopBtn').style.display='inline-flex';
        document.getElementById('stopBtn').disabled = false;
        document.getElementById('voiceStatus').textContent='🔴 Recording... speak clearly now';
        if (autoStopTimer) clearTimeout(autoStopTimer);
        autoStopTimer=setTimeout(()=>{ if(mediaRecorder&&mediaRecorder.state==='recording')stopRec(); },10000);
    }

    function stopRec(){
        if(autoStopTimer){clearTimeout(autoStopTimer);autoStopTimer=null;}
        if(mediaRecorder&&mediaRecorder.state==='recording'){
            try { mediaRecorder.stop(); } catch(e){}
        }
        if (recStream) {
            try { recStream.getTracks().forEach(t => t.stop()); } catch(e){}
            recStream = null;
        }
        document.getElementById('recBtn').style.display='inline-flex';
        document.getElementById('recBtn').disabled = false;
        document.getElementById('stopBtn').style.display='none';
    }

    function registerStudent(){
        const regNo=document.getElementById('regNo').value.trim();
        const name=document.getElementById('studentName').value.trim();
        if(!regNo||!name){alert('Please fill registration number and name');return;}
        if(!imageData){alert('Please upload a student photo');return;}
        if(!voiceB64){alert('Please record a voice sample');return;}
        const btn=event.target;btn.disabled=true;btn.textContent='Registering...';
        fetch('/api/admin/create-student',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({regNo,name,image:imageData,voice:voiceB64})})
        .then(r=>r.json()).then(d=>{
            if(d.success){alert('Student registered successfully!');window.location.href='/view-students';}
            else{alert('Error: '+(d.message||'Unknown error'));btn.disabled=false;btn.textContent='✅ Register Student';}
        }).catch(e=>{alert('Network error: '+e.message);btn.disabled=false;btn.textContent='✅ Register Student';});
    }
    </script>
    """
    return render_admin_layout('create-student', 'Add Student', 'Register a new student with biometric face and voice profiles.', body)

@app.route('/view-students')
def view_students():
    with get_db() as conn:
        students = conn.cursor().execute("SELECT reg_no,name,image,voice_embedding FROM students ORDER BY created_at DESC").fetchall()
    cards = ''
    if students:
        for s in students:
            has_voice = '<span class="badge badge-success">✅ Voice Registered</span>' if s['voice_embedding'] else '<span class="badge badge-warning">⚠️ No Voice</span>'
            cards += f'''
            <div class="card card-hoverable student-item-card" style="margin-bottom:0; text-align:center; padding:28px 24px;" data-search="{s['name'].lower()} {s['reg_no'].lower()}">
                <div style="width:96px; height:96px; border-radius:50%; margin:0 auto 16px; overflow:hidden; border:3px solid var(--purple-accent); box-shadow:var(--shadow-md);">
                    <img src="{s['image']}" alt="{s['name']}" style="width:100%; height:100%; object-fit:cover;">
                </div>
                <h4 style="font-size:16px; font-weight:700; color:var(--text-dark); margin-bottom:4px;">{s['name']}</h4>
                <p style="font-size:13px; color:var(--text-muted); margin-bottom:12px;">Reg: {s['reg_no']}</p>
                <div style="margin-bottom:20px;">{has_voice}</div>
                <button onclick="delS('{s['reg_no']}')" class="btn btn-sm btn-danger" style="width:100%;">🗑 Delete Student</button>
            </div>'''
    else:
        cards = '''<div style="grid-column:1/-1;">
            <div class="empty-state">
                <div class="empty-state-icon">
                    <svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                </div>
                <h3>No registered students yet</h3>
                <p>Add your first student to start managing profiles.</p>
                <a href="/create-student" class="btn btn-primary">➕ Add Student</a>
            </div>
        </div>'''

    body = f"""
    <div style="margin-bottom:24px;">
        <input type="text" id="studentSearchInput" onkeyup="filterStudents()" placeholder="🔍 Search students by name or registration number..." class="form-control" style="max-width:400px;">
    </div>

    <div id="studentsGrid" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:24px;">
        {cards}
    </div>

    <script>
    function delS(r){{
        if(confirm('Delete student '+r+'? This cannot be undone.')){{
            fetch('/api/admin/delete-student',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{regNo:r}})}})
                .then(r=>r.json()).then(d=>{{if(d.success)location.reload();}});
        }}
    }}
    function filterStudents(){{
        const q=document.getElementById('studentSearchInput').value.toLowerCase();
        document.querySelectorAll('.student-item-card').forEach(el=>{{
            el.style.display=el.dataset.search.includes(q)?'block':'none';
        }});
    }}
    </script>
    """
    return render_admin_layout('view-students', 'Student Directory', 'Manage registered students and voice authentication status.', body)

@app.route('/create-exam', methods=['GET'])
def create_exam_page():
    body = """
    <div style="max-width: 680px; margin: 0 auto;">
        <div class="card">
            <h3 style="font-size:20px; font-weight:800; color:var(--text-dark); margin-bottom:16px;">Create New Examination</h3>
            
            <div style="background:var(--purple-soft); border:1px solid var(--purple-border); border-radius:var(--radius-md); padding:16px; margin-bottom:24px; font-size:13px; color:var(--purple-accent);">
                📌 <strong>PDF Requirements:</strong> Upload a PDF question paper containing numbered questions (e.g., <em>1. What is photosynthesis? 2. What is chlorophyll?</em>). Questions will be parsed automatically.
            </div>

            <div class="form-group">
                <label>Exam Title</label>
                <input type="text" id="examName" placeholder="e.g. Biology Midterm Exam" class="form-control">
            </div>

            <div class="form-group">
                <label>Duration (Minutes)</label>
                <input type="number" id="duration" value="60" min="1" class="form-control">
            </div>

            <div class="form-group">
                <label>Question Paper PDF</label>
                <div style="border:2px dashed var(--border-color); border-radius:var(--radius-lg); padding:36px; text-align:center; background:#F8FAFC;" id="dropzone">
                    <div style="width:54px; height:54px; border-radius:50%; background:var(--purple-soft); color:var(--purple-accent); display:flex; align-items:center; justify-content:center; margin:0 auto 12px; border:1px solid var(--purple-border);">
                        <svg width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
                    </div>
                    <div style="font-size:15px; font-weight:700; color:var(--text-dark);">Upload Question Paper PDF</div>
                    <div style="font-size:12px; color:var(--text-muted); margin-top:4px; margin-bottom:20px;">PDF documents only</div>
                    
                    <input type="file" id="pdfFile" accept="application/pdf" onchange="showFileName()" style="display:none;">
                    <button class="btn btn-secondary" onclick="document.getElementById('pdfFile').click()">Choose File</button>
                    <div id="fileName" style="font-size:13px; font-weight:600; color:var(--purple-accent); margin-top:14px;">No PDF selected</div>
                </div>
            </div>

            <button class="btn btn-primary" id="createBtn" onclick="createExam()" style="width:100%; margin-top:12px;">🚀 Create Examination</button>
            <div id="status" style="display:none; margin-top:16px; padding:14px; border-radius:var(--radius-md); font-size:13px; font-weight:600;"></div>
        </div>
    </div>

    <script>
    function showFileName() {
        const fileInput = document.getElementById('pdfFile');
        const fileName = document.getElementById('fileName');
        if (fileInput.files.length > 0) {
            fileName.textContent = "Selected: " + fileInput.files[0].name;
        } else {
            fileName.textContent = "No PDF selected";
        }
    }

    function showStatus(message, type) {
        const status = document.getElementById('status');
        status.textContent = message;
        status.style.display = 'block';
        if(type==='success'){
            status.style.background='var(--success-bg)'; status.style.color='#047857'; status.style.border='1px solid var(--success-border)';
        } else if(type==='error'){
            status.style.background='var(--danger-bg)'; status.style.color='#DC2626'; status.style.border='1px solid var(--danger-border)';
        } else {
            status.style.background='var(--purple-soft)'; status.style.color='var(--purple-accent)'; status.style.border='1px solid var(--purple-border)';
        }
    }

    async function createExam() {
        const name = document.getElementById('examName').value.trim();
        const duration = document.getElementById('duration').value;
        const fileInput = document.getElementById('pdfFile');
        const btn = document.getElementById('createBtn');

        if (!name) { showStatus('❌ Please enter an exam name.', 'error'); return; }
        if (!fileInput.files.length) { showStatus('❌ Please select a PDF question paper.', 'error'); return; }
        const file = fileInput.files[0];
        if (file.type !== 'application/pdf') { showStatus('❌ Please select a PDF file only.', 'error'); return; }

        btn.disabled = true; btn.textContent = '⏳ Creating Exam...';
        showStatus('📄 Reading question paper...', 'info');

        try {
            const reader = new FileReader();
            reader.onload = async function(e) {
                const pdfBase64 = e.target.result;
                showStatus('🤖 Extracting questions from PDF...', 'info');
                try {
                    const response = await fetch('/api/admin/create-exam', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: name, duration: parseInt(duration) || 60, pdf: pdfBase64 })
                    });
                    const data = await response.json();
                    if (!response.ok || !data.success) {
                        throw new Error(data.message || data.error || 'Failed to create exam');
                    }
                    showStatus('✅ Exam created successfully! ' + data.question_count + ' questions detected.', 'success');
                    btn.textContent = '✅ Exam Created';
                    setTimeout(function() { window.location.href = '/view-exams'; }, 1800);
                } catch(error) {
                    console.error('Create exam error:', error);
                    showStatus('❌ ' + error.message, 'error');
                    btn.disabled = false; btn.textContent = '🚀 Create Exam';
                }
            };
            reader.onerror = function() {
                showStatus('❌ Could not read the PDF file.', 'error');
                btn.disabled = false; btn.textContent = '🚀 Create Exam';
            };
            reader.readAsDataURL(file);
        } catch(error) {
            console.error(error);
            showStatus('❌ Something went wrong. Please try again.', 'error');
            btn.disabled = false; btn.textContent = '🚀 Create Exam';
        }
    }
    </script>
    """
    return render_admin_layout('create-exam', 'Create Exam', 'Upload question papers and configure examination settings.', body)

@app.route('/view-exams')
def view_exams():
    with get_db() as conn:
        exams = conn.cursor().execute("SELECT id,name,duration_minutes,created_at FROM exams ORDER BY created_at DESC").fetchall()
    cards = ''
    if exams:
        for e in exams:
            cards += f"""<div class="card card-hoverable" style="margin-bottom:0; text-align:left; padding:28px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
                    <h3 style="font-size:18px; font-weight:700; color:var(--text-dark);">{e['name']}</h3>
                    <span class="badge badge-primary">⏱ {e['duration_minutes'] or 60} mins</span>
                </div>
                <p style="font-size:13px; color:var(--text-muted); margin-bottom:24px;">📅 Created: {e['created_at']}</p>
                <div style="display:flex; gap:12px;">
                    <button onclick="window.open('/api/exam/pdf/{e['id']}','_blank')" class="btn btn-sm btn-secondary" style="flex:1;">📄 View PDF</button>
                    <button onclick="deleteExam('{e['id']}')" class="btn btn-sm btn-danger" style="flex:1;">🗑 Delete Exam</button>
                </div>
            </div>"""
    else:
        cards = """<div style="grid-column:1/-1;">
            <div class="empty-state">
                <div class="empty-state-icon">
                    <svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                </div>
                <h3>No examinations created yet</h3>
                <p>Upload your first question paper to create an exam.</p>
                <a href="/create-exam" class="btn btn-primary">➕ Create Exam</a>
            </div>
        </div>"""

    body = f"""
    <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:24px;">
        {cards}
    </div>

    <script>
    function deleteExam(id) {{
        if (!confirm('Delete this exam/question paper? This action cannot be undone.')) return;
        fetch('/api/admin/delete-exam/' + encodeURIComponent(id), {{method:'POST'}})
            .then(r=>r.json())
            .then(d=>{{if(d.success){{alert('Exam deleted successfully.');location.reload();}}else{{alert(d.message||'Could not delete exam.');}}}})
            .catch(err=>alert('Delete failed: '+err));
    }}
    </script>
    """
    return render_admin_layout('view-exams', 'Exam Management', 'View created exams, preview question papers and delete exams.', body)

@app.route('/student-verification')
def student_verification():
    return render_template_string("""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>Student Identity Verification - SmartScribe</title>
    <style>""" + COMMON_CSS + """
        .verify-wrapper {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background: linear-gradient(180deg, #0B0F19 0%, #111827 100%);
            color: #FFFFFF;
            position: relative;
            z-index: 1;
        }
        .verify-nav {
            padding: 20px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.05);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .box {
            max-width: 560px;
            margin: 0 auto;
            background: #FFFFFF;
            border-radius: var(--radius-xl);
            padding: 36px;
            box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.4);
            border: 1px solid var(--border-color);
            color: var(--text-dark);
        }
        .cam-prev {
            width: 100%;
            height: 320px;
            background: #000;
            border-radius: var(--radius-lg);
            margin: 16px 0;
            overflow: hidden;
            position: relative;
            border: 2px solid var(--purple-accent);
        }
        .status-box {
            padding: 14px;
            border-radius: var(--radius-md);
            margin: 16px 0;
            display: none;
            font-weight: 600;
            font-size: 14px;
            text-align: center;
        }
        .ok { background: var(--success-bg); color: #047857; border: 1px solid var(--success-border); }
        .err { background: var(--danger-bg); color: #DC2626; border: 1px solid var(--danger-border); }
        .voice-box {
            max-width: 560px;
            margin: 24px auto;
            background: #FFFFFF;
            border-radius: var(--radius-xl);
            padding: 36px;
            box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.4);
            border: 2px dashed var(--purple-border);
            text-align: center;
            display: none;
            color: var(--text-dark);
        }
    </style></head><body>
    <div class="animated-bg-overlay">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
    </div>
    <div class="verify-wrapper">
        <header class="verify-nav">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="width:40px; height:40px; border-radius:12px; background:linear-gradient(135deg, var(--purple-accent) 0%, var(--teal-accent) 100%); color:white; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:18px;">S</div>
                <span style="font-size:18px;font-weight:800;color:white;">SmartScribe Verification Suite</span>
            </div>
            <a href="/" class="btn btn-secondary btn-sm" style="background:rgba(255,255,255,0.1);color:white;border-color:rgba(255,255,255,0.2);">← Portal Home</a>
        </header>

        <div style="flex:1; padding: 32px 20px;">
            <!-- PROCESS / PROGRESS UI STEPPER -->
            <div class="student-progress-bar" style="max-width: 720px; margin: 0 auto 28px;">
                <div class="step-item completed">
                    <div class="step-num">✓</div>
                    <div class="step-label">Register</div>
                </div>
                <div class="step-line active"></div>
                <div class="step-item active" id="stStep2">
                    <div class="step-num">02</div>
                    <div class="step-label">Face Verification</div>
                </div>
                <div class="step-line" id="stLine2"></div>
                <div class="step-item" id="stStep3">
                    <div class="step-num">03</div>
                    <div class="step-label">Voice Verification</div>
                </div>
                <div class="step-line"></div>
                <div class="step-item">
                    <div class="step-num">04</div>
                    <div class="step-label">Start Exam</div>
                </div>
                <div class="step-line"></div>
                <div class="step-item">
                    <div class="step-num">05</div>
                    <div class="step-label">Submit</div>
                </div>
            </div>

            <div style="max-width: 560px; margin: 0 auto 20px;">
                <input type="text" id="regNo" placeholder="Enter Registration Number" class="form-control" style="font-size:18px; text-align:center; padding:16px; font-weight:700;">
            </div>

            <div id="statusMsg" class="status-box"></div>

            <!-- CAMERA / FACE VERIFICATION UI -->
            <div class="box" id="faceBox">
                <div style="display:flex; align-items:center; justify-content:center; gap:8px; margin-bottom:12px;">
                    <span style="font-size:24px;">📷</span>
                    <h3 style="color:var(--text-dark); text-align:center; font-size:20px; font-weight:800;">Face Verification</h3>
                </div>
                <div class="cam-prev">
                    <video id="cam" autoplay style="width:100%;height:100%;object-fit:cover;"></video>
                    <canvas id="camCanvas" style="display:none;"></canvas>
                    <div style="position:absolute; top:12px; left:12px; background:rgba(0,0,0,0.6); backdrop-filter:blur(4px); color:#38BDF8; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:700; border:1px solid rgba(56,189,248,0.3);">
                        ● Camera Ready
                    </div>
                </div>
                <div style="text-align:center;">
                    <button class="btn btn-primary" id="capBtn" onclick="captureImg()">📸 Capture Face</button>
                    <button class="btn btn-secondary" id="retakeBtn" onclick="retake()" style="display:none;">🔄 Retake</button>
                </div>
                <div id="faceStatus" style="text-align:center; margin-top:10px; color:var(--text-muted); font-size:13px;"></div>
                <button class="btn btn-primary" id="verifyFaceBtn" onclick="verifyFace()" style="margin-top:20px; width:100%;">Verify Face →</button>
            </div>

            <!-- VOICE VERIFICATION UI -->
            <div class="voice-box" id="voiceBox">
                <div style="display:flex; align-items:center; justify-content:center; gap:8px; margin-bottom:12px;">
                    <span style="font-size:24px;">🎙️</span>
                    <h3 style="color:var(--text-dark); font-size:20px; font-weight:800;">Voice Verification</h3>
                </div>
                <p style="color:var(--text-muted); margin-bottom:16px; font-size:14px;">
                    Please say: <strong>"My name is [your name] and I am ready for my exam"</strong>
                </p>
                <div style="display:flex; justify-content:center; gap:10px;">
                    <button class="btn btn-danger" id="vRecBtn" onclick="startVoice()">🎙️ Record Voice</button>
                    <button class="btn btn-secondary" id="vStopBtn" onclick="stopVoice()" style="display:none;">⏹ Stop</button>
                </div>
                <div id="vStatus" style="font-size:14px; color:var(--text-muted); margin-top:12px;">Ready to listen</div>
                <audio id="vPlayback" controls style="display:none; width:100%; margin-top:14px; border-radius:8px;"></audio>
                <button class="btn btn-primary" id="verifyVoiceBtn" onclick="verifyVoice()" style="margin-top:20px; width:100%; display:none;">Verify Voice →</button>
            </div>
        </div>
    </div>

    <script>
    let capturedImg=null,faceCaptured=false,voiceB64=null,vMR=null,vChunks=[],vAutoStop=null;

    navigator.mediaDevices.getUserMedia({video:true})
        .then(s=>{document.getElementById('cam').srcObject=s;})
        .catch(()=>showStatus('Camera access denied','err'));

    function showStatus(msg,type){
        const d=document.getElementById('statusMsg');
        d.textContent=msg; d.className='status-box '+type; d.style.display='block';
        setTimeout(()=>d.style.display='none',6000);
    }
    function captureImg(){
        const v=document.getElementById('cam'),c=document.getElementById('camCanvas');
        c.width=v.videoWidth;c.height=v.videoHeight;
        c.getContext('2d').drawImage(v,0,0);
        capturedImg=c.toDataURL('image/jpeg');
        const img=document.createElement('img');img.src=capturedImg;img.style='width:100%;height:100%;object-fit:cover;';
        v.style.display='none';v.parentNode.appendChild(img);
        document.getElementById('capBtn').style.display='none';
        document.getElementById('retakeBtn').style.display='inline-flex';
        document.getElementById('faceStatus').textContent='✓ Face detected';
        faceCaptured=true;
    }
    function retake(){
        capturedImg=null;faceCaptured=false;
        const v=document.getElementById('cam');v.style.display='block';
        const img=v.parentNode.querySelector('img');if(img)img.remove();
        document.getElementById('capBtn').style.display='inline-flex';
        document.getElementById('retakeBtn').style.display='none';
        document.getElementById('faceStatus').textContent='';
    }
    function verifyFace(){
        const regNo=document.getElementById('regNo').value.trim();
        if(!regNo){showStatus('Enter registration number','err');return;}
        if(!faceCaptured){showStatus('Capture your face first','err');return;}
        const btn=document.getElementById('verifyFaceBtn');btn.disabled=true;btn.textContent='Verifying...';
        fetch('/api/student/verify-face',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({regNo,image:capturedImg})})
        .then(r=>r.json()).then(d=>{
            if(d.success){
                showStatus('✅ Face verified! Now verify your voice.','ok');
                document.getElementById('faceBox').style.opacity='0.55';
                document.getElementById('voiceBox').style.display='block';
                document.getElementById('stStep2').className='step-item completed';
                document.getElementById('stStep2').querySelector('.step-num').textContent='✓';
                document.getElementById('stLine2').className='step-line active';
                document.getElementById('stStep3').className='step-item active';
            }else{showStatus('❌ '+d.message,'err');btn.disabled=false;btn.textContent='Verify Face →';}
        }).catch(()=>{showStatus('Error. Try again.','err');btn.disabled=false;btn.textContent='Verify Face →';});
    }

    let vStream = null;

    async function startVoice(){
        vChunks = []; voiceB64 = null;
        if (vMR && vMR.state !== 'inactive') {
            try { vMR.stop(); } catch(e){}
        }
        if (vStream) {
            try { vStream.getTracks().forEach(t => t.stop()); } catch(e){}
            vStream = null;
        }
        document.getElementById('vPlayback').style.display = 'none';
        document.getElementById('verifyVoiceBtn').style.display = 'none';
        document.getElementById('vRecBtn').disabled = true;

        try {
            vStream = await navigator.mediaDevices.getUserMedia({audio:{sampleRate:16000,channelCount:1,echoCancellation:true}});
        } catch(e) {
            showStatus('Microphone denied: ' + e.message, 'err');
            document.getElementById('vRecBtn').disabled = false;
            return;
        }

        const mime = MediaRecorder.isTypeSupported('audio/wav') ? 'audio/wav' :
                     MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : 'audio/webm';
        
        vMR = new MediaRecorder(vStream, {mimeType: mime});
        vMR.ondataavailable = e => {
            if (e.data && e.data.size > 0) vChunks.push(e.data);
        };
        vMR.onstop = () => {
            if (vStream) {
                try { vStream.getTracks().forEach(t => t.stop()); } catch(e){}
                vStream = null;
            }
            const blob = new Blob(vChunks, {type: mime});
            if (blob.size > 0) {
                document.getElementById('vPlayback').src = URL.createObjectURL(blob);
                document.getElementById('vPlayback').style.display = 'block';
                const reader = new FileReader();
                reader.onload = e => {
                    voiceB64 = e.target.result.split(',')[1];
                    document.getElementById('vStatus').textContent = '✓ Recording captured (' + (blob.size/1024).toFixed(1) + ' KB)';
                    document.getElementById('verifyVoiceBtn').style.display = 'block';
                    document.getElementById('verifyVoiceBtn').disabled = false;
                };
                reader.readAsDataURL(blob);
            } else {
                document.getElementById('vStatus').textContent = '❌ Recording empty. Please try again.';
            }
            document.getElementById('vRecBtn').style.display = 'inline-flex';
            document.getElementById('vRecBtn').disabled = false;
            document.getElementById('vStopBtn').style.display = 'none';
        };

        vMR.start(100);
        document.getElementById('vRecBtn').style.display = 'none';
        document.getElementById('vStopBtn').style.display = 'inline-flex';
        document.getElementById('vStopBtn').disabled = false;
        document.getElementById('vStatus').textContent = '🔴 Recording... speak clearly';

        if (vAutoStop) clearTimeout(vAutoStop);
        vAutoStop = setTimeout(() => {
            if (vMR && vMR.state === 'recording') stopVoice();
        }, 8000);
    }

    function stopVoice(){
        if (vAutoStop) { clearTimeout(vAutoStop); vAutoStop = null; }
        if (vMR && vMR.state === 'recording') {
            try { vMR.stop(); } catch(e){}
        }
        if (vStream) {
            try { vStream.getTracks().forEach(t => t.stop()); } catch(e){}
            vStream = null;
        }
        document.getElementById('vRecBtn').style.display = 'inline-flex';
        document.getElementById('vRecBtn').disabled = false;
        document.getElementById('vStopBtn').style.display = 'none';
    }
    function verifyVoice(){
        const regNo=document.getElementById('regNo').value.trim();
        if(!voiceB64){showStatus('Record voice first','err');return;}
        const btn=document.getElementById('verifyVoiceBtn');btn.disabled=true;btn.textContent='Verifying voice...';
        fetch('/api/student/verify-voice',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({regNo,voice:voiceB64})})
        .then(r=>r.json()).then(d=>{
            if(d.success){
                showStatus('✅ Voice verified! Entering exam...','ok');
                setTimeout(()=>window.location.href='/exam-page?regNo='+regNo,1200);
            }else{showStatus('❌ '+d.message+' — please try again','err');btn.disabled=false;btn.textContent='Verify Voice →';}
        }).catch(()=>{showStatus('Error. Try again.','err');btn.disabled=false;btn.textContent='Verify Voice →';});
    }
    </script></body></html>
    """)

@app.route('/exam-page')
def exam_page():
    regNo = request.args.get('regNo', '')
    return render_template_string("""
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
    <title>SmartScribe — Examination Suite</title>
    <style>""" + COMMON_CSS + """
        body { background: #0B0F19; color: #FFFFFF; font-size: 18px; position: relative; }
        .exam-shell {
            max-width: 980px;
            margin: 24px auto;
            padding: 0 20px;
            position: relative;
            z-index: 1;
        }
        .exam-header-bar {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: white;
            padding: 22px 32px;
            border-radius: var(--radius-xl);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            margin-bottom: 24px;
        }
        .timer-box {
            background: rgba(124, 58, 237, 0.2);
            color: #C4B5FD;
            padding: 8px 24px;
            border-radius: 30px;
            font-size: 26px;
            font-weight: 800;
            border: 1.5px solid rgba(139, 92, 246, 0.4);
            letter-spacing: 1px;
        }
        .timer-box.warn { color: #FF6B6B; background: rgba(239,68,68,0.2); border-color: rgba(239,68,68,0.4); animation: blink 0.8s infinite; }
        @keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.4;} }
        
        .status-bubble {
            background: #FFFFFF;
            border: 3px solid var(--purple-accent);
            border-radius: var(--radius-xl);
            padding: 32px;
            font-size: 24px;
            font-weight: 700;
            color: var(--text-dark);
            line-height: 1.6;
            min-height: 110px;
            margin-bottom: 24px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }
        .mic-area {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
            padding: 28px;
            border-radius: var(--radius-xl);
            border: 1px solid rgba(255, 255, 255, 0.12);
        }
        .mic-icon { font-size: 64px; }
        .mic-icon.listening { animation: pulse 1.2s infinite; }
        @keyframes pulse { 0%,100%{transform:scale(1);} 50%{transform:scale(1.2);} }
        .mic-label { font-size: 16px; color: #94A3B8; font-weight: 600; }
        .mic-label.active { color: #C4B5FD; font-weight: 800; }
        .wave-anim { display: none; justify-content: center; gap: 6px; height: 40px; align-items: center; }
        .wave-anim.show { display: flex; }
        .wbar { width: 8px; background: var(--purple-accent); border-radius: 4px; animation: wave 1s ease-in-out infinite; }
        .wbar:nth-child(1){height:16px;animation-delay:0s;}.wbar:nth-child(2){height:32px;animation-delay:.15s;}
        .wbar:nth-child(3){height:46px;animation-delay:.3s;}.wbar:nth-child(4){height:32px;animation-delay:.45s;}
        .wbar:nth-child(5){height:16px;animation-delay:.6s;}
        @keyframes wave{0%,100%{transform:scaleY(.4);}50%{transform:scaleY(1);}}
        
        .transcript-box {
            background: rgba(255, 255, 255, 0.05);
            border: 2px dashed rgba(139, 92, 246, 0.4);
            border-radius: var(--radius-lg);
            padding: 20px;
            font-size: 18px;
            color: #FFFFFF;
            min-height: 60px;
            display: none;
            margin-bottom: 20px;
        }
        .transcript-box.show { display: block; }
        .progress-wrap { background: rgba(255, 255, 255, 0.1); border-radius: 10px; height: 12px; margin-bottom: 8px; display: none; overflow:hidden; }
        .progress-wrap.show { display: block; }
        .progress-fill { background: linear-gradient(90deg, var(--purple-accent) 0%, var(--teal-accent) 100%); height: 100%; border-radius: 10px; transition: width .4s; }
        .progress-text { text-align: center; color: #94A3B8; font-size: 15px; font-weight: 700; margin-bottom: 16px; display: none; }
        .progress-text.show { display: block; }
        
        .hint-box {
            background: rgba(13, 148, 136, 0.15);
            border: 1px solid rgba(20, 184, 166, 0.35);
            border-radius: var(--radius-lg);
            padding: 16px 24px;
            font-size: 15px;
            color: #99F6E4;
            display: none;
            margin-top: 20px;
        }
        .hint-box.show { display: block; }
        .hint-pill { display: inline-block; background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 20px; margin: 4px; border: 1px solid rgba(20, 184, 166, 0.4); font-weight: 700; color:white; }
        .voice-warn { display: none; background: rgba(245, 158, 11, 0.15); border: 2px solid #F59E0B; color: #FDE68A; border-radius: var(--radius-md); padding: 14px; font-size: 15px; font-weight: 700; margin-bottom: 16px; text-align: center; }
        .voice-warn.show { display: block; }
    </style></head><body>
    <div class="animated-bg-overlay">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
    </div>
    <div class="exam-shell">
        <!-- PROCESS STEPPER BAR -->
        <div class="student-progress-bar" style="margin-bottom: 24px;">
            <div class="step-item completed">
                <div class="step-num">✓</div>
                <div class="step-label">Register</div>
            </div>
            <div class="step-line active"></div>
            <div class="step-item completed">
                <div class="step-num">✓</div>
                <div class="step-label">Face Verified</div>
            </div>
            <div class="step-line active"></div>
            <div class="step-item completed">
                <div class="step-num">✓</div>
                <div class="step-label">Voice Verified</div>
            </div>
            <div class="step-line active"></div>
            <div class="step-item active">
                <div class="step-num">04</div>
                <div class="step-label">Start Exam</div>
            </div>
            <div class="step-line"></div>
            <div class="step-item">
                <div class="step-num">05</div>
                <div class="step-label">Submit</div>
            </div>
        </div>

        <div class="exam-header-bar">
            <div style="display:flex;align-items:center;gap:12px;">
                <div style="width:40px; height:40px; border-radius:12px; background:linear-gradient(135deg, var(--purple-accent) 0%, var(--teal-accent) 100%); color:white; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:18px;">S</div>
                <h1 style="font-size:20px;font-weight:800;color:white;">SmartScribe Examination</h1>
            </div>
            <div style="display:flex;align-items:center;gap:16px;">
                <div class="timer-box" id="timerBox">--:--</div>
                <button class="btn btn-secondary btn-sm" onclick="confirmLogout()" style="background:rgba(255,255,255,0.1);color:white;border-color:rgba(255,255,255,0.2);">🚪 Logout</button>
            </div>
        </div>

        <div class="voice-warn" id="voiceWarn">⚠️ Warning: Unrecognised voice detected — please speak yourself</div>
        <div class="status-bubble" id="statusBubble">Initializing... please wait.</div>
        
        <div class="progress-text" id="progressText">Question 1 of 0</div>
        <div class="progress-wrap" id="progressWrap"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>

        <div class="mic-area">
            <div class="mic-icon" id="micIcon">🎙️</div>
            <div class="mic-label" id="micLabel">Waiting...</div>
            <div class="wave-anim" id="waveAnim">
                <div class="wbar"></div><div class="wbar"></div><div class="wbar"></div>
                <div class="wbar"></div><div class="wbar"></div>
            </div>
        </div>

        <div class="transcript-box" id="transcriptBox">
            <div style="font-size:12px;color:#C4B5FD;font-weight:700;margin-bottom:6px;">🗣️ Speech Detected:</div>
            <div id="transcriptText"></div>
        </div>

        <div class="hint-box" id="hintBox">
            <strong>Voice Commands:</strong>
            <span class="hint-pill">"next" → next question</span>
            <span class="hint-pill">"repeat" → hear again</span>
            <span class="hint-pill">"submit" → finish exam</span>
        </div>

        <div class="submit-area" id="submitArea" style="display:none; text-align:center; margin-top:32px;">
            <p style="color:#94A3B8; margin-bottom:12px;">Or click to submit:</p>
            <button class="btn btn-primary btn-lg" id="submitBtn" onclick="manualSubmit()">📄 Submit Exam</button>
        </div>
    </div>

    <script>
    const urlP = new URLSearchParams(window.location.search);
    const regNo = urlP.get('regNo') || '""" + regNo + """';
    if(!regNo){alert('No reg number. Please verify first.');window.location.href='/student-verification';}

    let questions=[], answers=[], currentIndex=0, examId=null, examName='', studentName='';
    let examDurSec=3600, timerLeft=0, timerIntvl=null;

    const S = {IDLE:'idle',WAIT:'waiting_start',SEL:'selecting_exam',
               READQ:'reading_q',LISTENS:'listening_ans',CONFIRM:'confirming_ans',
               SUBMIT_Q:'asking_submit',SUBMITTING:'submitting'};
    let state = S.IDLE;

    let recognition=null, finalT='', interimT='', isSpeaking=false, silTimer=null;
    let recognitionRunning = false;
    let recognitionStarting = false;
    let answerBuffer = '';
    let restartTimer = null;
    let availExams=[];

    function startTimer(s){
        timerLeft=s;
        timerIntvl=setInterval(()=>{
            timerLeft--; updateTimerUI();
            if(timerLeft<=300) document.getElementById('timerBox').classList.add('warn');
            if(timerLeft>0 && timerLeft<=60 && timerLeft%30===0) speak(timerLeft+' seconds remaining.');
            if(timerLeft<=0){clearInterval(timerIntvl); autoSubmit();}
        },1000);
    }
    function updateTimerUI(){
        const m=Math.floor(timerLeft/60), s=timerLeft%60;
        document.getElementById('timerBox').textContent=String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');
    }
    function autoSubmit(){
        stopListening();
        const cur=(finalT+interimT).trim(); if(cur) saveAnswer(cur);
        setStatus('⏰ Time is up! Submitting...');
        speak('Time is up. Submitting your exam now.',()=>doSubmit());
    }

    function setStatus(msg){ document.getElementById('statusBubble').textContent=msg; }
    function setMic(st){
        const ic=document.getElementById('micIcon'), lb=document.getElementById('micLabel'), wv=document.getElementById('waveAnim');
        if(st==='listening'){ic.textContent='🎙️';ic.className='mic-icon listening';lb.textContent='🔴 Recording... speak now';lb.className='mic-label active';wv.classList.add('show');}
        else if(st==='speaking'){ic.textContent='🔊';ic.className='mic-icon';lb.textContent='Speaking...';lb.className='mic-label';wv.classList.remove('show');}
        else{ic.textContent='🎙️';ic.className='mic-icon';lb.textContent='Waiting...';lb.className='mic-label';wv.classList.remove('show');}
    }
    function showT(t){document.getElementById('transcriptText').textContent=t;document.getElementById('transcriptBox').classList.add('show');}
    function hideT(){document.getElementById('transcriptBox').classList.remove('show');}
    function showProgress(){
        ['progressText','progressWrap','hintBox','submitArea'].forEach(id=>document.getElementById(id).style.display='block');
    }
    function updProgress(){
        const pct=((currentIndex+1)/questions.length)*100;
        document.getElementById('progressFill').style.width=pct+'%';
        document.getElementById('progressText').textContent='Question '+(currentIndex+1)+' of '+questions.length;
    }

    function speak(text, cb){
        isSpeaking=true; setMic('speaking');
        window.speechSynthesis.cancel();
        const u=new SpeechSynthesisUtterance(text);
        u.rate=1.05; u.pitch=1;
        u.onend=()=>{isSpeaking=false; if(cb)cb();};
        u.onerror=()=>{isSpeaking=false; if(cb)cb();};
        window.speechSynthesis.speak(u);
    }

    function initRec(){
        if(!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)){
            setStatus('❌ Speech recognition is not supported. Please use Google Chrome.');
            return false;
        }
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SR();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        recognition.onstart = function(){
            recognitionRunning = true;
            recognitionStarting = false;
            console.log('🎤 Microphone listening started');
            setMic('listening');
        };

        recognition.onresult = function(ev){
            finalT = ''; interimT = '';
            for(let i = ev.resultIndex; i < ev.results.length; i++){
                const t = ev.results[i][0].transcript;
                if(ev.results[i].isFinal){ finalT += t; }else{ interimT += t; }
            }
            const currentSpeech = (finalT + interimT).trim();
            const lower = currentSpeech.toLowerCase();
            if(currentSpeech){ showT(currentSpeech); console.log('🎤 Heard:', currentSpeech); }

            if(state === S.WAIT){
                if(lower.includes('yes') || lower.includes('yeah') || lower.includes('yep') || lower.includes('ready') || lower.includes('start')){
                    stopListening(); startExamFlow(); return;
                }
            } else if(state === S.SEL){
                const m = matchExam(lower);
                if(m !== null){ stopListening(); examId = availExams[m].id; examName = availExams[m].name; loadQuestions(); return; }
            } else if(state === S.LISTENS){
                if(finalT){ answerBuffer += ' ' + finalT.trim(); answerBuffer = answerBuffer.trim(); }
                const displayText = (answerBuffer + ' ' + interimT).trim();
                if(displayText){ showT(displayText); console.log('📝 Current answer:', displayText); }
                resetSilTimer();
                const commandText = currentSpeech.toLowerCase();
                const words = commandText.trim().split(/\s+/);
                const isShort = words.length <= 4;

                if(isShort && (commandText.includes('next') || commandText.includes('done') || commandText.includes('move on'))){
                    stopListening(); saveAnswer(answerBuffer); confirmAndProceed(); return;
                }
                if(isShort && (commandText.includes('repeat') || commandText.includes('again') || commandText.includes('reread'))){
                    stopListening(); readQ(); return;
                }
                if(isShort && (commandText.includes('submit') || commandText.includes('finish') || commandText.includes('end exam'))){
                    stopListening(); saveAnswer(answerBuffer); askSubmit(); return;
                }
            } else if(state === S.CONFIRM){
                if(lower.includes('next') || lower.includes('yes') || lower.includes('continue') || lower.includes('ok')){
                    stopListening(); goNext(); return;
                } else if(lower.includes('repeat') || lower.includes('again') || lower.includes('no') || lower.includes('redo')){
                    stopListening(); readQ(); return;
                } else if(lower.includes('submit') || lower.includes('finish')){
                    stopListening(); askSubmit(); return;
                }
            } else if(state === S.SUBMIT_Q){
                if(lower.includes('yes') || lower.includes('submit') || lower.includes('confirm') || lower.includes('ok')){
                    stopListening(); doSubmit(); return;
                } else if(lower.includes('no') || lower.includes('cancel') || lower.includes('back')){
                    stopListening(); state = S.LISTENS; readQ(); return;
                }
            }
        };

        recognition.onerror = function(e){
            console.log('🎤 Speech recognition error:', e.error);
            recognitionStarting = false;
            if(e.error === 'not-allowed' || e.error === 'service-not-allowed'){
                recognitionRunning = false; setMic('idle');
                setStatus('❌ Microphone permission denied. Please allow microphone access in Chrome.');
                return;
            }
            if(e.error === 'audio-capture'){
                recognitionRunning = false; setMic('idle');
                setStatus('❌ Microphone not found. Please check your microphone.');
                return;
            }
            recognitionRunning = false; scheduleRecognitionRestart();
        };

        recognition.onend = function(){
            console.log('🎤 Speech recognition ended');
            recognitionRunning = false; recognitionStarting = false;
            if([S.LISTENS, S.WAIT, S.SEL, S.CONFIRM, S.SUBMIT_Q].includes(state) && !isSpeaking){
                scheduleRecognitionRestart();
            }
        };
        return true;
    }

    function scheduleRecognitionRestart(){
        if(restartTimer){ clearTimeout(restartTimer); }
        restartTimer = setTimeout(()=>{
            restartTimer = null;
            if(!recognition || recognitionRunning || recognitionStarting){ return; }
            if(![S.LISTENS, S.WAIT, S.SEL, S.CONFIRM, S.SUBMIT_Q].includes(state)){ return; }
            try{
                recognitionStarting = true; recognition.start();
                console.log('🔄 Speech recognition restarted');
            }catch(e){
                recognitionStarting = false; scheduleRecognitionRestart();
            }
        }, 700);
    }

    function startListening(){
        finalT = ''; interimT = ''; hideT();
        if(!recognition){
            setStatus('❌ Voice recognition is not available. Please use Google Chrome.');
            setMic('idle'); return;
        }
        setMic('listening'); setStatus('🎤 Listening... Please speak now.');
        if(recognitionRunning || recognitionStarting){ return; }
        try{
            recognitionStarting = true; recognition.start();
        }catch(e){
            recognitionStarting = false; scheduleRecognitionRestart();
        }
    }

    function stopListening(){
        clearSilTimer(); setMic('idle');
        try{ recognition.stop(); }catch(e){}
    }

    function resetSilTimer(){
        clearSilTimer();
        silTimer = setTimeout(()=>{
            if(state === S.LISTENS && !isSpeaking){
                const ans = answerBuffer.trim();
                if(ans.length > 1){
                    setStatus('🎤 You can continue your answer or say NEXT when finished.');
                    resetSilTimer();
                }
            }
        },5000);
    }

    function clearSilTimer(){ if(silTimer){clearTimeout(silTimer);silTimer=null;} }

    function fmtTTS(q){
        const pat=/(?:^|\s)([a-dA-D])\)\s*/g;
        const matches=[...q.matchAll(pat)];
        if(!matches.length) return q;
        const stem=q.substring(0,matches[0].index).trim();
        let res=stem;
        matches.forEach((m,idx)=>{
            const letter=m[1].toLowerCase();
            const start=m.index+m[0].length;
            const end=idx+1<matches.length?matches[idx+1].index:q.length;
            const opt=q.substring(start,end).trim().replace(/\.$/, '');
            res+='. '+letter+', '+opt;
        });
        return res;
    }

    function init(){
        if(!initRec()) return;
        fetch('/api/student/data?regNo='+regNo).then(r=>r.json()).then(d=>{ if(d.name)studentName=d.name; });
        fetch('/api/student/available-exams').then(r=>r.json()).then(d=>{
            availExams=d.exams||[]; greet();
        });
    }

    function greet(){
        state=S.WAIT;
        const g=studentName
            ?('Hello '+studentName+'! Welcome to SmartScribe. Are you ready to begin your exam? Say YES when ready.')
            :'Welcome to SmartScribe exam. Are you ready? Say YES when ready.';
        setStatus(g); speak(g,()=>startListening());
    }

    function matchExam(text){
        text = (text || '').toLowerCase().trim();
        const numberWords = ['zero','one','two','three','four','five','six','seven','eight','nine','ten'];
        for(let i = 0; i < availExams.length; i++){
            const num = i + 1; const word = numberWords[num];
            if(new RegExp(`\\\\b${num}\\\\b`).test(text) || new RegExp(`\\\\b${word}\\\\b`).test(text) || text.includes('option ' + word) || text.includes('option ' + num)){ return i; }
            if(availExams[i].name && text.includes(availExams[i].name.toLowerCase())){ return i; }
        }
        return null;
    }

    function startExamFlow(){
        if(availExams.length===0){speak('No exams available. Contact your administrator.');return;}
        if(availExams.length===1){examId=availExams[0].id;examName=availExams[0].name;loadQuestions();return;}
        state=S.SEL;
        let msg='You have '+availExams.length+' exams available. ';
        availExams.forEach((e,i)=>msg+='Option '+(i+1)+': '+e.name+'. ');
        msg+='Say the number or name of your exam.';
        setStatus(msg); speak(msg,()=>startListening());
    }

    function loadQuestions(){
        setStatus('Loading exam...'); speak('Loading '+examName+'. Please wait.',null);
        fetch('/api/exam/questions/'+examId).then(r=>r.json()).then(d=>{
            if(d.questions&&d.questions.length>0){
                questions=d.questions; answers=new Array(questions.length).fill('');
                examDurSec=(d.duration_minutes||60)*60;
                currentIndex=0; showProgress(); updProgress();
                startTimer(examDurSec);
                const intro='Exam loaded. You have '+questions.length+' questions and '+(d.duration_minutes||60)+
                    ' minutes. After each question I will start recording your answer. '+
                    'Say NEXT after your answer, REPEAT to hear the question again, or SUBMIT when finished. '+
                    'Starting now. Question 1.';
                setStatus('✅ Exam started!'); speak(intro,()=>readQ());
            }else{speak('No questions found. Contact your administrator.');}
        }).catch(()=>speak('Error loading exam. Please try again.'));
    }

    function readQ(){
        state=S.READQ; updProgress(); clearSilTimer(); hideT();
        const raw = questions[currentIndex];
        const cleanQuestion = raw.replace(/^\s*\d+\s*[\.\):\-]?\s*/, '').trim();
        const spoken = fmtTTS(cleanQuestion);
        setStatus('📢 Q'+(currentIndex+1)+': '+raw);
        speak('Question '+(currentIndex+1)+'. '+spoken,()=>{
            state = S.LISTENS;
            finalT = ''; interimT = ''; answerBuffer = '';
            setStatus('🎤 Listening... speak your answer.');
            startListening(); resetSilTimer();
        });
    }

    function saveAnswer(text){
        const cleaned = (text || '').trim();
        if(cleaned){ answers[currentIndex] = cleaned; }
    }

    function confirmAndProceed(){
        state=S.CONFIRM;
        const ans=answers[currentIndex];
        if(!ans||!ans.trim()){
            const m='I did not catch your answer. Say REPEAT to hear the question again, or NEXT to skip.';
            setStatus('⚠️ '+m); speak(m,()=>startListening()); return;
        }
        const m='I recorded: '+ans+'. Say NEXT to move on, or REPEAT to redo this question.';
        setStatus('✅ Recorded: '+ans); speak(m,()=>startListening());
    }

    function goNext(){
        if(currentIndex<questions.length-1){currentIndex++;readQ();}else{askSubmit();}
    }

    function askSubmit(){
        state=S.SUBMIT_Q;
        const m='You have completed all '+questions.length+' questions. Say YES to submit and download your answer sheet, or NO to go back to the last question.';
        setStatus('📄 Ready to submit?'); speak(m,()=>startListening());
    }

    function manualSubmit(){
        if(state===S.SUBMITTING) return;
        const cur=(finalT+interimT).trim(); if(cur) saveAnswer(cur);
        stopListening();
        if(confirm('Submit your exam now? Your answers will be downloaded as a PDF.')) doSubmit();
    }

    function doSubmit(){
        if(state===S.SUBMITTING) return;
        state=S.SUBMITTING;
        clearInterval(timerIntvl); 
        const btn=document.getElementById('submitBtn');
        if(btn){btn.disabled=true;btn.textContent='⏳ Submitting...';}
        setMic('idle'); setStatus('⏳ Submitting and generating your answer PDF...');
        speak('Submitting your exam. Please wait.',null);
        const aData=questions.map((q,i)=>({question:q,answer:answers[i]||''}));
        fetch('/api/exam/submit',{method:'POST',headers:{'Content-Type':'application/json'},
            body:JSON.stringify({regNo,examId,examName,studentName,answers:aData})})
        .then(res=>{if(!res.ok)throw new Error('Server error '+res.status);return res.blob();})
        .then(blob=>{
            const url=window.URL.createObjectURL(blob);
            const a=document.createElement('a');a.href=url;
            const sn=(studentName||regNo).replace(/[^a-zA-Z0-9]/g,'_');
            const se=(examName||'Exam').replace(/[^a-zA-Z0-9]/g,'_');
            a.download=sn+'.'+se+'.pdf';
            document.body.appendChild(a);a.click();a.remove();
            window.URL.revokeObjectURL(url);
            setStatus('🎉 Exam submitted! Answer sheet downloaded.');
            speak('Congratulations! Your exam has been submitted and your answer sheet downloaded. Well done!',null);
            document.getElementById('timerBox').textContent='Done';
            document.getElementById('timerBox').classList.remove('warn');
        }).catch(err=>{
            console.error(err);
            setStatus('❌ Submission error. Please contact your invigilator.');
            speak('There was an error submitting. Please inform your invigilator.',null);
            if(btn){btn.disabled=false;btn.textContent='📄 Submit Exam';}
            state=S.SUBMIT_Q;
        });
    }

    function confirmLogout(){
        if(confirm('Logout? Unsaved answers will be lost.')){
            window.speechSynthesis.cancel();
            clearInterval(timerIntvl); 
            if(recognition)try{recognition.stop();}catch(e){}
            window.location.href='/';
        }
    }

    window.addEventListener('load',()=>setTimeout(init,500));
    window.addEventListener('beforeunload',()=>{
        window.speechSynthesis.cancel(); 
        if(recognition)try{recognition.stop();}catch(e){}
    });
    </script></body></html>
    """, regNo=regNo)

# ─── ADMIN ─────────────────────────────────────────────────
@app.route('/api/admin/register', methods=['POST'])
def api_admin_register():
    d=request.json; u=d.get('username'); p=d.get('password')
    if not u or not p: return jsonify({'success':False,'message':'Username and password required'})
    with get_db() as conn:
        c=conn.cursor()
        if c.execute("SELECT id FROM admins WHERE username=?",(u,)).fetchone():
            return jsonify({'success':False,'message':'Username already exists'})
        c.execute("INSERT INTO admins (username,password) VALUES (?,?)",(u,hashlib.sha256(p.encode()).hexdigest()))
    return jsonify({'success':True})

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    d=request.json
    with get_db() as conn:
        a=conn.cursor().execute("SELECT password FROM admins WHERE username=?",(d.get('username'),)).fetchone()
        if a and a['password']==hashlib.sha256(d.get('password','').encode()).hexdigest():
            return jsonify({'success':True})
    return jsonify({'success':False})

@app.route('/api/admin/create-student', methods=['POST'])
def api_create_student():
    data=request.json; regNo=data.get('regNo')
    with get_db() as conn:
        if conn.cursor().execute("SELECT reg_no FROM students WHERE reg_no=?",(regNo,)).fetchone():
            return jsonify({'success':False,'message':'Student already exists'})

    # Face
    face_enc=extract_face_features(data.get('image',''))
    if face_enc is None:
        return jsonify({'success':False,'message':'No face detected. Upload a clear, well-lit photo.'})

    # Voice — accept any audio format, convert to MFCC embedding + store WAV
    raw_voice=data.get('voice','')
    if not raw_voice:
        return jsonify({'success':False,'message':'Voice sample missing. Please record voice in Step 2.'})

    emb, wav_b64 = compute_voice_embedding(raw_voice)
    if emb is None:
        return jsonify({'success':False,'message':'Voice sample too short or silent. Please record 5+ seconds of clear speech.'})

    with get_db() as conn:
        conn.cursor().execute(
            "INSERT INTO students (reg_no,name,image,face_encoding,voice_embedding,voice_wav_b64) VALUES (?,?,?,?,?,?)",
            (regNo, data.get('name'), data.get('image'),
             json.dumps(face_enc), json.dumps(emb.tolist()), wav_b64)
        )
    print(f"Student registered: {regNo} | voice_emb_len={len(emb)}")
    return jsonify({'success':True})

@app.route('/api/admin/delete-student', methods=['POST'])
def api_delete_student():
    with get_db() as conn:
        conn.cursor().execute("DELETE FROM students WHERE reg_no=?",(request.json.get('regNo'),))
    return jsonify({'success':True})

@app.route('/api/admin/stats', methods=['GET'])
def api_stats():
    with get_db() as conn:
        c=conn.cursor()
        ts=c.execute("SELECT COUNT(*) as n FROM students").fetchone()['n']
        te=c.execute("SELECT COUNT(*) as n FROM exams").fetchone()['n']
        tsub=c.execute("SELECT COUNT(*) as n FROM exam_submissions").fetchone()['n']
    return jsonify({'totalStudents':ts,'totalExams':te,'totalSubmissions':tsub})

@app.route('/api/admin/create-exam', methods=['POST'])
def api_create_exam():

    d = request.json
    dur = int(d.get('duration', 60))

    qs = parse_questions_from_text(
        extract_text_from_pdf(d.get('pdf', ''))
    )

    print("🔥 QUESTIONS BEING SAVED:", qs)

    eid = str(uuid.uuid4())[:8]

    with get_db() as conn:
        conn.cursor().execute(
            "INSERT INTO exams (id,name,pdf,questions,duration_minutes) VALUES (?,?,?,?,?)",
            (
                eid,
                d.get('name'),
                d.get('pdf'),
                json.dumps(qs),
                dur
            )
        )

    return jsonify({
        'success': True,
        'exam_id': eid,
        'question_count': len(qs)
    })


@app.route('/api/admin/delete-exam/<exam_id>', methods=['POST'])
def api_delete_exam(exam_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            exam = cursor.execute("SELECT id FROM exams WHERE id=?", (exam_id,)).fetchone()
            if not exam:
                return jsonify({'success':False,'message':'Exam not found'}), 404
            cursor.execute("DELETE FROM exams WHERE id=?", (exam_id,))
        return jsonify({'success':True,'message':'Exam and question paper deleted successfully'})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)}), 500

@app.route('/api/admin/delete-submission/<int:sid>', methods=['POST'])
def api_delete_submission(sid):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            submission = cursor.execute("SELECT id FROM exam_submissions WHERE id=?", (sid,)).fetchone()
            if not submission:
                return jsonify({'success':False,'message':'Submission not found'}), 404
            cursor.execute("DELETE FROM exam_submissions WHERE id=?", (sid,))
        return jsonify({'success':True,'message':'Submission deleted successfully'})
    except Exception as e:
        return jsonify({'success':False,'message':str(e)}), 500

@app.route('/api/admin/download-submission/<int:sid>', methods=['GET'])
def api_dl_submission(sid):
    with get_db() as conn:
        row=conn.cursor().execute("SELECT pdf_data,pdf_filename FROM exam_submissions WHERE id=?",(sid,)).fetchone()
    if not row or not row['pdf_data']: return 'PDF not found',404
    return send_file(io.BytesIO(row['pdf_data']),as_attachment=True,
        download_name=row['pdf_filename'] or f'submission_{sid}.pdf',mimetype='application/pdf')

# ─── STUDENT ───────────────────────────────────────────────
@app.route('/api/student/data', methods=['GET'])
def api_student_data():
    rn=request.args.get('regNo')
    with get_db() as conn:
        s=conn.cursor().execute("SELECT name FROM students WHERE reg_no=?",(rn,)).fetchone()
    return jsonify({'name':s['name'] if s else ''})

@app.route('/api/student/available-exams', methods=['GET'])
def api_available_exams():
    with get_db() as conn:
        exams=conn.cursor().execute("SELECT id,name FROM exams ORDER BY created_at DESC").fetchall()
    return jsonify({'exams':[{'id':e['id'],'name':e['name']} for e in exams]})

@app.route('/api/student/verify-face', methods=['POST'])
def api_verify_face():
    d=request.json; rn=d.get('regNo')
    with get_db() as conn:
        s=conn.cursor().execute("SELECT face_encoding FROM students WHERE reg_no=?",(rn,)).fetchone()
    if not s: return jsonify({'success':False,'message':'Registration number not found'})
    try: enc=json.loads(s['face_encoding'])
    except: return jsonify({'success':False,'message':'Face data corrupted'})
    ok,msg=verify_face(enc,d.get('image',''))
    print(f"Face verify {rn}: {ok} — {msg}")
    return jsonify({'success':ok,'message':msg})

@app.route('/api/student/verify-voice', methods=['POST'])
def api_verify_voice():
    d=request.json; rn=d.get('regNo')
    with get_db() as conn:
        s=conn.cursor().execute("SELECT voice_embedding FROM students WHERE reg_no=?",(rn,)).fetchone()
    if not s: return jsonify({'success':False,'message':'Student not found'})
    if not s['voice_embedding']:
        # No voice enrolled — block login, student must re-register with voice
        return jsonify({'success':False,'message':'No voice registered for this student. Please contact your administrator to re-register with a voice sample.','sim':0.0})
    reg_emb=json.loads(s['voice_embedding'])
    ok,msg,sim=verify_voice_embedding(reg_emb, d.get('voice',''))
    print(f"Voice verify {rn}: {ok} sim={sim:.3f}")
    return jsonify({'success':ok,'message':msg,'sim':round(sim,3)})

@app.route('/api/student/verify-voice-monitor', methods=['POST'])
def api_voice_monitor():
    """Real-time guard during exam — lenient threshold, silent on short samples."""
    d=request.json; rn=d.get('regNo')
    with get_db() as conn:
        s=conn.cursor().execute("SELECT voice_embedding FROM students WHERE reg_no=?",(rn,)).fetchone()
    if not s or not s['voice_embedding']:
        return jsonify({'ok':False,'sim':0.0})  # no enrollment → fail guard
    reg_emb=json.loads(s['voice_embedding'])
    pcm, _=audio_b64_to_pcm_numpy(d.get('voice',''))
    if pcm is None or len(pcm)<8000:
        return jsonify({'ok':True,'sim':1.0})   # too short → skip
    emb=extract_mfcc_embedding(pcm)
    if emb is None:
        return jsonify({'ok':True,'sim':1.0})
    sim=cosine_sim(reg_emb, emb.tolist())
    print(f"Voice monitor {rn}: sim={sim:.3f}")
    return jsonify({'ok': sim>=VOICE_MONITOR_THRESHOLD,'sim':round(sim,3)})

# ─── EXAM ──────────────────────────────────────────────────
@app.route('/api/exam/questions/<exam_id>', methods=['GET'])
def api_exam_questions(exam_id):
    with get_db() as conn:
        e=conn.cursor().execute("SELECT questions,duration_minutes FROM exams WHERE id=?",(exam_id,)).fetchone()
    if e:
        return jsonify({'questions':json.loads(e['questions']),'duration_minutes':e['duration_minutes'] or 60})
    return jsonify({'questions':[],'duration_minutes':60})

@app.route('/api/exam/pdf/<exam_id>', methods=['GET'])
def api_exam_pdf(exam_id):
    with get_db() as conn:
        e=conn.cursor().execute("SELECT name,questions,duration_minutes,created_at FROM exams WHERE id=?",(exam_id,)).fetchone()
    if e:
        qs=json.loads(e['questions'])
        qs_html=''.join([f'<div style="margin-bottom:14px;padding:12px;background:#f8f9fa;border-radius:8px;border-left:4px solid #D082D9;"><strong style="color:#D082D9;">Q{i}:</strong> {q}</div>' for i,q in enumerate(qs,1)])
        return f'<!DOCTYPE html><html><head><title>{e["name"]}</title><style>body{{font-family:Segoe UI,sans-serif;padding:20px;}}.hdr{{background:#D082D9;color:white;padding:18px;border-radius:10px;margin-bottom:18px;}}</style></head><body><div class="hdr"><h1>{e["name"]}</h1><p>Duration: {e["duration_minutes"]} min | Created: {e["created_at"] or "N/A"}</p></div>{qs_html}<button onclick="window.print()" style="background:#D082D9;color:white;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;">🖨️ Print</button></body></html>'
    return '<h2>Exam not found</h2>',404

@app.route('/api/exam/submit', methods=['POST'])
def api_exam_submit():
    try:
        d=request.json
        rn=d.get('regNo'); eid=d.get('examId')
        ename=d.get('examName','Exam'); sname=d.get('studentName','')
        answers=d.get('answers',[])
        if not rn or not eid or not answers: return jsonify({'error':'Missing data'}),400
        if not sname:
            with get_db() as conn:
                s=conn.cursor().execute("SELECT name FROM students WHERE reg_no=?",(rn,)).fetchone()
                if s: sname=s['name']
        pdf_bytes=generate_exam_pdf(rn,sname or 'Unknown',ename,answers)
        safe_s=(sname or rn).replace(' ','_').replace('/','_')
        safe_e=(ename or 'Exam').replace(' ','_').replace('/','_')
        fname=f"{safe_s}.{safe_e}.pdf"
        with get_db() as conn:
            conn.cursor().execute(
                "INSERT INTO exam_submissions (reg_no,student_name,exam_id,exam_name,answers,pdf_data,pdf_filename) VALUES (?,?,?,?,?,?,?)",
                (rn,sname or 'Unknown',eid,ename,json.dumps(answers),pdf_bytes,fname)
            )
        return send_file(io.BytesIO(pdf_bytes),as_attachment=True,download_name=fname,mimetype='application/pdf')
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error':str(e)}),500

# ==================== RENDER / LOCAL STARTUP ====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 70)
    print("SMARTSCRIBE SERVER STARTING")
    print(f"Listening on 0.0.0.0:{port}")
    print("=" * 70)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
