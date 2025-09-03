import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import os
import yaml
import fitz  # PyMuPDF


# --- パス設定 ---
BASE_DIR = Path(__file__).resolve().parents[1]
VISION_PATH = os.path.join(BASE_DIR, "team_knowledge", "company.yaml")
def company_vision_learning():
    st.subheader("🏢 会社ビジョンを学習させる")

    # ✅ 現在の保存先パスを表示
    st.info(f"📁 保存先: `{VISION_PATH}`")
    
    # ✅ 既存ファイルの確認と詳細表示
    if os.path.exists(VISION_PATH):
        try:
            with open(VISION_PATH, "r", encoding="utf-8") as f:
                existing_data = yaml.safe_load(f)
            
            if existing_data and "company_vision" in existing_data:
                # ファイル情報の表示
                file_size = os.path.getsize(VISION_PATH)
                file_mtime = os.path.getmtime(VISION_PATH)
                import datetime
                formatted_time = datetime.datetime.fromtimestamp(file_mtime).strftime("%Y年%m月%d日 %H:%M:%S")
                
                st.success("✅ 会社ビジョンが設定済みです")
                
                # ✅ 詳細情報カード
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 文字数", f"{len(existing_data['company_vision'])}文字")
                with col2:
                    st.metric("💾 ファイルサイズ", f"{file_size}bytes")
                with col3:
                    st.metric("🕒 最終更新", formatted_time)
                
                # ✅ メタデータ表示（更新者、タイムスタンプなど）
                if "updated_by" in existing_data:
                    st.caption(f"👤 更新者: {existing_data['updated_by']}")
                if "original_filename" in existing_data:
                    st.caption(f"📎 元ファイル名: {existing_data['original_filename']}")
                
                # ✅ 内容プレビュー（折りたたみ式）
                with st.expander("📄 現在の会社ビジョン内容を確認"):
                    st.text_area(
                        "設定済みの内容", 
                        existing_data["company_vision"], 
                        height=250, 
                        disabled=True,
                        help="この内容がAIの評価に使用されます"
                    )
                
                # ✅ バックアップ機能
                if st.button("💾 現在の内容をバックアップ", help="現在の設定を日時付きでバックアップします"):
                    backup_filename = f"company_vision_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
                    backup_path = os.path.join(os.path.dirname(VISION_PATH), backup_filename)
                    
                    with open(backup_path, "w", encoding="utf-8") as f:
                        yaml.dump(existing_data, f, allow_unicode=True, default_flow_style=False)
                    
                    st.success(f"✅ バックアップを作成しました: {backup_filename}")
                    
            else:
                st.warning("⚠️ ファイルは存在しますが、内容が正しくありません")
                
        except Exception as e:
            st.error(f"❌ 既存ファイルの読み込みエラー: {e}")
    else:
        st.warning("⚠️ まだ会社ビジョンが設定されていません")
        st.info("👇 下記の方法で会社ビジョンを設定してください")
    
    st.markdown("---")
    
    # ✅ 入力方法選択（より分かりやすく）
    st.subheader("📋 会社ビジョンの登録・更新")
    input_method = st.radio(
        "入力方法を選択してください", 
        ["📁 PDFファイルからアップロード", "✏️ テキストを直接入力"],
        help="PDFから自動抽出するか、テキストを直接貼り付けるかを選択"
    )
    
    extracted_text = ""
    original_filename = ""
    
    if input_method == "📁 PDFファイルからアップロード":
        uploaded_file = st.file_uploader(
            "会社ビジョン・ミッション資料（PDF）をアップロード", 
            type=["pdf"],
            help="会社案内、ビジョン資料、企業理念などのPDFファイルを選択してください"
        )
        
        if uploaded_file:
            original_filename = uploaded_file.name
            st.info(f"📎 選択されたファイル: **{original_filename}**")
            
            try:
                # ✅ プログレスバー表示
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("PDF読み込み中...")
                progress_bar.progress(0.25)  # 25% → 0.25に修正
                
                with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                    total_pages = len(doc)  # ドキュメントが開いている間に取得
                    status_text.text(f"テキスト抽出中... ({total_pages}ページ)")
                    progress_bar.progress(0.5)  # 50% → 0.5に修正
                    
                    pages_text = []
                    for i, page in enumerate(doc):
                        pages_text.append(page.get_text())
                        # プログレス値を0.0-1.0の範囲に正規化
                        progress_value = 0.5 + (i + 1) / total_pages * 0.3  # 50%から80%の範囲
                        progress_bar.progress(min(progress_value, 1.0))  # 1.0を超えないよう制限
                    
                    extracted_text = "\n".join(pages_text)
                
                progress_bar.progress(1.0)  # 100% → 1.0に修正
                status_text.text("✅ 完了")
                
                if extracted_text.strip():
                    st.success(f"✅ PDFからテキストを抽出しました（{len(extracted_text)}文字、{total_pages}ページ）")
                    
                    # ✅ プレビュー表示（最初の500文字）
                    preview_text = extracted_text[:500] + ("..." if len(extracted_text) > 500 else "")
                    st.text_area(
                        "抽出内容プレビュー（最初の500文字）", 
                        preview_text, 
                        height=150, 
                        disabled=True
                    )
                    
                    # ✅ 全文表示オプション
                    if st.checkbox("📖 抽出された全文を表示"):
                        st.text_area("抽出された全文", extracted_text, height=300, key="pdf_full_text")
                        
                else:
                    st.warning("⚠️ PDFからテキストを抽出できませんでした")
                    st.info("💡 スキャンされた画像PDFの場合、OCR処理が必要です")
                    
            except ImportError:
                st.error("❌ PyMuPDF (fitz) がインストールされていません")
                st.code("pip install PyMuPDF", language="bash")
            except Exception as e:
                st.error(f"❌ PDF読み込みエラー: {e}")
                with st.expander("🔧 詳細エラー情報"):
                    st.code(f"エラー詳細: {str(e)}")
    
    elif input_method == "✏️ テキストを直接入力":
        st.info("💡 会社のビジョン、ミッション、価値観、企業理念などを入力してください")
        extracted_text = st.text_area(
            "会社ビジョン・企業理念", 
            height=300, 
            placeholder="""例：
            【企業ビジョン】
            私たちは、革新的なソリューションを通じて...

            【ミッション】
            顧客の成功を第一に考え...

            【コアバリュー】
            1. 誠実性
            2. 革新性
            3. 顧客第一主義""",
            key="manual_vision_text"
        )
        
        if extracted_text.strip():
            st.success(f"✅ テキストが入力されました（{len(extracted_text)}文字）")
    
    # ✅ 保存処理（改良版）
    if extracted_text.strip():
        st.markdown("---")
        st.subheader("💾 保存設定")
        
        # ✅ 保存前の確認
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**保存される内容:**")
            st.info(f"📝 文字数: {len(extracted_text)}文字")
            if original_filename:
                st.info(f"📎 元ファイル: {original_filename}")
        
        with col2:
            if st.button("📥 保存する", type="primary", help="会社ビジョンとしてAIに学習させます"):
                try:
                    # ✅ ディレクトリ作成
                    vision_dir = os.path.dirname(VISION_PATH)
                    if not os.path.exists(vision_dir):
                        os.makedirs(vision_dir, exist_ok=True)
                        st.info(f"📁 ディレクトリを作成: {vision_dir}")
                    
                    # ✅ 詳細なメタデータ付きで保存
                    import datetime
                    vision_data = {
                        "company_vision": extracted_text.strip(),
                        "updated_by": st.session_state.get("username", "unknown"),
                        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "character_count": len(extracted_text.strip()),
                        "input_method": input_method,
                        "original_filename": original_filename if original_filename else "manual_input"
                    }
                    
                    with open(VISION_PATH, "w", encoding="utf-8") as f:
                        yaml.dump(vision_data, f, allow_unicode=True, default_flow_style=False)
                    
                    st.success("✅ 会社ビジョンを保存しました！")
                    st.balloons()
                    
                    # ✅ 保存結果の詳細表示
                    st.info(f"""
                    💾 **保存完了情報**
                    - ファイル: {os.path.basename(VISION_PATH)}
                    - サイズ: {os.path.getsize(VISION_PATH)} bytes
                    - 更新者: {vision_data['updated_by']}
                    - 更新日時: {vision_data['updated_at']}
                    """)
                    
                    # ✅ 自動リロード
                    st.rerun()
                    
                except PermissionError:
                    st.error("❌ ファイル書き込み権限がありません")
                    st.code(f"権限確認: chmod 755 {os.path.dirname(VISION_PATH)}")
                except Exception as e:
                    st.error(f"❌ 保存エラー: {e}")
                    with st.expander("🔧 詳細エラー情報"):
                        st.code(f"詳細: {str(e)}")
    
    # ✅ 操作ガイド
    with st.expander("❓ 会社ビジョン学習について"):
        st.markdown("""
        ### 📚 会社ビジョン学習機能とは？
        
        この機能では、会社の理念やビジョンをAIに学習させることで、
        営業評価がより会社の方針に沿った内容になります。
        
        ### 📋 設定できる内容
        - 🎯 企業ビジョン・ミッション
        - 💎 コアバリュー・企業価値観
        - 🏢 企業理念・経営方針
        - 🎪 企業文化・行動指針
        
        ### 🔄 活用方法
        設定された内容は、営業通話の評価時にAIが参考にして、
        会社の価値観に合った評価・アドバイスを提供します。
        """)
    
    # ✅ 技術情報（管理者向け）
    with st.expander("🔧 技術情報"):
        st.code(f"""
            パス情報:
            - 保存先: {VISION_PATH}
            - ディレクトリ: {os.path.dirname(VISION_PATH)}
            - ファイル存在: {os.path.exists(VISION_PATH)}
            - ディレクトリ存在: {os.path.exists(os.path.dirname(VISION_PATH))}

            依存関係:
            - PyMuPDF: {"✅ OK" if 'fitz' in globals() else "❌ 未インストール"}
            - YAML: {"✅ OK" if 'yaml' in globals() else "❌ 未インストール"}
        """)