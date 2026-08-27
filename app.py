import os
import glob
import json
import pandas as pd
import streamlit as st
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="PPE Detection Dashboard",
    page_icon="👷",
    layout="wide"
)

st.title("🎛️ PPE Safety & Equipment Analytics Dashboard")
st.markdown("Real-time monitoring and analytics for Personal Protective Equipment (PPE) compliance.")

# --- Helper Function: Locate Latest Saved Video ---
def get_latest_output_video():
    """Finds the most recently created video output in runs/detect/predict*."""
    dirs = glob.glob("runs/detect/predict*")
    if not dirs:
        return None
    
    # Sort folders by creation time to get the latest output
    latest_dir = max(dirs, key=os.path.getctime)
    
    # Check for AVI or MP4 files inside the latest run directory
    for file in os.listdir(latest_dir):
        if file.endswith((".mp4", ".avi")):
            return os.path.join(latest_dir, file)
            
    return None

# --- Step 1: Load Dashboard Metrics JSON ---
json_path = "dashboard_data.json"

if not os.path.exists(json_path):
    st.error(f"⚠️ Could not find `{json_path}` in the current directory.")
    st.info("Please run your processing script (`python process_video.py`) first to generate detection metrics.")
    st.stop()

with open(json_path, "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# --- Step 2: KPI Metrics Cards ---
total_frames = len(df)
max_persons = int(df["persons"].max()) if "persons" in df else 0
max_hardhats = int(df["hardhats"].max()) if "hardhats" in df else 0
total_violations = int(df["no_masks"].sum()) if "no_masks" in df else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric(label="Total Frames Processed", value=total_frames)
col2.metric(label="Max Persons Detected", value=max_persons)
col3.metric(label="Max Hardhats Seen", value=max_hardhats)
col4.metric(
    label="Total Safety Violations", 
    value=total_violations, 
    delta="-Violations" if total_violations > 0 else "Compliant",
    delta_color="inverse"
)

st.divider()

# --- Step 3: Main Dashboard Content (Video + Line Chart) ---
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("📹 Annotated Output Video")
    
    # First check for the dedicated web-ready MP4 file
    web_ready_video = "annotated_output.mp4"
    target_video = web_ready_video if os.path.exists(web_ready_video) else get_latest_output_video()
    
    if target_video and os.path.exists(target_video):
        st.caption(f"Loaded source: `{target_video}`")
        try:
            with open(target_video, "rb") as v_file:
                video_bytes = v_file.read()
            st.video(video_bytes)
        except Exception as e:
            st.error(f"Unable to play video file: {e}")
    else:
        st.warning("No detection output video was found in `runs/detect/` or root project folder.")

with right_col:
    st.subheader("📈 Detection Metrics Timeline")
    
    # Create interactive multi-line chart using Plotly
    fig = px.line(
        df,
        x="frame",
        y=["hardhats", "vests", "no_masks", "persons"],
        labels={"value": "Count", "frame": "Frame Index", "variable": "Class Category"},
        title="Equipment and Person Count per Frame"
    )
    
    fig.update_layout(
        hovermode="x unified",
        legend_title_text="Equipment Type",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Step 4: Data Inspection Table ---
st.subheader("📋 Frame-by-Frame Detection Log")

# Filter controls
equipment_filter = st.multiselect(
    "Filter Columns:",
    options=["hardhats", "vests", "no_masks", "persons"],
    default=["hardhats", "vests", "no_masks", "persons"]
)

if equipment_filter:
    st.dataframe(df[["frame"] + equipment_filter], use_container_width=True)
else:
    st.dataframe(df, use_container_width=True)