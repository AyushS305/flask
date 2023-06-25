from flask import Flask, render_template, request
from numtoword import number_to_word
from db_processor import *
import sqlite3 as sql

app = Flask(__name__)

def db_connect():
    con = sql.connect('prikaway.db')
    cur = con.cursor()
    return cur

@app.route('/')
def student():
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
      sync=output
      return render_template("student_invoice_output_template.html",output = output)
   
@app.route('/print_invoice',methods = ['POST', 'GET'])
def print_invoice():
   if request.method == 'POST':
      output=sync
      output['Invoice No.']= db_injector(output)
      return render_template("student_invoice_print_template.html",output = output)
   
def input_template_process(out):
    cur=db_connect()
    cur.execute("select * from products")
    rows=cur.fetchall()
    ter={}
    s=0
    for x in out.keys():
       if x not in ['Name','Class','Roll No.', 'Date', 'House']:
          if out[x]=='':
             continue
          for y in rows:
             if x==y[1]:
                ter[x]=([int(out[x]),y[2],int(out[x])*y[2]])
                s+=int(out[x])*y[2]
       else:
          ter[x]=out[x]
    ter['Grand Total']=s
    ter['Word Amount']=number_to_word(s)
    return(ter)


if __name__ == '__main__':
   app.run(debug = True)