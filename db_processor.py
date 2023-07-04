import psycopg2
from datetime import datetime

DATABASE_URL = 'postgres://root:m2FL9uhdq3uTNTuX3mui9SXA2cljGT1d@dpg-cigaj85ph6erq6jal3p0-a.oregon-postgres.render.com/prikaway'
con = psycopg2.connect(DATABASE_URL)
cur = con.cursor()

def db_auth(dict_with_data):
    cur.execute("select * from users")
    result={}
    for rows in cur.fetchall():
        if rows[1] == dict_with_data['username'] and rows[2] == dict_with_data['password']:
            result['user_id']=rows[0]
            result['school_id']=rows[3]
            result['flag']=True
            result['username']=rows[1]
            break
        else:
            result['flag']=False
            continue
    cur.execute('select * from schools where id=%s',(rows[3],))
    for y in cur.fetchall():
        result['img_url']=y[2]
        result['school_name']=y[1]
        result['school_code']=y[3]
    return result

def db_house_search(dict_with_data):
    cur.execute('SELECT house_name from house where school_id=%s', (dict_with_data,))
    return cur.fetchall()

def db_product_search(dict_with_data):
    cur.execute('select product_name from products where school_id=%s', (dict_with_data,))
    return cur.fetchall()

def db_injector(dict_with_invoice_data,set):
    cur1=con.cursor()
    my_date= datetime.strptime(dict_with_invoice_data['Date'], '%Y-%m-%d')
    if set['school_id'] == 1:
        bill_no= 'PWPL/RW/'+str(my_date.year)+'/'+str(my_date.month)+'/'+str(dict_with_invoice_data['Roll No.'])
    if set['school_id'] == 2:
        bill_no= 'PWPL/GJ/'+str(my_date.year)+'/'+str(my_date.month)+'/'+str(dict_with_invoice_data['Roll No.'])
    for x in dict_with_invoice_data.keys():
        if x not in ['Roll No.','Name','Class','House','Date', 'Grand Total', 'Word Amount', 'Item Total']:
            cur1.execute('select id, product_name from products  where school_id=%s', (set['school_id'],))
            for y in cur1.fetchall():
                if x==y[1]:
                    break
            cur1.execute('select id,house_name from house where school_id=%s', (set['school_id'],))  
            for z in cur1.fetchall():
                if x==z[1]:
                    break
            render=tuple([dict_with_invoice_data['Roll No.'],dict_with_invoice_data['Name'],dict_with_invoice_data['Class'],z[0],y[0],dict_with_invoice_data[x][0],dict_with_invoice_data[x][2],False,dict_with_invoice_data['Date'], bill_no, set['school_id'],set['user_id']])
            sql1='insert into sales(roll_no,student_name,class,house_id,item_id,item_quantity,total_price,tc_leave,date_of_purchase,bill_no,school_id,user_id) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            cur.execute(sql1,render)
            con.commit()
    return bill_no

def db_search(dict_with_data, set):
    query=""" select p.product_name, p.product_price, sum(item_quantity), sum(total_price) 	
                    from sales s
                    join products p on p.id=s.item_id
                    where date_of_purchase BETWEEN %s AND %s  AND s.school_id=%s 
                    group by p.product_name, p.product_price;""" 
    cur.execute(query,(dict_with_data['start_date'],dict_with_data['end_date'],set))
    return cur.fetchall()

def db_search_house_cover(dict_with_data,set):
    query=""" select roll_no, student_name, class, sum(item_quantity), sum(total_price) 	
                from sales s
                where date_of_purchase BETWEEN %s AND %s AND house=%s AND s.school_id=%s
                group by roll_no, student_name, class 
                order by class,roll_no ;""" 
    cur.execute(query,(dict_with_data['start_date'],dict_with_data['end_date'],dict_with_data['House'],set))
    return cur.fetchall()

def db_search_all_house_cover(dict_with_data):
    query=""" select house, sum(item_quantity), sum(total_price) 	
                from sales
                where date_of_purchase BETWEEN %s AND %s group by house order by house;""" 
    cur.execute(query,(dict_with_data['start_date'],dict_with_data['end_date']))
    return cur.fetchall()
    
def db_delete_invoice(dict_with_data):
    query= """  select count(distinct bill_no) from sales where bill_no=%s and date_of_purchase=%s and class=%s;  """
    cur.execute(query, (dict_with_data['bill_no'],dict_with_data['date_of_purchase'], dict_with_data['class']))
    records=cur.fetchall()
    for x in records:
        if x[0] == 0:
            return "NF"
        else:
            query= """delete from sales
                    where bill_no=%s and date_of_purchase=%s and class=%s;""" 
            cur.execute(query,(dict_with_data['bill_no'],dict_with_data['date_of_purchase'], dict_with_data['class']))
            con.commit()
            return "S"

def db_change_invoice_status(dict_with_data):
    query= """  select count(distinct bill_no) from sales where bill_no=%s and date_of_purchase=%s and class=%s;  """
    cur.execute(query, (dict_with_data['bill_no'],dict_with_data['date_of_purchase'], dict_with_data['class']))
    records=cur.fetchall()
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
            cur.execute(query,(dict_with_data['tc_leave'],dict_with_data['bill_no'],dict_with_data['date_of_purchase'], dict_with_data['class']))
            con.commit()
            return "S"