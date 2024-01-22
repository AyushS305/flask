from babel.numbers import format_currency
from datetime import date
from date_format_change import *
from db_processor import *
import requests
import pandas as pd
from numtoword import *

def input_template_process(out,x):  

   response = requests.get("http://127.1.1.1:8080/db_product_search", params={'school_id':x})
   dictr = response.json()
   df=pd.DataFrame.from_dict(dictr['product_price'], orient='index', columns=['product_price'])
   ter={}
   s=q=0
   for x in out.keys():
      if x not in ['Name','Class','Roll No.', 'Date', 'House'] and ('_size' in x) == False and out[x]!='': #Skipping these keys in the loop
         #Calculating the price using the df from api call and df slashing
         ter[x]=([int(out[x]),df.loc[x]['product_price'],int(out[x])*df.loc[x]['product_price']])
         s+=int(out[x])*df.loc[x]['product_price'] #Total price
         q+=int(out[x])     #Total quantity  
      elif x not in ['Name','Class','Roll No.', 'Date', 'House'] and ('_size' in x) == False and out[x]=='':
         continue
      elif x not in ['Name','Class','Roll No.', 'Date', 'House'] and ('_size' in x) == True and out[x]=='':
         continue
      elif x not in ['Name','Class','Roll No.', 'Date', 'House']and ('_size' in x) == True and out[x]!='':
         ter[x]=out[x]        
      else:
         ter[x]=out[x] #Saving the remaining details in the dictionary      
   ter['Grand Total']=s
   ter['Item Total']=q
   #we have to use decimal class to convert currency using the num2words package
   ter['Word Amount']=number_to_word(s)
   return(ter)

def output_template_format(out):
   for x in out.keys():
      if x not in ['Name','Class','Roll No.', 'Date', 'House', 'Grand Total', 'Word Amount', 'Item Total','Invoice No.'] and ('_size' in x) == False:
         out[x][1]=format_currency(out[x][1], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
         out[x][2]=format_currency(out[x][2], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
      else:
         if ('_size' in x) == True and out[x]!='':
            out[x]=out[x]
   out['Grand Total']=format_currency(out['Grand Total'], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
   return(out)

def school_pricipal_bill_process(res,set):
   result={}
   s=q=0
   for x in res:
      result[x[0]]=([format_currency(x[1], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False),x[2],format_currency(x[3], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)])      
      s=s+x[3]
      q=q+x[2]
   result['Date']=change_date_format(str(date.today()))
   result['Invoice No.']=str(abs(hash('PWPL/'+set+'/'+str(date.today()))))
   result['Grand Total']=format_currency(s, 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
   result['Item Total']=q
   result['Word Amount']=number_to_word(s)
   return result

def house_cover_process(res):
   result={}
   s=q=0
   for x in res:
      result[x[0]]=([x[1],x[2],x[3],format_currency(x[4], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)])      
      s=s+x[4]
      q=q+x[3]
   result['Date']=change_date_format(str(date.today()))
   result['Invoice No.']=str(abs(hash('PWPL/RW/'+str(date.today()))))
   result['Grand Total']=format_currency(s, 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
   result['Item Total']=q
   result['Word Amount']=number_to_word(s)
   return result 

def all_house_cover_process(res):
   result={}
   s=q=0
   for x in res:
      result[x[0]]=([x[1],format_currency(x[2], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)])      
      s=s+x[2]
      q=q+x[1]
   result['Date']=change_date_format(str(date.today()))
   result['Invoice No.']=str(abs(hash('PWPL/RW/'+str(date.today()))))
   result['Grand Total']=format_currency(s, 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
   result['Item Total']=q
   result['Word Amount']=number_to_word(s)
   return result

def check_raashan_details(data,z):
   result=db_raashan_product_search(z)
   ter={}
   s=0
   for x in data:
      if data[x] == '':
         continue
      else:
         for y in result:
            if x == y[1]:
               ter[x]=([data[x],y[2],y[3],y[4],round(float(data[x])*(y[3]+y[4]),2),y[0]])
               s+=round(float(data[x])*(y[3]+y[4]),2)          
   ter['Grand Total']=s
   ter['Word Amount']=number_to_word(s)
   ter['Word Amount']=result['Word Amount'].replace(' And 00 Paise','') #replacing the  and 00 paise with empty space
   ter['Invoice No.']=abs(hash('PWPL/GJ/'+str(z)+'/'+str(date.today().year)+'/'+str(date.today().month)+'/'+str(s)))
   ter['start_date']= data['start_date']
   ter['end_date']= data['end_date']
   ter['inv_date']= data['inv_date']
   return(ter)