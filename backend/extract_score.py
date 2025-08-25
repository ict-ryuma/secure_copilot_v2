import re
from typing import List
import json


def extract_scores_and_sections(gpt_output: str, score_items: List[str] = None) -> dict:
    result = {
        "scores": {},
        "strengths": "（強みの記述が確認できませんでした）",
        "improvements": "（改善点の記述が確認できませんでした）",
        "cautions": "（注意ポイントの記述が確認できませんでした）",
        "actions": "（アクション提案の記述が確認できませんでした）"
    }

    # === Default evaluation items ===
    if not score_items:
        score_items = [
            "ヒアリング姿勢",
            "説明のわかりやすさ",
            "クロージングの一貫性",
            "感情の乗せ方と誠実さ",
            "対話のテンポ"
        ]

    # ✅ Ensure score_items is a list, not a JSON string
    if isinstance(score_items, str):
        try:
            score_items = json.loads(score_items)  # try to parse JSON
        except Exception:
            score_items = [score_items]  # fallback: wrap as single item

    # === Score extraction ===
    for key in score_items:
        result["scores"][key] = 0.0
        patterns = [
            rf"{re.escape(key)}[：:\s\-]*([0-9]+(?:\.[0-9]+)?)[ ]*/[ ]*10",  # e.g. ○○: 8.0/10
            rf"{re.escape(key)}[：:\s\-]*([0-9]+(?:\.[0-9]+)?)点",           # e.g. ○○: 8.0点
            rf"{re.escape(key)}[：:\s\-]*([0-9]+(?:\.[0-9]+)?)"              # e.g. ○○: 8.0
        ]
        for pat in patterns:
            match = re.search(pat, gpt_output, re.MULTILINE)
            if match:
                try:
                    result["scores"][key] = float(match.group(1))
                    break
                except ValueError:
                    continue

    # === Section labels ===
    section_labels = {
        "strengths": ["強み", "良かった点", "ポジティブな点"],
        "improvements": ["改善点", "課題", "弱み"],
        "cautions": ["注意すべきポイント", "注意点", "リスク", "懸念点"],
        "actions": ["推奨アクション", "次に取るべき推奨アクション", "次の打ち手", "次のアクション"]
    }

    # === Find section positions ===
    label_positions = []
    for section_key, labels in section_labels.items():
        for label in labels:
            pattern = rf"(?:^|\n)[\s\-●・\d\.【\[]*{label}[\]】\s：:\-]*"
            match = re.search(pattern, gpt_output)
            if match:
                label_positions.append((match.start(), section_key, match.end()))
                break

    # === Extract sections ===
    label_positions.sort()
    for i, (start_pos, section_key, content_start) in enumerate(label_positions):
        end_pos = label_positions[i + 1][0] if i + 1 < len(label_positions) else len(gpt_output)
        content = gpt_output[content_start:end_pos].strip()
        if content:
            result[section_key] = content

    return result
