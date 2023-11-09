import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv
from numtoword import *
from babel.numbers import format_currency

load_dotenv()
DATABASE_URL = os.environ['DATABASE_URL']

class pgsql:
    def __init__(self):
        self.con=psycopg2.connect(DATABASE_URL)
        self.cur=self.con.cursor()

    def query_execute(self,query,parameter):
        global res
        try:
            self.cur.execute(query,parameter)
            self.con.commit()
            res=self.cur.fetchall()
            self.cur.close()
            self.con.close()
        except Exception: 
            self.con=psycopg2.connect(DATABASE_URL)
            self.cur=self.con.cursor()
        return res

def db_auth(dict_with_data):
    cur=pgsql()
    p=cur.query_execute("select * from users",None)      
    result={}
    for rows in p:
        if rows[1] == dict_with_data['username'] and rows[2] == dict_with_data['password']:
            result['user_id']=rows[0]
            result['school_id']=rows[3]
            result['flag']=True
            result['username']=rows[1]
            break
        else:
            result['flag']=False
            continue
    cur=pgsql()
    p=cur.query_execute('select * from schools where id=%s',(rows[3],))

    for y in p:
        result['img_url']=y[2]
        result['school_name']=y[1]
        result['school_code']=y[3]
    return result

def db_house_search(dict_with_data):
    cur=pgsql()
    return cur.query_execute('SELECT house_name from house where school_id=%s', (dict_with_data,))

def db_product_search(dict_with_data):
    cur=pgsql()
    return cur.query_execute('select * from products where school_id=%s', (dict_with_data,))

def db_injector(dict_with_invoice_data,set):
    cur1=pgsql()
    my_date= datetime.strptime(dict_with_invoice_data['Date'], '%Y-%m-%d')

    bill_no= 'PWPL/'+str(set['school_code'])+'/'+str(my_date.year)+'/'+str(my_date.month)+'/'+str(dict_with_invoice_data['Roll No.'])
    p=cur1.query_execute('select id,house_name from house where school_id=%s', (set['school_id'],))
    
    for z in p:
        if dict_with_invoice_data['House']==z[1]:
            house_id=z[0]
            break
    cur1=pgsql()    
    for x in dict_with_invoice_data.keys():
        if x not in ['Roll No.','Name','Class','House','Date', 'Grand Total', 'Word Amount', 'Item Total']:
            p=cur1.query_execute('select id, product_name from products  where school_id=%s', (set['school_id'],))           
            for y in p:
                if x==y[1]:
                    item_id=y[0]
                    break
            render=tuple([dict_with_invoice_data['Roll No.'],dict_with_invoice_data['Name'],dict_with_invoice_data['Class'],house_id,item_id,dict_with_invoice_data[x][0],dict_with_invoice_data[x][2],False,dict_with_invoice_data['Date'], bill_no, set['school_id'],set['user_id']])
            sql1='insert into sales(roll_no,student_name,class,house_id,item_id,item_quantity,total_price,tc_leave,date_of_purchase,bill_no,school_id,user_id) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            cur=pgsql()
            cur.query_execute(sql1,render)    
    return bill_no

def db_search_student_invoice(dict_with_data):
    cur=pgsql()
    query="""select count(distinct bill_no) from sales where bill_no=%s and date_of_purchase= %s"""
    output=cur.query_execute(query, (dict_with_data['inv_no'],dict_with_data['date_of_purchase']))
    for x in output:
        if x[0] == 0:
            return "NF"
        else:
            cur=pgsql()
            cur1=pgsql()
            query="""select student_name, class, roll_no, to_char(date_of_purchase, 'DD-MM-YYYY'), house_name, bill_no, img_url, tc_leave, sum(item_quantity), sum(total_price)
                        from sales s 
                        join house h on h.id=s.house_id
                        join schools s1 on s1.id=s.school_id
                        where bill_no=%s and date_of_purchase=%s
                        group by 1,2,3,4,5,6,7,8"""
            out=cur.query_execute(query, (dict_with_data['inv_no'],dict_with_data['date_of_purchase']))
            column_names = ['Name', 'Class', 'Roll No.', 'Date', 'House', 'Invoice No.', 'image', 'tc/leave', 'Item Total', 'Grand Total']
            result={}
            for x in range(len(out[0])):
                result[column_names[x]]=out[0][x]
            result['Word Amount']=number_to_word(result['Grand Total'])
            query="""select product_name, item_quantity, product_price, total_price from sales s
                        join products p on s.item_id=p.id
                        where bill_no=%s and date_of_purchase=%s"""
            out=cur1.query_execute(query, (dict_with_data['inv_no'],dict_with_data['date_of_purchase']))
            for x in out:
                temp=x[0]
                x=list(x)
                x.pop(0)
                x[1]=format_currency(x[1], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
                x[2]=format_currency(x[2], 'INR', format=u'#,##0\xa0¤', locale='en_IN', currency_digits=False)
                result[temp]=x
            if result['tc/leave']==False:
                result['tc/leave']="Current TC/Leave Status of this Invoice is NO"
            else:
                result['tc/leave']="Current TC/Leave Status of this Invoice is YES"
    return result

def db_search(dict_with_data, set):
    cur=pgsql()
    query=""" select p.product_name, p.product_price, sum(item_quantity), sum(total_price) 	
                    from sales s
                    join products p on p.id=s.item_id
                    where date_of_purchase BETWEEN %s AND %s  AND s.school_id=%s AND s.tc_leave=%s
                    group by p.product_name, p.product_price;""" 

    return cur.query_execute(query,(dict_with_data['start_date'],dict_with_data['end_date'],set, dict_with_data['tc_leave'])) 

def db_search_house_cover(dict_with_data,set):
    cur=pgsql()
    query=""" select roll_no, student_name, class, sum(item_quantity), sum(total_price) 	
                from sales s
                join house h on s.house_id=h.id
                where date_of_purchase BETWEEN %s AND %s AND h.house_name=%s AND s.school_id=%s AND s.tc_leave=%s
                group by roll_no, student_name, class 
                order by class,roll_no ;""" 
    
    return cur.query_execute(query,(dict_with_data['start_date'],dict_with_data['end_date'],dict_with_data['House'],set, dict_with_data['tc_leave']))

def db_search_all_house_cover(dict_with_data,set):
    cur=pgsql()
    query=""" select h.house_name, sum(item_quantity), sum(total_price) 	
                from sales s
                join house h on s.house_id=h.id
                where date_of_purchase BETWEEN %s AND %s AND s.school_id=%s AND s.tc_leave=%s
                group by h.house_name order by h.house_name;""" 

    return cur.query_execute(query,(dict_with_data['start_date'],dict_with_data['end_date'], set, dict_with_data['tc_leave']))
    
def db_delete_invoice(dict_with_data):
    cur=pgsql()
    query= """  select count(distinct bill_no) from sales where bill_no=%s and date_of_purchase=%s and class=%s;  """
    records=cur.query_execute(query, (dict_with_data['bill_no'],dict_with_data['date_of_purchase'], dict_with_data['class']))
    for x in records:
        if x[0] == 0:
            return "NF"
        else:
            query= """delete from sales
                    where bill_no=%s and date_of_purchase=%s and class=%s;""" 
            cur=pgsql()
            cur.query_execute(query,(dict_with_data['bill_no'],dict_with_data['date_of_purchase'], dict_with_data['class']))
            return "S"

def db_change_invoice_status(dict_with_data):
    cur=pgsql()
    query= """  select count(distinct bill_no) from sales where bill_no=%s and date_of_purchase=%s and class=%s;  """
    records=cur.query_execute(query, (dict_with_data['bill_no'],dict_with_data['date_of_purchase'], dict_with_data['class']))
    for x in records:
        if x[0] == 0:
            return "NF"
        else:
            if dict_with_data['tc_leave'].lower() == 'true':
                dict_with_data['tc_leave']=True
            elif dict_with_data['tc_leave'].lower() == 'false':
                dict_with_data['tc_leave']=False
            query= """update sales
                        set tc_leave=%s
                        where bill_no=%s and date_of_purchase=%s and class=%s;""" 
            cur=pgsql()
            cur.query_execute(query,(dict_with_data['tc_leave'],dict_with_data['bill_no'],dict_with_data['date_of_purchase'], dict_with_data['class']))
            return "S"
        
def db_raashan_product_search(data):
    cur=pgsql()
    return cur.query_execute('select * from raashan_products where tender_number=%s order by tender_number,tender_s_no',(data,))

def save_raashan_line_items(data,z):
    for x in data:
        if x not in ('Grand Total','Word Amount','Item Total', 'Date', 'Invoice No.', 'start_date', 'end_date', 'inv_date'):
            render= tuple([data['Invoice No.'], data[x][5], z,data[x][0], data['start_date'], data['end_date'], data[x][4], data['inv_date']])
            query="""insert into raashan_sales 
            (invoice_no, product_id, tender_no, quantity, start_date, end_date, total_price, inv_date)
            values(%s,%s,%s,%s,%s,%s,%s,%s)"""
            cur=pgsql()
            cur.query_execute(query,render)