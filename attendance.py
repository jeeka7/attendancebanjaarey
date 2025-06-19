import streamlit as st
import sqlite3
import datetime

# --- Admin credentials (change these!) ---
ADMIN_USER = "admin"
ADMIN_PASS = "supersecret"  # CHANGE THIS TO YOUR OWN PASSWORD

# --- Database Setup ---
def get_connection():
    return sqlite3.connect("banjaarey.db", check_same_thread=False)

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
    conn.commit()

def add_banjaara(conn, name):
    try:
        conn.execute("INSERT INTO banjaarey (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_banjaarey(conn):
    return conn.execute("SELECT id, name FROM banjaarey ORDER BY name").fetchall()

def delete_banjaara(conn, banjaara_id):
    conn.execute("DELETE FROM banjaarey WHERE id = ?", (banjaara_id,))
    conn.execute("DELETE FROM attendance WHERE banjaara_id = ?", (banjaara_id,))
    conn.commit()

def mark_attendance(conn, date, present_ids):
    for banjaara_id in present_ids:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO attendance (banjaara_id, date) VALUES (?, ?)",
                (banjaara_id, date)
            )
        except Exception as e:
            st.error(f"Error: {e}")
    conn.commit()

def get_attendance_by_date(conn, date):
    rows = conn.execute(
        "SELECT b.name FROM attendance a JOIN banjaarey b ON a.banjaara_id = b.id WHERE a.date = ?", (date,)
    ).fetchall()
    return [row[0] for row in rows]

def get_attendance_ids_by_date(conn, date):
    # Returns banjaara_id's who are present for the date
    rows = conn.execute(
        "SELECT a.banjaara_id FROM attendance a WHERE a.date = ?", (date,)
    ).fetchall()
    return [row[0] for row in rows]

def get_dates_by_banjaara(conn, banjaara_id):
    rows = conn.execute(
        "SELECT date FROM attendance WHERE banjaara_id = ? ORDER BY date", (banjaara_id,)
    ).fetchall()
    return [row[0] for row in rows]

def delete_attendance_for_date(conn, date):
    conn.execute("DELETE FROM attendance WHERE date = ?", (date,))
    conn.commit()

def update_attendance_for_date(conn, date, present_ids):
    # Remove all for this date, then re-add
    delete_attendance_for_date(conn, date)
    mark_attendance(conn, date, present_ids)

# --- Initialize DB ---
conn = get_connection()
create_tables(conn)

# --- Admin Login ---
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        with st.form("login_form"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                if user == ADMIN_USER and pw == ADMIN_PASS:
                    st.session_state.logged_in = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
        return False
    return True

# --- Streamlit UI ---
st.title("Banjaarey Attendance Tracker")

# --- Check login only once, before creating tabs ---
is_admin = check_login()

tab1, tab2, tab3 = st.tabs(["Manage Banjaarey", "Take Attendance", "Search/Modify Attendance"])

with tab1:
    if is_admin:
        st.header("Add Banjaara")
        name = st.text_input("Name")
        if st.button("Add"):
            if name.strip():
                if add_banjaara(conn, name.strip()):
                    st.success(f"Added {name}")
                    st.rerun()
                else:
                    st.warning("Name already exists!")
            else:
                st.warning("Enter a name.")

        st.header("Current Banjaarey")
        banjaarey = get_banjaarey(conn)
        delete_id = None
        for banjaara_id, banjaara_name in banjaarey:
            col1, col2 = st.columns([3,1])
            col1.write(banjaara_name)
            if col2.button("Delete", key=f"del_{banjaara_id}"):
                delete_id = banjaara_id
        if delete_id is not None:
            delete_banjaara(conn, delete_id)
            st.rerun()
    else:
        st.info("Admin login is required to manage Banjaarey.")

with tab2:
    if is_admin:
        st.header("Mark Attendance")
        banjaarey = get_banjaarey(conn)
        if banjaarey:
            today = st.date_input("Date", datetime.date.today())
            selected = st.multiselect(
                "Select present banjaarey:",
                options=[b[1] for b in banjaarey]
            )
            if st.button("Mark Attendance"):
                present_ids = [b[0] for b in banjaarey if b[1] in selected]
                mark_attendance(conn, str(today), present_ids)
                st.success("Attendance marked!")
        else:
            st.info("No banjaarey found. Please add them first (admin only).")
    else:
        st.info("Admin login is required to mark attendance.")

with tab3:
    st.header("Attendance Search / Modify")
    search_mode = st.radio("Search by", ["Date", "Banjaara", "Modify by Date"])

    if search_mode == "Date":
        date = st.date_input("Select date", datetime.date.today(), key="search_date")
        present = get_attendance_by_date(conn, str(date))
        if present:
            st.success(f"Present on {date}: {', '.join(present)}")
        else:
            st.info("No attendance recorded for this date.")

    elif search_mode == "Banjaara":
        banjaarey = get_banjaarey(conn)
        banjaara_names = [b[1] for b in banjaarey]
        if banjaara_names:
            selected_name = st.selectbox("Select Banjaara", banjaara_names)
            banjaara_id = [b[0] for b in banjaarey if b[1] == selected_name][0]
            dates = get_dates_by_banjaara(conn, banjaara_id)
            if dates:
                st.success(f"{selected_name} was present on: {', '.join(dates)}")
            else:
                st.info(f"No attendance found for {selected_name}.")
        else:
            st.info("No banjaarey available. Please add some first (admin only).")

    elif search_mode == "Modify by Date":
        if is_admin:
            st.subheader("Modify Attendance for a Date")
            all_dates = conn.execute("SELECT DISTINCT date FROM attendance ORDER BY date DESC").fetchall()
            all_dates = [row[0] for row in all_dates]
            if all_dates:
                mod_date = st.selectbox("Select a date to modify", all_dates, key="mod_date")
                # Show current attendance for that date
                present_ids = get_attendance_ids_by_date(conn, mod_date)
                banjaarey = get_banjaarey(conn)
                present_names = [b[1] for b in banjaarey if b[0] in present_ids]
                st.write(f"Current present: {', '.join(present_names) if present_names else 'None'}")

                # Provide form to modify
                selected = st.multiselect(
                    "Modify present banjaarey for this date:",
                    options=[b[1] for b in banjaarey],
                    default=present_names,
                    key="mod_select"
                )
                if st.button("Update Attendance", key="update_attendance"):
                    new_present_ids = [b[0] for b in banjaarey if b[1] in selected]
                    update_attendance_for_date(conn, mod_date, new_present_ids)
                    st.success("Attendance updated!")
                    st.rerun()
                if st.button("Delete This Attendance Record", key="delete_attendance"):
                    delete_attendance_for_date(conn, mod_date)
                    st.success("Attendance record deleted for this date!")
                    st.rerun()
            else:
                st.info("No attendance records available to modify.")
        else:
            st.info("Admin login is required to modify attendance.")
