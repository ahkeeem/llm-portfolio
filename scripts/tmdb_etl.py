import os
import json
import sqlite3
import requests
from datetime import datetime

# 1. Fetch Data
def fetch_tmdb_data(api_key=None):
    if not api_key:
        print("ℹ️ No TMDB_API_KEY provided. Using local sample dataset.")
        sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "tmdb_sample.json")
        try:
            with open(sample_path, 'r') as f:
                data = json.load(f)
            return data.get("results", [])
        except FileNotFoundError:
            print(f"❌ Sample data not found at {sample_path}")
            return []

    url = "https://api.themoviedb.org/3/discover/movie"
    # 2. Filter Strictly: Jan 1, 2025 to Dec 31, 2026
    params = {
        "api_key": api_key,
        "primary_release_date.gte": "2025-01-01",
        "primary_release_date.lte": "2026-12-31",
        "sort_by": "popularity.desc",
        "page": 1
    }

    movies = []
    for page in range(1, 4):
        params["page"] = page
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch page {page}: {response.text}")
            break

        data = response.json()
        movies.extend(data.get("results", []))

        if page >= data.get("total_pages", 1):
            break

    return movies

# 3. Optimize Storage & 4. Sanitize
def save_to_sqlite(movies, db_name="movies_2025_26.db"):
    # Connect to SQLite
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", db_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table with proper DATE format
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            title TEXT,
            release_date DATE,
            vote_average REAL,
            vote_count INTEGER,
            popularity REAL,
            overview TEXT
        )
    """)

    # Clear existing data just in case
    cursor.execute("DELETE FROM movies")

    # Insert sanitized data
    records_to_insert = []
    for m in movies:
        raw_date = m.get("release_date")
        sanitized_date = None
        if raw_date:
            try:
                # Validate date format (YYYY-MM-DD)
                dt = datetime.strptime(raw_date, "%Y-%m-%d")
                sanitized_date = dt.date()
            except ValueError:
                sanitized_date = None

        # Only insert if date is valid
        if sanitized_date:
            records_to_insert.append((
                m.get("id"),
                m.get("title"),
                sanitized_date,
                m.get("vote_average"),
                m.get("vote_count"),
                m.get("popularity"),
                m.get("overview")
            ))

    cursor.executemany("""
        INSERT INTO movies (id, title, release_date, vote_average, vote_count, popularity, overview)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, records_to_insert)

    conn.commit()
    print(f"✅ Successfully inserted {len(records_to_insert)} movies into {db_path}")
    return conn

# 5. Validation
def run_validation(conn):
    cursor = conn.cursor()
    print("\n🔍 Validating Data: Top Rated Movie of 2026")

    # Leveraging the DATE format we enforced
    query = """
        SELECT title, release_date, vote_average, vote_count
        FROM movies
        WHERE release_date >= '2026-01-01' AND release_date <= '2026-12-31'
          AND vote_count > 0
        ORDER BY vote_average DESC, vote_count DESC
        LIMIT 1
    """

    cursor.execute(query)
    result = cursor.fetchone()

    if result:
        print(f"🎬 Top Rated Movie (2026): {result[0]}")
        print(f"📅 Release Date: {result[1]}")
        print(f"⭐ Rating: {result[2]} ({result[3]} votes)")
    else:
        print("⚠️ No movies found for 2026 with votes.")

if __name__ == "__main__":
    API_KEY = os.environ.get("TMDB_API_KEY")

    print("🚀 Starting TMDB ETL Demo...")
    movies_data = fetch_tmdb_data(API_KEY)

    if movies_data:
        db_conn = save_to_sqlite(movies_data)
        run_validation(db_conn)
        db_conn.close()
    else:
        print("⚠️ No data fetched. Exiting.")
