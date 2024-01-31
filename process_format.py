from babel.numbers import format_currency
from datetime import date, datetime
from date_format_change import *
from db_processor import *
import requests
import pandas as pd
from numtoword import *
import json

def input_template_process(out,x):  

   response = requests.get(os.environ['DB_SEARCH_API']+"db_product_search", params={'school_id':x})
   dictr = response.json()
   df_products=pd.DataFrame(dictr)
   df_products.set_index('product_name',inplace=True) #creating dataframe of product data from database
   header_data={}
   product_data={}
   size_data={}

   for x in out.keys():
      if x not in ['Name','Class','Roll No.', 'Date', 'House'] and ('_size' in x) == False and out[x]!='': 
         #seperating the product data
         product_data[x]=out[x]
      elif x not in ['Name','Class','Roll No.', 'Date', 'House'] and ('_size' in x) == False and out[x]=='': #Skipping these keys in the loop
         continue
      elif x not in ['Name','Class','Roll No.', 'Date', 'House'] and ('_size' in x) == True and out[x]=='': #Skipping these keys in the loop
         continue
      elif x not in ['Name','Class','Roll No.', 'Date', 'House']and ('_size' in x) == True and out[x]!='':
         #seperating the size data
         size_data[x]=out[x]        
      else:
         #seperating the header data
         header_data[x]=out[x]      
   
   #Converting the improper name input to proper title form
   header_data['Name']=header_data['Name'].title()
   #altering the size dataframe
   size_df=pd.DataFrame.from_dict(size_data, orient='index', columns=['product_size'])
   size_df.reset_index(0, inplace=True)
   size_df['index']=size_df['index'].apply(lambda x:x.replace("_size",""))
   size_df.set_index('index', inplace=True)
   #creating the product dataframe from the product data in the invoice
   product_df=pd.DataFrame.from_dict(product_data, orient='index', columns=['product_quantity'])
   #joining the three dataframes i.e. size, product data from invoice and product data from database
   df=product_df.join(size_df).join(df_products)
   #creatring another column of total price in the dataframe
   df['total_price']=df['product_quantity'].astype('int')*df['product_price'].astype('int')
   #rearringing the columns of df
   df=df[['product_size', 'product_quantity', 'product_price', 'total_price']]
   #capturing additional header data and formatting in currency
   header_data['item_quantity']=df['product_quantity'].astype('int').sum()
   word_amount=number_to_word(df['total_price'].sum()) #converting amount in words
   header_data['total_price']=df['total_price'].sum()
   #changing the index of df
   df.reset_index(0, inplace=True)
   df.index=pd.RangeIndex(start=1, stop=1+len(df), step=1)
   df.rename(columns={'index':'Product Name', 'product_size':'Product Size', 'product_quantity':'Quantity', 'product_price':'Unit Price', 'total_price':'Total Price'}, inplace=True)
   #creating header dataframe from header data
   header_df=pd.DataFrame([header_data], columns=header_data.keys())
   header_df.rename(columns={'item_quantity':'Total Items', 'total_price':'Grand Total'}, inplace=True)
   return {'header':header_df, 'products':df, 'word_amount':word_amount}

"""def output_template_format(out):
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
   return result"""

def check_raashan_details(data,z):
   #result=db_raashan_product_search(z)
   #product search API call
   response = requests.get(os.environ['DB_SEARCH_API']+"db_raashan_products_search", params={'tender':z})
   #converting to dictionary
   response = response.json()
   df=pd.DataFrame(response)
   df.set_index('item_name', inplace=True)
   ter=[]
   for x in data:
      if data[x] == '':
         continue
      else:
         if (x in df.index) is True:
               #dictionary key=item_name values is [teneder_s_no, item_name, unit, rate_per_unit, gst, item_quantity, total_price ]
               #ter[x]=([data[x],y[2],y[3],y[4],round(float(data[x])*(y[3]+y[4]),2),y[0]])
               ter.append([df.loc[x,'tender_s_no'], x, df.loc[x,'item_unit'], df.loc[x,'rate'], df.loc[x,'gst_amount'], data[x], round(float(data[x])*(df.loc[x,'rate'] + df.loc[x,'gst_amount']),2)])
               #s+=round(float(data[x])*(y[3]+y[4]),2)
   df=pd.DataFrame(ter, columns=['Tender S. No.', 'Item Name', 'Unit', 'Rate per Unit', 'GST Amount per Unit', 'Total Quantity', 'Total Price'])  
   df.index = pd.RangeIndex(start=1, stop=1+len(df), step=1)
   ter={}
   final={}            
   ter['Grand Total']=round(df['Total Price'].sum(),2)
   ter['Word Amount']=number_to_word(ter['Grand Total'])
   #ter['Word Amount']=result['Word Amount'].replace(' And 00 Paise','') #replacing the  and 00 paise with empty space
   ter['Invoice No.']=abs(hash('PWPL/GJ/'+str(z)+'/'+str(date.today().year)+'/'+str(date.today().month)+'/'+str(datetime.now())))
   ter['start_date']= data['start_date']
   ter['end_date']= data['end_date']
   ter['inv_date']= data['inv_date']
   ter['tender']=z
   final['products']=df.to_json(orient='columns')
   final['header']=json.dumps(ter, default=int)   
   return(final)