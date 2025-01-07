from flask import Flask,render_template,request,url_for,flash,redirect,session
import mysql.connector
from otp import genotp
from cmail import sendmail
import os
from adminmail import adminsendmail
from adminotp import adotp
from itemid import itemidotp
import razorpay
RAZORPAY_KEY_ID = "rzp_test_nKMhhbSQoripGE"
RAZORPAY_KEY_SECRET = "VT8EU3XT7FlL9irQeAbzchPx"
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

db=os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']

# mydb=mysql.connector.connect(host='localhost',
# user='root',
# password='root',
# db='ecomerce')

app=Flask(__name__)
app.secret_key='asdfghjkl'

@app.route('/')
def base():
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        mobile = request.form['mobile']
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']
        
        cursor = mydb.cursor()
        cursor.execute('SELECT email FROM signup')
        data = cursor.fetchall()
        cursor.execute('SELECT mobile FROM signup')
        edata = cursor.fetchall()
        
        # Check if the user already exists
        if (mobile,) in edata:
            flash('User already exists.')
            return render_template('register.html')
        
        if (email,) in data:
            flash('Email address already exists.')
            return render_template('register.html')
        
        cursor.close()

        return render_template('otp.html', otp=otp, username=username, mobile=mobile, email=email, address=address, password=password)
    
    return render_template('register.html')

@app.route('/otp/<otp>/<username>/<mobile>/<email>/<address>/<password>', methods=['GET', 'POST'])
def otp(otp, username, mobile, email, address, password):
    if request.method == 'POST':
        uotp = request.form['otp']
        
        if otp == uotp:  # If OTP matches
            cursor = mydb.cursor()
            lst = [username, mobile, email, address, password]
            query = 'INSERT INTO signup (username, mobile, email, address, password) VALUES (%s, %s, %s, %s, %s)'
            cursor.execute(query, lst)
            mydb.commit()  # Commit to save data in the database
            cursor.close()
            
            flash('Details registered successfully!')
            return redirect(url_for('login'))  # Redirect to login after successful registration
        else:
            flash('Incorrect OTP. Please try again.')  # Show error if OTP is incorrect
            return render_template('otp.html', otp=otp, username=username, mobile=mobile, email=email, address=address, password=password)
    
    return render_template('otp.html', otp=otp, username=username, mobile=mobile, email=email, address=address, password=password)


    
    
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mydb.cursor()
        cursor.execute('select count(*) from signup where username =%s and password=%s',[username,password])
        count = cursor.fetchone()[0]
        print(count)
        if count == 0:
            flash('Invalid email or password')
            return render_template('login.html')
        else:
            session['user']=username
            if not session.get(username):
                session[username]={}
            return redirect(url_for('home1'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home1'))
    else:
        flash('already logged out!')
        return render_template(url_for('login'))
    
    
@app.route('/adregister', methods=['GET', 'POST'])
def adminregister():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        mobile = request.form['mobile']
        email = request.form['email']
        address = request.form.get('address', '')  # Handle missing address field
        
        # Checking for existing email and mobile
        cursor = mydb.cursor()
        cursor.execute('SELECT email FROM admin WHERE email = %s', (email,))
        email_data = cursor.fetchone()
        
        cursor.execute('SELECT mobile FROM admin WHERE mobile = %s', (mobile,))
        mobile_data = cursor.fetchone()
        
        if email_data:
            flash('Email address already exists')
            return render_template('adminregister.html')
        if mobile_data:
            flash('Mobile number already exists')
            return render_template('adminregister.html')
        
        cursor.close()
        
        # Generate OTP
        otp = adotp()  # Calling the OTP generation function
        subject = 'Admin Registration OTP'
        body = f'Use this OTP to register: {otp}'
        
        # Send OTP via email
        adminsendmail(email, subject, body)
        
        # Render the OTP page and pass the necessary information to the template
        return render_template('adminotp.html', otp=otp, username=username, mobile=mobile, email=email, address=address, password=password)
    
    return render_template('adminregister.html')

@app.route('/adminotp/<adminotp>/<username>/<mobile>/<email>/<password>', methods=['GET', 'POST'])
def adminotp(adminotp, username, mobile, email, password):
    if request.method == 'POST':
        uotp = request.form['adminotp']
        
        if adminotp == uotp: 
            address = request.form.get('address', '')  
            cursor = mydb.cursor()
            lst = [username, mobile, email, password, address]
            query = 'INSERT INTO admin (username, mobile, email, password, address) VALUES (%s, %s, %s, %s, %s)'
            cursor.execute(query, lst)
            mydb.commit()
            cursor.close()
            flash('Admin details registered successfully')
            return redirect(url_for('adminlogin'))
        else:
            flash('Invalid OTP')
            return render_template('adminotp.html', adminotp=adminotp, username=username, mobile=mobile, email=email, password=password)
    
    return render_template('adminotp.html', adminotp=adminotp, username=username, mobile=mobile, email=email, password=password)

 
 
@app.route('/adlogin', methods=['GET', 'POST'])
def adminlogin():
    if session.get('admin'):
        return redirect(url_for('adminhome'))  # Redirect if already logged in
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = mydb.cursor()
        cursor.execute('SELECT count(*) FROM admin WHERE username = %s AND password = %s', [username, password])
        count = cursor.fetchone()[0]
        
        if count == 0:
            flash('Invalid username or password')
            return render_template('adminlogin.html')
        else:
            session['admin'] = username  # Set the session for the logged-in admin
            return redirect(url_for('adminhome'))  # Redirect to the admin homepage
    
    return render_template('adminlogin.html')

@app.route('/adminhome')
def adminhome():
    if session.get('admin'):  
        return render_template('adminhome.html')
    else:
        flash('Please log in first')
        return redirect(url_for('adminlogin'))  

    
@app.route('/adlogout')
def adminlogout():
    if session.get('admin'):
        session.pop('admin')
        flash('Successfully logged out')
        return redirect(url_for('adminlogin'))
    else:
        flash('Already logged out or no admin session found!')
        return redirect(url_for('adminlogin'))

@app.route('/additems',methods=['GET','POST'])
def additems():
    if session.get('admin'):
        if request.method == 'POST':
            name = request.form['name']
            discription = request.form['desc']
            quantity = request.form['qty']
            category=request.form['category']
            price = request.form['price']   
            image=request.files['image']
            valid_categories=['electronics','grocery','fashion','home']
            if category not in valid_categories:
                flash('Invalid category Please select a valid option')
                return render_template('items.html')
            cursor = mydb.cursor()
            idotp=itemidotp()
            filename=idotp+'.jpg'
            cursor.execute('insert into additems(itemid,name,discription,qty,category,price) values(%s,%s,%s,%s,%s,%s)',[idotp,name,discription,quantity,category,price])
            mydb.commit()
            path = os.path.dirname(os.path.abspath(__file__))
            static_path=os.path.join(path,'static')
            image.save(os.path.join(static_path,filename))
            flash('Item added successfuly')
        return render_template('items.html')   
    else:
        return redirect(url_for('adminlogin'))
    
@app.route('/homepage')
def home1():
    return render_template('homepage.html')

@app.route('/dashboard')
def dashboardpage():
    cursor=mydb.cursor()
    cursor.execute('select *from additems')
    items=cursor.fetchall()
    print(items)
    return render_template('dashboard.html',items=items)

@app.route('/status')
def status():
    cursor=mydb.cursor()
    cursor.execute('select * from additems')
    items=cursor.fetchall()
    return render_template('status.html',items=items)

  
@app.route('/updateproducts/<itemid>',methods=['GET','POST'])  
def updateproducts(itemid):
    if session.get('admin'):
        print(itemid)
        cursor=mydb.cursor()
        cursor.execute('select name,discription,qty,category,price from additems where itemid=%s',[itemid])
        items=cursor.fetchone()
        cursor.close()
        if request.method == "POST":
            name = request.form['name']
            discription = request.form['desc']
            quantity = request.form['qty']
            category=request.form['category']
            price = request.form['price']  
            cursor = mydb.cursor()
            cursor.execute('update additems set name =%s, discription=%s,qty=%s,category=%s,price=%s where itemid=%s',[name,discription,quantity,category,price,itemid])
            mydb.commit()
            cursor.close()
            return redirect(url_for('adminhome'))
        return render_template('updateproducts.html',items=items)
    else:
        return redirect(url_for('adminlogin'))

@app.route('/deleteproducts/<itemid>')
def deleteproducts(itemid):
    cursor=mydb.cursor()
    cursor.execute('delete from additems where itemid=%s',[itemid])
    mydb.commit()
    cursor.close()
    path=os.path.dirname(os.path.abspath(__file__))
    static_path=os.path.join(path,'static')
    filename=itemid+'jpg'
    os.remove(os.path.join(static_path,filename))
    flash('deleted')
    return redirect(url_for('status'))

@app.route('/index')
def index():
    cursor = mydb.cursor(buffered=True)
    cursor.execute('SELECT itemid, name, qty, category, price FROM additems')
    item_data = cursor.fetchall()
    print(item_data) 
    return render_template('index.html', item_data=item_data)





@app.route('/addcart/<itemid>/<name>/<category>/<price>/<quantity>',methods=['GET','POST'])
def addcart(itemid,name,category,price,quantity):
    if not session.get('user'):
        return redirect(url_for('login'))
    else:
        print(session)
        if itemid not in session.get(session['user'],{}):
            if session.get(session['user']) is None:
                session[session['user']]={}
            session[session['user']][itemid]=[name,price,1,f'{itemid}.jpg',category]
            session.modified=True
            flash(f'{name} added to cart')
            return '<h2>added to cart</h2>'
        session[session['user']][itemid][2]+=1
        session.modified=True
        flash(f'{name} quantity increased in the cart')
        return '<h2>quantity increased in the cart</h2>'
    
@app.route('/removecart/<itemid>')
def removecart(itemid):
    if session.get('user'):
        session[session.get('user')].pop(itemid)
        session.modified=True
        flash('item Removed')
        return redirect(url_for('viewcart'))
    else:
        return redirect(url_for('login'))
    
@app.route('/viewcart')
def viewcart():
    if not session.get('user'):
        return redirect(url_for('login'))
    user_cart=session.get(session.get('user'))#retrive the cart items from the session
    if not user_cart:
        items='empty'
    else:
        items=user_cart     #fetch the items from the session
    if items=='empty':
        return '<h3> Your cart is empty</h3>'
    return render_template('cart.html',items=items)


    
@app.route('/dis/<itemid>')
def dis(itemid):
    cursor = mydb.cursor()
    cursor.execute('select * from additems where itemid=%s',[itemid])
    items=cursor.fetchone()
    return render_template('discription.html',items=items)

@app.route('/category/<category>',methods=['GET','POST'])
def category(category):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from additems where category=%s',[category] )
        data = cursor.fetchall()
        cursor.close()
        return render_template('categories.html',data=data)
    else:
        return redirect(url_for('login'))
    
#for payment --> id,name,price
@app.route('/pay/<itemid>/<name>/<price>', methods=['POST'])
def pay(itemid, name, price):
    try:
        price = price.replace(',', '') 
        price = int(price)
        qyt = int(request.form.get('qyt', 0))
        if qyt <= 0:
            raise ValueError("Quantity must be greater than zero.")
        
        total_price = price * qyt

        print(f'Creating payment for item: {itemid}, name: {name}, total price: {total_price}')

        order = client.order.create({
            'amount': total_price * 100, 
            'currency': 'INR',
            'payment_capture': '1'
        })
        print(f'Order created: {order}')
        return render_template('pay.html', order=order, itemid=itemid, name=name, price=total_price, qyt=qyt)

    except ValueError as ve:
        print(f'ValueError: {str(ve)}')
        return f'Invalid input: {str(ve)}', 400
    except Exception as e:
        print(f'Error creating order: {str(e)}')
        return str(e), 400

    
@app.route('/success', methods=['POST'])
def success():
    payment_id = request.form.get('razorpay_payment_id')
    order_id = request.form.get('razorpay_order_id')
    signature = request.form.get('razorpay_signature')  
    itemid = request.form.get('itemid')
    total_price = request.form.get('total_price')
    qyt = request.form.get('qyt') 

    
    try:
        qyt = int(qyt) if qyt else 1 
    except ValueError:
        return "Invalid quantity value", 400 
    
    # Verification process
    params_dict = {
        'razorpay_order_id': order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature
    }
    try:
        # Verify payment signature
        client.utility.verify_payment_signature(params_dict)
        
        # Insert order into the database
        cursor = mydb.cursor(buffered=True)
        cursor.execute('INSERT INTO orders (itemid, item_name, total_price, user, qty) VALUES (%s, %s, %s, %s, %s)', 
                       [itemid, itemid, total_price, session.get('user'), qyt])  # Changed 'signature' to 'itemid' for item_name
        mydb.commit()
        cursor.close()
        
        flash('Order placed successfully')
        return 'orders'
    
    except razorpay.errors.SignatureVerificationError as e:
        return f'Payment verification failed! Error: {str(e)}', 400



    
@app.route('/orders')
def orders():
    if session.get('user'):
        user=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from orders where user=%s',[user])
        data=cursor.fetchall()
        cursor.close()
        return render_template('orderdispaly.html',data=data)
    else:
        return redirect(url_for('login'))
    
@app.route('/search',methods=['GET','POST'])
def search():
    if request.method == 'POST':
        name=request.form['search']
        cursor=mydb.cursor()
        cursor.execute('select * from additems where name=%s',[name])
        data=cursor.fetchall()
        return render_template('dashboard.html',items=data)
        
if __name__ == '__main__':
        app.run(debug=True)



        
