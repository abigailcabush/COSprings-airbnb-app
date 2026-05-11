import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Update the Tab Title
st.set_page_config(page_title="AirBnB Bed Selection", layout="centered")

# --- APP CONFIG & DATA ---
NAMES = [
    "Abby", "Anna", "Cara", "CJ", "Gabby", "Hannah", "Isabelle G",
    "Jane", "Laurel", "Lauren B", "Lauren P", "Lily", "Liv", "Logan",
    "Max", "Molly"
]

# Bed Inventory Data
BED_DATA = [
    {"id": 1, "room": "BEDROOM A (Main Level)", "desc": "Shared King #1 (with Ensuite bathroom)", "price": 90},
    {"id": 2, "room": "BEDROOM A (Main Level)", "desc": "Shared King #2 (with Ensuite bathroom)", "price": 90},
    {"id": 3, "room": "BEDROOM B (Main Level)", "desc": "Shared Queen #1 (bottom bunk)", "price": 80},
    {"id": 4, "room": "BEDROOM B (Main Level)", "desc": "Shared Queen #2 (bottom bunk)", "price": 80},
    {"id": 5, "room": "BEDROOM B (Main Level)", "desc": "Twin (top bunk)", "price": 82.50},
    {"id": 6, "room": "BEDROOM C (Main Level --> 3 bathrooms on main level)", "desc": "Shared Queen #1", "price": 85},
    {"id": 7, "room": "BEDROOM C (Main Level --> 3 bathrooms on main level)", "desc": "Shared Queen #2", "price": 85},
    {"id": 8, "room": "BEDROOM D (Lower Level --> only 1 bathroom on lower level)", "desc": "Shared Queen #1", "price": 82.50},
    {"id": 9, "room": "BEDROOM D (Lower Level --> only 1 bathroom on lower level)", "desc": "Shared Queen #2", "price": 82.50},
    {"id": 10, "room": "BEDROOM E (Lower Level)", "desc": "Shared King #1", "price": 70},
    {"id": 11, "room": "BEDROOM E (Lower Level)", "desc": "Shared King #2", "price": 70},
    {"id": 12, "room": "BEDROOM E (Lower Level)", "desc": "Twin (top bunk of bed A)", "price": 75},
    {"id": 13, "room": "BEDROOM E (Lower Level)", "desc": "Twin (top bunk of bed B)", "price": 75},
    {"id": 14, "room": "BEDROOM E (Lower Level)", "desc": "Twin (bottom bunk of bed A)", "price": 75},
    {"id": 15, "room": "BEDROOM E (Lower Level)", "desc": "Twin (top bunk of bed B)", "price": 75},
    {"id": 16, "room": "SHARED SPACE", "desc": "Couch (3 options: 2 upstairs, 1 downstairs)", "price": 55},
]

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    df = conn.read(ttl=0)
    df['occupant'] = df['occupant'].fillna("").astype(str)
    df['nights'] = df['nights'].fillna("").astype(str)
    df['bed_id'] = df['bed_id'].astype(int)
    df['occupant'] = df['occupant'].replace(['nan', 'None'], "")
    df['nights'] = df['nights'].replace(['nan', 'None'], "")
    return df

def update_bed(bed_id, name, nights):
    df = get_data()
    if bed_id is not None:
        target_row = df.loc[df['bed_id'] == bed_id]
        current_occupant = str(target_row['occupant'].values[0]).strip()
        if current_occupant != "" and current_occupant != name:
            return False
    
    df.loc[df['occupant'] == name, ['occupant', 'nights']] = ["", ""]
    if bed_id is not None:
        df.loc[df['bed_id'] == bed_id, 'occupant'] = str(name)
        df.loc[df['bed_id'] == bed_id, 'nights'] = str(nights)
    
    conn.update(data=df)
    return True

# --- UI LOGIC ---
# Updated Title with requested spacing
st.title("CO Springs AirBnB")
st.markdown(
    "<h2 style='font-weight: 500; margin-top: -10px;'>Bed & Room Selection with approximate prices</h2>", 
    unsafe_allow_html=True
)
st.markdown("<div id='linkto_top'></div>", unsafe_allow_html=True)

# Step 1: Identity
user_name = st.selectbox("Who are you?", ["Select a name..."] + NAMES)

if user_name != "Select a name...":
    df = get_data()
    user_record = df[df['occupant'] == user_name]
    
    # 1. MOVE NIGHTS HERE (So it's always above the confirmation)
    num_nights = st.radio("How many nights are you staying?", [2, 3], horizontal=True)
    st.divider()
    
    # 2. THEN SHOW THE SUCCESS BOX
    if not user_record.empty:
        current_bed = user_record.iloc[0]
        p_night = float(current_bed['price'])
        n_count = int(float(current_bed['nights']))
        total_p = int(p_night * n_count)
        
        st.success(
            f"**Selection Saved!**\n\n"
            f"{current_bed['room']}, {current_bed['description']}\n\n"
            f"\n\n" 
            f"**Estimated Total Cost for the Weekend**: \${total_p} ± \$15 for {n_count} nights"
        )
        
        if st.button("Clear My Selection"):
            update_bed(None, user_name, None)
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    # Step 3: Bed Grid
    st.subheader("Select a Bed, Bedroom, and Roommates:")
    
    rooms = ["BEDROOM A (Main Level)", "BEDROOM B (Main Level)", "BEDROOM C (Main Level --> 3 bathrooms on main level)", 
             "BEDROOM D (Lower Level --> only 1 bathroom on lower level)", "BEDROOM E (Lower Level)", "SHARED SPACE"]
             
    for room in rooms:
        with st.expander(f"{room}", expanded=True):
            room_beds = [b for b in BED_DATA if b['room'] == room]
            for bed in room_beds:
                db_row = df[df['bed_id'] == bed['id']].iloc[0]
                is_taken = db_row['occupant'] != ""
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{bed['desc']}**")
                    st.caption(f"approximately \${bed['price']}/night")
                
                with col2:
                    if is_taken:
                         n_display = int(float(db_row['nights'])) if db_row['nights'] != "" else 0
                         st.error(f"**Taken**: {db_row['occupant']} ({n_display} nights)")
                    else:
                        if st.button(f"Claim", key=f"btn_{bed['id']}"):
                            success = update_bed(bed['id'], user_name, num_nights)
                            if success:
                                # 1. Clear the internal cache so the "Success" box at the top sees the new data
                                st.cache_data.clear() 
                                
                                # 2. A subtle "toast" instead of big balloons
                                st.toast("Selection updated!", icon="✅")
                                
                                # 3. The "Teleport" script (optional, keep it if you want the jump)
                                st.components.v1.html("<script>window.parent.scrollTo(0,0);</script>", height=0)
                                
                                # 4. Refresh the page to show the new selection at the top
                                st.rerun()
                            else:
                                st.error("Error. Someone might have just taken this bed!")