import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Airbnb Bed Selection", layout="centered")

# --- APP CONFIG & DATA ---
NAMES = [
    "Hannah", "Max", "CJ", "Lily", "Lauren P", "Jane", "Abby", "Anna", 
    "Lauren B", "Cara", "Liv", "Molly", "Laurel", "Logan", "Gabby", "Isabelle G"
]

# Bed Inventory Data
BED_DATA = [
    {"id": 1, "room": "BEDROOM A", "desc": "Shared King Spot 1 (Main/Ensuite)", "price": 88.0},
    {"id": 2, "room": "BEDROOM A", "desc": "Shared King Spot 2 (Main/Ensuite)", "price": 88.0},
    {"id": 3, "room": "BEDROOM B", "desc": "Shared Queen Spot 1 (Main)", "price": 78.5},
    {"id": 4, "room": "BEDROOM B", "desc": "Shared Queen Spot 2 (Main)", "price": 78.5},
    {"id": 5, "room": "BEDROOM B", "desc": "Twin Top Bunk (Main)", "price": 81.0},
    {"id": 6, "room": "BEDROOM C", "desc": "Shared Queen Spot 1 (Main)", "price": 83.0},
    {"id": 7, "room": "BEDROOM C", "desc": "Shared Queen Spot 2 (Main)", "price": 83.0},
    {"id": 8, "room": "BEDROOM D", "desc": "Shared Queen Spot 1 (Lower)", "price": 83.0},
    {"id": 9, "room": "BEDROOM D", "desc": "Shared Queen Spot 2 (Lower)", "price": 83.0},
    {"id": 10, "room": "BEDROOM E", "desc": "Shared King Spot 1 (Lower)", "price": 71.0},
    {"id": 11, "room": "BEDROOM E", "desc": "Shared King Spot 2 (Lower)", "price": 71.0},
    {"id": 12, "room": "BEDROOM E", "desc": "Twin Top Bunk 1 (Lower)", "price": 76.0},
    {"id": 13, "room": "BEDROOM E", "desc": "Twin Top Bunk 2 (Lower)", "price": 76.0},
    {"id": 14, "room": "BEDROOM E", "desc": "Twin Bottom Bunk (Lower)", "price": 76.0},
    {"id": 15, "room": "BEDROOM E", "desc": "Twin Top Bunk 3 (Lower)", "price": 76.0},
    {"id": 16, "room": "SHARED SPACE", "desc": "Couch (Living Room)", "price": 56.0},
]

# --- DATABASE CONNECTION ---
# Note: You will set up the 'connections.gsheets' in the Streamlit Cloud dashboard
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # We force 'occupant' and 'nights' to be strings so pandas doesn't panic
    raw_df = conn.read(ttl=0)
    df = raw_df.astype({
        'occupant': str, 
        'nights': str,
        'bed_id': int
    })
    # Clean up: change "nan" strings back to empty space
    df['occupant'] = df['occupant'].replace(['nan', 'None', ''], None)
    return df

def update_bed(bed_id, name, nights):
    df = get_data()
    # Check if someone else took it while we were looking
    current_occupant = df.loc[df['bed_id'] == bed_id, 'occupant'].values[0]
    if pd.notna(current_occupant) and current_occupant != "" and current_occupant != name:
        return False
    
    # Clear user's old selection first
    df.loc[df['occupant'] == name, ['occupant', 'nights']] = [None, None]
    
    # Make new selection if not clearing
    if bed_id is not None:
        df.loc[df['bed_id'] == bed_id, ['occupant', 'nights']] = [name, nights]
    
    conn.update(data=df)
    return True

# --- UI LOGIC ---
st.title("🛏️ Bed Selection")

# Step 1: Identity
user_name = st.selectbox("Who are you?", ["Select a name..."] + NAMES)

if user_name != "Select a name...":
    df = get_data()
    user_record = df[df['occupant'] == user_name]
    
    # Step 2: Nights
    num_nights = st.radio("How many nights are you staying?", [2, 3], horizontal=True)
    
    st.divider()
    
    # Show current selection
    if not user_record.empty:
        current_bed = user_record.iloc[0]
        st.success(f"You currently have: **{current_bed['desc']}**")
        if st.button("❌ Clear My Selection"):
            update_bed(None, user_name, None)
            st.rerun()
    
    # Step 3: Bed Grid
    st.subheader("Peruse & Select a Bed")
    
    for room in ["BEDROOM A", "BEDROOM B", "BEDROOM C", "BEDROOM D", "BEDROOM E", "SHARED SPACE"]:
        with st.expander(f"📍 {room}", expanded=True):
            room_beds = [b for b in BED_DATA if b['room'] == room]
            for bed in room_beds:
                # Find status in DB
                db_row = df[df['bed_id'] == bed['id']].iloc[0]
                is_taken = pd.notna(db_row['occupant']) and db_row['occupant'] != ""
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{bed['desc']}**")
                    st.caption(f"${bed['price']}/night")
                
                with col2:
                    if is_taken:
                        st.error(f"Taken: {db_row['occupant']} ({int(db_row['nights'])} nights)")
                    else:
                        if st.button(f"Claim", key=f"btn_{bed['id']}"):
                            success = update_bed(bed['id'], user_name, num_nights)
                            if success:
                                total = (bed['price'] * num_nights)
                                st.balloons()
                                st.info(f"Your total cost is approximately ${total} +/- $15")
                                st.rerun()
                            else:
                                st.error("Error. Please pick a different bed.")
