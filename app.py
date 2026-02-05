from flask import Flask, render_template, request
import joblib
import re
from database import get_connection, create_table
from flask import redirect
from flask import session
from flask import jsonify
from datetime import datetime




app = Flask(__name__)
app.secret_key = "super_secret_admin_key"

create_table()
# =========================
# LOAD TRAINED ML MODELS
# =========================
tfidf = joblib.load("models/tfidf.pkl")
category_model = joblib.load("models/category_model.pkl")
urgency_model = joblib.load("models/urgency_model.pkl")
category_encoder = joblib.load("models/category_encoder.pkl")
urgency_encoder = joblib.load("models/urgency_encoder.pkl")

# =========================
# TEXT CLEANING
# =========================
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text

# =========================
# ML ANALYSIS FUNCTION
# =========================
def analyze_complaint(text):
    cleaned = clean_text(text)
    vec = tfidf.transform([cleaned])

    cat_pred = category_model.predict(vec)[0]
    urg_pred = urgency_model.predict(vec)[0]

    category = category_encoder.inverse_transform([cat_pred])[0]
    urgency = urgency_encoder.inverse_transform([urg_pred])[0]

    priority = "Immediate" if urgency == "High" else "Normal"

    return category, urgency, priority

# =========================
# ROUTES
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # HARD-CODED ADMIN (OK FOR NOW)
        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            return redirect("/admin")
        else:
            error = "Invalid credentials"

    return render_template("login.html", error=error)
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        email = request.form["email"]
        complaint = request.form["complaint"]

        # ML analysis (backend only)
        category, urgency, priority = analyze_complaint(complaint)

        # Timestamp
        created_at = datetime.now().isoformat()

        # Save to DB
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO complaints
            (email, complaint, category, urgency, priority, status, created_at, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (email, complaint, category, urgency, priority, "Pending", created_at, None)
        )

        conn.commit()
        conn.close()

        result = "Complaint submitted successfully. Our team will review it."

    return render_template("index.html", result=result)

@app.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, status, COUNT(*) 
        FROM complaints 
        GROUP BY category, status
    """)
    raw_stats = cursor.fetchall()

    stats = {}
    for category, status, count in raw_stats:
        if category not in stats:
            stats[category] = {"Resolved": 0, "Pending": 0}
        stats[category][status] = count

    cursor.execute("SELECT * FROM complaints ORDER BY id DESC")
    complaints = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        stats=stats,
        complaints=complaints
    )



    
@app.route("/update_status/<int:cid>")
def update_status(cid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE complaints SET status='Resolved' WHERE id=?",
        (cid,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/acknowledge/<int:cid>", methods=["POST"])
def acknowledge(cid):
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Unauthorized"}), 403

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE complaints SET status='Resolved' WHERE id=?",
        (cid,)
    )

    conn.commit()
    conn.close()

    return jsonify({"success": True})



# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run()
