# backend/prompt_optimizer.py

from backend.analyze_logs import get_top_keywords_from_column, get_success_ratio

# 成約に繋がった頻出キーワードから強化プロンプトを生成
def generate_optimized_prompt():
    success_keywords = get_top_keywords_from_column(label="成約", top_n=5)
    success_ratio = get_success_ratio()

    keyword_phrases = [f"\u300c{k}\u300d" for k, _ in success_keywords]
    joined = "\uff0c".join(keyword_phrases)

    prompt = (
        f"最近の成約データから以下のような傾向が見られました：\n"
        f"- 成約率：{success_ratio}%\n"
        f"- 特に多く見られた重要な要素：{joined}\n\n"
        "今後の評価では、これらの要素をより重視し、\n"
        "改善点や強みに反映するようにしてください。\n"
        "また、アクション提案にもこれらを意識した具体的な提案を含めてください。"
    )
    return prompt
