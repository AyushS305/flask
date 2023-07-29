import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_message(x):
    TOKEN = os.environ['TOKEN']
    chat_id = os.environ['CHAT_ID']
    message = x
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url).json() # this sends the message