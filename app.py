import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Update the Tab Title
st.set_page_config(page_title="AirBnB Bed Selection", layout="centered")

# --- APP CONFIG & DATA ---
NAMES = [
    "Abby", "Anna", "Cara", "CJ", "Gabby", "Hannah", "Isabelle G",
    "Jane", "Lauren B", "Lauren P", "Lily", "Liv", "Logan", "Molly"
]

# Bed Inventory Data
BED_DATA = [
    {"id": 1, "room": "BEDROOM A (Main Level)", "desc": "Shared King #1 (with Ensuite bathroom)", "price": 96.5, "type": "standard"},
    {"id": 2, "room": "BEDROOM A (Main Level)", "desc": "Shared King #2 (with Ensuite bathroom)", "price": 96.5, "type": "standard"},
    {"id": 3, "room": "BEDROOM B (Main Level)", "desc": "Shared Queen #1 (bottom bunk)", "price": 86.5, "type": "standard"},
    {"id": 4, "room": "BEDROOM B (Main Level)", "desc": "Shared Queen #2 (bottom bunk)", "price": 86.5, "type": "standard"},
    {"id": 5, "room": "BEDROOM B (Main Level)", "desc": "Twin (top bunk)", "price": 89, "type": "standard"},
    {"id": 6, "room": "BEDROOM C (Main Level)", "desc": "Shared Queen #1", "price": 91.5, "type": "standard"},
    {"id": 7, "room": "BEDROOM C (Main Level)", "desc": "Shared Queen #2", "price": 91.5, "type": "standard"},
    
    {"id": 8, "room": "BEDROOM D (Lower Level)", "desc": "Shared Queen #1", "price": 86.5, "type": "shared"},
    {"id": 9, "room": "BEDROOM D (Lower Level)", "desc": "Shared Queen #2", "price": 86.5, "type": "shared"},
    {"id": 17, "room": "BEDROOM D (Lower Level)", "desc": "Solo Queen", "price": 114.5, "type": "solo"},
    
    {"id": 10, "room": "BEDROOM E (Lower Level)", "desc": "Shared King #1", "price": 74, "type": "standard"},
    {"id": 11, "room": "BEDROOM E (Lower Level)", "desc": "Shared King #2", "price": 74, "type": "standard"},
    {"id": 12, "room": "BEDROOM E (Lower Level)", "desc": "Twin (top bunk of bed A)", "price": 79, "type": "standard"},
    {"id": 13, "room": "BEDROOM E (Lower Level)", "desc": "Twin (top bunk of bed B)", "price": 79, "type": "standard"},
    {"id": 14, "room": "BEDROOM E (Lower Level)", "desc": "Twin (bottom bunk of bed A)", "price": 79, "type": "standard"},
    {"id": 15, "room": "BEDROOM E (Lower Level)", "desc": "Twin (top bunk of bed B)", "price": 79, "type": "standard"},
]

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=3)
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
        if not target_row.empty:
            current_occupant = str(target_row['occupant'].values[0]).strip()
            if current_occupant != "" and current_occupant != name:
                return False
    
    # Reset user's previous selection completely
    df.loc[df['occupant'] == name, ['occupant', 'nights']] = ["", ""]
    
    if bed_id is not None:
        df.loc[df['bed_id'] == bed_id, 'occupant'] = str(name)
        df.loc[df['bed_id'] == bed_id, 'nights'] = str(nights)
    
    conn.update(data=df)
    return True

@st.dialog("Selection Confirmed!")
def show_success_modal(room, desc, total, nights):
    st.write(f"🎉 **You're all set!**")
    st.write(f"**Room:** {room}")
    st.write(f"**Bed Layout Chosen:** {desc}")
    st.write(f"**Total Cost:** \${total} ± \$15 for {nights} nights")
    st.divider()
    if st.button("Close"):
        st.rerun()

# --- UI LOGIC ---
st.title("CO Springs AirBnB")
st.markdown(
    "<h2 style='font-weight: 500; margin-top: -10px;'>Bed & Room Selection with approximate prices</h2>", 
    unsafe_allow_html=True
)

user_name = st.selectbox("Who are you?", ["Select a name..."] + NAMES)

if user_name != "Select a name...":
    df = get_data()
    user_record = df[df['occupant'] == user_name]
    
    num_nights = st.radio("How many nights are you staying?", [2, 3], horizontal=True)
    st.divider()
    
    if not user_record.empty:
        current_bed = user_record.iloc[0]
        current_bed_id = int(current_bed['bed_id'])
        
        # Pull matching UI configuration item for accurate dynamic pricing displaying
        ui_bed_match = next((b for b in BED_DATA if b['id'] == current_bed_id), None)
        p_night = float(ui_bed_match['price']) if ui_bed_match else float(current_bed['price'])
        
        n_count = int(float(current_bed['nights']))
        total_p = int(p_night * n_count)
        
        # Dynamic fallback if sheet text description columns mismatch 
        bed_label = ui_bed_match['desc'] if ui_bed_match else current_bed.get('description', 'Your Selection')
        
        st.success(
            f"**Selection Saved!**\n\n"
            f"{current_bed['room']}, {bed_label}\n\n"
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
    
    rooms = ["BEDROOM A (Main Level)", "BEDROOM B (Main Level)", "BEDROOM C (Main Level)", 
             "BEDROOM D (Lower Level)", "BEDROOM E (Lower Level)"]
             
    # Pre-extract occupant logic specifically mapping out Bedroom D interlocking rules
    occ_8 = df[df['bed_id'] == 8].iloc[0]['occupant'] != ""
    occ_9 = df[df['bed_id'] == 9].iloc[0]['occupant'] != ""
    occ_17 = df[df['bed_id'] == 17].iloc[0]['occupant'] != "" if 17 in df['bed_id'].values else False

    name_8 = df[df['bed_id'] == 8].iloc[0]['occupant'] if occ_8 else ""
    name_9 = df[df['bed_id'] == 9].iloc[0]['occupant'] if occ_9 else ""
    name_17 = df[df['bed_id'] == 17].iloc[0]['occupant'] if occ_17 else ""

    for room in rooms:
        with st.expander(f"{room}", expanded=True):
            room_beds = [b for b in BED_DATA if b['room'] == room]
            
            # --- SPECIAL VISUAL LAYOUT FOR BEDROOM D ---
            if "BEDROOM D" in room:
                st.markdown(
                    "<p style='font-style: italic; color: #555; margin-top: -5px; margin-bottom: 20px;'>"
                    "This room contains one Queen Bed. <br>"
                    "2 Options: reserve the room for yourself OR share the bed with a friend. <br> <br>"
                    "[A shared spot in this room is cheaper than the one on the main floor since it has less convenient access to bathrooms. Most of the bathrooms are on the main floor]"
                    "</p>", 
                    unsafe_allow_html=True
                )
                
                # Create the two columns for side-by-side configurations
                col_solo, col_shared = st.columns(2)
                
                solo_beds = [b for b in room_beds if b['type'] == 'solo']
                shared_beds = [b for b in room_beds if b['type'] == 'shared']
                
                # Left Column: Solo Choice
                with col_solo:
                    for bed in solo_beds:
                        is_taken = False
                        blocking_msg = ""
                        if occ_8 or occ_9:
                            is_taken = True
                            roommates = [n for n in [name_8, name_9] if n != ""]
                            blocking_msg = f"Bed will be shared: {', '.join(roommates)}"
                        elif occ_17:
                            is_taken = True
                            db_row = df[df['bed_id'] == 17].iloc[0]
                            n_disp = int(float(db_row['nights'])) if db_row['nights'] != "" else 0
                            blocking_msg = f"{name_17} ({n_disp} nights)"
                        
                        st.write(f"**{bed['desc']}**")
                        st.caption(f"~\${bed['price']}/night")
                        
                        if is_taken:
                            st.error(f"**Unavailible:**\n\n{blocking_msg}")
                        else:
                            if st.button(f"Claim Solo Bed", key=f"btn_{bed['id']}", use_container_width=True):
                                success = update_bed(bed['id'], user_name, num_nights)
                                if success:
                                    st.cache_data.clear()
                                    total_val = int(bed['price'] * num_nights)
                                    show_success_modal(room, bed['desc'], total_val, num_nights)
                                else:
                                    st.error("Error. Someone might have just taken this bed!")
                
                # Right Column: Shared Choices
                with col_shared:
                    for bed in shared_beds:
                        is_taken = False
                        blocking_msg = ""
                        db_row = df[df['bed_id'] == bed['id']].iloc[0]
                        if occ_17:
                            is_taken = True
                            blocking_msg = f"Bed claimed by {name_17}"
                        elif db_row['occupant'] != "":
                            is_taken = True
                            n_disp = int(float(db_row['nights'])) if db_row['nights'] != "" else 0
                            blocking_msg = f"{db_row['occupant']} ({n_disp} nights)"
                        
                        st.write(f"**{bed['desc']}**")
                        st.caption(f"~\${bed['price']}/night")
                        
                        if is_taken:
                            st.error(f"**Unavailible:**\n\n{blocking_msg}")
                        else:
                            if st.button(f"Claim Shared Slot", key=f"btn_{bed['id']}", use_container_width=True):
                                success = update_bed(bed['id'], user_name, num_nights)
                                if success:
                                    st.cache_data.clear()
                                    total_val = int(bed['price'] * num_nights)
                                    show_success_modal(room, bed['desc'], total_val, num_nights)
                                else:
                                    st.error("Error. Someone might have just taken this bed!")
            
            # --- STANDARD VISUAL LAYOUT FOR ALL OTHER ROOMS ---
            else:
                for bed in room_beds:
                    db_row = df[df['bed_id'] == bed['id']].iloc[0]
                    is_taken = db_row['occupant'] != ""
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{bed['desc']}**")
                        st.caption(f"~\${bed['price']}/night")
                    
                    with col2:
                        if is_taken:
                             n_display = int(float(db_row['nights'])) if db_row['nights'] != "" else 0
                             st.error(f"**Unavailible:**\n\n"
                                      f"{db_row['occupant']} ({n_display} nights)")
                        else:
                            if st.button(f"Claim", key=f"btn_{bed['id']}"):
                                success = update_bed(bed['id'], user_name, num_nights)
                                if success:
                                    st.cache_data.clear() 
                                    total_val = int(bed['price'] * num_nights)
                                    show_success_modal(room, bed['desc'], total_val, num_nights)
                                else:
                                    st.error("Error. Someone might have just taken this bed!")
