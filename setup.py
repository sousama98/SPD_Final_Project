import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('community.db')
cursor = conn.cursor()

# Create Users table with a role column
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        profile_image TEXT,
        location TEXT,
        role TEXT DEFAULT 'User',  -- Role column to distinguish between Admin and User
        date_created TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

# Create Resources table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Resources (
        resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        images TEXT,
        category TEXT,
        availability TEXT,
        date_posted TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
    )
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS Community (
    community_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    images TEXT,
    location TEXT,  -- Changed from category to location
    availability TEXT,
    date_posted TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
)
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (sender_id) REFERENCES Users(user_id),
        FOREIGN KEY (receiver_id) REFERENCES Users(user_id)
    )
''')

# Create Reviews table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        reviewer_id INTEGER,
        rating INTEGER NOT NULL,
        comment TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users(user_id),
        FOREIGN KEY (reviewer_id) REFERENCES Users(user_id)
    )
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS Notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, -- The user who will receive the notification
    content TEXT NOT NULL, -- The notification message
    is_read INTEGER DEFAULT 0, -- Flag to indicate if the notification is read
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP, -- When the notification was created
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
''')
# # Insert the records
# cursor.execute('''
#     INSERT INTO Users (name, email, password, role) 
#     VALUES ('Sourabrata Samanta', 'sourabrata@example.com', 'adminpassword', 'Admin')
# ''')

# cursor.execute('''
#     INSERT INTO Users (name, email, password, role) 
#     VALUES ('Nikhil Sista', 'nikhil@example.com', 'customerpassword', 'Customer')
# ''')

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and tables created successfully.")
