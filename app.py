from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail, Message
from db_processor import *
from date_format_change import *
from process_format import *
from flask_session import Session
from telegram_messenger import *
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
mail = Mail(app)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.secret_key = os.environ['APP_SECRET_KEY']
app.config['MAIL_SERVER']=os.environ['MAIL_SERVER']
app.config['MAIL_PORT'] = os.environ['MAIL_PORT']
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

@app.route('/', methods = ['POST', 'GET'])
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
         return redirect(url_for('homepage'))     
   return render_template('login.html', error=error)

@app.route('/homepage')
def homepage():
   send_message("user " + session['username']+ " logged in")
   return render_template('homepage.html', sync_user=session)

@app.route('/logout')
def logout():
   send_message("user " + session['username']+ " logged out")
   session.pop('username',None)
   return redirect(url_for('auth'))

@app.route('/input', methods = ['POST', 'GET'])
def input ():
   h=[]
   y=[]
   for rows in db_house_search(session['school_id']):
      h.append(rows[0])
   for rows in db_product_search(session['school_id']):
      y.append(rows[1])  
   return render_template('student_invoice_input_template.html', items=y, house=h)

@app.route('/output',methods = ['POST', 'GET'])
def output():
   if request.method == 'POST':
      out = request.form.to_dict()
      global sync
      output=input_template_process(out, session['school_id'])
      sync=output
      print(session['img_url']+'"')
      return render_template("student_invoice_output_template.html",output = output, image=session['img_url'])
   
@app.route('/print_invoice',methods = ['POST', 'GET'])
def print_invoice():
   if request.method == 'POST':
      output=sync
      output['Invoice No.']= db_injector(output, session)
      output['Date']=change_date_format(output['Date'])
      msg = Message(
                "STUDENT INVOICE GENERATED# "+output['Invoice No.'],
                sender ='MailBot',
                recipients = ['prikawayinvoicemailbot@gmail.com']
               )
      
      msg.body = " Please see the details below."
      output=output_template_format(output)
      ping="INVOICE GENERATED"+"\nSCHOOL NAME: "+ session['school_name']+"\nINVOICE NO: "+ output['Invoice No.'] +"\n GENERATED BY USER: "+session['username']+"\n STUDENT NAME: "+ output['Name']+"\n CLASS: "+ output['Class']+"\n ROLL NO: " +output['Roll No.']+"\n HOUSE: "+ output['House']+"\n INVOICE DATE: " +output['Date']+"\n TOTAL ITEMS: "+ str(output['Item Total'])+"\n TOTAL AMOUNT: " +output['Grand Total']
      send_message(ping)
      msg.html = render_template("student_invoice_print_template.html", output=output, image=session['img_url'])
      mail.send(msg)
      return render_template("student_invoice_print_template.html",output = output, image=session['img_url'])
   
@app.route('/principal_bill',methods=['POST','GET'])
def principal_bill():
   return render_template('principal_bill_input_template.html')

@app.route('/generate_bill',methods=['POST','GET'])
def generate_bill():
   if request.method == 'POST':
      out = request.form.to_dict()
      res=db_search(out, session['school_id'])
      result=school_pricipal_bill_process(res, session['school_code'])
      global sync_school_bill
      sync_school_bill=result
      return render_template('principal_bill_output_template.html', result=result, image=session)

@app.route('/print_school_bill',methods=['POST','GET'])
def print_school_bill():
   if request.method == 'POST':
      result=sync_school_bill
      msg = Message(
                "BILL TO " +(session['school_name']).upper()+ " PRINCIPAL GENERATED# "+result['Invoice No.'],
                sender ='MailBot',
                recipients = ['prikawayinvoicemailbot@gmail.com']
               )
      msg.body = "Please see the details below."
      msg.html = render_template("pricipal_bill_print_template.html", result=result, image=session)
      mail.send(msg)
      ping="BILL TO PRINCIPAL GENERATED"+"\nSCHOOL NAME: "+ session['school_name']+"\nINVOICE NO: "+ result['Invoice No.'] +"\n GENERATED BY USER: "+session['username']+"\n INVOICE DATE: " +result['Date']+"\n TOTAL ITEMS: "+ str(result['Item Total'])+"\n TOTAL AMOUNT: " +result['Grand Total']
      send_message(ping)
      return render_template("pricipal_bill_print_template.html",result = result, image=session)
   
@app.route('/cover_page_input', methods=['POST','GET'])
def cover_page_input():
   h=[]
   for rows in db_house_search(session['school_id']):
      h.append(rows[0])
   return render_template('cover_page_input.html', house=h)

@app.route('/confirm_cover_page', methods=['POST','GET'])
def confirm_cover_page():
   if request.method == 'POST':
         data = request.form.to_dict()
         if data['House'] == 'All':
            result=db_search_all_house_cover(data, session['school_id'])
            result=all_house_cover_process(result)
            result['House']='All'
         else:
            result=db_search_house_cover(data, session['school_id'])
            result=house_cover_process(result)
            result['House']=data['House']
         global sync_cover_data
         sync_cover_data=result
         return render_template("cover_page_house.html", result=result)
   
@app.route('/print_house_cover_page',methods=['POST','GET'])
def print_house_cover_page():
   if request.method == 'POST':
      result=sync_cover_data
      msg = Message(
                "COVER PAGE TO SAINIK SCHOOL REWARI PRINCIPAL GENERATED# "+result['Invoice No.'],
                sender ='MailBot',
                recipients = ['prikawayinvoicemailbot@gmail.com']
               )
      msg.body = " Please see the details below."
      msg.html = render_template("cover_page_print.html", result=result)
      mail.send(msg)
      ping="COVER PAGE GENERATED"+"\nSCHOOL NAME: "+ session['school_name']+"\n GENERATED BY USER: "+session['username']+"\n TOTAL ITEMS: "+ str(result['Item Total'])+"\n TOTAL AMOUNT: " +result['Grand Total']
      send_message(ping)
      return render_template("cover_page_print.html",result = result)

@app.route('/delete_invoice_input', methods=['POST', 'GET'])
def delete_invoice_input():
      return render_template("delete_invoice_input_template.html")

@app.route('/delete_invoice_confirmed', methods=['POST', 'GET'])
def delete_invoice_confirmed():
   if request.method == 'POST':
      data=request.form.to_dict()
      result= db_delete_invoice(data)
      if result=="S":
         msg = Message(
                "STUDENT INVOICE# "+data['bill_no']+ "DELETED",
                sender ='MailBot',
                recipients = ['prikawayinvoicemailbot@gmail.com']
               )
         msg.body = " Student Invoice has been deleted from the database. Please note that this action is irreversible and if it was done by mistake then a new invoice needs to be generated"
         mail.send(msg)
         result="INVOICE NO. "+data['bill_no']+"DELETED FROM DATABASE"
         ping=result+"\n DELETED BY USER: "+session['username']
         send_message(ping)
         return render_template("delete_invoice_confirmed.html", result=result)
      if result=="NF":
         result="INVOICE DOES NOT EXISTS IN DATABSE. CHECK DETAILS AND TRY AGAIN"
         return render_template("delete_invoice_confirmed.html", result=result)

@app.route('/change_invoice_status_input', methods=['POST', 'GET'])
def change_invoice_status_input():
      return render_template("change_invoice_status_input.html")

@app.route('/change_invoice_status_confirmed', methods=['POST', 'GET'])
def change_invoice_status_confirmed():
   if request.method == 'POST':
      data=request.form.to_dict()
      result= db_change_invoice_status(data)
      if result=="S":
         msg = Message(
                "STUDENT INVOICE# "+data['bill_no']+ "SET AS TC/LEAVE "+str(data['tc_leave'])+ " IN THE DATABASE",
                sender ='MailBot',
                recipients = ['prikawayinvoicemailbot@gmail.com']
               )
         msg.body = " Student Invoice TC/Leave status has been changed"
         mail.send(msg)
         result="INVOICE NO. "+data['bill_no']+" MARKED AS TC/LEAVE "+str(data['tc_leave'])+ " IN THE DATABASE"
         send_message(result+" BY USER "+session['username'])
         return render_template("change_invoice_status_confirmed.html", result=result)
      if result=="NF":
         result="INVOICE DOES NOT EXISTS IN DATABSE. CHECK DETAILS AND TRY AGAIN"
         return render_template("change_invoice_status_confirmed.html", result=result)

@app.route('/select_raashan_tender', methods=['POST', 'GET'])
def select_raashan_tender():
   return render_template('select_raashan_tender.html')

@app.route('/input_raashan_details', methods=['POST', 'GET'])
def input_raashan_details():
   if request.method == 'POST':
      data=request.form.to_dict()
      session['tender_no']=data['tender']
      items=db_raashan_product_search(data['tender'])
      return render_template('input_raashan_details.html', items=items)
   
@app.route('/confirm_raashan_details', methods=['POST', 'GET'])
def confirm_raashan_details():
   if request.method == 'POST':
      data=request.form.to_dict()
      result=check_raashan_details(data, session['tender_no'])
      global sync_raashan
      sync_raashan=result
      return render_template('confirm_raashan_details.html', result=result, image=session)

@app.route('/print_raashan_bill', methods=['POST', 'GET'])
def print_raashan_bill():
   if request.method == 'POST':
      result=sync_raashan
      save_raashan_line_items(result, session['tender_no'])
      result['start_date']=change_date_format(result['start_date'])
      result['end_date']=change_date_format(result['end_date'])
      msg = Message(
                "RAASHAN BILL TO SAINIK SCHOOL GOPALGANJ PRINCIPAL GENERATED# "+str(result['Invoice No.']),
                sender ='MailBot',
                recipients = ['prikawayinvoicemailbot@gmail.com']
               )
      msg.body = " Please see the details below."
      msg.html = render_template("print_raashan_bill.html", result=result, image=session)
      mail.send(msg)
      ping="RAASHAN BILL TO SAINIK SCHOOL GOPALGANJ PRINCIPAL GENERATED# "+"\nINVOICE NO: "+ str(result['Invoice No.']) +"\n GENERATED BY USER: "+session['username']+"\n TOTAL AMOUNT: " +str(result['Grand Total'])
      send_message(ping)
      return render_template('print_raashan_bill.html', result=result, image=session)

@app.route('/analytics', methods=['POST','GET'])
def analytics():
   error=None
   if request.method == 'POST':
      data=request.form.to_dict()
      if data['otp'] == str(8092):
         return redirect(url_for('tableau_dashboard'))
      else:
         error = 'Invalid Credentials. Please try again.'
   return render_template('enter_otp.html', error=error)

@app.route('/tableau_dashboard', methods=['POST','GET'])
def tableau_dashboard():
   return render_template('tableau.html')

if __name__ == '__main__':
   app.run(debug = True)