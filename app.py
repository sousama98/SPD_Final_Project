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
    conn = get_db_connection()
    
    # Sample queries to get data (replace with actual database logic)
    total_users = conn.execute('SELECT COUNT(*) FROM Users').fetchone()[0]
    active_users = conn.execute('SELECT COUNT(*) FROM Users WHERE last_login > DATE("now", "-7 day")').fetchone()[0]
    # new_messages = conn.execute('SELECT COUNT(*) FROM Messages WHERE status="unread"').fetchone()[0]

    # Top 3 Resources
    top_resources_query = '''
    SELECT title, description, date_posted
    FROM Resources
    ORDER BY date_posted DESC
    LIMIT 3;
    '''
    top_resources = conn.execute(top_resources_query).fetchall()

    # Top 3 Community Events
    top_community_events_query = '''
    SELECT title, description, location, date_posted
    FROM Community
    ORDER BY date_posted DESC
    LIMIT 3;
    '''
    top_community_events = conn.execute(top_community_events_query).fetchall()

    most_active_users_query = '''
    SELECT name, email, COUNT(*) AS activity_count
    FROM Users
    JOIN Resources ON Users.user_id = Resources.user_id
    GROUP BY Users.user_id
    ORDER BY activity_count DESC
    LIMIT 3;
    '''
    most_active_users = conn.execute(most_active_users_query).fetchall()
    
    conn.close()
    return render_template(
        'admin_dashboard.html', user_name=session['user_name'],
        total_users=total_users,
        active_users=active_users,
        top_resources=top_resources,
        top_community_events=top_community_events,
        
        most_active_users=most_active_users
    )




@app.route('/customer_dashboard')
@login_required
def customer_dashboard():
    if 'user_id' not in session or session['role'] != 'Customer':
        return redirect('/login')

    conn = get_db_connection()

    # Fetch the current user's information
    user_id = session['user_id']
    user_name = session['user_name']

    # Query to get top 3 resources listed by the current user
    top_resources_query = '''
    SELECT title, description, date_posted
    FROM Resources
    WHERE user_id = ?
    ORDER BY date_posted DESC
    LIMIT 3;
    '''
    top_resources = conn.execute(top_resources_query, (user_id,)).fetchall()

    # Query to get top 3 community events listed by the current user
    top_community_events_query = '''
    SELECT title, description, location, date_posted
    FROM Community
    WHERE user_id = ?
    ORDER BY date_posted DESC
    LIMIT 3;
    '''
    top_community_events = conn.execute(top_community_events_query, (user_id,)).fetchall()

    # Reserved Resources
    reserved_resources_query = '''
    SELECT title, description, category, date_posted
    FROM Resources
    WHERE user_id = ? AND availability = 'Reserved';
    '''
    reserved_resources = conn.execute(reserved_resources_query, (user_id,)).fetchall()

    # Reserved Communities
    reserved_communities_query = '''
    SELECT title, description, location, date_posted
    FROM Community
    WHERE user_id = ? AND availability = 'Reserved';
    '''
    reserved_communities = conn.execute(reserved_communities_query, (user_id,)).fetchall()

    conn.close()

    return render_template(
        'customer_dashboard.html',
        user_name=user_name,
        top_resources=top_resources,
        top_community_events=top_community_events,
        reserved_resources=reserved_resources,
        reserved_communities=reserved_communities
    )


@app.route('/user_management')
@login_required
def user_management():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM Users').fetchall()
    conn.close()
    return render_template('user_management.html', users=users)



@app.route('/products_listed')
@login_required
def products_listed():
    conn = get_db_connection()
    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 6

    # Search and pagination query
    base_query = '''
    SELECT *
    FROM Resources
    WHERE title LIKE ?
    ORDER BY date_posted DESC
    LIMIT ? OFFSET ?;
    '''
    total_count_query = '''
    SELECT COUNT(*)
    FROM Resources
    WHERE title LIKE ?;
    '''
    params = (f'%{search_query}%',)
    total_count = conn.execute(total_count_query, params).fetchone()[0]
    total_pages = (total_count + per_page - 1) // per_page
    offset = (page - 1) * per_page

    resources = conn.execute(base_query, params + (per_page, offset)).fetchall()
    conn.close()

    return render_template(
        'products_listed.html',
        resources=resources,
        search_query=search_query,
        page=page,
        total_pages=total_pages
    )



@app.route('/community_events')
@login_required
def community_events():
    conn = get_db_connection()
    
    # Fetch search and pagination parameters from the URL
    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 4  # Set to 4 items per page

    # SQL query to search only by title for communities
    base_query = 'SELECT * FROM Community WHERE title LIKE ?'
    count_query = 'SELECT COUNT(*) FROM Community WHERE title LIKE ?'
    params = (f'%{search_query}%',)

    # Get total count for pagination
    total_communities = conn.execute(count_query, params).fetchone()[0]
    total_pages = (total_communities + per_page - 1) // per_page

    # Offset and limit for pagination
    offset = (page - 1) * per_page
    paginated_query = f'{base_query} LIMIT ? OFFSET ?'
    communities_data = conn.execute(paginated_query, params + (per_page, offset)).fetchall()

    conn.close()

    return render_template(
        'community_events.html',
        communities=communities_data,
        search_query=search_query,
        page=page,
        total_pages=total_pages
    )





# @app.route('/customer_messages')
# @login_required
# def customer_messages():
#     # Logic to fetch and display messages from customers
#     return render_template('customer_messages.html')

@app.route('/notifications')
@login_required
def notifications():
    conn = get_db_connection()
    user_id = session['user_id']  # Current user ID

    # Fetch notifications for the current user
    notifications_query = '''
    SELECT notification_id, content, is_read, timestamp
    FROM Notifications
    WHERE user_id = ?
    ORDER BY timestamp DESC;
    '''
    notifications = conn.execute(notifications_query, (user_id,)).fetchall()

    # Mark notifications as read
    mark_as_read_query = '''
    UPDATE Notifications
    SET is_read = 1
    WHERE user_id = ?;
    '''
    conn.execute(mark_as_read_query, (user_id,))
    conn.commit()
    conn.close()

    return render_template('notifications.html', notifications=notifications)


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


@app.route('/reserve_community/<int:community_id>', methods=['POST'])
@login_required
def reserve_community(community_id):
    conn = get_db_connection()
    user_id = session['user_id']  # The user reserving the community

    # Get the community and check availability
    community_query = '''
    SELECT user_id, title, availability
    FROM Community
    WHERE community_id = ?;
    '''
    community = conn.execute(community_query, (community_id,)).fetchone()

    if community:
        if community['availability'] == 'Available':
            # Update the community to mark it as reserved
            reserve_query = '''
            UPDATE Community
            SET availability = 'Reserved'
            WHERE community_id = ?;
            '''
            conn.execute(reserve_query, (community_id,))

            # Optional: Add a notification for the owner of the community
            notification_content = f"Your community '{community['title']}' has been reserved."
            notification_query = '''
            INSERT INTO Notifications (user_id, content)
            VALUES (?, ?);
            '''
            conn.execute(notification_query, (community['user_id'], notification_content))

            conn.commit()
            flash("Community reserved successfully!", "success")
        else:
            flash("Community is already reserved.", "danger")
    else:
        flash("Community not found.", "danger")

    conn.close()
    return redirect(url_for('community_events'))




@app.route('/reserve/<int:resource_id>', methods=['POST'])
@login_required
def reserve_resource(resource_id):
    conn = get_db_connection()
    user_id = session['user_id']  # The user reserving the resource

    # Get the resource and check availability
    resource_query = '''
    SELECT user_id, title, availability
    FROM Resources
    WHERE resource_id = ?;
    '''
    resource = conn.execute(resource_query, (resource_id,)).fetchone()

    if resource:
        if resource['availability'] == 'Available':
            # Update the resource to mark it as reserved
            reserve_query = '''
            UPDATE Resources
            SET availability = 'Reserved'
            WHERE resource_id = ?;
            '''
            conn.execute(reserve_query, (resource_id,))

            # Notify the owner
            notification_content = f"Your resource '{resource['title']}' has been reserved."
            notification_query = '''
            INSERT INTO Notifications (user_id, content)
            VALUES (?, ?);
            '''
            conn.execute(notification_query, (resource['user_id'], notification_content))

            conn.commit()
            flash("Resource reserved successfully!", "success")
        else:
            flash("Resource is already reserved.", "danger")
    else:
        flash("Resource not found.", "danger")

    conn.close()
    return redirect(url_for('products_listed'))



@app.route('/message/<int:resource_id>', methods=['GET', 'POST'])
@login_required
def message_page(resource_id):
    conn = get_db_connection()
    user_id = session['user_id']  # The current user

    # Get the resource and its owner details
    resource_query = '''
    SELECT user_id, title
    FROM Resources
    WHERE resource_id = ?;
    '''
    resource = conn.execute(resource_query, (resource_id,)).fetchone()

    if not resource:
        flash("Resource not found.", "danger")
        conn.close()
        return redirect(url_for('products_listed'))

    owner_id = resource['user_id']
    resource_title = resource['title']

    # Handle message submission
    if request.method == 'POST':
        message_content = request.form['message']

        # Insert the message into the database
        message_query = '''
        INSERT INTO Messages (sender_id, recipient_id, resource_id, content, timestamp)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);
        '''
        
        conn.execute(message_query, (user_id, owner_id, resource_id, message_content))
        conn.commit()

        flash("Message sent successfully!", "success")
        conn.close()
        return redirect(url_for('products_listed'))

    conn.close()
    return render_template('message_page.html', resource_title=resource_title, owner_id=owner_id)

@app.route('/my_messages')
@login_required
def my_messages():
    conn = sqlite3.connect('community.db')
    conn.row_factory = sqlite3.Row  # Enables dictionary-like access
    user_id = session['user_id']  # ID of the currently logged-in user

    # Query to fetch messages
    messages_query = '''
    SELECT m.message_id, 
           m.content, 
           m.timestamp, 
           u.name AS sender_name, 
           u.email AS sender_email,
           r.title AS resource_title
    FROM Messages m
    JOIN Users u ON m.sender_id = u.user_id  -- Join to get sender's name and email
    LEFT JOIN Resources r ON m.resource_id = r.resource_id  -- Join to get resource title (if applicable)
    WHERE m.recipient_id = ?
    ORDER BY m.timestamp DESC;
    '''
    messages = conn.execute(messages_query, (user_id,)).fetchall()
    conn.close()

    return render_template('my_messages.html', messages=messages)


@app.route('/reply_message/<int:message_id>', methods=['POST'])
@login_required
def reply_message(message_id):
    conn = sqlite3.connect('community.db')
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    cursor = conn.cursor()

    # Fetch original message to get the sender as the new receiver
    original_message_query = '''
    SELECT sender_id, resource_id 
    FROM Messages 
    WHERE message_id = ?;
    '''
    original_message = cursor.execute(original_message_query, (message_id,)).fetchone()

    if not original_message:
        flash("Message not found.", "danger")
        return redirect(url_for('my_messages'))

    sender_id = session['user_id']  # Current user replying
    receiver_id = original_message['sender_id']  # The original sender becomes the receiver
    resource_id = original_message['resource_id']  # Keep the associated resource

    # Get the reply content from the form
    reply_content = request.form['reply_content']

    # Insert the reply as a new message
    reply_query = '''
    INSERT INTO Messages (sender_id, recipient_id, resource_id, content, timestamp)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);
    '''
    cursor.execute(reply_query, (sender_id, receiver_id, resource_id, reply_content))
    conn.commit()
    conn.close()

    flash("Your reply has been sent!", "success")
    return redirect(url_for('my_messages'))

@app.route('/message_community/<int:community_id>', methods=['GET', 'POST'])
@login_required
def message_community(community_id):
    conn = get_db_connection()
    user_id = session['user_id']  # The current user

    # Get the community and its owner details
    community_query = '''
    SELECT user_id, title
    FROM Community
    WHERE community_id = ?;
    '''
    community = conn.execute(community_query, (community_id,)).fetchone()

    if not community:
        flash("Community not found.", "danger")
        conn.close()
        return redirect(url_for('community_events'))

    owner_id = community['user_id']
    community_title = community['title']

    # Handle message submission
    if request.method == 'POST':
        message_content = request.form['message']

        # Insert the message into the database
        message_query = '''
        INSERT INTO Messages (sender_id, recipient_id, resource_id, content, timestamp)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);
        '''
        conn.execute(message_query, (user_id, owner_id, community_id, message_content))
        conn.commit()

        flash("Message sent successfully!", "success")
        conn.close()
        return redirect(url_for('community_events'))

    conn.close()
    return render_template('message_page.html', community_title=community_title, owner_id=owner_id)




@app.route('/list_item', methods=['GET', 'POST'])
@login_required
def list_item():
    if request.method == 'POST':
        listing_type = request.form.get('listing_type')

        conn = get_db_connection()
        user_id = session['user_id']

        if listing_type == 'resource':
            # Resource fields
            title = request.form.get('resource_title')
            description = request.form.get('resource_description')
            category = request.form.get('resource_category')
            images = request.files['resource_images']  # File upload handling

            # Save image to static/images folder
            if images:
                image_filename = f"images/{images.filename}"
                images.save(f"static/{image_filename}")
            else:
                image_filename = None

            # Insert resource into database
            resource_query = '''
            INSERT INTO Resources (user_id, title, description, images, category, availability, date_posted)
            VALUES (?, ?, ?, ?, ?, 'Available', CURRENT_TIMESTAMP);
            '''
            conn.execute(resource_query, (user_id, title, description, image_filename, category))
            # Notify the user
            notification_content = f"Your resource '{title}' has been listed successfully."
            notification_query = '''
            INSERT INTO Notifications (user_id, content)
            VALUES (?, ?);
            '''
            conn.execute(notification_query, (user_id, notification_content))

        elif listing_type == 'community':
            # Community fields
            title = request.form.get('community_title')
            description = request.form.get('community_description')
            location = request.form.get('community_location')
            images = request.files['community_images']  # File upload handling

            # Save image to static/images folder
            if images:
                image_filename = f"images/{images.filename}"
                images.save(f"static/{image_filename}")
            else:
                image_filename = None

            # Insert community into database
            community_query = '''
            INSERT INTO Community (user_id, title, description, images, location, availability, date_posted)
            VALUES (?, ?, ?, ?, ?, 'Available', CURRENT_TIMESTAMP);
            '''
            conn.execute(community_query, (user_id, title, description, image_filename, location))
            # Notify the user
            notification_content = f"Your community '{title}' has been listed successfully."
            notification_query = '''
            INSERT INTO Notifications (user_id, content)
            VALUES (?, ?);
            '''
            conn.execute(notification_query, (user_id, notification_content))
        conn.commit()
        conn.close()

        flash("Your listing has been added successfully!", "success")
        return redirect(url_for('customer_dashboard'))

    return render_template('list_item.html')


@app.route('/submit_review', methods=['POST'])
@login_required
def submit_review():
    item_type = request.form['item_type']
    item_id = request.form['item_id']
    rating = request.form['rating']
    review_text = request.form['review_text']
    user_id = session['user_id']

    conn = get_db_connection()

    if item_type == 'resource':
        review_query = '''
        INSERT INTO Reviews (user_id, reviewer_id, rating, comment, timestamp)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);
        '''
        conn.execute(review_query, (item_id, user_id, rating, review_text))

    elif item_type == 'community':
        review_query = '''
        INSERT INTO Reviews (user_id, reviewer_id, rating, comment, timestamp)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);
        '''
        conn.execute(review_query, (item_id, user_id, rating, review_text))

    conn.commit()
    conn.close()

    flash("Review submitted successfully!", "success")
    return redirect(url_for('reviews'))




@app.route('/reviews')
@login_required
def reviews():
    conn = get_db_connection()
    user_id = session['user_id']

    # Fetch reserved resources
    reserved_resources_query = '''
    SELECT resource_id, title, description, category, date_posted
    FROM Resources
    WHERE user_id = ? AND availability = 'Reserved';
    '''
    reserved_resources = conn.execute(reserved_resources_query, (user_id,)).fetchall()

    # Fetch reserved communities
    reserved_communities_query = '''
    SELECT community_id, title, description, location, date_posted
    FROM Community
    WHERE user_id = ? AND availability = 'Reserved';
    '''
    reserved_communities = conn.execute(reserved_communities_query, (user_id,)).fetchall()

    conn.close()

    return render_template(
        'reviews.html',
        reserved_resources=reserved_resources,
        reserved_communities=reserved_communities
    )


@app.route('/reviews_list')
@login_required
def reviews_list():
    conn = get_db_connection()
    query = '''
    SELECT 
        r.rating,
        r.comment,
        r.timestamp,
        u.name AS reviewer_name,
        res.title AS resource_title,
        com.title AS community_title
    FROM Reviews r
    LEFT JOIN Users u ON r.reviewer_id = u.user_id
    LEFT JOIN Resources res ON r.user_id = res.resource_id
    LEFT JOIN Community com ON r.user_id = com.community_id
    ORDER BY r.timestamp DESC;
    '''
    reviews = conn.execute(query).fetchall()
    conn.close()

    return render_template('reviews_list.html', Reviews=reviews)

if __name__ == '__main__':
    app.run(debug=True)
    
