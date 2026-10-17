import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pymysql
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASS = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_TEST_DB" if "--test" in sys.argv else "MYSQL_DB", "eyabantu")

def execute_schema(cursor):
    with open(ROOT / "db" / "schema.sql", "r") as f:
        sql_file = f.read().replace("eyabantu", DB_NAME)
    for statement in sql_file.split(";"):
        if statement.strip():
            cursor.execute(statement)

def seed_data(cursor):
    pw_hash = generate_password_hash("Demo1234!", method="pbkdf2:sha256")
    
    cursor.execute("INSERT INTO associations (name, region) VALUES ('Tshwane Transit', 'Gauteng')")
    assoc_id = cursor.lastrowid

    users = [
        ("Commuter", "commuter@eyabantu.test", pw_hash, "commuter", None),
        ("Association Admin", "association@eyabantu.test", pw_hash, "association", assoc_id)
    ]
    for i in range(1, 21):
        users.append((f"Driver {i}", f"driver{i}@eyabantu.test", pw_hash, "driver", None))
    
    cursor.executemany("INSERT INTO users (name, email, password_hash, role, association_id) VALUES (%s, %s, %s, %s, %s)", users)
    
    stops = [
        ("Pretoria CBD Rank", -25.7461, 28.1881, True), ("Hatfield Plaza", -25.7480, 28.2376, False),
        ("Brooklyn Mall", -25.7718, 28.2368, False), ("Menlyn Park", -25.7825, 28.2754, True),
        ("Mamelodi West", -25.7135, 28.3687, True), ("Mamelodi East", -25.7001, 28.4010, False),
        ("Silverton", -25.7275, 28.3031, False), ("Lynnwood", -25.7661, 28.2831, False),
        ("Centurion Mall", -25.8605, 28.1873, True), ("Irene", -25.8752, 28.2131, False),
        ("Sunnyside", -25.7533, 28.2039, False), ("Arcadia", -25.7441, 28.2110, False),
        ("Garsfontein", -25.7950, 28.3000, False), ("Faerie Glen", -25.7850, 28.3200, False),
        ("Equestria", -25.7550, 28.3400, False), ("Waterkloof", -25.7800, 28.2400, False)
    ]
    cursor.executemany("INSERT INTO stops (name, lat, lng, is_rank) VALUES (%s, %s, %s, %s)", stops)

    routes = [
        (assoc_id, "R1", "Mamelodi to Menlyn", 25.00, 35.0, True),
        (assoc_id, "R2", "Pretoria CBD to Hatfield", 18.00, 25.0, True),
        (assoc_id, "R3", "Centurion to Pretoria CBD", 30.00, 45.0, False),
        (assoc_id, "R4", "Silverton to Menlyn", 22.00, 40.0, True)
    ]
    cursor.executemany("INSERT INTO routes (association_id, code, name, fare_zar, avg_speed_kmh, in_open_dataset) VALUES (%s, %s, %s, %s, %s, %s)", routes)

    route_stops = [
        (1, 1, 5, 0.0), (1, 2, 6, 4.2), (1, 3, 7, 12.5), (1, 4, 8, 16.0), (1, 5, 4, 21.3),
        (2, 1, 1, 0.0), (2, 2, 11, 2.1), (2, 3, 12, 3.5), (2, 4, 2, 6.8),
        (3, 1, 9, 0.0), (3, 2, 10, 5.5), (3, 3, 1, 18.2),
        (4, 1, 7, 0.0), (4, 2, 15, 6.1), (4, 3, 14, 10.5), (4, 4, 13, 14.2), (4, 5, 4, 19.0)
    ]
    cursor.executemany("INSERT INTO route_stops (route_id, seq, stop_id, km_from_start) VALUES (%s, %s, %s, %s)", route_stops)

    taxis = []
    driver_id = 3
    for route_id in range(1, 5):
        for _ in range(5):
            status = random.choices(["en_route", "loading", "off_duty"], weights=[60, 30, 10])[0]
            taxis.append((f"GP-{random.randint(100,999)}-TX", driver_id, route_id, True, status, 15))
            driver_id += 1
    cursor.executemany("INSERT INTO taxis (registration, driver_id, route_id, sharing_gps, status, capacity) VALUES (%s, %s, %s, %s, %s, %s)", taxis)

    now = datetime.utcnow()
    gps_pings = []
    for taxi_id in range(1, 21):
        gps_pings.append((taxi_id, -25.7461 + random.uniform(-0.05, 0.05), 28.1881 + random.uniform(-0.05, 0.05), now - timedelta(minutes=random.randint(0, 10))))
    cursor.executemany("INSERT INTO gps_pings (taxi_id, lat, lng, created_at) VALUES (%s, %s, %s, %s)", gps_pings)

    demand_pins, safety_ratings = [], []
    for _ in range(10000):
        route_id = random.randint(1, 4)
        stop_id = random.choice([rs[2] for rs in route_stops if rs[0] == route_id])
        created = now - timedelta(days=random.randint(0, 119), minutes=random.randint(0, 1440))
        demand_pins.append((1, route_id, stop_id, 'pickup', created))
        if random.random() > 0.8:
            safety_ratings.append((1, stop_id, None, random.randint(2, 5), created + timedelta(minutes=30)))

    cursor.executemany("INSERT INTO demand_pins (user_id, route_id, stop_id, pin_type, created_at) VALUES (%s, %s, %s, %s, %s)", demand_pins)
    cursor.executemany("INSERT INTO safety_confirmations (user_id, stop_id, taxi_id, rating, created_at) VALUES (%s, %s, %s, %s, %s)", safety_ratings)

def main():
    conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, autocommit=True)
    with conn.cursor() as cur:
        print(f"Executing schema and seeding data into '{DB_NAME}'...")
        execute_schema(cur)
        seed_data(cur)
        print("Database seeded successfully.")
    conn.close()

if __name__ == "__main__":
    main()