import os
import sys
import wave
import contextlib
import collections
import numpy as np
import pandas as pd
from pydub import AudioSegment
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile
import webrtcvad
import requests
from logger_config import logger

# ==== 環境変数・API初期化 ====
load_dotenv()
API_TYPE = os.getenv("OPENAI_API_TYPE", "openai")

BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost:8000")
GPT_API_URL = BASE_API_URL+"/secure-gpt-chat"

if API_TYPE == "azure":
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
else:
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# ==== 音声処理 ====
def read_wave(path):
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        channels = wf.getnchannels()
        assert channels == 1, "Mono audio only"
        width = wf.getsampwidth()
        assert width == 2
        rate = wf.getframerate()
        assert rate in (8000, 16000, 32000, 48000)
        frames = wf.readframes(wf.getnframes())
        return frames, rate

def frame_generator(frame_duration_ms, audio, sample_rate):
    n = int(sample_rate * frame_duration_ms / 1000.0) * 2
    offset = 0
    while offset + n < len(audio):
        yield audio[offset:offset + n]
        offset += n

def vad_collector(rate, frame_duration_ms, padding_duration_ms, vad, frames):
    num_padding = int(padding_duration_ms / frame_duration_ms)
    ring_buffer = collections.deque(maxlen=num_padding)
    triggered = False
    voiced = []
    start, end = 0, 0
    timestamp = 0.0
    duration = float(frame_duration_ms) / 1000

    for frame in frames:
        is_speech = vad.is_speech(frame, rate)
        if not triggered:
            ring_buffer.append((frame, timestamp))
            if len([f for f, t in ring_buffer if vad.is_speech(f, rate)]) > 0.9 * ring_buffer.maxlen:
                triggered = True
                start = ring_buffer[0][1]
                ring_buffer.clear()
        else:
            ring_buffer.append((frame, timestamp))
            if len([f for f, t in ring_buffer if not vad.is_speech(f, rate)]) > 0.9 * ring_buffer.maxlen:
                end = timestamp + duration
                voiced.append((start, end))
                triggered = False
                ring_buffer.clear()
        timestamp += duration

    if triggered:
        end = timestamp
        voiced.append((start, end))

    return voiced

def extract_vad_segments(wav_path, aggressiveness=3):
    audio, rate = read_wave(wav_path)
    vad = webrtcvad.Vad(aggressiveness)
    frames = list(frame_generator(30, audio, rate))
    segments = vad_collector(rate, 30, 300, vad, frames)
    df = pd.DataFrame(segments, columns=["start", "end"])
    df["duration"] = df["end"] - df["start"]
    df["speaker"] = "user"
    return df

def analyze_loudness(wav_path):
    audio = AudioSegment.from_wav(wav_path)
    return {
        "average_loudness_dBFS": round(audio.dBFS, 2),
        "max_loudness_dBFS": round(audio.max_dBFS, 2),
        "duration_sec": round(audio.duration_seconds, 2)
    }

def create_prompt(transcript_text, vad_df, loudness_info):
    avg_speech = round(vad_df["duration"].mean(), 2)
    max_pause = round(vad_df["start"].iloc[1:].sub(vad_df["end"].shift()[1:]).max(), 2)

    return f"""
この通話を以下の観点で評価してください：

1. 声の大きさやトーン（ラウドネス）
2. 沈黙の取り方や「間」の適切さ
3. クロージングや要点の伝え方
4. ラポール形成や自然な会話かどうか
5. 総合スコア（5点満点）とその理由

# 書き起こし
{transcript_text}

# 音声特徴量
- 平均発話時間: {avg_speech} 秒
- 最大沈黙時間: {max_pause} 秒
- 平均音量: {loudness_info['average_loudness_dBFS']} dBFS
- 最大音量: {loudness_info['max_loudness_dBFS']} dBFS
- 通話全体長: {loudness_info['duration_sec']} 秒
"""

def evaluate_with_gpt(prompt_text):
    """GPTでテキストを評価"""
    try:
        # ✅ 'text' → 'user_message' に修正
        response = requests.post(
            GPT_API_URL, 
            json={"user_message": prompt_text},  # ← 修正
            timeout=30
        )
        response.raise_for_status()
        return True, response.json().get("reply", "評価に失敗しました")
    except Exception as e:
        logger.error(f"❌ GPT評価エラー: {e}")
        return False, f"❌ GPT評価エラー: {e}"

def extract_audio_features_from_uploaded_file(uploaded_file_or_path):
    try:
        if isinstance(uploaded_file_or_path, str) and os.path.isfile(uploaded_file_or_path):
            wav_path = uploaded_file_or_path
        else:
            with NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(uploaded_file_or_path.read())
                wav_path = tmp.name

        df = extract_vad_segments(wav_path)
        loudness = analyze_loudness(wav_path)

        return {
            "平均発話時間（秒）": round(df["duration"].mean(), 2),
            "最大沈黙時間（秒）": round(df["start"].iloc[1:].sub(df["end"].shift()[1:]).max(), 2),
            "平均音量（dBFS）": loudness["average_loudness_dBFS"],
            "最大音量（dBFS）": loudness["max_loudness_dBFS"],
            "通話時間（秒）": loudness["duration_sec"]
        }
    except Exception as e:
        logger.error(f"❌ 音声処理エラー: {e}")
        return ""

# if __name__ == "__main__":
#     if len(sys.argv) != 3:
#         print("Usage: python audio_features.py <wav_path> <transcript_path>")
#         sys.exit(1)

#     wav_path = sys.argv[1]
#     txt_path = sys.argv[2]

#     df = extract_vad_segments(wav_path)
#     loudness = analyze_loudness(wav_path)
#     transcript = open(txt_path, encoding="utf-8").read()
#     prompt = create_prompt(transcript, df, loudness)
#     gpt_result = evaluate_with_gpt(prompt)

#     print("\n==== 🧠 GPT評価結果 ====")
#     print(gpt_result)
