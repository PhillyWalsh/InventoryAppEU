from flask import Flask, session, render_template, request, flash, url_for, redirect, Response, jsonify, json

from functools import wraps
from collections import namedtuple
from passlib.hash import md5_crypt
from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
from io import StringIO
import logging
from logging import Formatter, FileHandler
import pytesseract
import imghdr
import DBcm
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)

def check_login(func):
	@wraps(func)
	def wrapped_function(*args, **kwargs):
		if 'logged_in' in session:
			return func(*args, **kwargs)
		flash('You are NOT logged in. Please log in to continue')
		return redirect(url_for('login'))
	return wrapped_function

def db_details():
    DBconfig = { 'host': 'localhost',
                'user': 'root',
                'password': 'rootuserpasswd',
                'database': 'inventoryapp' }
    return DBconfig

#--------------------------------
#named tuples for database tables
#--------------------------------
Book = namedtuple('Book', 'iid, uid, barcode, title, author, category, pic_url, price, ts')
Item = namedtuple('Item', 'iid, uid, barcode, title, category, pic_url, price, ts')

#----------------
# LANDING PAGE
#----------------
@app.route('/')
def homepage():
    return render_template("main.html")

#----------------
# DASHBOARD
#----------------
@app.route('/dashboard/')
@check_login
def dashboard():    
    return render_template("dashboard.html")

#----------------
# 404 ERROR
#----------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

#----------------
# CREATE USER
#----------------
def create_user(username, email, password):
    details = db_details()
    hash = md5_crypt.encrypt(password)
    with DBcm.UseDatabase(details) as cursor:
        _SQL = "insert into users (username, email, password) values (%s, %s, %s)"
        cursor.execute(_SQL, (username, email, hash,))

#----------------
# CHECK PASSWORD
#----------------
def user_login(username, password):
    login = False
    details = db_details()
    with DBcm.UseDatabase(details) as cursor:
        cursor.execute("select uid, username, password from users where username != ''")
        the_data = cursor.fetchall()

    for row in the_data:
        if row[1].lower() == username.lower() and md5_crypt.verify(password, row[2]) == True:
            login = True
            session['uid'] = row[0]
    return login

#----------------
# CHECK EMAIL
#----------------
def email_register(email):
    email_used = False
    details = db_details()
    with DBcm.UseDatabase(details) as cursor:
        cursor.execute("select email from users where email != ''")
        the_data = cursor.fetchall()

    for row in the_data:
        if row[0].lower() == email.lower():
            email_used = True
    return email_used

#----------------
# CHECK USERNAMES
#----------------
def username_register(username):
    username_used = False
    details = db_details()
    with DBcm.UseDatabase(details) as cursor:
        cursor.execute("select username from users where username != ''")
        the_data = cursor.fetchall()

    for row in the_data:
        if row[0].lower() == username.lower():
            username_used = True
    return username_used

#----------------
# CHECK BARCODE
#----------------
def check_barcode(uid, barcode):
    barcode_status = False
    details = db_details()
    with DBcm.UseDatabase(details) as cursor:
        cursor.execute("SELECT uid, barcode FROM books UNION SELECT uid, barcode FROM items where barcode != ''")
        the_data = cursor.fetchall()

    for row in the_data:
        if row[0] == uid and row[1] == barcode:
            barcode_status = True
    return barcode_status


#----------------
# LOGIN
#----------------
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
            flash('Already logged in')
            return redirect(url_for('dashboard'))
    else:
        if request.method == 'POST':
            username = request.form['user_name']
            password = request.form['password']
            user_details = user_login(username, password)

            if user_details == False:
                flash('Invalid Details')
            else:
                session['logged_in'] = True
                session['username'] = request.form['user_name']
                flash('Logged In')
                return redirect(url_for('dashboard'))

    return render_template('login.html')

#----------------
# LOGIN APP
#----------------
@app.route('/app/login/', methods=['GET', 'POST'])
def login_app():
    data = request.get_json(force=True)
    incoming_data = (data['template']['data'][0])

    user_name = incoming_data['username']
    password = incoming_data['password']
    
    user_details = user_login(user_name, password)
    items = []
    if user_details == False:
        data = "failed"
        template =      {
                            "response": data
                        }
        items.append(template)
        js = json.dumps({"collection":items})
        return js
    else:
        data = "success"
        userid = str(session['uid'])
        template =      {
                            "response": data,
                            "username": user_name,
                            "userid": userid
                        }
        items.append(template)
        session.pop('uid', None)
        js = json.dumps({"collection":items})
        return js

#----------------
# REGISTER APP
#----------------
@app.route('/app/register/', methods=['GET', 'POST'])
def register_app():
    data = request.get_json(force=True)
    incoming_data = (data['template']['data'][0])

    user_name = incoming_data['username']
    email = incoming_data['email']
    password = incoming_data['password']
    
    username_used = username_register(user_name)
    email_used = email_register(email)

    if username_used == True:
        data = "user-exist"
        return json.dumps(data)
    elif email_used == True:
        data = "email-exist"
        return json.dumps(data)
    else:
        data = "success"
        create_user(user_name, email, password)
        return json.dumps(data)
    
    data = "failed"
    return json.dumps(data)

#----------------
# LOGOUT
#----------------
@app.route('/logout/')
def logout():
    if 'logged_in' in session:
        session.pop('logged_in')
        session.pop('username', None)
        flash('Logged Out')
        return redirect(url_for('homepage'))
    else:
        flash('Already logged out!')
        return redirect(url_for('homepage'))

#----------------------
# DASHBOARD/ GET ITEMS
#----------------------
@app.route('/dashboard/<string:name>/', methods = ['GET'])
@check_login
def dashboard_items(name):
    with DBcm.UseDatabase(db_details()) as cursor: 
        if name == "books":
            SQL_command = "SELECT * FROM " + name + " WHERE uid = " + str(session['uid'])
            cursor.execute(SQL_command)
            data = [Book(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Book(*row))
            
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "author": row.author,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                       
                items.append(template)

            collection = items
            #js = json.dumps({"collection":collection})
            #book_json = jsonify({"collection":collection})
            #return collection
            return render_template('book_list.html', json=collection)
        
        elif name == "items":
            SQL_command = "SELECT * FROM " + name + " WHERE uid = " + str(session['uid'])
            cursor.execute(SQL_command)
            data = [Item(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Item(*row))
            
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                               
                items.append(template)
        
            collection = items
            #js = json.dumps({"collection":collection})
            #item_json = jsonify({"collection":collection})
            #return collection
            return render_template('item_list.html', json=collection)
        
        elif name == "games":
            SQL_command = "SELECT * FROM items WHERE category = 'Games' AND uid = " + str(session['uid'])
            cursor.execute(SQL_command)
            data = [Item(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Item(*row))
            
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                               
                items.append(template)
        
            collection = items
            #js = json.dumps({"collection":collection})
            #item_json = jsonify({"collection":collection})
            #return collection
            return render_template('item_list.html', json=collection)
        
        elif name == "dvds":
            SQL_command = "SELECT * FROM items WHERE category = 'DVDs & Blu-rays' AND uid = " + str(session['uid'])
            cursor.execute(SQL_command)
            data = [Item(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Item(*row))
            
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                               
                items.append(template)
        
            collection = items
            #js = json.dumps({"collection":collection})
            #item_json = jsonify({"collection":collection})
            #return collection
            return render_template('item_list.html', json=collection)

        else:
            return render_template("404.html")

#----------------------
# DASHBOARD/ UPDATE ITEM
#----------------------
@app.route('/dashboard/<string:name>/update/<string:iid>/', methods = ['PUT','POST'])
@check_login
def update_item(name, iid):
    with DBcm.UseDatabase(db_details()) as cursor: 
        if name == "books":
            title = request.form['title-text']
            author = request.form['author-text']
            cat = request.form['cat-text']
            SQL_command = 'UPDATE books SET title = "'+ title +'", author = "'+ author +'", category = "'+ cat +'" WHERE iid = ' + iid + ' AND uid = ' + str(session['uid']) + ''
            cursor.execute(SQL_command)
            
            flash('Item Updated')
            return redirect('/dashboard/books/')
        
        elif name == "items":
            title = request.form['title-text']
            cat = request.form['cat-text']
            SQL_command = 'UPDATE items SET title = "'+ title +'", category = "'+ cat +'" WHERE iid = ' + iid + ' AND uid = ' + str(session['uid']) + ''
            cursor.execute(SQL_command)
            
            flash('Item Updated')
            return redirect('/dashboard/items/')

        else:
            return render_template("404.html") 
        
        
#----------------------
# DASHBOARD/ DELETE ITEM
#----------------------
@app.route('/dashboard/<string:name>/delete/<string:iid>/', methods = ['GET','DELETE'])
@check_login
def delete_item(name, iid):
    with DBcm.UseDatabase(db_details()) as cursor: 
        if name == "books":
            SQL_command = "DELETE FROM books WHERE iid = " + iid + " AND uid = " + str(session['uid']) + ""
            cursor.execute(SQL_command)

            flash('Item Deleted')
            return redirect('/dashboard/books/')
                
        elif name == "items":
            SQL_command = "DELETE FROM items WHERE iid = " + iid + " AND uid = " + str(session['uid']) + ""
            cursor.execute(SQL_command)

            flash('Item Deleted')
            return redirect('/dashboard/items/')
    
        else:
            return render_template("404.html")        
        
#----------------------
# DASHBOARD/ EDIT ITEM
#----------------------
@app.route('/dashboard/<string:name>/edit/<string:iid>/', methods = ['GET'])
@check_login
def edit_item(name, iid):
    with DBcm.UseDatabase(db_details()) as cursor: 
        if name == "books":
            SQL_command = "SELECT * FROM books WHERE iid = " + iid + " AND uid = " + str(session['uid']) + ""
            cursor.execute(SQL_command)
            data = [Book(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Book(*row))
            
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "author": row.author,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                       
                items.append(template)

            collection = items
            return render_template('edit_book.html', json=collection)
        
        elif name == "items":
            SQL_command = "SELECT * FROM items WHERE iid = " + iid + ""
            cursor.execute(SQL_command)
            data = [Item(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Item(*row))
            
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                               
                items.append(template)
        
            collection = items
            return render_template('edit_item.html', json=collection)

        else:
            return render_template("404.html")
        
    
#-----------------
# POST /table/post
#-----------------
@app.route("/table/post/<string:tableName>/", methods = ['POST'])
def tablePost(tableName):
    data = request.get_json(force=True)
    incoming_data = (data['template']['data'][0])
    
    uid = int(incoming_data['uid'])
    barcode = incoming_data['barcode']
    title = incoming_data['title']
    category = incoming_data['category']
    pic_url = incoming_data['pic_url']
    price = incoming_data['price']
    items = []
    
    used = check_barcode(uid, barcode)
    
    if used == False:
        if tableName == "books":
            author = incoming_data['author']
            with DBcm.UseDatabase(db_details()) as cursor:
                SQL_command = "INSERT INTO books (uid, barcode, title, author, category, pic_url, price) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(SQL_command, (uid, barcode, title, author, category, pic_url, price))

        elif tableName == "items":
            with DBcm.UseDatabase(db_details()) as cursor:
                SQL_command = "INSERT INTO items (uid, barcode, title, category, pic_url, price) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(SQL_command, (uid, barcode, title, category, pic_url, price))         

        data = "item-added"
        template =      {
                            "response": data
                        }
        items.append(template)
        js = json.dumps({"collection":items})
        return js
    
    else:
        details = "item-exist"
        with DBcm.UseDatabase(db_details()) as cursor:
            SQL_command = "SELECT ts FROM books UNION SELECT ts FROM items where barcode = "+ barcode +" AND uid = "+ str(uid) +""
            cursor.execute(SQL_command)
            data = cursor.fetchall()
            items = []
            
            for row in data:
                date = row[0]
                
            template =      {
                                "response": details,
                                "date": row[0]
                            }
        items.append(template)
        js = json.dumps({"collection":items})
        return js

    
#--------------------------
# GET item list
#--------------------------    
@app.route('/app/<string:name>/<string:uid>/', methods = ['GET'])
def app_list(name, uid):
    with DBcm.UseDatabase(db_details()) as cursor: 
        if name == "books":
            SQL_command = "SELECT * FROM " + name + " WHERE uid = "+ uid +""
            cursor.execute(SQL_command)
            data = [Book(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Book(*row))
            
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "author": row.author,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                       
                items.append(template)

            collection = items
            js = json.dumps({"collection":collection})
            #book_json = jsonify({"collection":collection})
            return js
        
        elif name == "items":
            SQL_command = "SELECT * FROM " + name + " WHERE uid = "+ uid +""
            cursor.execute(SQL_command)
            data = [Item(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Item(*row))
            
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                       
                items.append(template)

            collection = items
            js = json.dumps({"collection":collection})
            #book_json = jsonify({"collection":collection})
            return js
        
        elif name == "games":
            SQL_command = "SELECT * FROM items WHERE category = 'Games' AND uid = "+ uid +""
            cursor.execute(SQL_command)
            data = [Item(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Item(*row))
            
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                       
                items.append(template)

            collection = items
            js = json.dumps({"collection":collection})
            #book_json = jsonify({"collection":collection})
            return js
        
        elif name == "dvds":
            SQL_command = "SELECT * FROM items WHERE category = 'DVDs & Blu-rays' AND uid = "+ uid +""
            cursor.execute(SQL_command)
            data = [Item(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Item(*row))
            
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                       
                items.append(template)

            collection = items
            js = json.dumps({"collection":collection})
            #book_json = jsonify({"collection":collection})
            return js

        
#--------------------------
# DELETE item app
#--------------------------        
@app.route('/app/delete/<string:itemId>/<string:code>/', methods = ['DELETE'])
def app_delete_item(itemId, code):
    with DBcm.UseDatabase(db_details()) as cursor: 
        if (code[:3] == "978" or code[:3] == "979"):
            SQL_command = "DELETE FROM books WHERE iid = "+ itemId +" AND barcode = "+ code +""
            cursor.execute(SQL_command)
        
        else:
            SQL_command = "DELETE FROM items WHERE iid = "+ itemId +" AND barcode = "+ code +""
            cursor.execute(SQL_command)
              
    resp = Response(status=204, mimetype='application/json')
    resp.headers['Link'] = 'http://178.62.87.155/app/delete/'
    return resp

#--------------------------
# UPDATE item app
#-------------------------- 
@app.route('/app/update/<string:itemId>/<string:code>/', methods = ['PUT'])
def app_update_item(itemId, code):
    data = request.get_json(force=True)
    incoming_data = (data['template']['data'][0])
    
    title = incoming_data['title']
    
    with DBcm.UseDatabase(db_details()) as cursor: 
        if (code[:3] == "978" or code[:3] == "979"):
            SQL_command = 'UPDATE books SET title= "'+ title +'" WHERE iid = '+ itemId +' AND barcode = '+ code +''
            cursor.execute(SQL_command)
        
        else:
            SQL_command = 'UPDATE items SET title= "'+ title +'" WHERE iid = '+ itemId +' AND barcode = '+ code +''
            cursor.execute(SQL_command)
              
    resp = Response(status=204, mimetype='application/json')
    resp.headers['Link'] = 'http://178.62.87.155/app/delete/'
    return resp

#--------------------------
# GET single item
#--------------------------
@app.route('/app/showitem/<string:itemId>/<string:code>/', methods = ['GET'])
def app_get_item(itemId,code):
    with DBcm.UseDatabase(db_details()) as cursor:
        if (code[:3] == "978" or code[:3] == "979"):
            SQL_command = "SELECT * FROM books WHERE iid = "+ itemId +" AND barcode = "+ code +""
            cursor.execute(SQL_command)
            data = [Book(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Book(*row))
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "author": row.author,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                items.append(template)
                
            collection = items
            return json.dumps({"collection":collection})
        
        else:
            SQL_command = "SELECT * FROM items WHERE iid = "+ itemId +" AND barcode = "+ code +""
            cursor.execute(SQL_command)
            data = [Item(*row) for row in cursor.fetchall()]
            rows = []
            items = []
            
            for row in data:
                rows.append(Item(*row))
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                items.append(template)
            
            collection = items
            return json.dumps({"collection":collection})
        

#--------------------------
# POST picture for OCR
#--------------------------

@app.route('/upload/', methods=["POST"])
def get_picture():
    try:
        im = request.files["file"]
        image = Image.open(im).convert('L')
        image.filter(ImageFilter.SHARPEN)
        result = pytesseract.image_to_string(image)
        return result
    except:
        return 'Error'

    
#--------------------------
# GET search results
#--------------------------    

@app.route('/app/search/<string:userId>/<string:text>/', methods = ['GET'])
def search_items(userId, text):
    with DBcm.UseDatabase(db_details()) as cursor:
        rows = []
        items = []
        SQL_command = "SELECT * FROM books WHERE uid = "+ userId +""
        cursor.execute(SQL_command)
        data = [Book(*row) for row in cursor.fetchall()]

        for row in data:
            if  (text in row.title.lower() or text in row.author.lower() or text in row.category.lower()):
                rows.append(Book(*row))
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "author": row.author,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                items.append(template)
            
        SQL_command = "SELECT * FROM items WHERE uid = "+ userId +""
        cursor.execute(SQL_command)
        data = [Item(*row) for row in cursor.fetchall()]

        for row in data:
            if  (text in row.title.lower() or text in row.category.lower()):
                rows.append(Item(*row))
                template =          {
                                        "iid": row.iid,
                                        "barcode": row.barcode,
                                        "title": row.title,
                                        "category": row.category,
                                        "pic_url": row.pic_url,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
                items.append(template)    

        collection = items
        return json.dumps({"collection":collection})
    

#--------------------------
# SEND CSV Email
#--------------------------    
def sendEmail(user_address):
    fromMy = 'inventoryapp@yahoo.com'
    to  = user_address
    
    msg = MIMEMultipart()
    msg['From'] = fromMy
    msg['To'] = to
    msg['Subject'] = 'CSV Item Report'

    body = 'Please find the CSV report attached..'

    msg.attach(MIMEText(body, 'plain'))
    
    filename = "/tmp/ItemList.csv"
    attachment = open(filename, "rb")
    
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    
    msg.attach(part)
    
    username = str('inventoryapp@yahoo.com')  
    password = str('password1234')  

    try :
        server = smtplib.SMTP("smtp.mail.yahoo.com",587)
        server.starttls()
        server.login(username,password)
        text = msg.as_string()
        server.sendmail(fromMy, to, text)
        server.quit()    
        print ('ok the email has sent')
        return True
    except :
        print ('cant send the Email')
        return False

    
    
#--------------------------
# POST Export Items CSV
#--------------------------

@app.route('/export/', methods=["POST"])
def export_items():
    data = request.get_json(force=True)
    incoming_data = (data['template']['data'][0])
    
    userId = incoming_data['uid']
    rows = []
    items = []
    itemResp = []
    
    with DBcm.UseDatabase(db_details()) as cursor:
        SQL_command = "SELECT email FROM users WHERE uid = "+ userId +""
        cursor.execute(SQL_command)
        the_data = cursor.fetchall()
        for row in the_data:
            emailAdd = row[0]
    
    with DBcm.UseDatabase(db_details()) as cursor:
        SQL_command = "SELECT * FROM books WHERE uid = "+ userId +""
        cursor.execute(SQL_command)
        data = [Book(*row) for row in cursor.fetchall()]

        for row in data:
            rows.append(Book(*row))
            template =          {
                                        "barcode": str(row.barcode),
                                        "title": row.title,
                                        "category": row.category,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
            items.append(template)
            
        SQL_command = "SELECT * FROM items WHERE uid = "+ userId +""
        cursor.execute(SQL_command)
        data = [Item(*row) for row in cursor.fetchall()]

        for row in data:
            rows.append(Item(*row))
            template =          {
                                        "barcode": str(row.barcode),
                                        "title": row.title,
                                        "category": row.category,
                                        "price": row.price,
                                        "ts": row.ts
                                    }
            items.append(template)    
        
        x = json.loads(json.dumps(items))
        theFile = open('/tmp/ItemList.csv', 'w')
        f = csv.writer(theFile)
        f.writerow(["Barcode", "Title", "Category", "Price(Euro)", "Added/Modified"])
        
        for x in x:
            f.writerow([x["barcode"], 
                        x["title"], 
                        x["category"],
                        x["price"],
                        x["ts"],])
        
        theFile.close()
        answer = sendEmail(emailAdd)
        if (answer == True):
            template =      {
                                "result": "Sent",
                                "email": emailAdd
                            }
            itemResp.append(template)
            return json.dumps({"collection":itemResp})
        else:
            template =      {
                                "result": "Not Sent"
                            }
            itemResp.append(template)
            return json.dumps({"collection":itemResp})
        
        resp = Response(status=204, mimetype='application/json')
        resp.headers['Link'] = 'http://178.62.87.155/export/'
        return resp
        
    
    
    
if __name__ == "__main__":
    app.run()
