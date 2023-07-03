from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from db_processor import *
from date_format_change import *
from process_format import *

app = Flask(__name__)
mail = Mail(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'cc.prikaway@gmail.com'
app.config['MAIL_PASSWORD'] = 'razxzzfslhyrxcni'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

@app.route('/', methods = ['POST', 'GET'])
def auth():
   error=None
   if request.method == 'POST':
      result=request.form.to_dict()
      global sync_user
      result=db_auth(result)
      sync_user=result
      if result['flag'] == False:
         error = 'Invalid Credentials. Please try again.'
      else:
         return redirect(url_for('homepage'))     
   return render_template('login.html', error=error)

@app.route('/homepage')
def homepage():
   
   return render_template('homepage.html', sync_user=sync_user)
   
@app.route('/input', methods = ['POST', 'GET'])
def input ():
   h=[]
   y=[]
   for rows in db_house_search(sync_user['school_id']):
      h.append(rows[0])
   print(h)
   for rows in db_product_search(sync_user['school_id']):
      y.append(rows[0])  
   print(y)
   return render_template('student_invoice_input_template.html', items=y, house=h)

@app.route('/output',methods = ['POST', 'GET'])
def output():
   if request.method == 'POST':
      out = request.form.to_dict()
      global sync
      output=input_template_process(out, sync_user['school_id'])
      sync=output
      return render_template("student_invoice_output_template.html",output = output, image=sync_user['school_id'])
   
@app.route('/print_invoice',methods = ['POST', 'GET'])
def print_invoice():
   if request.method == 'POST':
      output=sync
      output['Invoice No.']= db_injector(output, sync_user)
      output['Date']=change_date_format(output['Date'])
      msg = Message(
                "STUDENT INVOICE GENERATED# "+output['Invoice No.'],
                sender ='MailBot',
                recipients = ['prikawayinvoicemailbot@gmail.com']
               )
      
      msg.body = " Please see the details below."
      output=output_template_format(output)
      msg.html = render_template("student_invoice_print_template.html", output=output, image=sync_user['school_id'])
      mail.send(msg)
      return render_template("student_invoice_print_template.html",output = output, image=sync_user['school_id'])
   
@app.route('/principal_bill',methods=['POST','GET'])
def principal_bill():
   return render_template('principal_bill_input_template.html')

@app.route('/generate_bill',methods=['POST','GET'])
def generate_bill():
   if request.method == 'POST':
      out = request.form.to_dict()
      res=db_search(out)
      result=school_pricipal_bill_process(res)
      global sync_school_bill
      sync_school_bill=result
      return render_template('principal_bill_output_template.html', result=result)

@app.route('/print_school_bill',methods=['POST','GET'])
def print_school_bill():
   if request.method == 'POST':
      result=sync_school_bill
      msg = Message(
                "BILL TO SAINIK SCHOOL REWARI PRINCIPAL GENERATED# "+result['Invoice No.'],
                sender ='MailBot',
                recipients = ['prikawayinvoicemailbot@gmail.com']
               )
      msg.body = " Please see the details below."
      msg.html = render_template("pricipal_bill_print_template.html", result=result)
      mail.send(msg)
      return render_template("pricipal_bill_print_template.html",result = result)
   
@app.route('/cover_page_input', methods=['POST','GET'])
def cover_page_input():
   return render_template('cover_page_input.html')

@app.route('/confirm_cover_page', methods=['POST','GET'])
def confirm_cover_page():
   if request.method == 'POST':
         data = request.form.to_dict()
         if data['House'] == 'All':
            result=db_search_all_house_cover(data)
            result=all_house_cover_process(result)
            result['House']='All'
         else:
            result=db_search_house_cover(data)
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
         result="INVOICE# "+data['bill_no']+"DELETED FROM DATABASE"
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
                "STUDENT INVOICE# "+data['bill_no']+ "SET AS TC/LEAVE "+str(data['tc_leave'])+ " IN THE DATABSE",
                sender ='MailBot',
                recipients = ['prikawayinvoicemailbot@gmail.com']
               )
         msg.body = " Student Invoice has been deleted from the database. Please note that this action is irreversible and if it was done by mistake then a new invoice needs to be generated"
         mail.send(msg)
         result="INVOICE# "+data['bill_no']+" MARKED AS TC/LEAVE "+str(data['tc_leave'])+ " IN THE DATABSE"
         return render_template("change_invoice_status_confirmed.html", result=result)
      if result=="NF":
         result="INVOICE DOES NOT EXISTS IN DATABSE. CHECK DETAILS AND TRY AGAIN"
         return render_template("change_invoice_status_confirmed.html", result=result)


if __name__ == '__main__':
   app.run(debug = True)