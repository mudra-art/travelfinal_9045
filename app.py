from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# ================= LOAD ENV =================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "dev-secret-key"  # ✅ FIX

# ================= MYSQL CONNECTION =================
def get_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT", 3306))
    )

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html", user=session.get("user"))

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT user_id FROM users WHERE email=%s",
            (email,)
        )
        if cursor.fetchone():
            cursor.close()
            db.close()
            return "Email already exists"

        sql = """
        INSERT INTO users (username, email, password)
        VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (username, email, hashed_password))
        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for("login"))

    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )
        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = user["username"]
            session["user_id"] = user["user_id"]
            return redirect(url_for("home"))
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

# ================= BOOKING =================
@app.route("/booking", methods=["GET", "POST"])
def booking():
    if "user_id" not in session:                      # ✅ FIX
        return redirect(url_for("login"))

    if request.method == "POST":
        destination = request.form.get("destination")
        travel_date = request.form.get("date")
        travelers = int(request.form.get("travelers"))  # ✅ FIX

        db = get_db()
        cursor = db.cursor()

        sql = """
        INSERT INTO bookings (user_id, destination, travel_date, travelers)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(
            sql,
            (session["user_id"], destination, travel_date, travelers)
        )
        db.commit()

        cursor.close()
        db.close()

        return f"""
        <h2>Booking Successful ✅</h2>
        <p><b>Destination:</b> {destination}</p>
        <p><b>Date:</b> {travel_date}</p>
        <p><b>Travelers:</b> {travelers}</p>
        <a href="/booking">Book Again</a>
        """

    return render_template("booking.html")

# ================= CONTACT =================
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)",
            (name, email, message)
        )
        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for("home"))

    return render_template("contactus.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
