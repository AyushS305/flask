from flask import Flask, render_template, request, redirect, url_for, session, json, jsonify
#from db_processor import *
from date_format_change import *
from process_format import *
from flask_session import Session
from datetime import timedelta
from dotenv import load_dotenv
import os
import requests

load_dotenv() #loading environment variables from .env 

app = Flask(__name__) #creating app
#app configuration
app.config['SECRET_KEY']=os.environ['SECRET_KEY']
app.config["SESSION_TYPE"] = "filesystem"
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

Session(app) #creating session variable

def force():
   os.system("curl https://telegram-api-lwkv.onrender.com/check")
   os.system("curl https://email-api-war5.onrender.com/check")
   os.system("curl https://db-plug-api-e8q9.onrender.com/check")

@app.route('/check', methods=['GET']) #health check 
def check():
    if request.method == 'GET':
      os.system("curl https://telegram-api-lwkv.onrender.com/check")
      os.system("curl https://email-api-war5.onrender.com/check")
      os.system("curl https://db-plug-api-e8q9.onrender.com/check")
      return jsonify({'result':'EMS app and other services are live!'})
    
@app.route('/', methods = ['POST', 'GET']) #landing page
def auth():
   error=None
   if request.method == 'POST':
      result=request.form.to_dict()
      result=db_auth(result)
      for x in result:
         session[x]=result[x]
      if result['flag'] == False:
         error = 'Invalid Credentials. Please try again.'
      else:
         ping="user " + session['username']+ " logged in"
         force()
         requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
         return redirect(url_for('homepage'))     
   return render_template('login.html', error=error)

@app.route('/homepage')
def homepage():
   return render_template('homepage.html', sync_user=session)

@app.route('/logout')
def logout():
   ping="user " + session['username']+ " logged out"
   requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
   session.pop('username',None)
   return redirect(url_for('auth'))

@app.route('/input', methods = ['POST', 'GET'])
def input ():
   #set flag key in session list to None
   session['flag']=None
   #house search API call
   response = requests.get(os.environ['DB_SEARCH_API']+"db_house_search", params={'school_id':session['school_id']})
   #converting to dictionary
   dictr = response.json()
   #converting to list
   house_list=list(dictr['house_name'].values())
   #product search API call
   response = requests.get(os.environ['DB_SEARCH_API']+"db_product_search", params={'school_id':session['school_id']})
   #converting to dictionary
   dictr = response.json()
   df=pd.DataFrame(dictr, columns=['product_name', 'product_price'])
   #rendering template
   return render_template('student_invoice_input_template.html', items=df['product_name'], house=house_list)

@app.route('/output',methods = ['POST', 'GET'])
def output():
   if request.method == 'POST':
      out = request.form.to_dict()
      global sync
      output=input_template_process(out, session['school_id'])
      sync=output
      return render_template("student_invoice_output_template.html", header=output['header'].to_html(classes='data', index=False, justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), products=output['products'].to_html(classes='data', index=True, justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), word_amount = output['word_amount'], image=session['img_url'])
   
@app.route('/print_invoice',methods = ['POST', 'GET'])
def print_invoice():
   if request.method == 'POST':
      if session['flag'] is not None:
         action="EDITED"
         #db_delete_invoice(session['flag'])
         requests.get(os.environ['DB_SEARCH_API']+'db_delete_student_invoice', params=session['flag'])
      else:
         action="GENERATED"
      json_output={}
      #save student invoice details API call
      json_output['header']=sync['header'].to_json(orient='columns')
      json_output['products']=sync['products'].to_json(orient='columns')
      json_output['word_amount']=sync['word_amount']
      json_output['school_id']=session['school_id']
      json_output['user_id']=session['user_id']
      json_output=json.dumps(json_output)
      response = requests.post(os.environ['DB_SEARCH_API']+"db_save_student_invoice", json=json_output) #posting data to API
      sync['header']=sync['header'].assign(inv_no= response.json())
      sync['header'].rename(columns={'inv_no':'Invoice No.'}, inplace=True)
      df_header=sync['header']
      df_header['Grand Total']=df_header['Grand Total'].apply(lambda x:format_currency(x, 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False))
      df_products=sync['products']
      df_products['Unit Price']=df_products['Unit Price'].apply(lambda x:format_currency(x, 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False))
      df_products['Total Price']=df_products['Total Price'].apply(lambda x:format_currency(x, 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False))
      ping="STUDENT INVOICE "+action+ "\nSCHOOL NAME: "+ session['school_name']+"\nINVOICE NO: "+ df_header['Invoice No.'][0] +"\n"+ action+ " BY USER: "+session['username']+"\n STUDENT NAME: "+ df_header['Name'][0]+"\n CLASS: "+ df_header['Class'][0]+"\n ROLL NO: " +df_header['Roll No.'][0]+"\n HOUSE: "+ df_header['House'][0]+"\n INVOICE DATE: " +df_header['Date'][0]+"\n TOTAL ITEMS: "+ str(df_header['Total Items'][0])+"\n TOTAL AMOUNT: " +df_header['Grand Total'][0]
      #call telegram messenger API
      requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
      email_dict={} #email dict to be sent to email messenger api
      email_dict['img_url']=session['img_url']
      email_dict['header']=df_header.to_json(orient='columns')
      email_dict['products']=df_products.to_json(orient='columns')
      email_dict['action']=action
      email_dict['word_amount']=sync['word_amount']
      email_dict['img_url']=session['img_url']
      #call email messenger api
      requests.post(os.environ['EMAIL_API']+"student_invoice_emailer", json=json.dumps(email_dict))
      return render_template("student_invoice_print_template.html",header=df_header.to_html(classes='data', index=False, justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), products=df_products.to_html(classes='data', index=True, justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), word_amount = sync['word_amount'], image=session['img_url'])
   
@app.route('/search_invoice',methods = ['POST', 'GET'])
def search_invoice():
      return render_template("search_invoice_input_template.html")
      
@app.route('/view_invoice',methods = ['POST', 'GET'])
def view_invoice():
   if request.method == 'POST':
      out = request.form.to_dict()
      #product search API call
      response = requests.get(os.environ['DB_SEARCH_API']+"db_search_student_invoice", params={'inv_no':out['inv_no'], 'date_of_purchase':out['date_of_purchase']})
      respons=response.json()
      if respons['found'] == False:
         return render_template("student_invoice_not_found.html")
      else:
         respons_header=json.loads(respons['headers'])
         respons_products=json.loads(respons['products'])
         img_url=respons_header['img_url']
         response_products=pd.DataFrame(respons_products)
         response_products.index = pd.RangeIndex(start=1, stop=1+len(response_products), step=1)
         response_products.rename(columns={'product_name':'Product Name', 'size':'Product Size', 'item_quantity':'Item Quantity', 'product_price':'Unit Price', 'total_price':'Total Price'}, inplace=True)
         respons_header=pd.DataFrame(respons_header, columns=respons_header.keys())
         x=datetime.utcfromtimestamp(respons_header['date_of_purchase'][0]/1000)
         temp_date=x.date()
         temp_date=change_date_format(str(temp_date))
         respons_header=respons_header.assign(temp_date=temp_date)
         respons_header.drop(columns={'date_of_purchase'}, inplace=True)
         #respons_header['date_of_purchase'][0] = x.date()
         #respons_header['date_of_purchase'][0]=change_date_format(str(respons_header['date_of_purchase'][0])) 
         tc_leave=respons_header['tc_leave'][0]
         word_amount=respons_header['Word Amount']
         word_amount=word_amount[0]
         respons_header.drop(respons_header.iloc[:,5:8], inplace=True, axis=1)
         respons_header.rename(columns={'student_name':'Name', 'class':'Class', 'roll_no':'Roll No.', 'temp_date':'Purchase Date', 'house_name':'House', 'bill_no':'Invoice No.', 'item_quantity':'Total Items', 'total_price':'Grand Total'}, inplace=True)
         respons_header=respons_header[['Name', 'Class', 'Roll No.', 'House', 'Purchase Date', 'Invoice No.', 'Total Items', 'Grand Total']]
         return render_template("view_student_invoice_template copy.html", header=respons_header.to_html(classes='data', index=False, justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), products=response_products.to_html(classes='data', justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), word_amount=word_amount, tc_leave=tc_leave, image=img_url['0'])
         
@app.route('/principal_bill',methods=['POST','GET'])
def principal_bill():
   return render_template('principal_bill_input_template.html')

@app.route('/generate_bill',methods=['POST','GET'])
def generate_bill():
   if request.method == 'POST':
      out = request.form.to_dict()
      res=requests.get(os.environ['DB_SEARCH_API']+"db_product_pivot_principal_bill", params={'start_date':out['start_date'], 'end_date':out['end_date'],'school_id':session['school_id'], 'tc_leave':out['tc_leave']})
      res=res.json()
      header_data=res['header']
      product_data=json.loads(res['products'])
      product_data=pd.DataFrame(product_data, columns=product_data.keys())
      global sync_school_bill
      sync_school_bill=res
      return render_template('principal_bill_output_template.html', header=header_data, products=product_data.to_html(classes='data', justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), image=session['img_url'])

@app.route('/print_school_bill',methods=['POST','GET'])
def print_school_bill():
   if request.method == 'POST':
      header_data=sync_school_bill['header']
      product_data=json.loads(sync_school_bill['products'])
      product_data=pd.DataFrame(product_data, columns=product_data.keys())
      email_dict={} #email dict to be sent to email messenger api
      email_dict['img_url']=session['img_url']
      email_dict['header']=header_data
      email_dict['products']=sync_school_bill['products']
      #call email messenger api  
      requests.post(os.environ['EMAIL_API']+"school_principal_bill_emailer", json=json.dumps(email_dict))
      ping="BILL TO PRINCIPAL GENERATED"+"\nSCHOOL NAME: "+ header_data['school_name']+"\nINVOICE NO: "+ header_data['inv_no'] +"\n GENERATED BY USER: "+session['username']+"\n INVOICE DATE: " +header_data['bill_date']+"\n TOTAL ITEMS: "+ str(header_data['item_quantity'])+"\n TOTAL AMOUNT: " +header_data['total_price']
      #call telegram messenger API
      requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
      return render_template("pricipal_bill_print_template.html",header=header_data, products=product_data.to_html(classes='data', justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), image=session['img_url'])
   
@app.route('/cover_page_input', methods=['POST','GET'])
def cover_page_input():
   #house search API call
   response = requests.get(os.environ['DB_SEARCH_API']+"db_house_search", params={'school_id':session['school_id']})
   #converting to dictionary
   dictr = response.json()
   #converting to list
   house_list=list(dictr['house_name'].values())
   return render_template('cover_page_input.html', house=house_list)

@app.route('/confirm_cover_page', methods=['POST','GET'])
def confirm_cover_page():
   if request.method == 'POST':
      data = request.form.to_dict()
      if data['house'] == 'All':
         response = requests.get(os.environ['DB_SEARCH_API']+"db_all_house_cover_page", params={'start_date':data['start_date'], 'end_date': data['end_date'], 'school_id':session['school_id'], 'tc_leave':data['tc_leave']})
      else:
         response = requests.get(os.environ['DB_SEARCH_API']+"db_individual_house_cover_page", params={'start_date':data['start_date'], 'end_date': data['end_date'], 'house':data['house'], 'school_id':session['school_id'], 'tc_leave':data['tc_leave']})     
      response=response.json()
      house_data=json.loads(response['data'])
      house_data=pd.DataFrame(house_data, columns=house_data.keys())
      header_data=response['header']
      response['house']=data['house']
      response['img_url']=session['img_url']
      global sync_cover_data
      sync_cover_data=response
      return render_template("cover_page_all_house.html", house_name=data['house'], header=header_data, house_data=house_data.to_html(classes='data', justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), image=session['img_url'])
   
@app.route('/print_house_cover_page',methods=['POST','GET'])
def print_house_cover_page():
   if request.method == 'POST':
      house_data=json.loads(sync_cover_data['data'])
      house_data=pd.DataFrame(house_data, columns=house_data.keys())
      header_data=sync_cover_data['header']  
      requests.post(os.environ['EMAIL_API']+"house_cover_emailer", json=json.dumps(sync_cover_data))
      ping="COVER PAGE GENERATED"+"\nSCHOOL NAME: "+ session['school_name']+"\n GENERATED BY USER: "+session['username']+"\n TOTAL ITEMS: "+ str(header_data['item_quantity'])+"\n TOTAL AMOUNT: " +header_data['total_price']
      #call telegram API
      requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
      return render_template("cover_page_print.html",house_name=sync_cover_data['house'], header=sync_cover_data['header'], house_data=house_data.to_html(classes='data', justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), image=session['img_url'])

@app.route('/delete_invoice_input', methods=['POST', 'GET'])
def delete_invoice_input():
   return render_template("delete_invoice_input_template.html")

@app.route('/delete_invoice_confirmed', methods=['POST', 'GET'])
def delete_invoice_confirmed():
   if request.method == 'POST':
      data=request.form.to_dict()
      response=requests.get(os.environ['DB_SEARCH_API']+'db_check_student_invoice_present', params=data )
      response=response.json()
      if response['found'] == False:
         return render_template("student_invoice_not_found.html")
      else:
         response=requests.get(os.environ['DB_SEARCH_API']+'db_delete_student_invoice', params=data )
         response=response.json()      
         requests.post(os.environ['EMAIL_API']+"delete_invoice_emailer", json=json.dumps(data['inv_no']))
         ping=response+"\n DELETED BY USER: "+session['username']
         #call telegram API
         requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
         return render_template("delete_invoice_confirmed.html", result=response)
      

@app.route('/change_invoice_status_input', methods=['POST', 'GET'])
def change_invoice_status_input():
      return render_template("change_invoice_status_input.html")

@app.route('/change_invoice_status_confirmed', methods=['POST', 'GET'])
def change_invoice_status_confirmed():
   if request.method == 'POST':
      data=request.form.to_dict()
      response=requests.get(os.environ['DB_SEARCH_API']+'db_check_student_invoice_present', params={'inv_no':data['inv_no'], 'date_of_purchase':data['date_of_purchase']} )
      response=response.json()
      if response['found'] == False:
         return render_template("student_invoice_not_found.html")
      else:
         response1=requests.get(os.environ['DB_SEARCH_API']+'db_change_student_invoice_tc_leave_status', params=data )
         response1=response1.json()      
         requests.post(os.environ['EMAIL_API']+"update_tc_leave_status_emailer", json=json.dumps({'inv_no':data['inv_no'], 'tc_leave':data['tc_leave']}))
         ping=response1 +" BY USER "+session['username']
         requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
         return render_template("change_invoice_status_confirmed.html", result=response1)
      

@app.route('/select_raashan_tender', methods=['POST', 'GET'])
def select_raashan_tender():
   return render_template('select_raashan_tender.html')

@app.route('/input_raashan_details', methods=['POST', 'GET'])
def input_raashan_details():
   if request.method == 'POST':
      data=request.form.to_dict()
      session['tender_no']=data['tender']
      #items=db_raashan_product_search(data['tender'])
      #product search API call
      response = requests.get(os.environ['DB_SEARCH_API']+"db_raashan_products_search", params={'tender':data['tender']})
      #converting to dictionary
      response = response.json()
      df=pd.DataFrame(response)
      df.rename(columns={'tender_s_no':'Tender S. No.','item_name':'Item Name','rate':'Rate per unit','gst_amount':'GST Amount per unit', 'item_unit':'Unit'}, inplace=True)
      items=[]
      for x in df.itertuples(index=False):
         items.append(x)
      return render_template('input_raashan_details.html', items=items)
   
@app.route('/confirm_raashan_details', methods=['POST', 'GET'])
def confirm_raashan_details():
   if request.method == 'POST':
      data=request.form.to_dict()
      result=check_raashan_details(data, session['tender_no'])
      global sync_raashan
      sync_raashan=result
      header=json.loads(result['header'])
      items=pd.DataFrame(json.loads(result['products']))
      return render_template('confirm_raashan_details.html', result=header, items=items.to_html(classes='data', justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), image=session)

@app.route('/print_raashan_bill', methods=['POST', 'GET'])
def print_raashan_bill():
   if request.method == 'POST':
      result=sync_raashan
      header=json.loads(result['header'])
      items=pd.DataFrame(json.loads(result['products']))
      items['Rate per Unit']=items['Rate per Unit'].apply(lambda x:format_currency(x, 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False))
      items['GST Amount per Unit']=items['GST Amount per Unit'].apply(lambda x:format_currency(x, 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False))
      items['Total Price']=items['Total Price'].apply(lambda x:format_currency(x, 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False))
      header['Grand Total']=format_currency(header['Grand Total'], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
      sync_raashan['session']={'school_name':session['school_name'], 'img_url':session['img_url']}
      #save_raashan_line_items(result, session['tender_no'])
      requests.post(os.environ['DB_SEARCH_API']+"db_save_raashan_bill_details", json=sync_raashan)
      header['start_date']=change_date_format(header['start_date'])
      header['end_date']=change_date_format(header['end_date'])
      header['inv_date']=change_date_format(header['inv_date'])
      #create ping
      ping="RAASHAN BILL TO SAINIK SCHOOL GOPALGANJ PRINCIPAL GENERATED# "+"\nINVOICE NO: "+ str(header['Invoice No.']) +"\n GENERATED BY USER: "+session['username']+"\n TOTAL AMOUNT: " +str(header['Grand Total'])
      #call email messenger api
      requests.post(os.environ['EMAIL_API']+"raashan_bill_emailer", json=sync_raashan)
      #call telegram API
      requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
      return render_template('print_raashan_bill.html', result=header, items=items.to_html(classes='data', justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">'), image=session)

@app.route('/analytics', methods=['POST','GET'])
def analytics():
   error=None
   if request.method == 'POST':
      data=request.form.to_dict()
      if data['otp'] == str(8092):
         return redirect(url_for('looker_dashboard'))
      else:
         error = 'Invalid Credentials. Please try again.'
   return render_template('enter_otp.html', error=error)

@app.route('/looker_dashboard', methods=['POST','GET'])
def looker_dashboard():
   return render_template('looker.html')

@app.route('/inventory_input', methods = ['POST', 'GET'])
def inventory_input ():
   #call to product search API
   response = requests.get(os.environ['DB_SEARCH_API']+"db_product_search", params={'school_id':session['school_id']})
   #converting to dictionary
   dictr = response.json()
   df=pd.DataFrame(dictr, columns=['product_name', 'product_price'])
   #rendering template
   return render_template('stock_input_template.html', items=df['product_name'])

@app.route('/inventory_output',methods = ['POST', 'GET'])
def inventory_output():
   if request.method == 'POST':
      out = request.form.to_dict()
      output={}
      json_data={}
      for x in out:
         if out[x] == '':
            continue
         else:   
            output[x]=out[x].split(",")
      #stock_input(output,session['school_id'])
      json_data['school_id']=session['school_id']
      json_data['products']=output      
      requests.post(os.environ['DB_SEARCH_API']+"db_stock_input", json=json.dumps(json_data))
      #create ping  
      ping="STOCK SUCCESSFULLY ENTERED \n BY USER: "+session['username']+"\n FOR SCHOOL: "+session['school_name']+"\n PLEASE READ IN THE FORMAT 'ITEM NAME':['SIZE:QUANTITY'] \n"+str(output)
      #call email messenger api
      requests.post(os.environ['EMAIL_API']+"inventory_entry_emailer", json=json.dumps(ping))
      #call telegram API
      requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
      return render_template("stock_input_success.html")

@app.route('/inventory_view',methods = ['POST', 'GET'])
def inventory_view():
   #output=view_stock(session['school_id'])
   response=requests.get(os.environ['DB_SEARCH_API']+"db_view_inventory", params={'school_id':session['school_id']})
   response=response.json()
   df=pd.DataFrame(response).transpose() #creating dataframe of the response received
   html_dict={} #create empty dict to store the dataframe in html form
   for x in df.index: #iterating over indices of df
            temp=pd.DataFrame(df.loc[x,'stock_present']).transpose() #creating the size and quantity df
            temp.set_index('size', inplace=True) #setting the index
            html_dict[x]=temp.to_html(classes='data', justify='center').replace('<th>','<th style = "background-color: rgb(173, 171, 171)">') #stroing the html in the dict
   #create ping
   ping="INVENTORY VIEWED BY USER: "+session['username']
   #call email messenger api
   requests.post(os.environ['EMAIL_API']+"inventory_view_emailer", json=json.dumps({'ping':ping, 'username': session['username']}))
   #call telegram API
   requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
   return render_template('stock_view_template.html', output=html_dict)

@app.route('/inventory_modify',methods = ['POST', 'GET'])
def inventory_modify():
   #call to product search API
   response = requests.get(os.environ['DB_SEARCH_API']+"db_product_search", params={'school_id':session['school_id']})
   #converting to dictionary
   dictr = response.json()
   df=pd.DataFrame(dictr, columns=['product_name', 'product_price'])
   #rendering template
   return render_template('stock_modify_template.html', items=df['product_name'])

@app.route('/inventory_modify_task',methods = ['POST', 'GET'])
def inventory_modify_task():
   if request.method == 'POST':
      out = request.form.to_dict()
      output={}
      for x in out:
         if out[x] == '':
            continue
         else:   
            output[x]=out[x].split(",")
      #call inventory modify api
      response=requests.post(os.environ['DB_SEARCH_API']+"db_update_inventory", json=json.dumps({'school_id':session['school_id'], 'products':output}))
      response=response.json()
      if response['response'] == False:
         return render_template('stock_input_interrupt.html')
      else:
         #create ping
         ping="STOCK SUCCESSFULLY MODIFIED \n BY USER: "+session['username']+"\n FOR SCHOOL: "+session['school_name']+"\n PLEASE READ IN THE FORMAT 'ITEM NAME':['SIZE:QUANTITY'] \n"+str(output)
         #call email messenger api
         requests.post(os.environ['EMAIL_API']+"inventory_modify_emailer", json=json.dumps(ping))
         #call telegram API
         requests.post(os.environ['TELEGRAM_MESSENGER'], json=json.dumps(ping))
         return render_template("stock_input_success.html")

@app.route('/edit_invoice', methods=['POST', 'GET'])
def edit_invoice_input():
      return render_template("edit_invoice_input_template.html")

@app.route('/edit_invoice_details', methods=['POST', 'GET'])
def edit_invoice_details():
   if request.method == 'POST':
      out=request.form.to_dict()
      response=requests.get(os.environ['DB_SEARCH_API']+'db_search_student_invoice', params={'inv_no':out['inv_no'], 'date_of_purchase':out['date_of_purchase']} )
      response=response.json()
      if response['found'] == False:
         return render_template("student_invoice_not_found.html")
      else:
         response1 = requests.get(os.environ['DB_SEARCH_API']+"db_house_search", params={'school_id':session['school_id']})
         #converting to dictionary
         dictr = response1.json()
         #converting to list
         house_list=list(dictr['house_name'].values())
         #product search API call
         response1 = requests.get(os.environ['DB_SEARCH_API']+"db_product_search", params={'school_id':session['school_id']})
         #converting to diction
         dictr = response1.json()
         df=pd.DataFrame(dictr, columns=['product_name', 'product_price'])
         session['flag']=out
         dict_html={}
         #deserializing header data and converting to dict
         response['headers']=json.loads(response['headers'])
         df_header=pd.DataFrame(response['headers'])
         for x in df_header:
            dict_html[x]=df_header[x][0]
         x=datetime.utcfromtimestamp(dict_html['date_of_purchase']/1000)
         dict_html['date_of_purchase'] = x.date()
         #deserializing product data and converting to dict
         response['products']=json.loads(response['products'])
         df_products=pd.DataFrame(response['products'])
         for x in df_products.index:
            dict_html[df_products['product_name'][x]]=list([df_products['size'][x],df_products['item_quantity'][x]])      
         return render_template("student_invoice_edit_template.html", out=dict_html, items=df['product_name'], house=house_list)
         
if __name__ == '__main__':
   app.run(debug = True)