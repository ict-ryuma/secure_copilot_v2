from backend.mysql_connector import execute_query_with_dict_cursor,execute_query

def insert_batch_last_success_time(batch_name, last_success_time):
    """
    Inserts or updates the last_success_time for a given batch_name.
    """
    query = """
        INSERT INTO batch_last_success_times (batch_name, last_success_time)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE last_success_time = VALUES(last_success_time)
    """
    params = (batch_name, last_success_time)
    execute_query(query, params, fetch=False)

def get_last_success_time(batch_name):
    """
    Retrieves the last_success_time for a given batch_name.
    Returns None if not found.
    """
    query = """
        SELECT last_success_time
        FROM batch_last_success_times
        WHERE batch_name = %s
        LIMIT 1
    """
    params = (batch_name,)
    result = execute_query_with_dict_cursor(query, params, fetch=True)
    if result and len(result) > 0:
        return result[0]['last_success_time']
    return None