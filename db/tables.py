from backend.mysql_connector import execute_query

# user table
def create_users_table():
    """ユーザーDBの初期化"""
    execute_query('''
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(50) NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            is_admin TINYINT DEFAULT 0,
            created_by INT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ''')
    print("✅ ユーザーDBを初期化しました")
# Teams table
def create_teams_table():
    """チムーDBの初期化"""
    execute_query('''
        CREATE TABLE IF NOT EXISTS teams (
            id INT PRIMARY KEY AUTO_INCREMENT,
            team_name VARCHAR(50) NULL,
            descriptions VARCHAR(100) NULL,
            is_active TINYINT DEFAULT 1,
            created_by INT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ''')
    print("✅ ユーザーDBを初期化しました")

# prompts table 
def create_prompts_table():
    """promptsテーブル作成（9列対応）"""
    execute_query('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            prompt_key VARCHAR(255) NOT NULL,
            text_prompt TEXT,
            audio_prompt TEXT,
            score_items TEXT,
            notes VARCHAR(100) NULL,
            is_active TINYINT DEFAULT 1,
            created_by INT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ''')
    print("✅ team_master テーブル作成完了（9列対応）")
# team_has_prompts table 
def create_team_has_prompts_table():
    """team_has_promptsテーブル作成（6列対応）"""
    execute_query('''
        CREATE TABLE IF NOT EXISTS team_has_prompts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            team_id INT NOT NULL,
            prompt_id INT NOT NULL,
            is_active TINYINT DEFAULT 1,
            created_by INT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
            FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
            UNIQUE (team_id, prompt_id)
        );
    ''')
    print("✅ team_has_prompts テーブル作成完了（6列対応）")
# user_has_teams table 
def create_user_has_teams_table():
    """user_has_teamsテーブル作成（6列対応）"""
    execute_query('''
        CREATE TABLE IF NOT EXISTS user_has_teams (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            team_id INT NOT NULL,
            is_active TINYINT DEFAULT 1,
            created_by INT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
        );
    ''')
    print("✅ user_has_teams テーブル作成完了（6列対応）")

# shodans table 
def create_shodans_table():
    """shodansテーブル作成"""
    execute_query('''
        CREATE TABLE IF NOT EXISTS shodans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            team_id INT NOT NULL,
            prompt_id INT NOT NULL,
            kintone_id VARCHAR(10) DEFAULT NULL,
            phone_no VARCHAR(14) NOT NULL,
            shodan_date DATE DEFAULT NULL,
            shodan_text TEXT DEFAULT NULL,
            audio_file VARCHAR(50) DEFAULT NULL,
            outcome VARCHAR(50) DEFAULT NULL,
            is_evaluated TINYINT DEFAULT 0,
            is_evaluation_saved TINYINT DEFAULT 0,
            created_by INT NULL,
            evaluated_time DATETIME DEFAULT NULL,
            evaluation_save_time DATETIME DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_team_id (team_id),
            INDEX idx_prompt_id (prompt_id),
            INDEX idx_kintone_id (kintone_id),
            INDEX idx_phone_no (phone_no),
            INDEX idx_shodan_date (shodan_date)
        );
    ''')
    print("✅ shodans テーブル作成完了")

def create_evaluation_logs_table():
    """評価ログテーブルを初期化"""
    execute_query('''
        CREATE TABLE IF NOT EXISTS evaluation_logs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            shodan_id INT NOT NULL,
            reply TEXT DEFAULT NULL,
            full_prompt TEXT DEFAULT NULL,
            audio_features TEXT DEFAULT NULL,
            audio_feedback TEXT DEFAULT NULL,
            evaluation_outcome VARCHAR(10) DEFAULT NULL COMMENT 'Evaluation outcome after evaluation. (e.g., pass/fail/score code)',
            comment VARCHAR(5) DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_shodan_id (shodan_id)
        )
    ''')
    print("✅ evaluation_logs テーブル初期化完了")


# ✅ 商談評価ログ管理機能（拡張版）
# def create_conversation_logs_table():
#     """商談評価ログテーブルを作成・拡張（なければ）"""
#     # ✅ 基本テーブル作成
#     execute_query('''
#         CREATE TABLE IF NOT EXISTS conversation_logs (
#             id INT PRIMARY KEY AUTO_INCREMENT,
#             date VARCHAR(20) NOT NULL,
#             time VARCHAR(20),
#             customer_name VARCHAR(100),
#             conversation_text TEXT,
#             gpt_feedback TEXT,
#             score DECIMAL(3,1),
#             username VARCHAR(50) NOT NULL,
#             status VARCHAR(20) DEFAULT '未設定',
#             followup_date VARCHAR(20),
#             tags TEXT,
#             created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
#             updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
#         )
#     ''')
    
#     print("✅ conversation_logs テーブル初期化完了")