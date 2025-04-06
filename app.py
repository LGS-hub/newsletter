from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder to store uploaded newsletters
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper function to interact with the SQLite database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database (Run this part once to set up the database)
def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS months (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    class_id INTEGER,
                    FOREIGN KEY(class_id) REFERENCES classes(id))''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS newsletters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER,
                    month TEXT,
                    pdf_filename TEXT,
                    FOREIGN KEY(class_id) REFERENCES classes(id))''')
    conn.commit()
    conn.close()

# Uncomment this once to initialize the database
init_db()

# Homepage route
@app.route('/')
def homepage():
    conn = get_db_connection()
    classes = conn.execute('SELECT * FROM classes').fetchall()
    conn.close()
    return render_template('index.html', classes=classes)

# Class page route
@app.route('/class/<int:class_id>')
def class_page(class_id):
    conn = get_db_connection()
    months = conn.execute('SELECT * FROM months WHERE class_id = ?', (class_id,)).fetchall()
    conn.close()
    return render_template('class_page.html', months=months, class_id=class_id)

# Newsletter route
@app.route('/newsletter/<int:class_id>/<month>')
def newsletter(class_id, month):
    conn = get_db_connection()
    newsletter = conn.execute('SELECT * FROM newsletters WHERE class_id = ? AND month = ?', (class_id, month)).fetchone()
    conn.close()
    return render_template('newsletter.html', newsletter=newsletter)

# Admin page to upload classes, months, and newsletters
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # Add a new class
        if 'class_name' in request.form:
            class_name = request.form['class_name']
            conn = get_db_connection()
            conn.execute('INSERT INTO classes (name) VALUES (?)', (class_name,))
            conn.commit()
            conn.close()

        # Add a new month
        elif 'month_name' in request.form:
            month_name = request.form['month_name']
            class_id = request.form['class_id']
            conn = get_db_connection()
            conn.execute('INSERT INTO months (name, class_id) VALUES (?, ?)', (month_name, class_id))
            conn.commit()
            conn.close()

        # Upload newsletter PDF
        elif 'file' in request.files:
            file = request.files['file']
            class_id = request.form['class_id']
            month = request.form['month']
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Save the newsletter details in the database
            conn = get_db_connection()
            conn.execute('INSERT INTO newsletters (class_id, month, pdf_filename) VALUES (?, ?, ?)',
                         (class_id, month, filename))
            conn.commit()
            conn.close()

            return redirect('/admin')

    conn = get_db_connection()
    classes = conn.execute('SELECT * FROM classes').fetchall()
    conn.close()
    return render_template('admin.html', classes=classes)

if __name__ == '__main__':
    app.run(debug=True)

