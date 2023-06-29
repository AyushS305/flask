from flask import Flask, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from numtoword import number_to_word
import sqlite3 as sql
from db_processor import *
from date_format_change import *
from babel.numbers import format_currency
from datetime import date

app = Flask(__name__)
mail = Mail(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'cc.prikaway@gmail.com'
app.config['MAIL_PASSWORD'] = 'razxzzfslhyrxcni'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

def db_connect():
    con = sql.connect('prikaway.db')
    cur = con.cursor()
    return cur

@app.route('/', methods = ['POST', 'GET'])
def auth():
   error=None
   if request.method == 'POST':
      if request.form['username']!='rukaifu@gmail.com' or request.form['password']!='12345':
         error = 'Invalid Credentials. Please try again.'
      else:
         return redirect(url_for('homepage'))     
   return render_template('login.html', error=error)

@app.route('/homepage')
def homepage():
   return render_template('homepage.html')
   

@app.route('/input', methods = ['POST', 'GET'])
def input ():
   cur=db_connect()
   cur.execute("select item_name from products")
   y=z=[]
   for rows in cur.fetchall():
      y.append(rows[0])  
   return render_template('student_invoice_input_template.html', items=y)

@app.route('/output',methods = ['POST', 'GET'])
def output():
   if request.method == 'POST':
      out = request.form.to_dict()
      global sync
      output=input_template_process(out)
      output['Date']=change_date_format(output['Date'])
      sync=output
      return render_template("student_invoice_output_template.html",output = output)
   
@app.route('/print_invoice',methods = ['POST', 'GET'])
def print_invoice():
   if request.method == 'POST':
      output=sync
      output['Invoice No.']= db_injector(output)
      msg = Message(
                "STUDENT INVOICE GENERATED# "+output['Invoice No.'],
                sender ='MailBot',
                recipients = ['prikawayinvoicemailbot@gmail.com']
               )
      
      msg.body = " Please see the details below."
      output=output_template_format(output)
      msg.html = render_template("student_invoice_print_template.html", output=output)
      mail.send(msg)
      return render_template("student_invoice_print_template.html",output = output)
   
@app.route('/principal_bill',methods=['POST','GET'])
def principal_bill():
   return render_template('principal_bill_input_template.html')

@app.route('/generate_bill',methods=['POST','GET'])
def generate_bill():
   if request.method == 'POST':
      out = request.form.to_dict()
      res=db_search(out)
      result={}
      s=q=0
      for x in res:
         result[x[0]]=([format_currency(x[1], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False),x[2],format_currency(x[3], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)])      
         s=s+x[3]
         q=q+x[2]
      result['Date']=change_date_format(str(date.today()))
      result['Invoice No.']=str(abs(hash('PWPL/RW/'+str(date.today()))))
      result['Grand Total']=format_currency(s, 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
      result['Item Total']=q
      result['Word Amount']=number_to_word(s)
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
   
def input_template_process(out):
    cur=db_connect()
    cur.execute("select * from products")
    rows=cur.fetchall()
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

def output_school_bill_format(out):
   print(out)
   for x in out.keys():
       if x not in [ 'Date', 'Grand Total', 'Word Amount', 'Item Total','Invoice No.']:
         out[x][0]=format_currency(out[x][0], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
         out[x][2]=format_currency(out[x][2], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)  
   out['Grand Total']=format_currency(out['Grand Total'], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
   return(out)

if __name__ == '__main__':
   app.run(debug = True)