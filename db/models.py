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
            shodan_text MEDIUMTEXT DEFAULT NULL,
            audio_file VARCHAR(150) DEFAULT NULL,
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
# def add_evaluated_by_column_to_evaluation_logs_table():
#     """評価ログテーブルにevaluated_byカラムを追加"""
#     execute_query('''
#         ALTER TABLE evaluation_logs
#         ADD COLUMN IF NOT EXISTS evaluated_by INT DEFAULT NULL COMMENT 'User ID who evaluated the shodan' AFTER comment;

#     ''')
#     print("✅ evaluation_logs テーブルにevaluated_byカラムを追加完了")


def add_evaluated_by_column_to_evaluation_logs_table():
    """Add 'evaluated_by' column to evaluation_logs table after 'comment' column"""
    table_name="evaluation_logs"
    check_columns_and_create(TableName=table_name,
        ColumnName="evaluated_by",
        ColumnType="INT",
        Default="NULL",
        Comment="ID of the user who evaluated the shodan",
        After="comment"
    )

def create_batch_last_success_times_table():
    """batch_last_success_times table"""
    execute_query('''
        CREATE TABLE IF NOT EXISTS batch_last_success_times (
            id INT AUTO_INCREMENT PRIMARY KEY,
            batch_name VARCHAR(50) NOT NULL,
            last_success_time DATETIME DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_batch_name (batch_name)
        )
    ''')
    print("✅ batch_last_success_times テーブル初期化完了")

def create_shodan_details_table():
    """Create shodan_details table if it does not exist"""
    query = """
    CREATE TABLE IF NOT EXISTS `shodan_details` (
        `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        `shodan_id` VARCHAR(10) NOT NULL,
        `agent_id` VARCHAR(70) NULL,
        `initiation_method` VARCHAR(20) NULL,
        `channel` VARCHAR(20) NULL,
        `system_number` VARCHAR(20) NULL,
        `contact_id` VARCHAR(100) NULL,
        `input_s3_audio_uri` TEXT NULL,
        `initiation_ts` DATETIME NULL,
        `disconnect_ts` DATETIME NULL,
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    execute_query(query)
    print("✅ shodan_details table is ready.")



def add_some_columns_to_shodans_table():
    table_name="shodans"
    check_columns_and_create(TableName=table_name,ColumnName="customer_number",ColumnType="VARCHAR(20)", Default="NULL",Comment="Customer Phone number column",After="phone_no")
    check_columns_and_create(TableName=table_name,ColumnName="team_has_prompt_id",ColumnType="VARCHAR(10)", Default="NULL",Comment="Team has prompt ID",After="user_id")
def add_some_columns_to_users_table():
    table_name="users"
    check_columns_and_create(TableName=table_name,ColumnName="first_name",ColumnType="VARCHAR(30)",Default="NULL",Comment="User first name",After="id")
    check_columns_and_create(TableName=table_name,ColumnName="last_name",ColumnType="VARCHAR(30)",Default="NULL",Comment="User last name",After="first_name")
    check_columns_and_create(TableName=table_name,ColumnName="email",ColumnType="VARCHAR(100)",Default="NULL",Comment="User Email address",After="username")
    check_columns_and_create(TableName=table_name,ColumnName="phone_no",ColumnType="VARCHAR(20)",Default="NULL",Comment="User Phone number",After="password_hash")


def check_columns_and_create(
    TableName=None,
    ColumnName=None,
    ColumnType="VARCHAR(50)",
    Default=None,
    Comment=None,
    After=None
):
    """Add column to table after column if not exists"""

    # ✅ Basic validation
    if not TableName or not ColumnName:
        print("❌ TableName and ColumnName are required.")
        return

    # ✅ Quote string values for SQL safely
    default_clause = f"DEFAULT {Default}" if Default is not None else ""
    comment_clause = f"COMMENT '{Comment}'" if Comment else ""
    after_clause = f"AFTER `{After}`" if After else ""

    # 1️⃣ Check if the column already exists
    query_check = f"""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = '{TableName}'
          AND column_name = '{ColumnName}'
          AND table_schema = DATABASE();
    """
    exists = execute_query(query_check, fetch=True)

    if exists and exists[0][0] == 0:
        # 2️⃣ Add column with options
        query_add = f"""
            ALTER TABLE `{TableName}`
            ADD COLUMN `{ColumnName}` {ColumnType} {default_clause} {comment_clause} {after_clause};
        """
        execute_query(query_add)
        print(f"✅ {ColumnName} column added to {TableName} table {after_clause or ''}")
    else:
        print(f"ℹ {ColumnName} column already exists in {TableName}")


def check_column_and_delete(TableName=None, ColumnName=None):
    """Delete column from table if it exists"""

    # ✅ Basic validation
    if not TableName or not ColumnName:
        print("❌ TableName and ColumnName are required.")
        return

    # 1️⃣ Check if the column exists
    query_check = f"""
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = '{TableName}'
          AND column_name = '{ColumnName}'
          AND table_schema = DATABASE();
    """
    exists = execute_query(query_check, fetch=True)

    if exists and exists[0][0] > 0:
        # 2️⃣ Drop the column
        query_drop = f"""
            ALTER TABLE `{TableName}`
            DROP COLUMN `{ColumnName}`;
        """
        execute_query(query_drop)
        print(f"🗑 Column `{ColumnName}` deleted from `{TableName}` table.")
    else:
        print(f"ℹ Column `{ColumnName}` does not exist in `{TableName}`.")



