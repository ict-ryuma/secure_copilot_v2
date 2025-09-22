from datetime import datetime
import os
import random
import string
def save_audio_file(audio_file, upload_dir = "uploads"):
    """アップロードされた音声ファイルを一時ディレクトリに保存"""
    if audio_file is not None:
        os.makedirs(upload_dir, exist_ok=True)
        # Extract extension (without dot)
        _, ext = os.path.splitext(audio_file.name)
        extension = ext.lstrip(".").lower()  # e.g. "wav", "mp3"

        # Generate 10-digit random text
        random_text = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        # Save file to directory
        # audio_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{audio_file.name[-20:]}"
        audio_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{random_text}.{extension}"
        file_path = os.path.join(upload_dir, audio_filename)
        with open(file_path, "wb") as f:
            f.write(audio_file.getbuffer())
        return file_path
    return None