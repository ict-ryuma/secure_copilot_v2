from datetime import datetime
import os
def save_audio_file(audio_file, upload_dir = "uploads"):
    """アップロードされた音声ファイルを一時ディレクトリに保存"""
    if audio_file is not None:
        os.makedirs(upload_dir, exist_ok=True)
        # Save file to directory
        audio_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{audio_file.name}"
        file_path = os.path.join(upload_dir, audio_filename)
        with open(file_path, "wb") as f:
            f.write(audio_file.getbuffer())
        return file_path
    return None