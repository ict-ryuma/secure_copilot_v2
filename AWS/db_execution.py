from backend.mysql_connector import execute_query_with_dict_cursor,execute_query
from backend.auth import hash_password
from logger_config import logger
import re
from datetime import datetime, timezone, timedelta
import zoneinfo
import boto3
from urllib.parse import urlparse
import os


jst = zoneinfo.ZoneInfo("Asia/Tokyo")
def initialize_s3_client(type="s3"):
    """
    Initializes and returns a Boto3 S3 client.
    :return: Boto3 S3 client
    """
    return boto3.client(
        type,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        region_name=os.environ.get("AWS_REGION_NAME", "ap-northeast-1")
    )

def create_user(user_dict):
    username = user_dict["username"]
    password = "user123"
    team_name="イネーブラー"
    team_id=None
    hashed_password = hash_password(password)
    team_query = "SELECT id FROM teams WHERE team_name LIKE %s"
    team_result = execute_query_with_dict_cursor(team_query, ("%"+team_name+"%",), fetch=True)
    # logger.info(f"team_result: {team_result}")
    if team_result:
        team_id = team_result[0]['id']
    query = "SELECT id FROM users WHERE username = %s"
    result = execute_query_with_dict_cursor(query, (username,),fetch=True)
    if result:
        return result[0]['id'],team_id
    # Prepare insert query and values
    insert_query = """
        INSERT INTO users (first_name, last_name, name, username, email, phone_no, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        user_dict["first_name"],
        user_dict["last_name"],
        user_dict["name"],
        user_dict["username"],
        user_dict["email"],
        user_dict["phone_no"],
        hashed_password
    )
    execute_query(insert_query, values)
    user_result = execute_query_with_dict_cursor("SELECT id FROM users WHERE username = %s", (username,),fetch=True)
    if user_result:
        user_id=user_result[0]['id']
        execute_query(
        "INSERT INTO user_has_teams (user_id, team_id, is_active) VALUES (%s, %s, %s)",
        (user_id, team_id, 1)
        )
        return user_id, team_id
    


def get_prompts_for_team(team_id):
    """
    Fetch all active prompts associated with a given team.
    Returns a list of prompt dicts.
    """
    query = """
        SELECT p.id as prompt_id
        FROM team_has_prompts thp
        JOIN prompts p ON thp.prompt_id = p.id
        WHERE thp.team_id = %s AND thp.is_active = 1 AND p.is_active = 1
    """
    return execute_query_with_dict_cursor(query, (team_id,), fetch=True)


def transcripts_to_passage(transcripts):
    participant_map = {
        "CUSTOMER": "CUSTOMER",
        "AGENT": "AGENT"
    }
    lines = []
    for t in transcripts:
        role = participant_map.get(t.get("ParticipantId"), t.get("ParticipantId"))
        content = t.get("Content", "")
        if content:
            # Remove leading/trailing whitespace and replace newlines with spaces
            content = content.strip().replace('\n', ' ')
            lines.append(f"({role}){content}")
    return "\n".join(lines)


def file_path_to_date(file_path):
    file_name = file_path.split("/")[-1]

    match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z', file_name)
    if not match:
        raise ValueError("Timestamp not found in filename")
    
    # Convert extracted timestamp to UTC datetime
    timestamp_str = match.group(1)
    file_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)

    # Convert all times to JST
    file_time_local = file_time.astimezone(jst)

    return file_name,file_time_local

def download_audio_from_s3(s3_uri, local_dir="uploads"):
    """
    Downloads an audio file from the given S3 URI to the specified local directory.
    Returns the local file path.
    """
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3":
        raise ValueError("Invalid S3 URI")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    filename = os.path.basename(key)
    local_path = os.path.join(local_dir, filename)

    # Ensure the local directory exists
    os.makedirs(local_dir, exist_ok=True)

    s3 = initialize_s3_client(type="s3")
    s3.download_file(bucket, key, local_path)
    return local_path


def insert_shodans_for_team(shodan_array,prompt_id):
    """
    Insert shodans records for all prompts of a given team.
    
    Args:
        shodan_array (array): shodan_array
        prompt_id (int): Prompt ID
    """

    query = '''
        INSERT INTO shodans (
            user_id, team_id, prompt_id, phone_no, customer_number, shodan_date, shodan_text,audio_file
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''

    values = (
        shodan_array['user_id'],
        shodan_array['team_id'],
        prompt_id,
        shodan_array['phone_no'],
        shodan_array['customer_number'],
        shodan_array['shodan_date'],
        shodan_array['shodan_text'],
        shodan_array['audio_file']
    )

    last_inserted_id = execute_query(query, values, return_last_id=True)
    return last_inserted_id

def insert_shodan_details_for_team(shodan_details_array):
    """
    Insert shodan_details records for all prompts of a given team.
    
    Args:
        shodan_details_array (array): shodan_details_array
    """

    query = '''
        INSERT INTO shodan_details (
            shodan_id, agent_id, initiation_method, channel, system_number, contact_id, input_s3_audio_uri,initiation_ts,disconnect_ts
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''

    values = (
        shodan_details_array['shodan_id'],
        shodan_details_array['agent_id'],
        shodan_details_array['initiation_method'],
        shodan_details_array['channel'],
        shodan_details_array['system_number'],
        shodan_details_array['contact_id'],
        shodan_details_array['input_s3_audio_uri'],
        shodan_details_array['initiation_ts'],
        shodan_details_array['disconnect_ts']
    )
    last_inserted_id = execute_query(query, values, return_last_id=True)
    return last_inserted_id

def upsert_batch_last_success(batch_last_success_array):
    batch_name = batch_last_success_array['batch_name'].strip()
    last_success_time = batch_last_success_array['last_success_time']

    found = execute_query(
        "SELECT id FROM batch_last_success_times WHERE batch_name = %s LIMIT 1",
        (batch_name,),
        fetch=True
    )

    if found:
        execute_query(
            "UPDATE batch_last_success_times SET last_success_time = %s WHERE batch_name = %s",
            (last_success_time, batch_name)
        )
    else:
        execute_query(
            "INSERT INTO batch_last_success_times (batch_name, last_success_time) VALUES (%s, %s)",
            (batch_name, last_success_time)
        )



