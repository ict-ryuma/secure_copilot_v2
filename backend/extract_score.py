import re
from typing import List

def extract_scores_and_sections(gpt_output: str, score_items: List[str] = None) -> dict:
    result = {
        "scores": {},
        "strengths": "（強みの記述が確認できませんでした）",
        "improvements": "（改善点の記述が確認できませんでした）",
        "cautions": "（注意ポイントの記述が確認できませんでした）",
        "actions": "（アクション提案の記述が確認できませんでした）"
    }

    if not score_items:
        score_items = [
            "ヒアリング姿勢",
            "説明のわかりやすさ",
            "クロージングの一貫性",
            "感情の乗せ方と誠実さ",
            "対話のテンポ"
        ]

    for key in score_items:
        result["scores"][key] = 0.0
        patterns = [
            rf"{re.escape(key)}[：:\s]*([0-9]+(?:\.[0-9]+)?)\s*/\s*10",
            rf"{re.escape(key)}[：:\s]*([0-9]+(?:\.[0-9]+)?)点",
            rf"{re.escape(key)}[：:\s]*([0-9]+(?:\.[0-9]+)?)"
        ]
        for pat in patterns:
            match = re.search(pat, gpt_output)
            if match:
                try:
                    result["scores"][key] = float(match.group(1))
                    break
                except:
                    continue

    section_labels = {
        "strengths": ["強み", "良かった点"],
        "improvements": ["改善点"],
        "cautions": ["注意すべきポイント", "注意点"],
        "actions": ["次に取るべき推奨アクション", "推奨アクション"]
    }

    label_positions = []
    for section_key, labels in section_labels.items():
        for label in labels:
            pattern = rf"(^|\n)[\s\-\*\d\.]*{label}[：:\s]*\n?"
            match = re.search(pattern, gpt_output)
            if match:
                label_positions.append((match.start(), section_key, match.end()))
                break

    label_positions.sort()

    for i, (start_pos, section_key, content_start) in enumerate(label_positions):
        end_pos = label_positions[i + 1][0] if i + 1 < len(label_positions) else len(gpt_output)
        content = gpt_output[content_start:end_pos].strip()
        if content:
            result[section_key] = content

    return result
