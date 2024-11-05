from flask import Flask, request, render_template, redirect, session, url_for , flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to the database
def get_db_connection():
    conn = sqlite3.connect('community.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            session['user_name'] = user['name']  # For personalized greeting

            if user['role'] == 'Admin':
                return redirect('/admin_dashboard')
            elif user['role'] == 'Customer':
                return redirect('/customer_dashboard')
        else:
            error_message = "Invalid email or password"
            return render_template('login.html', error_message=error_message)

    return render_template('login.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect('/login')
    return render_template('admin_dashboard.html', user_name=session['user_name'])

@app.route('/customer_dashboard')
@login_required
def customer_dashboard():
    if 'user_id' not in session or session['role'] != 'Customer':
        return redirect('/login')
    return render_template('customer_dashboard.html', user_name=session['user_name'], user_location='City, Country', user_email='nikhil@example.com')

@app.route('/user_management')
@login_required
def user_management():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM Users').fetchall()
    conn.close()
    return render_template('user_management.html', users=users)

@app.route('/reviews')
@login_required
def reviews():
    # Connect to the database
    conn = get_db_connection()
    
    # Query to select reviewer_id, comment, timestamp, and rating from Reviews table
    reviews_data = conn.execute('''
        SELECT reviewer_id, comment, timestamp, rating
        FROM Reviews
    ''').fetchall()
    
    # Close the database connection
    conn.close()
    
    # Render the reviews page with the reviews data
    return render_template('reviews.html', reviews=reviews_data)

@app.route('/products_listed')
@login_required
def products_listed():
    # Logic to fetch and display listed products
    return render_template('products_listed.html')

@app.route('/community_events')
@login_required
def community_events():
    # Logic to fetch and display community events
    return render_template('community_events.html')

@app.route('/customer_messages')
@login_required
def customer_messages():
    # Logic to fetch and display messages from customers
    return render_template('customer_messages.html')

@app.route('/notifications')
@login_required
def notifications():
    # Logic to display notifications
    return render_template('notifications.html')

@app.route('/profile')
@login_required
def profile():
    # Logic to display user profile
    return render_template('profile.html')

@app.route('/edit_user', methods=['POST'])
def edit_user():
    user_id = request.form['user_id']
    name = request.form['name']
    email = request.form['email']
    location = request.form['location']
    role = request.form['role']

    conn = get_db_connection()
    conn.execute('UPDATE Users SET name = ?, email = ?, location = ?, role = ? WHERE user_id = ?',
                 (name, email, location, role, user_id))
    conn.commit()
    conn.close()

    # Optional: Flash a success message
    flash("User details updated successfully.")
    
    return redirect(url_for('user_management'))

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return f"Deleted user with ID: {user_id}"


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        email = request.form['email']
        password = request.form['password']

        # Insert new user as a 'Customer' role into Users table
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO Users (name, location, email, password, role) VALUES (?, ?, ?, ?, ?)',
                         (name, location, email, password, 'Customer'))
            conn.commit()
            flash('Sign-up successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email.', 'danger')
        finally:
            conn.close()

    return render_template('signup.html')


if __name__ == '__main__':
    app.run(debug=True)


