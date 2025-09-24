import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
from logger_config import logger
from datetime import datetime, timezone, timedelta
import zoneinfo
import json
from AWS.batch_execution import get_last_success_time
from AWS.db_execution import initialize_s3_client,create_user,get_prompts_for_team,transcripts_to_passage,file_path_to_date,download_audio_from_s3,insert_shodans_for_team,insert_shodan_details_for_team,upsert_batch_last_success
from dotenv import load_dotenv

load_dotenv()

batch_name="s3_client"
jst = zoneinfo.ZoneInfo("Asia/Tokyo")



def download_file_from_s3():
    """
    Downloads files from an S3 bucket with a given prefix.

    :return: List of downloaded file paths
    """
    try:
        last_success_time=get_last_success_time(batch_name)
        if last_success_time is None:
            last_success_time = datetime.now(timezone.utc) - timedelta(days=0)

            last_success_time_local = last_success_time.astimezone(jst) if last_success_time else None
            # Reset to midnight (00:00:00)
            last_success_time_local = last_success_time_local.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            last_success_time_local = last_success_time.astimezone(jst) if last_success_time else None
            
        now = datetime.now(timezone.utc)
        now_local = now.astimezone(jst)
        # Get today's date
        # today = datetime.today()
        json_file_prefixes=create_aws_prefix_url(last_success_time_local,now_local)
        logger.info(json_file_prefixes)

        s3 = initialize_s3_client(type="s3")
        bucket_name = os.environ.get("AWS_S3_BUCKET_NAME", "")
        # logger.info(f"bucket_name: {bucket_name}")
        # return True
        # prefix = "connect/norel-idom-caas-technology/CallRecordings/2025/09/09"
        # Build prefix dynamically
        # audio_file_prefix = f"connect/norel-idom-caas-technology/CallRecordings/{year}/{month}/{day}"
        # json_file_prefix = f"Analysis/Voice/{year}/{month}/{day}"
        batch_last_success_array={
            "batch_name":batch_name,
            "last_success_time":now
        }
        for prefix in json_file_prefixes:
            # logger.info(prefix)
            get_s3_sjon_files(s3,bucket_name,prefix,last_success_time_local,now_local,now)
        upsert_batch_last_success(batch_last_success_array)

        # return downloaded_files

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return []
    


def get_s3_sjon_files(s3,bucket_name,prefix,last_success_time_local,now_local,now):
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    # logger.info(f"prefix: {prefix} last_success_time_local: {last_success_time_local} now_local: {now_local}")
    # logger.info(response)

    downloaded_files = []

    if "Contents" in response:
        for obj in response["Contents"]:
            object_key_file_path = obj["Key"]
            success,file_name,file_time_local=get_time_from_filename(object_key_file_path,last_success_time_local,now_local)
            if success:
                prefix_parts = prefix.split("/")
                date_part = "/".join(prefix_parts[-3:])   # take last 3 parts (YYYY/MM/DD)
                download_json_path = f"./downloads/AWS/JSON/{date_part}/{file_name}"
                # Make sure local folder exists
                os.makedirs(os.path.dirname(download_json_path), exist_ok=True)

                # Download file
                s3.download_file(bucket_name, object_key_file_path, download_json_path)

                # logger.info(f"Downloaded: {object_key_file_path} -> {download_json_path}")
                # downloaded_files.append(download_json_path)
                # Append structured metadata
                downloaded_files.append({
                    "file_name": file_name,
                    "file_path": download_json_path,
                    "aws_prefix": prefix,
                    "file_time_local": file_time_local,
                })
    logger.info(f"downloaded_files: {downloaded_files}")
    if downloaded_files:
        for file_info in downloaded_files:
            file_path=file_info['file_path']
            aws_prefix=file_info['aws_prefix']
            shodan_date=file_info['file_time_local']
            success,customer_metadata,transcripts=get_json_dat(file_path)
            shodan_text=transcripts_to_passage(transcripts)
            if success is True:
                contact_id=customer_metadata.get("ContactId")
                input_s3_audio_uri=customer_metadata.get("InputS3Uri")
                instance_id=customer_metadata.get("InstanceId")
                contact=get_contact_info(contact_id,instance_id)
                AgentInfo=contact.get("AgentInfo")
                agent_id=AgentInfo.get("Id")
                initiation_method = contact.get("InitiationMethod")
                channel = contact.get("Channel")
                initiation_ts = contact.get("InitiationTimestamp")
                disconnect_ts = contact.get("DisconnectTimestamp")
                customer_number = contact.get("CustomerEndpoint", {}).get("Address")
                system_number = contact.get("SystemEndpoint", {}).get("Address")
                agent_details=get_agent_info(instance_id,agent_id)

                user = agent_details["User"]
                identity = user.get("IdentityInfo", {})
                phone_config = user.get("PhoneConfig", {})

                agent_username = user.get("Username")
                first_name=identity.get("FirstName")
                last_name=identity.get("LastName")
                email=identity.get("Email")
                mobile=identity.get("Mobile") # Mobile and DeskPhoneNumber are same of agent number. EG: 'Mobile': '+817032913643' 'DeskPhoneNumber': '+817032913643'
                desk_phone_number=phone_config.get("DeskPhoneNumber")

                # shodan_file_name,shodan_date=file_path_to_date(file_path)
                audio_file_local_path=download_audio_from_s3(input_s3_audio_uri, local_dir="uploads",aws_prefix=aws_prefix)

                user_array={
                    "first_name":first_name,
                    "last_name":last_name,
                    "name":first_name+" "+last_name,
                    "username":agent_username,
                    "email":email,
                    "phone_no": mobile if mobile is not None else desk_phone_number
                }
                shodan_array={
                    "phone_no":mobile if mobile is not None else desk_phone_number,
                    "customer_number":customer_number,
                    "shodan_date":shodan_date.date() if hasattr(shodan_date, "date") else shodan_date,
                    "shodan_text":shodan_text,
                    "audio_file":audio_file_local_path,
                    # "outcome":"",
                }

                shodan_details_array={
                    # "shodan_id":1,
                    "agent_id":agent_id,
                    "initiation_method":initiation_method,
                    "channel":channel,
                    "system_number":system_number,
                    "contact_id":contact_id,
                    "input_s3_audio_uri":input_s3_audio_uri,
                    "initiation_ts":initiation_ts,
                    "disconnect_ts":disconnect_ts,
                }
                
                # logger.info(f"user_array: {user_array} shodan_array: {shodan_array} shodan_details_array: {shodan_details_array} batch_last_success_array: {batch_last_success_array}")
                success=insert_to_db(user_array,shodan_array,shodan_details_array)
                if success:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        logger.error(f"❌ Error deleting {file_path}: {e}")


def insert_to_db(user_array,shodan_array,shodan_details_array):
    try:
        user_id,team_id=create_user(user_array)
        logger.info(f"user_id: {user_id}")
        shodan_array["user_id"] = user_id
        # shodan_array["team_id"] = team_id
        team_has_prompts=get_prompts_for_team(team_id)
        logger.info(f"team_has_prompts: {team_has_prompts}")
        for prompt in team_has_prompts:
            # Process each prompt as needed
            team_has_prompt_id=prompt['team_has_prompt_id']
            last_shodan_id=insert_shodans_for_team(shodan_array,team_has_prompt_id)
            logger.info(f"last_shodan_id: {last_shodan_id}")
            shodan_details_array['shodan_id']=last_shodan_id
            insert_shodan_details_for_team(shodan_details_array)
        return True
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return False


def get_contact_info(contactId,instanceId):
    connect = initialize_s3_client(type="connect")

    # Contact details
    contact = connect.describe_contact(
        InstanceId=instanceId,
        ContactId=contactId
    )

    # Contact attributes (set in Contact Flow)
    # attributes = connect.get_contact_attributes(
    #     InstanceId=InstanceId,
    #     InitialContactId=ContactId
    # )
    # print("Attributes:", attributes.get("Attributes", {}))
    return contact["Contact"]

def get_agent_info(instance_id,user_id): # user_id mean AgentInfo.Id

    connect = initialize_s3_client(type="connect")

    response = connect.describe_user(
        InstanceId=instance_id,
        UserId=user_id
    )
    return response


def get_time_from_filename(file_path, last_success_time_local, now_local):
    """
    Extract timestamp from filename and check if it is between last_success_time and now.
    
    :param filename: str
    :param last_success_time: datetime or None (should be UTC)
    :param now: datetime (should be UTC)
    :return: (bool, str) -> (is_valid, filename or "")
    """
    file_name,file_time_local=file_path_to_date(file_path)

    # ✅ Only accept files strictly between last_success_time and now
    if last_success_time_local is None:
        # If no last_success_time, allow all files up to now
        if file_time_local <= now_local:
            return True, file_name, file_time_local
    else:
        if last_success_time_local < file_time_local <= now_local:
            return True, file_name, file_time_local

    return False, "",""

def get_json_dat(file_path):
    customer_metadata=None,
    transcripts=None
    return_flag=True
    # for file_path in downloaded_files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract fields (safe lookup)
        customer_metadata = data.get("CustomerMetadata")
        transcripts = data.get("Transcript")

    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse JSON file {file_path}: {e}")
        return_flag=False
    except Exception as e:
        logger.error(f"❌ Unexpected error for {file_path}: {e}")
        return_flag=False
    return return_flag,customer_metadata,transcripts


def create_aws_prefix_url(last_success_time,now):

    # Make sure we compare only dates (not hours/minutes)
    start_date = last_success_time.date()
    end_date = now.date()

    json_file_prefixes = []
    current_date = start_date

    while current_date <= end_date:
        year = current_date.year
        # month = current_date.month
        # day = current_date.day
        month = f"{current_date.month:02d}"  # zero-padded
        day = f"{current_date.day:02d}"      # zero-padded
        prefix = f"Analysis/Voice/{year}/{month}/{day}"
        json_file_prefixes.append(prefix)
        current_date += timedelta(days=1)
    return json_file_prefixes


if __name__ == "__main__":
    download_file_from_s3()

