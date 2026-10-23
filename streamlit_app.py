import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from PIL import Image

# Page Configuration & Futuristic UI Theme
st.set_page_config(
    page_title="Reality-Spec // Next-Gen Vision Hub",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Quality Glassmorphic Cyberpunk Styling
st.markdown("""
<style>
  /* Global Background & Fonts */
  .stApp {
    background: radial-gradient(circle at 15% 15%, #0f1026 0%, #060712 100%);
    color: #f0f2fd;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  }
  
  /* Top Banner Card */
  .hud-banner {
    background: rgba(18, 20, 42, 0.65);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 229, 255, 0.25);
    border-radius: 14px;
    padding: 16px 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .hud-title {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 2px;
    background: linear-gradient(90deg, #00e5ff, #a855f7, #00ff88);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
  }

  /* Status Tags */
  .badge-tag {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  .badge-active {
    background: rgba(0, 255, 136, 0.15);
    color: #00ff88;
    border: 1px solid rgba(0, 255, 136, 0.4);
  }
  .badge-portal {
    background: rgba(0, 229, 255, 0.15);
    color: #00e5ff;
    border: 1px solid rgba(0, 229, 255, 0.4);
  }

  /* Card Containers */
  .glass-card {
    background: rgba(16, 18, 36, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 16px;
  }
  
  /* Sidebar Tweaks */
  section[data-testid="stSidebar"] {
    background-color: #090a18;
    border-right: 1px solid rgba(0, 229, 255, 0.15);
  }
  
  /* Buttons */
  div.stButton > button {
    background: linear-gradient(135deg, #00e5ff 0%, #7928ca 100%) !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3) !important;
  }
  div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 229, 255, 0.5) !important;
  }
</style>
""", unsafe_allow_html=True)

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
        bg[:] = [15, 10, 20]
        cv2.circle(bg, (w // 2, h // 2), 170, (80, 25, 70), -1)
        cv2.circle(bg, (w // 3, h // 3), 120, (50, 70, 30), -1)
        bg = cv2.GaussianBlur(bg, (99, 99), 0)
        for _ in range(130):
            sx = int(np.random.randint(0, w))
            sy = int(np.random.randint(0, h))
            br = int(np.random.randint(160, 255))
            cv2.circle(bg, (sx, sy), 1, (br, br, br), -1)
        return bg

    elif preset_name == "Modern Studio":
        bg = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            ratio = y / h
            bg[y, :] = [int(35 + 30 * ratio), int(40 + 35 * ratio), int(48 + 40 * ratio)]
        cv2.circle(bg, (int(w * 0.75), int(h * 0.3)), 190, (90, 120, 140), -1)
        bg = cv2.GaussianBlur(bg, (99, 99), 0)
        return bg

    return np.zeros((h, w, 3), dtype=np.uint8)

# Initialize Models (num_hands=2 for two-hand portal stretching)
if "hand_detector" not in st.session_state:
    hand_model_path = 'public/models/hand_landmarker.task'
    base_options = python.BaseOptions(model_asset_path=hand_model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=2,  # Tracks both hands simultaneously
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6
    )
    st.session_state.hand_detector = vision.HandLandmarker.create_from_options(options)

if "segmenter" not in st.session_state:
    segmenter_model_path = 'public/models/selfie_segmenter.task'
    base_options = python.BaseOptions(model_asset_path=segmenter_model_path)
    options = vision.ImageSegmenterOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        output_confidence_masks=True  # Continuous confidence for full face+body coverage
    )
    st.session_state.segmenter = vision.ImageSegmenter.create_from_options(options)

if "calibrated_bg" not in st.session_state:
    st.session_state.calibrated_bg = None

# Top Futuristic HUD Header
st.markdown("""
<div class="hud-banner">
  <div>
    <h1 class="hud-title">REALITY // SPEC</h1>
    <div style="color: #94a3b8; font-size: 13px; margin-top: 4px;">Next-Gen Computer Vision & Neural Invisibility Suite</div>
  </div>
  <div>
    <span class="badge-tag badge-active">● System Live</span>
    <span class="badge-tag badge-portal">MediaPipe Tasks v1.0</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown("### 🎛️ Control Deck")
run_cam = st.sidebar.checkbox("Start Live Stream", value=True)
mirror_mode = st.sidebar.checkbox("Mirror Feed", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🪄 Vision Modes")
bg_mode = st.sidebar.selectbox(
    "Active Mode",
    [
        "Default Feed",
        "Body Invisibility Cloak (Full Body & Face)",
        "Invisible Portal (Dual-Hand & Mouse Box)",
        "Virtual Background (Preset / Custom Image)",
        "AI Background Blur"
    ]
)

# Detailed Mode Settings
invisibility_opacity = 1.0
blur_amount = 35
selected_preset = "Cyberpunk Neon"
custom_bg_file = None

portal_control_mode = "Dual-Hand Gestures"
manual_x = 220
manual_y = 120
manual_w = 240
manual_h = 240

if bg_mode == "Body Invisibility Cloak (Full Body & Face)":
    invisibility_opacity = st.sidebar.slider(
        "Cloak Transparency (100% = Full Vanish, 50% = Predator Camo)",
        min_value=0.1, max_value=1.0, value=1.0, step=0.05
    )
    edge_dilation = st.sidebar.slider("Edge Coverage (Ensures Hair & Face are covered)", min_value=1, max_value=9, value=5, step=2)

elif bg_mode == "Invisible Portal (Dual-Hand & Mouse Box)":
    portal_control_mode = st.sidebar.radio(
        "Portal Control Mechanism",
        ["Dual-Hand Gestures (Move hands apart)", "Mouse / Manual Sliders"]
    )
    if portal_control_mode == "Mouse / Manual Sliders":
        st.sidebar.markdown("**Manual Box Coordinates:**")
        manual_x = st.sidebar.slider("Box Position X", 0, 500, 200, 10)
        manual_y = st.sidebar.slider("Box Position Y", 0, 360, 100, 10)
        manual_w = st.sidebar.slider("Box Width", 50, 400, 240, 10)
        manual_h = st.sidebar.slider("Box Height", 50, 400, 240, 10)

elif bg_mode == "Virtual Background (Preset / Custom Image)":
    bg_source = st.sidebar.radio("Backdrop Type", ["Built-in Presets", "Upload Custom Image"])
    if bg_source == "Built-in Presets":
        selected_preset = st.sidebar.selectbox("Choose Backdrop", ["Cyberpunk Neon", "Deep Space", "Modern Studio"])
    else:
        custom_bg_file = st.sidebar.file_uploader("Upload Image (JPG/PNG)", type=["jpg", "png", "jpeg"])

elif bg_mode == "AI Background Blur":
    blur_amount = st.sidebar.slider("Blur Radius", min_value=5, max_value=99, value=35, step=2)
    if blur_amount % 2 == 0:
        blur_amount += 1

# Room Calibration Section
st.sidebar.markdown("---")
st.sidebar.markdown("### 📸 Room Calibration")
st.sidebar.caption("Step completely out of view for 2 seconds, then click:")
if st.sidebar.button("📸 Calibrate Empty Room"):
    st.session_state.calibrate_request = True

# Main Layout Area
col_video, col_info = st.columns([3, 1])

with col_video:
    image_placeholder = st.empty()

with col_info:
    st.markdown("""
    <div class="glass-card">
      <h4 style="margin-top:0; color: #00e5ff;">Diagnostic Terminal</h4>
      <div id="diag-status" style="font-size: 13px; color: #94a3b8;">Awaiting camera frames...</div>
    </div>
    """, unsafe_allow_html=True)
    status_diag = st.empty()
    
    st.markdown(f"""
    <div class="glass-card">
      <h4 style="margin-top:0; color: #a855f7;">Mode Operations Guide</h4>
      <p style="font-size: 12px; line-height: 1.6; color: #cbd5e1;">
        <b>1. Full Body & Face Invisibility</b>:<br>
        Calibrate the room first. The AI isolates your full face, hair, and body to render you completely invisible while keeping the room live.<br><br>
        <b>2. Dual-Hand Invisibility Box</b>:<br>
        Hold up <b>both hands</b>: the box forms between your two index fingertips! Spread your hands apart to enlarge the portal box, or use the mouse sliders.<br><br>
        <b>3. Virtual Backgrounds</b>:<br>
        Isolates you seamlessly in front of procedural sci-fi backdrops or your uploaded image.
      </p>
    </div>
    """, unsafe_allow_html=True)

# Load custom background image if uploaded
loaded_custom_bg = None
if custom_bg_file is not None:
    try:
        pil_img = Image.open(custom_bg_file)
        loaded_custom_bg = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        st.error(f"Error loading image: {e}")

# Helper: Draw Sci-Fi Glowing Corner Brackets for the Portal Box
def draw_hud_box(img, x1, y1, x2, y2, color=(0, 229, 255), bracket_len=24, thickness=2):
    # Main rectangle border
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 1)
    
    # Top-Left Bracket
    cv2.line(img, (x1, y1), (x1 + bracket_len, y1), color, thickness)
    cv2.line(img, (x1, y1), (x1, y1 + bracket_len), color, thickness)
    # Top-Right Bracket
    cv2.line(img, (x2, y1), (x2 - bracket_len, y1), color, thickness)
    cv2.line(img, (x2, y1), (x2, y1 + bracket_len), color, thickness)
    # Bottom-Left Bracket
    cv2.line(img, (x1, y2), (x1 + bracket_len, y2), color, thickness)
    cv2.line(img, (x1, y2), (x1, y2 - bracket_len), color, thickness)
    # Bottom-Right Bracket
    cv2.line(img, (x2, y2), (x2 - bracket_len, y2), color, thickness)
    cv2.line(img, (x2, y2), (x2, y2 - bracket_len), color, thickness)
    
    # HUD Label
    cv2.putText(img, f"[ PORTAL BOX: {x2-x1}x{y2-y1} ]", (x1 + 6, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1)

# Main Webcam Execution Loop
if run_cam:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("Error: Could not access the webcam. Please verify camera permissions.")
        run_cam = False

    while run_cam:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to read frame from webcam.")
            break

        frame = cv2.resize(frame, (640, 480))
        h, w, c = frame.shape

        if mirror_mode:
            frame = cv2.flip(frame, 1)

        # Room Calibration Trigger
        if getattr(st.session_state, "calibrate_request", False):
            st.session_state.calibrated_bg = frame.copy()
            st.session_state.calibrate_request = False
            st.toast("Room calibrated successfully! You can now activate Invisibility.")

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # 1. Hand Tracking (tracks up to 2 hands)
        hand_results = st.session_state.hand_detector.detect(mp_image)

        # 2. Human Body + Face Segmentation (Full Coverage using Continuous Confidence Masks)
        person_mask = None
        if bg_mode in [
            "Body Invisibility Cloak (Full Body & Face)",
            "Virtual Background (Preset / Custom Image)",
            "AI Background Blur"
        ]:
            seg_result = st.session_state.segmenter.segment(mp_image)
            # Use confidence mask 0: Values > 0.45 accurately capture face, hair, and clothing
            conf_mask = np.squeeze(seg_result.confidence_masks[0].numpy_view())
            raw_mask = conf_mask > 0.42
            
            # Morphological dilation ensures edges (ears, jawline, hair, and chin) are fully covered
            dilation_k = edge_dilation if bg_mode == "Body Invisibility Cloak (Full Body & Face)" else 3
            kernel = np.ones((dilation_k, dilation_k), np.uint8)
            person_mask = cv2.dilate(raw_mask.astype(np.uint8), kernel, iterations=1).astype(bool)

        output_frame = frame.copy()

        # ==================== MODE 1: BODY + FACE INVISIBILITY CLOAK ====================
        if bg_mode == "Body Invisibility Cloak (Full Body & Face)":
            if st.session_state.calibrated_bg is not None:
                if person_mask is not None:
                    calibrated = st.session_state.calibrated_bg
                    if invisibility_opacity >= 0.98:
                        # Full Invisibility: 100% of Face & Body vanish into the room!
                        output_frame = np.where(person_mask[:, :, None], calibrated, frame)
                    else:
                        # Semi-transparent Ghost / Predator Camouflage
                        ghost = cv2.addWeighted(frame, 1.0 - invisibility_opacity, calibrated, invisibility_opacity, 0)
                        output_frame = np.where(person_mask[:, :, None], ghost, frame)
                status_diag.success("Body & Face Invisibility: ACTIVE")
            else:
                cv2.putText(output_frame, "CALIBRATE ROOM IN SIDEBAR FIRST!", (40, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                status_diag.warning("⚠️ Step out and click 'Calibrate Empty Room' in sidebar!")

        # ==================== MODE 2: RECTANGULAR INVISIBLE PORTAL (DUAL-HAND & MOUSE) ====================
        elif bg_mode == "Invisible Portal (Dual-Hand & Mouse Box)":
            if st.session_state.calibrated_bg is not None:
                bx1, by1, bx2, by2 = 0, 0, 0, 0
                portal_active = False

                if portal_control_mode == "Dual-Hand Gestures (Move hands apart)":
                    num_detected = len(hand_results.hand_landmarks) if hand_results.hand_landmarks else 0

                    if num_detected >= 2:
                        # DUAL HANDS DETECTED: Stretch box between both hands!
                        h1_tip = hand_results.hand_landmarks[0][8]
                        h2_tip = hand_results.hand_landmarks[1][8]

                        x_a, y_a = int(h1_tip.x * w), int(h1_tip.y * h)
                        x_b, y_b = int(h2_tip.x * w), int(h2_tip.y * h)

                        bx1 = max(0, min(x_a, x_b) - 15)
                        by1 = max(0, min(y_a, y_b) - 15)
                        bx2 = min(w, max(x_a, x_b) + 15)
                        by2 = min(h, max(y_a, y_b) + 15)
                        portal_active = True
                        status_diag.info("🙌 Dual Hands Detected: Box stretched between both hands!")

                    elif num_detected == 1:
                        # SINGLE HAND DETECTED: Box centered on hand, sized by thumb-index pinch
                        hand = hand_results.hand_landmarks[0]
                        index_tip = hand[8]
                        thumb_tip = hand[4]
                        
                        cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                        pinch_dist = np.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
                        box_size = int(np.clip(pinch_dist * 800, 50, 360))

                        bx1 = max(0, cx - box_size // 2)
                        by1 = max(0, cy - box_size // 2)
                        bx2 = min(w, cx + box_size // 2)
                        by2 = min(h, cy + box_size // 2)
                        portal_active = True
                        status_diag.info("☝️ Single Hand: Pinch thumb & index to resize box!")
                    else:
                        status_diag.warning("Hold up 1 or 2 hands to position & expand the Portal Box!")

                else:
                    # MOUSE / MANUAL SLIDERS
                    bx1 = manual_x
                    by1 = manual_y
                    bx2 = min(w, manual_x + manual_w)
                    by2 = min(h, manual_y + manual_h)
                    portal_active = True
                    status_diag.info("🖱️ Mouse Control: Adjust coordinates using the sidebar sliders.")

                if portal_active and (bx2 > bx1 + 10) and (by2 > by1 + 10):
                    # Replace area inside square/rectangular box with calibrated background
                    output_frame[by1:by2, bx1:bx2] = st.session_state.calibrated_bg[by1:by2, bx1:bx2]
                    # Draw futuristic sci-fi corner brackets
                    draw_hud_box(output_frame, bx1, by1, bx2, by2, color=(0, 229, 255))
            else:
                cv2.putText(output_frame, "CALIBRATE ROOM IN SIDEBAR FIRST!", (40, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                status_diag.warning("⚠️ Step out and click 'Calibrate Empty Room' in sidebar!")

        # ==================== MODE 3: VIRTUAL BACKGROUND ====================
        elif bg_mode == "Virtual Background (Preset / Custom Image)":
            if person_mask is not None:
                if loaded_custom_bg is not None:
                    target_bg = cv2.resize(loaded_custom_bg, (w, h))
                else:
                    target_bg = get_preset_bg(selected_preset, w, h)

                output_frame = np.where(person_mask[:, :, None], frame, target_bg)
                status_diag.success(f"Virtual Backdrop: {selected_preset if loaded_custom_bg is None else 'Custom Image'}")

        # ==================== MODE 4: AI BACKGROUND BLUR ====================
        elif bg_mode == "AI Background Blur":
            if person_mask is not None:
                blurred = cv2.GaussianBlur(frame, (blur_amount, blur_amount), 0)
                output_frame = np.where(person_mask[:, :, None], frame, blurred)
                status_diag.success(f"Background Blur: Intensity {blur_amount}")

        # Draw Glowing Hand Tracking Indicators
        if hand_results.hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(hand_results.hand_landmarks):
                # Color code hand 1 (cyan) and hand 2 (purple)
                h_color = (0, 229, 255) if hand_idx == 0 else (168, 85, 247)
                index_tip = hand_landmarks[8]
                cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                cv2.circle(output_frame, (cx, cy), 9, h_color, -1)
                cv2.circle(output_frame, (cx, cy), 13, h_color, 1)

        st_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)
        image_placeholder.image(st_frame, channels="RGB")

    cap.release()
else:
    status_diag.info("Stream paused.")
