from flask import Flask, render_template, send_file, request, redirect, url_for, session, make_response
import qrcode
import os
import sqlite3
from io import BytesIO

app = Flask(__name__)
app.config["SECRET_KEY"] = "super secret key"

#Database Initialization
DATABASE = os.path.join(app.root_path, "student.db")
app.config["DATABASE"] = DATABASE

def get_db():
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    return db

def create_tables():
    try:
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    qr_code BLOB
                )
            """)
            db.commit()
            print("Tables created successfully.")
    except sqlite3.Error as e:
        print("SQLite error:", e)

# Calling the function to create tables
create_tables()

# QR Code Generation
def generate_qr_code(student_id):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(student_id)
    qr.make(fit=True)

    qr_code_image = qr.make_image(fill_color="black", back_color="white")

    # Convert the QR code image to bytes
    img_bytes = BytesIO()
    qr_code_image.save(img_bytes, format="PNG")
    return img_bytes.getvalue()

# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        student_id = request.form["student_id"].strip()

        # Check if student_id is not empty
        if student_id:
            try:
                student_id = int(student_id)
                student_name = request.form["student_name"]
                db = get_db()
                cursor = db.cursor()
                
                # Generate and store the QR code image in the database
                qr_code_data = generate_qr_code(str(student_id))
                cursor.execute("INSERT INTO students (id, name, qr_code) VALUES (?, ?, ?)", (student_id, student_name, qr_code_data))
                db.commit()
                
                # Set the student_id in the session
                session["student_id"] = student_id
                
                # Redirect to the home page after a successful registration
                return redirect(url_for("home"))
                
            except ValueError:
                error_message = "Invalid student ID. Please enter a valid integer."
                print("Error:", error_message)
        else:
            error_message = "Student ID cannot be empty."
            print("Error:", error_message)

        return render_template("register.html", error_message=error_message)

    return render_template("register.html")

# Home Route
@app.route("/")
def home():
    return render_template("home.html")

# QR Code Route
@app.route("/qr_code")
def qr_code():
    # Retrieve the student_id from the session
    student_id = session.get("student_id")
    if student_id:
        # Retrieve the student name from the database
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM students WHERE id = ?", (student_id,))
        student_name = cursor.fetchone()
        
        if student_name:
            return render_template("qr_code.html", student_id=student_id, student_name=student_name[0])
    
    return "QR Code not found!"

# Download QR Code Route
@app.route("/download_qr_code/<int:student_id>")
def download_qr_code(student_id):
    # Retrieve student name from the database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM students WHERE id = ?", (student_id,))
    student_name = cursor.fetchone()

    if student_name:
        # Generate QR code image for the student ID
        qr_code_image = generate_qr_code(str(student_id))

        # Send the QR code image as a response for download
        response = make_response(qr_code_image)
        response.headers["Content-Type"] = "image/png"
        response.headers["Content-Disposition"] = f"attachment; filename=qr_code_{student_id}.png"
        return response
    else:
        return "Student not found!"

if __name__ == "__main__":
    app.run(debug=True)
