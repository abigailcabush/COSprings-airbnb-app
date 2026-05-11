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
    {"id": 1, "room": "BEDROOM A (Main Level)", "desc": "Shared King #1 (with Ensuite bathroom)", "price": 88},
    {"id": 2, "room": "BEDROOM A (Main Level)", "desc": "Shared King #2 (with Ensuite bathroom)", "price": 88},
    {"id": 3, "room": "BEDROOM B (Main Level)", "desc": "Shared Queen #1 (bottom bunk)", "price": 78.50},
    {"id": 4, "room": "BEDROOM B (Main Level)", "desc": "Shared Queen #2 (bottom bunk)", "price": 78.5},
    {"id": 5, "room": "BEDROOM B (Main Level)", "desc": "Twin (top bunk)", "price": 81},
    {"id": 6, "room": "BEDROOM C (Main Level)", "desc": "Shared Queen #1", "price": 83},
    {"id": 7, "room": "BEDROOM C (Main Level)", "desc": "Shared Queen #2", "price": 83},
    {"id": 8, "room": "BEDROOM D (Lower Level)", "desc": "Shared Queen #1", "price": 83},
    {"id": 9, "room": "BEDROOM D (Lower Level)", "desc": "Shared Queen #2", "price": 83},
    {"id": 10, "room": "BEDROOM E (Lower Level)", "desc": "Shared King #1", "price": 71},
    {"id": 11, "room": "BEDROOM E (Lower Level)", "desc": "Shared King #2", "price": 71},
    {"id": 12, "room": "BEDROOM E (Lower Level)", "desc": "Twin (top bunk of bed A)", "price": 76},
    {"id": 13, "room": "BEDROOM E (Lower Level)", "desc": "Twin (top bunk of bed B)", "price": 76},
    {"id": 14, "room": "BEDROOM E (Lower Level)", "desc": "Twin (bottom bunk of bed A)", "price": 76},
    {"id": 15, "room": "BEDROOM E (Lower Level)", "desc": "Twin (top bunk of bed B)", "price": 76},
    {"id": 16, "room": "SHARED SPACE", "desc": "Couch (3 options: 2 upstairs, 1 downstairs)", "price": 56},
]

# --- DATABASE CONNECTION ---
# Note: You will set up the 'connections.gsheets' in the Streamlit Cloud dashboard
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # Read the data
    df = conn.read(ttl=0)
    
    # 1. Force the columns to be "object" (this allows both text and empty values)
    # 2. Fill any empty/null cells with an empty string "" immediately
    df['occupant'] = df['occupant'].fillna("").astype(str)
    df['nights'] = df['nights'].fillna("").astype(str)
    df['bed_id'] = df['bed_id'].astype(int)
    
    # Clean up any weird "nan" strings that might have been read
    df['occupant'] = df['occupant'].replace(['nan', 'None'], "")
    df['nights'] = df['nights'].replace(['nan', 'None'], "")
    
    return df

def update_bed(bed_id, name, nights):
    df = get_data()
    
    # Check if someone else took it while we were looking
    # (We use .strip() to make sure we aren't tricked by hidden spaces)
    if bed_id is not None:
        target_row = df.loc[df['bed_id'] == bed_id]
        current_occupant = str(target_row['occupant'].values[0]).strip()
        if current_occupant != "" and current_occupant != name:
            return False
    
    # Clear user's old selection
    df.loc[df['occupant'] == name, ['occupant', 'nights']] = ["", ""]
    
    # Make new selection
    if bed_id is not None:
        # We explicitly cast everything to string here to satisfy the database
        df.loc[df['bed_id'] == bed_id, 'occupant'] = str(name)
        df.loc[df['bed_id'] == bed_id, 'nights'] = str(nights)
    
    conn.update(data=df)
    return True

# --- UI LOGIC ---
st.title("CO Springs AirBnB")
st.markdown("### Bed & Room Selection, considering approximate prices")

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
        
        # Calculate the total for the summary
        # We use float() just in case the spreadsheet stored it strangely
        price_per_night = float(current_bed['price'])
        nights_count = int(float(current_bed['nights']))
        total_price = int(price_per_night * nights_count)
        
        # Display the full summary
        st.success(
            f"✅ **Selection Saved!**\n\n"
            f"**{current_bed['room']}**: {current_bed['description']}\n\n"
            f"\n\n"  # This adds the extra enter/space you wanted
            f"**Total Cost for the Weekend**: approximately \${total_price} ± \$15"
        )
        
        if st.button("❌ Clear My Selection"):
            update_bed(None, user_name, None)
            st.rerun()
    
    # Step 3: Bed Grid
    st.subheader("Select a Bed, Bedroom, and Potential Roommates:")
    
    for room in ["BEDROOM A (Main Level)", "BEDROOM B (Main Level)", "BEDROOM C (Main Level)", "BEDROOM D (Lower Level)", "BEDROOM E (Lower Level)", "SHARED SPACE"]:
        with st.expander(f"{room}", expanded=True):
            room_beds = [b for b in BED_DATA if b['room'] == room]
            for bed in room_beds:
                # Find status in DB
                db_row = df[df['bed_id'] == bed['id']].iloc[0]
                is_taken = pd.notna(db_row['occupant']) and db_row['occupant'] != ""
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{bed['desc']}**")
                    st.caption(f"~${bed['price']}/night")
                
                with col2:
                    if is_taken:
                         nights_val = db_row['nights'] if db_row['nights'] != "" else "0"
                         if db_row['nights'] != "":
                             nights_display = int(float(db_row['nights']))
                         else:
                             nights_display = 0

                         st.error(f"Taken: {db_row['occupant']} ({nights_display} nights)")
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
