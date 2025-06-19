import streamlit as st
import sqlite3
import datetime

# ... [DB setup and functions stay the same] ...

st.title("Banjaarey Attendance Tracker")

tab1, tab2, tab3 = st.tabs(["Manage Banjaarey", "Take Attendance", "Search Attendance"])

with tab1:
    st.header("Add Banjaara")
    name = st.text_input("Name")
    if st.button("Add"):
        if name.strip():
            if add_banjaara(name.strip()):
                st.success(f"Added {name}")
                st.experimental_rerun()
            else:
                st.warning("Name already exists!")
        else:
            st.warning("Enter a name.")

    st.header("Current Banjaarey")
    banjaarey = get_banjaarey()

    # Use session state to check if a delete was requested
    for banjaara_id, banjaara_name in banjaarey:
        col1, col2 = st.columns([3,1])
        col1.write(banjaara_name)
        if col2.button("Delete", key=f"del_{banjaara_id}"):
            # Store the id in session state instead of rerunning in the loop
            st.session_state['delete_id'] = banjaara_id
            st.experimental_rerun()

    # After the loop, check if a delete was requested
    if 'delete_id' in st.session_state:
        delete_banjaara(st.session_state['delete_id'])
        del st.session_state['delete_id']
        st.experimental_rerun()
