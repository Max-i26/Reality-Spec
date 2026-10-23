import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from PIL import Image

# Set up Page Layout
st.set_page_config(page_title="AI Privacy Webcam Center", layout="wide", initial_sidebar_state="expanded")

st.title("🛡️ AI Privacy Webcam Center (Streamlit)")
st.caption("Real-time AI webcam powered by MediaPipe Tasks. True Body Invisibility, Background Replacement, Resizable Portals, and Hand Gestures.")

# Background Preset Generators
@st.cache_data
def get_preset_bg(preset_name, w=640, h=480):
    if preset_name == "Cyberpunk Neon":
        bg = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            r = int(25 + 75 * (y / h))
            g = int(10 + 25 * (1 - y / h))
            b = int(70 + 130 * (y / h))
            bg[y, :] = [b, g, r]
        # Grid lines
        for x in range(0, w, 40):
            cv2.line(bg, (x, h - 140), (x, h), (180, 50, 180), 1)
        for y in range(h - 140, h, 20):
            cv2.line(bg, (0, y), (w, y), (180, 50, 180), 1)
        return bg

    elif preset_name == "Deep Space":
        np.random.seed(42)
        bg = np.zeros((h, w, 3), dtype=np.uint8)
        bg[:] = [20, 10, 15]
        cv2.circle(bg, (w // 2, h // 2), 160, (70, 20, 60), -1)
        cv2.circle(bg, (w // 3, h // 3), 110, (40, 60, 20), -1)
        bg = cv2.GaussianBlur(bg, (99, 99), 0)
        for _ in range(120):
            sx = int(np.random.randint(0, w))
            sy = int(np.random.randint(0, h))
            br = int(np.random.randint(150, 255))
            cv2.circle(bg, (sx, sy), 1, (br, br, br), -1)
        return bg

    elif preset_name == "Modern Studio":
        bg = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            ratio = y / h
            bg[y, :] = [int(40 + 30 * ratio), int(45 + 35 * ratio), int(50 + 40 * ratio)]
        cv2.circle(bg, (int(w * 0.75), int(h * 0.3)), 180, (90, 120, 140), -1)
        bg = cv2.GaussianBlur(bg, (99, 99), 0)
        return bg

    return np.zeros((h, w, 3), dtype=np.uint8)

# Initialize MediaPipe models in session state so they only load once
if "hand_detector" not in st.session_state:
    hand_model_path = 'public/models/hand_landmarker.task'
    base_options = python.BaseOptions(model_asset_path=hand_model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        min_hand_detection_confidence=0.7
    )
    st.session_state.hand_detector = vision.HandLandmarker.create_from_options(options)

if "segmenter" not in st.session_state:
    segmenter_model_path = 'public/models/selfie_segmenter.task'
    base_options = python.BaseOptions(model_asset_path=segmenter_model_path)
    options = vision.ImageSegmenterOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        output_category_mask=True
    )
    st.session_state.segmenter = vision.ImageSegmenter.create_from_options(options)

if "calibrated_bg" not in st.session_state:
    st.session_state.calibrated_bg = None

# Sidebar Controls
st.sidebar.header("🎛️ Control Panel")
run_cam = st.sidebar.checkbox("Start Webcam Feed", value=True)
mirror_mode = st.sidebar.checkbox("Mirror Output", value=True)

st.sidebar.subheader("Effects Mode")
bg_mode = st.sidebar.selectbox(
    "Select Effect",
    [
        "Default Feed",
        "Body Invisibility Cloak (Vanishing Body)",
        "Virtual Background (Image / Preset)",
        "Invisible Portal (Hand Controlled)",
        "AI Background Blur"
    ]
)

# Effect parameter controls
invisibility_opacity = 1.0
blur_amount = 25
selected_preset = "Cyberpunk Neon"
custom_bg_file = None

if bg_mode == "Body Invisibility Cloak (Vanishing Body)":
    invisibility_opacity = st.sidebar.slider(
        "Cloak Opacity (100% = Completely Vanished, 50% = Ghost Camo)",
        min_value=0.1, max_value=1.0, value=1.0, step=0.05
    )

elif bg_mode == "Virtual Background (Image / Preset)":
    bg_source = st.sidebar.radio("Background Source", ["Built-in Presets", "Upload Custom Image"])
    if bg_source == "Built-in Presets":
        selected_preset = st.sidebar.selectbox("Choose Preset Backdrop", ["Cyberpunk Neon", "Deep Space", "Modern Studio"])
    else:
        custom_bg_file = st.sidebar.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "png", "jpeg"])

elif bg_mode == "AI Background Blur":
    blur_amount = st.sidebar.slider("Blur Intensity", min_value=5, max_value=99, value=35, step=2)
    if blur_amount % 2 == 0:
        blur_amount += 1

# Room Calibration
st.sidebar.subheader("📸 Room Calibration")
st.sidebar.write("Step out of camera view, then click Calibrate:")
if st.sidebar.button("Calibrate Empty Room"):
    st.session_state.calibrate_request = True

# Main Layout
col_video, col_info = st.columns([3, 1])

with col_video:
    image_placeholder = st.empty()

with col_info:
    st.subheader("System Status")
    status_box = st.empty()
    status_box.info("Ready. Check 'Start Webcam Feed' to begin.")
    
    st.markdown("""
    ### 💡 Quick Guide:
    * **Body Invisibility Cloak**:
      1. Step out of the camera's view.
      2. Click **Calibrate Empty Room** in the sidebar.
      3. Step back in — **only your body disappears**, leaving the live room visible!
    * **Virtual Background**:
      * Instantly replaces your room background with Cyberpunk, Space, Studio, or your own image.
    * **Invisible Portal**:
      * Move your hand around.
      * Pinch your index finger and thumb closer/further to resize the invisibility lens!
    """)

# Load custom background image if provided
loaded_custom_bg = None
if custom_bg_file is not None:
    try:
        pil_img = Image.open(custom_bg_file)
        loaded_custom_bg = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        st.error(f"Error reading uploaded image: {e}")

# Video processing loop
if run_cam:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("Error: Could not access the webcam. Check if another app is using it.")
        run_cam = False

    while run_cam:
        ret, frame = cap.read()
        if not ret:
            st.error("Error: Failed to read frame from webcam.")
            break

        frame = cv2.resize(frame, (640, 480))
        h, w, c = frame.shape

        if mirror_mode:
            frame = cv2.flip(frame, 1)

        # Handle calibration request
        if getattr(st.session_state, "calibrate_request", False):
            st.session_state.calibrated_bg = frame.copy()
            st.session_state.calibrate_request = False
            st.toast("Room calibrated successfully!")

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # 1. Hand Tracking
        hand_results = st.session_state.hand_detector.detect(mp_image)

        # 2. Body Segmentation Mask (needed for Invisibility Cloak, Virtual Background, and Blur)
        segment_mask = None
        if bg_mode in [
            "Body Invisibility Cloak (Vanishing Body)",
            "Virtual Background (Image / Preset)",
            "AI Background Blur"
        ]:
            seg_result = st.session_state.segmenter.segment(mp_image)
            cat_mask = seg_result.category_mask.numpy_view()
            segment_mask = np.squeeze(cat_mask) > 0.5

        output_frame = frame.copy()

        # Effect 1: Body Invisibility Cloak (True Invisibility: Body disappears into calibrated room)
        if bg_mode == "Body Invisibility Cloak (Vanishing Body)":
            if st.session_state.calibrated_bg is not None:
                if segment_mask is not None:
                    calibrated = st.session_state.calibrated_bg
                    if invisibility_opacity >= 0.98:
                        # Full invisibility of body
                        output_frame = np.where(segment_mask[:, :, None], calibrated, frame)
                    else:
                        # Semi-transparent Ghost / Predator camo effect
                        ghost = cv2.addWeighted(frame, 1.0 - invisibility_opacity, calibrated, invisibility_opacity, 0)
                        output_frame = np.where(segment_mask[:, :, None], ghost, frame)
            else:
                st.warning("⚠️ Please click 'Calibrate Empty Room' in the sidebar first!")

        # Effect 2: Virtual Background (Body stays visible, room replaced)
        elif bg_mode == "Virtual Background (Image / Preset)":
            if segment_mask is not None:
                if loaded_custom_bg is not None:
                    target_bg = cv2.resize(loaded_custom_bg, (w, h))
                else:
                    target_bg = get_preset_bg(selected_preset, w, h)

                output_frame = np.where(segment_mask[:, :, None], frame, target_bg)

        # Effect 3: Invisible Portal (Hand-Controlled Lens)
        elif bg_mode == "Invisible Portal (Hand Controlled)":
            if st.session_state.calibrated_bg is not None:
                if hand_results.hand_landmarks:
                    for hand_landmarks in hand_results.hand_landmarks:
                        index_tip = hand_landmarks[8]
                        cx, cy = int(index_tip.x * w), int(index_tip.y * h)

                        thumb_tip = hand_landmarks[4]
                        pinch_dist = np.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
                        portal_radius = int(np.clip(pinch_dist * 600, 25, 300))

                        y_idx, x_idx = np.ogrid[:h, :w]
                        dist_sq = (x_idx - cx)**2 + (y_idx - cy)**2
                        portal_mask = dist_sq <= portal_radius**2

                        output_frame = np.where(portal_mask[:, :, None], st.session_state.calibrated_bg, frame)
                        cv2.circle(output_frame, (cx, cy), portal_radius, (0, 255, 136), 2)
                        cv2.putText(output_frame, f"Portal: {portal_radius}px", (cx - 40, max(20, cy - portal_radius - 8)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 136), 1)
            else:
                st.warning("⚠️ Please click 'Calibrate Empty Room' in the sidebar first!")

        # Effect 4: AI Background Blur
        elif bg_mode == "AI Background Blur":
            if segment_mask is not None:
                blurred = cv2.GaussianBlur(frame, (blur_amount, blur_amount), 0)
                output_frame = np.where(segment_mask[:, :, None], frame, blurred)

        # Draw Hand Landmark Indicator
        if hand_results.hand_landmarks:
            for hand_landmarks in hand_results.hand_landmarks:
                index_tip = hand_landmarks[8]
                cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                cv2.circle(output_frame, (cx, cy), 8, (0, 255, 136), -1)

                thumb_tip = hand_landmarks[4]
                pinky_tip = hand_landmarks[20]
                dist = np.hypot(thumb_tip.x - pinky_tip.x, thumb_tip.y - pinky_tip.y)
                if dist > 0.4:
                    cv2.putText(output_frame, "OPEN PALM DETECTED", (20, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 136), 2)
                    status_box.success("Palm: Open")
                else:
                    status_box.info("Palm: Tracking Active")
        else:
            status_box.warning("No Hands in view.")

        st_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)
        image_placeholder.image(st_frame, channels="RGB")

    cap.release()
else:
    status_box.info("Webcam paused.")
