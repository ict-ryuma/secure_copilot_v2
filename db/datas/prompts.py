from backend.mysql_connector import execute_query
def create_prompts():
    """プレースホルダーチームをpromptsに登録"""
    
    prompts = [
        {
            "prompt_key": "prompt_a_team", 
            "text_prompt": "以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。",
            "audio_prompt": "音声の印象から話し方・テンポ・感情のこもり具合を評価してください。",
            "score_items": '["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
            "notes": "プレースホルダーチーム（移行用）",
            "is_active": 1  # ✅ 有効状態に変更
        },
        {
            "prompt_key": "prompt_b_team",
            "text_prompt": "以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。",
            "audio_prompt": "音声の印象から話し方・テンポ・感情のこもり具合を評価してください。",
            "score_items": '["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
            "notes": "プレースホルダーチーム（移行用）",
            "is_active": 0
        },
        {
            "prompt_key": "prompt_c_team", 
            "text_prompt": "以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。",
            "audio_prompt": "音声の印象から話し方・テンポ・感情のこもり具合を評価してください。",
            "score_items": '["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
            "notes": "プレースホルダーチーム（移行用）",
            "is_active": 0
        },
        {
            "prompt_key": "prompt_f_team",
            "text_prompt": "以下の会話内容を読み、次の5つの評価項目について10点満点で数値を出し、理由を含めてフィードバックを記載してください。",
            "audio_prompt": "音声の印象から話し方・テンポ・感情のこもり具合を評価してください。",
            "score_items": '["ヒアリング姿勢","説明のわかりやすさ","クロージングの一貫性","感情の乗せ方と誠実さ","対話のテンポ"]',
            "notes": "プレースホルダーチーム（移行用）",
            "is_active": 0
        }
    ]
    
    for prompt in prompts:
        try:
            execute_query('''
                INSERT INTO prompts 
                (prompt_key, text_prompt, audio_prompt, score_items, notes, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                text_prompt = VALUES(text_prompt),
                audio_prompt = VALUES(audio_prompt),
                score_items = VALUES(score_items),
                notes = VALUES(notes),
                is_active = VALUES(is_active)
            ''', (
                prompt["prompt_key"], 
                prompt["text_prompt"],
                prompt["audio_prompt"],
                prompt["score_items"],
                prompt["notes"],
                prompt["is_active"]
            ))
            print(f"✅ プレースホルダーチーム '{prompt['prompt_key']}' を登録しました")
        except Exception as e:
            print(f"❌ {prompt['prompt_key']} 登録エラー: {e}")
    print("🎉 プレースホルダーチーム初期化完了")