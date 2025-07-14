from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from PIL import Image
import qrcode
import base64
import uuid
import time
import os
import io

app = Flask(__name__)
app.secret_key = os.urandom(24)


menu_items_data = [
    {"id": "item1", "name": "Burger", "price": 5.99, "description": "Delicious beef burger with fresh lettuce and tomato"},
    {"id": "item2", "name": "Pizza Slice", "price": 3.49, "description": "Crispy pizza slice with cheese and pepperoni"},
    {"id": "item3", "name": "Fries", "price": 2.50, "description": "Golden crispy french fries"},
    {"id": "item4", "name": "Sandwich", "price": 4.25, "description": "Fresh club sandwich with chicken and vegetables"},
    {"id": "item5", "name": "Coke", "price": 1.99, "description": "Chilled coca cola"},
    {"id": "item6", "name": "Coffee", "price": 2.25, "description": "Hot coffee with milk"},
]

orders_data = {}  
order_token_counter = 1001  

def generate_qr_code(token, order_id):
    """Generate QR code for order tracking"""
    try:
        
        qr_data = f"Order ID: {order_id}\nToken: {token}\nCanteen Order System"
        
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

@app.route('/')
def index():
    
    return render_template('index.html', menu_items=menu_items_data)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_id = request.form.get('item_id')
    item_name = request.form.get('item_name')
    try:
        item_price = float(request.form.get('item_price'))
        cart = session.get('cart', {})
        if item_id in cart:
            cart[item_id]['quantity'] += 1
        else:
            cart[item_id] = {'name': item_name, 'price': item_price, 'quantity': 1}
        session['cart'] = cart
    except (ValueError, TypeError):
        
        print(f"Invalid price received for item: {item_name}")

    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', {})
    total_price = sum(item['price'] * item['quantity'] for item in cart_items.values())
    time_slots = [
        '10:00 AM - 10:15 AM', 
        '10:15 AM - 10:30 AM', 
        '10:30 AM - 10:45 AM', 
        '10:45 AM - 11:00 AM',
        '11:00 AM - 11:15 AM',
        '11:15 AM - 11:30 AM'
    ]  
    return render_template('cart.html', cart_items=cart_items, total_price=total_price, time_slots=time_slots)

@app.route('/remove_from_cart/<item_id>')
def remove_from_cart(item_id):
    
    cart = session.get('cart', {})
    if item_id in cart:
        del cart[item_id]
        session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart-data')
def get_cart_data():
    cart_items = session.get('cart', {})
    return jsonify(cart_items)

@app.route('/place_order', methods=['POST'])
def place_order():
    time_slot = request.form.get('time_slot')
    cart_items = session.get('cart', {})

    if not cart_items:
        return redirect(url_for('cart'))  
    
    if not time_slot:
        return redirect(url_for('cart'))  

    
    total_price = sum(item['price'] * item['quantity'] for item in cart_items.values())

    
    order_id = str(uuid.uuid4())
    
    
    global order_token_counter
    token = order_token_counter
    order_token_counter += 1

    
    qr_code_data = generate_qr_code(token, order_id)

    order_data = {
        'order_items': cart_items,
        'total': total_price,
        'timeSlot': time_slot,
        'token': token,
        'status': 'pending',
        'timestamp': int(time.time()),
        'order_id': order_id,
        'qr_code': qr_code_data
    }

    
    orders_data[order_id] = order_data
    session['cart'] = {}  

    return redirect(url_for('confirmation', token=token))

@app.route('/confirmation/<int:token>')
def confirmation(token):
    
    order = next((o for o in orders_data.values() if o.get('token') == token), None)

    if not order:
        return redirect(url_for('index'))  

    estimated_time = "15-20 minutes"  

    return render_template('confirmation.html', token=token, order=order, estimated_time=estimated_time)

@app.route('/admin')
def admin():
    
    sorted_orders = dict(sorted(orders_data.items(), key=lambda x: x[1]['timestamp'], reverse=True))
    return render_template('admin.html', orders=sorted_orders)

@app.route('/order_status/<int:token>')
def order_status(token):
    """API endpoint to get order status for real-time updates"""
    order = next((o for o in orders_data.values() if o.get('token') == token), None)
    if order:
        return jsonify({
            'status': order['status'],
            'token': token,
            'estimated_time': "15-20 minutes" if order['status'] == 'pending' else "Ready for pickup!"
        })
    return jsonify({'error': 'Order not found'}), 404

@app.route('/mark_ready/<order_id>')
def mark_ready(order_id):
    
    if order_id in orders_data:
        orders_data[order_id]['status'] = 'ready'
        print(f"Order {order_id} marked as ready.")
    else:
        print(f"Order {order_id} not found.")

    return redirect(url_for('admin'))

if __name__ == '__main__':
    
    
    app.run(debug=True)
