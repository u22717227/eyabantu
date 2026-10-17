import os
import pymysql
from pymysql.cursors import DictCursor
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash

bp = Blueprint("main", __name__)

def get_db():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DB", "eyabantu"),
        cursorclass=DictCursor,
        autocommit=True
    )

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("main.dashboard"))
        
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@bp.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT r.*, 
                   COUNT(DISTINCT CASE WHEN t.status = 'en_route' THEN t.id END) AS active_taxis,
                   COUNT(DISTINCT CASE WHEN t.status = 'loading' THEN t.id END) AS loading_taxis
            FROM routes r
            LEFT JOIN taxis t ON r.id = t.route_id
            GROUP BY r.id
        """)
        routes = cur.fetchall()

        cur.execute("""
            SELECT rs.route_id, rs.seq, rs.km_from_start, s.id AS stop_id, s.name, s.lat, s.lng, s.is_rank,
                   ROUND(AVG(sc.rating), 1) AS safety_score,
                   COUNT(DISTINCT dp.id) AS recent_demand
            FROM route_stops rs
            JOIN stops s ON rs.stop_id = s.id
            LEFT JOIN safety_confirmations sc ON s.id = sc.stop_id
            LEFT JOIN demand_pins dp ON s.id = dp.stop_id AND rs.route_id = dp.route_id
            GROUP BY rs.route_id, rs.seq, rs.km_from_start, s.id, s.name, s.lat, s.lng, s.is_rank
            ORDER BY rs.route_id, rs.seq
        """)
        stops = cur.fetchall()

        cur.execute("""
            SELECT t.*, r.code AS route_code, r.name AS route_name, u.name AS driver_name
            FROM taxis t
            LEFT JOIN routes r ON t.route_id = r.id
            LEFT JOIN users u ON t.driver_id = u.id
        """)
        taxis = cur.fetchall()

        driver_taxi = None
        if session.get("role") == "driver":
            cur.execute("SELECT * FROM taxis WHERE driver_id = %s", (session["user_id"],))
            driver_taxi = cur.fetchone()

    conn.close()
    return render_template("dashboard.html", routes=routes, stops=stops, taxis=taxis, driver_taxi=driver_taxi)

@bp.route("/pin", methods=["POST"])
def add_pin():
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    
    route_id = request.form.get("route_id")
    stop_id = request.form.get("stop_id")
    pin_type = request.form.get("pin_type", "pickup")

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO demand_pins (user_id, route_id, stop_id, pin_type) VALUES (%s, %s, %s, %s)",
            (session["user_id"], route_id, stop_id, pin_type)
        )
    conn.close()
    flash("Demand pin dropped successfully.", "success")
    return redirect(url_for("main.dashboard"))

@bp.route("/rate", methods=["POST"])
def rate_stop():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    stop_id = request.form.get("stop_id")
    rating = request.form.get("rating")

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO safety_confirmations (user_id, stop_id, rating) VALUES (%s, %s, %s)",
            (session["user_id"], stop_id, rating)
        )
    conn.close()
    flash("Safety rating submitted.", "success")
    return redirect(url_for("main.dashboard"))

@bp.route("/taxi/status", methods=["POST"])
def update_taxi_status():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    status = request.form.get("status")
    taxi_id = request.form.get("taxi_id")

    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("UPDATE taxis SET status = %s WHERE id = %s", (status, taxi_id))
    conn.close()
    flash("Taxi status updated.", "info")
    return redirect(url_for("main.dashboard"))