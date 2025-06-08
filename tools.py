import json
import re

# JSON :: Discord Bot Token
def get_discord_token():
    """
    :return: discord token
    """
    with open("key.json", "r") as f:
        return json.load(f)["discord"]

def is_url(string):
    """
    Checks if the string is URL
    :param string:
    :return: boolean
    """
    # 정규 URL 패턴
    url_pattern = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$')
    return bool(url_pattern.match(string))
