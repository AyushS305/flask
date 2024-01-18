import requests
import pandas as pd
import json
import urllib.request
from num2words import num2words
import os
"""
response = requests.get("http://127.1.1.1:8080/db_product_search", params={'school_id':1})
dictr = response.json()
df=pd.DataFrame.from_dict(dictr['product_price'], orient='index', columns=['product_price'])
print(df)
if 'Towel Turkish' in df.index:
    print(df.loc['Towel Turkish']['product_price'])

response = requests.get("http://127.1.1.1:8080/db_house_search", params={'school_id':2})
dictr = response.json()
df=pd.DataFrame.from_dict(dictr['house_name'], orient='index', columns=['house_name'])
if 'Vikramshila' in df['house_name'].values:
    print(True)
else:
    print(False)
print(df)
print(list(dictr['house_name'].values()))
print(num2words(3671245.25, to='currency',  lang='en_IN' , separator=' and', cents=False, currency='INR'))
"""
print(os.getcwd())