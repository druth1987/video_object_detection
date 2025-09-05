# connection setup variables
# fist ensure the API and Application servers can ping each other successfully, then fill in the variables below

# add aws s3 keys
aws_access_key_id = ""
aws_secret_access_key = ""

# replace the placeholder <> fields with required connection credentials
sql_connection_string = "mssql+pyodbc://<sql_login>:<sql_password>@<api_server_IP>\<server_name>/<database_name>?driver=ODBC Driver 17 for SQL Server"

# add file path to the video_saves folder on the API server from the Application server
# can use smbclient to connect from Ubuntu Application server
video_saves_file_path = ""

# add password, IP and port of Ubuntu redis server (redis uses port 6379 and db_number 0 by default)
# https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html
redis_url = "redis://:password@hostname:port/db_number"


