import sqlite3 as sql
from datetime import datetime

def db_injector(dict_with_invoice_data):
    con = sql.connect('prikaway.db')
    cur = con.cursor()
    my_date= datetime.strptime(dict_with_invoice_data['Date'], '%d-%m-%Y')
    bill_no= 'PWPL/RW/'+str(my_date.year)+'/'+str(my_date.month)+'/'+str(dict_with_invoice_data['Roll No.'])
    for x in dict_with_invoice_data.keys():
        if x not in ['Roll No.','Name','Class','House','Date', 'Grand Total', 'Word Amount']:
            render=tuple([dict_with_invoice_data['Roll No.'],'"'+dict_with_invoice_data['Name']+'"',dict_with_invoice_data['Class'],'"'+dict_with_invoice_data['House']+'"','"'+x+'"',dict_with_invoice_data[x][0],dict_with_invoice_data[x][2],False,'"'+dict_with_invoice_data['Date']+'"', '"'+bill_no+'"'])
            sql1='insert into sales(roll_no,student_name,class,house,item_purchased,item_quantity,total_price,tc_leave,date_of_purchase,bill_no) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            cur.execute(sql1%render)
            cur.execute("UPDATE sales set item_id=(select id from products where item_purchased=item_name)")
            con.commit()
    return bill_no