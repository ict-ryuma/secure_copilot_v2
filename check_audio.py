# check_audio.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / "backend"))

try:
    from audio_features import extract_audio_features
except Exception as import_err:
    print(f"❌ モジュール読み込みエラー: {import_err}")
    sys.exit(1)

file_path = "data/sample.wav"

try:
    result = extract_audio_features(file_path)
    print("🎧 音声特徴量の抽出結果：")
    for key, value in result.items():
        print(f"{key}: {value}")
except AssertionError as ae:
    print(f"❌ 入力チェックエラー: {ae}")
except FileNotFoundError as fe:
    print(f"❌ ファイルが存在しません: {fe}")
except Exception as e:
    print(f"❌ その他のエラーが発生しました: {e}")
