import random

from flask import Flask, render_template, request
import sqlite3 as sql
import hashlib

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'

current_email = ''

@app.route('/main', methods=['GET'])
def main_page():
    return render_template('main.html')

@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        global current_email
        current_email = email
        result = valid_login(email, password)
        if result:
            return render_template('main.html')
        else:
            return render_template('index.html', error='Invalid email or password')
    return render_template('index.html')

@app.route('/sell', methods=['GET'])
def sell_page():
    result = categories()
    return render_template('sell.html', error=result)

@app.route('/info', methods=['GET'])
def info_page():
    result = get_user_info(current_email)
    return render_template('info.html', error=result)

def valid_login(email, password):
    connection = sql.connect('identifier.sqlite')
    cursor = connection.execute('SELECT password FROM Users WHERE email = (?);', (email,))
    connection.commit()
    result = cursor.fetchone()

    if result is not None and hashlib.sha256(password.encode('utf-8')).hexdigest() == result[0]:
        return True
    return False

def get_user_info(email):
    connection = sql.connect('identifier.sqlite')

    cursor = connection.execute('SELECT Users.email, '
                                'Buyers.first_name, Buyers.last_name, Buyers.gender, Buyers.age, '
                                'Home.street_num, Home.street_name, Home_Zip.city, Home_Zip.state_id, Home.zipcode, '
                                'Billing.street_num, Billing.street_name, Billing_Zip.city, Billing_Zip.state_id, Billing.zipcode, Credit_Cards.credit_card_num '
                                'FROM Users '
                                'INNER JOIN Buyers ON Users.email = Buyers.email '
                                'INNER JOIN Address Home ON Buyers.home_address_id = Home.address_id '
                                'INNER JOIN Address Billing ON Buyers.billing_address_id = Billing.address_id '
                                'INNER JOIN Zipcode_Info Home_Zip on Home.zipcode = Home_Zip.zipcode '
                                'INNER JOIN Zipcode_Info Billing_Zip on Billing.zipcode = Billing_Zip.zipcode '
                                'INNER JOIN Credit_Cards ON Buyers.email = Credit_Cards.owner_email '
                                'WHERE Buyers.email = (?);',(email,))
    result = cursor.fetchone()
    return result

@app.route('/info', methods=['POST', 'GET'])
def change_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        connection = sql.connect('identifier.sqlite')
        cursor = connection.execute('UPDATE Users SET password = (?) WHERE email = (?);', (hashlib.sha256(new_password.encode('utf-8')).hexdigest(), current_email))
        connection.commit()
        return render_template('info.html', error=get_user_info(current_email))
    return render_template('info.html')

@app.route('/products', methods=['GET'])
def products():
    connection = sql.connect('identifier.sqlite')
    cursor = connection.execute(
        'SELECT Product_Listing.title, Product_Listing.product_name, Product_Listing.product_description, Product_Listing.price, Product_Listing.quantity, Product_Listing.category, Product_Listing.seller_email FROM Product_Listing')
    result = cursor.fetchall()
    return render_template('products.html', error=result)

@app.route('/subcategory', methods=['POST', 'GET'])
def filter_products():
    connection = sql.connect('identifier.sqlite')
    if request.method == 'POST':
        cursor = connection.execute('SELECT category_name FROM Categories WHERE parent_category = (?);',
                                    (request.form['category1'],))
        result = cursor.fetchall()
        cursor = connection.execute(
            'SELECT Product_Listing.title, Product_Listing.product_name, Product_Listing.product_description, Product_Listing.price, Product_Listing.quantity, Product_Listing.category, Product_Listing.seller_email '
            'FROM Product_Listing WHERE category = (?);', (request.form['category1'],))
        error = cursor.fetchall()
        return render_template('subcategory.html', result=result, error=error)
    return render_template('subcategory.html')

@app.route('/subsub', methods=['POST', 'GET'])
def filter_subcategory():
    connection = sql.connect('identifier.sqlite')
    if request.method == 'POST':
        cursor = connection.execute('SELECT category_name FROM Categories WHERE parent_category = (?);',
                                    (request.form['category2'],))
        result = cursor.fetchall()
        cursor = connection.execute(
            'SELECT Product_Listing.title, Product_Listing.product_name, Product_Listing.product_description, Product_Listing.price, Product_Listing.quantity, Product_Listing.category, Product_Listing.seller_email '
            'FROM Product_Listing WHERE category = (?);', (request.form['category2'],))
        error = cursor.fetchall()
        return render_template('subsub.html', result=result, error=error)
    return render_template('subsub.html')


@app.route('/catresult', methods=['POST', 'GET'])
def final_filter():
    connection = sql.connect('identifier.sqlite')
    cursor = connection.execute('SELECT Product_Listing.title, Product_Listing.product_name, Product_Listing.product_description, Product_Listing.price, Product_Listing.quantity, Product_Listing.category, Product_Listing.seller_email '
                                'FROM Product_Listing WHERE category = (?);', (request.form['category3'],))
    result = cursor.fetchall()
    return render_template('catresult.html', error=result)

def categories():
    connection = sql.connect('identifier.sqlite')
    cursor = connection.execute('SELECT category_name FROM Categories')
    result = cursor.fetchall()
    return result

def generate_id():
    id = random.randint(1, 1000000)
    connection = sql.connect('identifier.sqlite')
    cursor = connection.execute('SELECT listing_id FROM Product_Listing WHERE listing_id = (?);', (id,))
    result = cursor.fetchall()
    if result:
        generate_id()
    else:
        return id

@app.route('/sell', methods=['POST', 'GET'])
def add_product():
    connection = sql.connect('identifier.sqlite')
    if request.method == 'POST':
        title = request.form['title']
        product_name = request.form['productname']
        product_description = request.form['productdesc']
        price = request.form['price']
        quantity = request.form['quantity']
        category = request.form['sellcat']
        product_id = generate_id()
        seller_email = current_email
        connection.execute('INSERT INTO Product_Listing (listing_id, title, product_name, product_description, price, quantity, category, seller_email) VALUES (?, ?, ?, ?, ?, ?, ?, ?);',
                           (product_id, title, product_name, product_description, price, quantity, category, seller_email))
        connection.commit()
        return render_template('products.html')
    return render_template('products.html')

@app.route('/mylistings', methods=['POST', 'GET'])
def my_listings():
    connection = sql.connect('identifier.sqlite')
    cursor = connection.execute('SELECT Product_Listing.listing_id, Product_Listing.title, Product_Listing.product_name, Product_Listing.product_description, Product_Listing.price, Product_Listing.quantity, Product_Listing.category, Product_Listing.seller_email '
                                'FROM Product_Listing WHERE seller_email = (?);', (current_email,))
    result = cursor.fetchall()
    if request.method == 'POST':
        connection.execute('DELETE FROM Product_Listing WHERE listing_id = (?);', (request.form['id'],))
        connection.commit()
        return render_template('mylistings.html', error=result)
    return render_template('mylistings.html', error=result)

if __name__ == "__main__":
    app.run()
