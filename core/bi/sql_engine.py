"""
BI SQL Engine
=============
Loads project CSV data samples into an in-memory SQLite database and
executes real SQL queries. Returns row data, column names, and chart config.

Tables available:
  - sec_filings   (financial_sample.csv)  — access_number, symbol, cik, form, filed_date, accepted_date, period_date
  - transactions  (creditcard_sample.csv) — Time, V1-V28, Amount, Class

This module is intentionally stateless: each call spins up a short-lived
SQLite connection so it is safe to use in a multi-threaded web server.
"""
import sqlite3
import csv
import os
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
_SAMPLES_DIR = os.path.join(_PROJECT_ROOT, "data", "samples")

# Table registry: logical name → CSV filename
TABLE_REGISTRY: Dict[str, str] = {
    "sec_filings": "financial_sample.csv",
    "transactions": "creditcard_sample.csv",
}


def _load_csv_to_sqlite(conn: sqlite3.Connection, table_name: str, csv_path: str) -> List[str]:
    """Read a CSV into an SQLite table. Returns the list of column names."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        # Sanitize column names (remove spaces, special chars)
        safe_cols = [c.strip().replace(" ", "_").replace("-", "_") for c in columns]

        col_defs = ", ".join(f'"{c}" TEXT' for c in safe_cols)
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({col_defs})')

        placeholders = ", ".join("?" for _ in safe_cols)
        for row in reader:
            values = [row.get(orig, "") for orig in columns]
            conn.execute(
                f'INSERT INTO "{table_name}" VALUES ({placeholders})', values
            )
    conn.commit()
    return safe_cols


def get_schema() -> Dict[str, List[str]]:
    """Return the column lists for each available table."""
    schema = {}
    for table_name, csv_file in TABLE_REGISTRY.items():
        path = os.path.join(_SAMPLES_DIR, csv_file)
        if not os.path.exists(path):
            schema[table_name] = []
            continue
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cols = [
                c.strip().replace(" ", "_").replace("-", "_")
                for c in (reader.fieldnames or [])
            ]
            schema[table_name] = cols

    # Add movies table from sqlite if it exists
    movies_db_path = os.path.join(_PROJECT_ROOT, "data", "movies_2025_26.db")
    if os.path.exists(movies_db_path):
        try:
            m_conn = sqlite3.connect(movies_db_path)
            cur = m_conn.execute("PRAGMA table_info(movies)")
            cols = [row[1] for row in cur.fetchall()]
            if cols:
                schema["movies"] = cols
            m_conn.close()
        except Exception:
            pass

    return schema


def get_preview(table_name: str, n_rows: int = 10) -> Tuple[List[str], List[List[Any]]]:
    """Return (columns, rows) preview for the dataset viewer."""
    if table_name == "movies":
        movies_db_path = os.path.join(_PROJECT_ROOT, "data", "movies_2025_26.db")
        if os.path.exists(movies_db_path):
            conn = sqlite3.connect(movies_db_path)
            try:
                cur = conn.execute(f'SELECT * FROM movies LIMIT {n_rows}')
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = [list(r) for r in cur.fetchall()]
                return columns, rows
            finally:
                conn.close()
        return [], []

    csv_file = TABLE_REGISTRY.get(table_name)
    if not csv_file:
        return [], []
    path = os.path.join(_SAMPLES_DIR, csv_file)
    if not os.path.exists(path):
        return [], []

    conn = sqlite3.connect(":memory:")
    try:
        cols = _load_csv_to_sqlite(conn, table_name, path)
        cur = conn.execute(f'SELECT * FROM "{table_name}" LIMIT {n_rows}')
        rows = [list(r) for r in cur.fetchall()]
        return cols, rows
    finally:
        conn.close()


def execute_query(sql: str, max_rows: int = 200) -> Tuple[List[str], List[List[Any]], str]:
    """
    Execute a SQL query against the in-memory database.

    Returns:
        columns  : list of column header strings
        rows     : list of row value lists (max_rows capped)
        error    : empty string on success, error message on failure
    """
    conn = sqlite3.connect(":memory:")
    try:
        # Load all registered tables
        for table_name, csv_file in TABLE_REGISTRY.items():
            path = os.path.join(_SAMPLES_DIR, csv_file)
            if os.path.exists(path):
                _load_csv_to_sqlite(conn, table_name, path)

        # Attach and copy movies table from sqlite db if it exists
        movies_db_path = os.path.join(_PROJECT_ROOT, "data", "movies_2025_26.db")
        if os.path.exists(movies_db_path):
            conn.execute(f"ATTACH DATABASE '{movies_db_path}' AS movies_db")
            conn.execute("CREATE TABLE movies AS SELECT * FROM movies_db.movies")
            conn.execute("DETACH DATABASE movies_db")

        # Safety: only allow SELECT statements
        sql_stripped = sql.strip().lstrip(";").strip()
        if not sql_stripped.upper().startswith("SELECT"):
            return [], [], "Only SELECT statements are permitted."

        cur = conn.execute(sql_stripped)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = [list(r) for r in cur.fetchmany(max_rows)]
        return columns, rows, ""

    except Exception as exc:
        logger.warning(f"SQL execution error: {exc}\nQuery: {sql}")
        return [], [], str(exc)
    finally:
        conn.close()


def infer_chart_config(question: str, columns: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    """
    Derive a Chart.js-compatible config from the result shape.
    Returns a dict with {type, labels, datasets, title}.
    """
    if not rows or not columns:
        return {}

    n_cols = len(columns)
    question_lower = question.lower()

    # Determine chart type
    chart_type = "bar"
    if any(kw in question_lower for kw in ["trend", "over time", "by date", "monthly", "yearly", "daily"]):
        chart_type = "line"
    elif any(kw in question_lower for kw in ["distribution", "breakdown", "proportion", "share", "pie"]):
        chart_type = "doughnut" if len(rows) <= 8 else "bar"
    elif any(kw in question_lower for kw in ["scatter", "correlation"]):
        chart_type = "scatter"

    # --- Step 1: Identify value columns by name keywords ---
    VALUE_KEYWORDS = ("count", "sum", "avg", "average", "total", "amount", "revenue",
                      "rate", "pct", "percent", "score", "num", "qty", "quantity", "max", "min")
    LABEL_KEYWORDS = ("name", "type", "form", "symbol", "ticker", "region", "category",
                      "class", "label", "key", "id", "date", "month", "year", "period")

    value_col_idx = -1
    label_col_idx = -1

    # Pass 1: check names
    for i, col in enumerate(columns):
        col_l = col.lower()
        if any(kw in col_l for kw in VALUE_KEYWORDS):
            if value_col_idx == -1:
                value_col_idx = i
        elif any(kw in col_l for kw in LABEL_KEYWORDS):
            if label_col_idx == -1:
                label_col_idx = i

    # Pass 2: if still not found, classify by native type of first row
    if value_col_idx == -1 or label_col_idx == -1:
        for i in range(n_cols):
            val = rows[0][i]
            is_numeric = isinstance(val, (int, float))
            if not is_numeric:
                try:
                    float(str(val).replace(",", ""))
                    is_numeric = len(str(val)) < 4   # short purely numeric strings might be categories
                except (ValueError, TypeError):
                    is_numeric = False
            if is_numeric and value_col_idx == -1:
                value_col_idx = i
            elif not is_numeric and label_col_idx == -1:
                label_col_idx = i

    # Pass 3: absolute fallback
    if n_cols >= 2:
        if label_col_idx == -1:
            label_col_idx = 0
        if value_col_idx == -1:
            value_col_idx = 1
    else:
        label_col_idx = 0
        value_col_idx = 0

    # Make sure they don't clash
    if label_col_idx == value_col_idx and n_cols > 1:
        value_col_idx = 1 - label_col_idx  # flip

    labels = [str(r[label_col_idx]) for r in rows]
    values = []
    for r in rows:
        try:
            values.append(round(float(str(r[value_col_idx]).replace(",", "")), 4))
        except (ValueError, TypeError):
            values.append(0)

    # Colour palette
    palette = [
        "rgba(99,102,241,0.8)", "rgba(16,185,129,0.8)", "rgba(245,158,11,0.8)",
        "rgba(239,68,68,0.8)", "rgba(59,130,246,0.8)", "rgba(168,85,247,0.8)",
        "rgba(236,72,153,0.8)", "rgba(20,184,166,0.8)",
    ]

    dataset = {
        "label": columns[value_col_idx],
        "data": values,
        "backgroundColor": palette[:len(values)] if chart_type in ("doughnut", "pie") else palette[0],
        "borderColor": "rgba(99,102,241,1)" if chart_type == "line" else None,
        "fill": False,
        "tension": 0.4,
    }

    return {
        "type": chart_type,
        "title": f"{columns[value_col_idx]} by {columns[label_col_idx]}",
        "labels": labels,
        "datasets": [dataset],
    }
