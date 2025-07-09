from pathlib import Path
import yaml
from typing import Optional, Dict, List, Any

PROMPT_CONFIG_PATH = Path(__file__).resolve().parent / "prompt_config.yaml"

def load_prompt_config(path: Path = PROMPT_CONFIG_PATH) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"プロンプト設定ファイルが見つかりません: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if not isinstance(config, dict):
            raise ValueError("YAMLの最上位構造は辞書形式である必要があります（チーム名またはscore_items）。")
        return config
    except yaml.YAMLError as e:
        raise RuntimeError(f"YAMLの読み込み中にエラーが発生しました: {e}")

def get_prompts_for_team(team_name: str,
                         fallback_text: Optional[str] = "",
                         fallback_audio: Optional[str] = "") -> Dict[str, Any]:
    config = load_prompt_config()
    global_score_items: List[str] = config.get("score_items", [])
    team_config = config.get(team_name, {})

    if not isinstance(team_config, dict):
        raise ValueError(f"チーム「{team_name}」の設定が無効です（辞書形式である必要があります）。")

    return {
        "text_prompt": team_config.get("text_prompt", fallback_text),
        "audio_prompt": team_config.get("audio_prompt", fallback_audio),
        "product": team_config.get("product", ""),
        "notes": team_config.get("notes", ""),
        "score_items": global_score_items
    }

def get_all_team_names() -> List[str]:
    config = load_prompt_config()
    return [key for key in config if key != "score_items"]
