import streamlit as st
import sqlite3
import datetime

# --- DB Setup ---
def create_tables(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS banjaarey (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banjaara_id INTEGER,
            date TEXT,
            FOREIGN KEY (banjaara_id) REFERENCES banjaarey(id),
            UNIQUE (banjaara_id, date)
        )
    ''')

def get_connection():
    return sqlite3.connect("banjaarey.db", check_same_thread=False)

conn = get_connection()
create_tables(conn)

# --- CRUD for Banjaarey ---
def add_banjaara(name):
    try:
        conn.execute("INSERT INTO banjaarey (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_banjaarey():
    return conn.execute("SELECT id, name FROM banjaarey ORDER BY name").fetchall()

def delete_banjaara(banjaara_id):
    conn.execute("DELETE FROM banjaarey WHERE id = ?", (banjaara_id,))
    conn.execute("DELETE FROM attendance WHERE banjaara_id = ?", (banjaara_id,))
    conn.commit()

# --- Attendance ---
def mark_attendance(date, present_ids):
    for banjaara_id in present_ids:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO attendance (banjaara_id, date) VALUES (?, ?)",
                (banjaara_id, date)
            )
        except Exception as e:
            st.error(f"Error: {e}")
    conn.commit()

def get_attendance_by_date(date):
    rows = conn.execute(
        "SELECT b.name FROM attendance a JOIN banjaarey b ON a.banjaara_id = b.id WHERE a.date = ?", (date,)
    ).fetchall()
    return [row[0] for row in rows]

def get_dates_by_banjaara(banjaara_id):
    rows = conn.execute(
        "SELECT date FROM attendance WHERE banjaara_id = ? ORDER BY date", (banjaara_id,)
    ).fetchall()
    return [row[0] for row in rows]

# --- Streamlit UI ---
st.title("Banjaarey Attendance Tracker")

tab1, tab2, tab3 = st.tabs(["Manage Banjaarey", "Take Attendance", "Search Attendance"])

with tab1:
    st.header("Add Banjaara")
    name = st.text_input("Name")
    if st.button("Add"):
        if name.strip():
            if add_banjaara(name.strip()):
                st.success(f"Added {name}")
            else:
                st.warning("Name already exists!")
        else:
            st.warning("Enter a name.")

    st.header("Current Banjaarey")
    banjaarey = get_banjaarey()
    for banjaara_id, banjaara_name in banjaarey:
        col1, col2 = st.columns([3,1])
        col1.write(banjaara_name)
        if col2.button("Delete", key=f"del_{banjaara_id}"):
            delete_banjaara(banjaara_id)
            st.experimental_rerun()

with tab2:
    st.header("Mark Attendance")
    banjaarey = get_banjaarey()
    if banjaarey:
        today = st.date_input("Date", datetime.date.today())
        selected = st.multiselect(
            "Select present banjaarey:",
            options=[b[1] for b in banjaarey]
        )
        if st.button("Mark Attendance"):
            present_ids = [b[0] for b in banjaarey if b[1] in selected]
            mark_attendance(str(today), present_ids)
            st.success("Attendance marked!")
    else:
        st.info("No banjaarey found. Please add them first.")

with tab3:
    st.header("Attendance Search")

    search_mode = st.radio("Search by", ["Date", "Banjaara"])

    if search_mode == "Date":
        date = st.date_input("Select date", datetime.date.today(), key="search_date")
        present = get_attendance_by_date(str(date))
        if present:
            st.success(f"Present on {date}: {', '.join(present)}")
        else:
            st.info("No attendance recorded for this date.")

    else:  # By Banjaara
        banjaarey = get_banjaarey()
        banjaara_names = [b[1] for b in banjaarey]
        selected_name = st.selectbox("Select Banjaara", banjaara_names)
        banjaara_id = [b[0] for b in banjaarey if b[1] == selected_name][0]
        dates = get_dates_by_banjaara(banjaara_id)
        if dates:
            st.success(f"{selected_name} was present on: {', '.join(dates)}")
        else:
            st.info(f"No attendance found for {selected_name}.")
