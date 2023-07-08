import requests

def send_message(x):
    TOKEN = "6174269173:AAEwwcowMZVeCpoLk7bkADwvjDzIXEtiNzU"
    chat_id = "-989458360"
    message = x
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url).json() # this sends the message