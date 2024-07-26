from flask import Flask, request, redirect, render_template, make_response, url_for, session, flash
import sqlite3
import os
import subprocess

app = Flask(__name__)
app.secret_key = 'secret'  # Required for session management and flash messages

# Database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the uploads and video folders
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def check_login():
    username = session.get('user')
    user_id = session.get('id')
    if username and user_id:
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            # Vulnerable SQL query with SQL Injection
            cursor.execute(f"SELECT * FROM users WHERE username='{username}' AND id='{user_id}'")
            user = cursor.fetchone()
            if user:
                return user
        except Exception as e:
            print(f"Error: {e}")
        finally:
            connection.close()
    return None


@app.route('/')
def home():
    user = check_login()
    return render_template('home.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            # Vulnerable SQL query with SQL Injection
            cursor.execute(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")
            user = cursor.fetchone()
            if user:
                session['user'] = user['username']
                session['id'] = user['id']
                session['role'] = user['role']  # Ensure role is set in session
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password', 'danger')
                return redirect(url_for('login'))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            connection.close()
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            # Vulnerable SQL query with SQL Injection
            cursor.execute(f"INSERT INTO users (email, username, password) VALUES ('{email}', '{username}', '{password}')")
            connection.commit()
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            connection.close()
    return render_template('signup.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = check_login()
    if not user:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
                # Update the user profile with the uploaded image filename (not checked)
                try:
                    connection = get_db_connection()
                    cursor = connection.cursor()
                    # Vulnerable SQL query with SQL Injection
                    cursor.execute(f"UPDATE users SET file = '{image.filename}' WHERE id = '{user['id']}'")
                    connection.commit()
                except Exception as e:
                    print(f"Error: {e}")
                finally:
                    connection.close()

        if 'password' in request.form:
            new_password = request.form['password']
            try:
                connection = get_db_connection()
                cursor = connection.cursor()
                # Vulnerable SQL query with SQL Injection
                cursor.execute(f"UPDATE users SET password = '{new_password}' WHERE id = '{user['id']}'")
                connection.commit()
            except Exception as e:
                print(f"Error: {e}")
            finally:
                connection.close()

        email = request.form.get('email')
        username = request.form.get('username')
        if email and username:
            try:
                connection = get_db_connection()
                cursor = connection.cursor()
                # Vulnerable SQL query with SQL Injection
                cursor.execute(f"UPDATE users SET email = '{email}', username = '{username}' WHERE id = '{user['id']}'")
                connection.commit()
            except Exception as e:
                print(f"Error: {e}")
            finally:
                connection.close()            

    return render_template('profile.html', user=user)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    user = check_login()
    command_output = ''
    if user and user['role'] == 'admin':
        users = []
        if request.method == 'POST':
            if 'delete_users' in request.form:
                try:
                    connection = get_db_connection()
                    cursor = connection.cursor()
                    # Vulnerable SQL query with SQL Injection
                    cursor.execute("DELETE FROM users")
                    connection.commit()
                except Exception as e:
                    print(f"Error: {e}")
                finally:
                    connection.close()
            elif 'update_user' in request.form:
                user_id = request.form['user_id']
                email = request.form['email']
                username = request.form['username']
                try:
                    connection = get_db_connection()
                    cursor = connection.cursor()
                    # Vulnerable SQL query with SQL Injection
                    cursor.execute(f"UPDATE users SET email='{email}', username='{username}' WHERE id='{user_id}'")
                    connection.commit()
                except Exception as e:
                    print(f"Error: {e}")
                finally:
                    connection.close()
            elif 'execute_command' in request.form:
                command = request.form['command']
                try:
                    # Execute command and capture output
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    command_output = result.stdout + result.stderr
                except Exception as e:
                    command_output = str(e)

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            # Vulnerable SQL query with SQL Injection
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            connection.close()
        return render_template('admin.html', users=users, user=user, command_output=command_output)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('id', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists('database.db'):
        # Initialize database if it does not exist
        connection = get_db_connection()
        # Create table for users if it doesn't exist
        with connection:
            connection.execute('''CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                username TEXT,
                password TEXT,
                role TEXT,
                file TEXT
            )''')
        connection.close()

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True)
