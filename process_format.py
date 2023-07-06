from babel.numbers import format_currency
from datetime import date
from numtoword import number_to_word
from date_format_change import *
from db_processor import *

def input_template_process(out,x):  
    rows=db_product_search(x)
    ter={}
    s=q=0
    for x in out.keys():
       if x not in ['Name','Class','Roll No.', 'Date', 'House']:
          if out[x]=='':
             continue
          for y in rows:
             if x==y[1]:
                ter[x]=([int(out[x]),y[2],int(out[x])*y[2]])
                s+=int(out[x])*y[2]
                q+=int(out[x])
       else:
          ter[x]=out[x]
    ter['Grand Total']=s
    ter['Item Total']=q
    ter['Word Amount']=number_to_word(s)
    return(ter)

def output_template_format(out):
    for x in out.keys():
       if x not in ['Name','Class','Roll No.', 'Date', 'House', 'Grand Total', 'Word Amount', 'Item Total','Invoice No.']:
         out[x][1]=format_currency(out[x][1], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
         out[x][2]=format_currency(out[x][2], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)  
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
               ter[x]=([data[x],y[2],y[3],y[4],round(float(data[x])*y[3]*(1+y[4]/100),2),y[0]])
               s+=round(float(data[x])*y[3]*(1+y[4]/100),2)           
   ter['Grand Total']=s
   ter['Word Amount']=number_to_word(s)
   ter['Invoice No.']=abs(hash('PWPL/GJ/'+str(z)+'/'+str(date.today().year)+'/'+str(date.today().month)+'/'+str(s)))
   ter['start_date']= data['start_date']
   ter['end_date']= data['end_date']
   return(ter)