import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from PIL import Image

# Set up Page Layout
st.set_page_config(page_title="AI Privacy Webcam Center", layout="wide")

st.title("🛡️ AI Privacy Webcam Center (Streamlit)")
st.write("An interactive computer vision workspace combining hand-tracking gestures, invisible portals, background blur, and custom background images.")

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

# Persistent storage for background calibration frame
if "calibrated_bg" not in st.session_state:
    st.session_state.calibrated_bg = None

# Sidebar Controls
st.sidebar.header("🎛️ Control Panel")
run_cam = st.sidebar.checkbox("Start Webcam Feed", value=True)
mirror_mode = st.sidebar.checkbox("Mirror Output")

st.sidebar.subheader("Effects")
bg_mode = st.sidebar.selectbox(
    "Background Layer",
    [
        "Default Feed", 
        "Invisible Cloak (Full Body)", 
        "Invisible Portal (Hand Controlled)", 
        "AI Background Blur", 
        "Custom Background Image"
    ]
)

# Render specific options depending on the mode chosen
blur_amount = 25
if bg_mode == "AI Background Blur":
    blur_amount = st.sidebar.slider("Blur Intensity", min_value=5, max_value=99, value=25, step=2)
    # OpenCV requires odd kernel size for blur
    if blur_amount % 2 == 0:
        blur_amount += 1

custom_bg_file = None
if bg_mode == "Custom Background Image":
    custom_bg_file = st.sidebar.file_uploader("Upload custom background image", type=["jpg", "png", "jpeg"])

# Calibration Button (always visible in sidebar)
if st.sidebar.button("📸 Calibrate Background Room"):
    st.session_state.calibrate_request = True
    st.sidebar.success("Next frame will be saved as calibrated background room!")

# Layout Columns
col_video, col_diagnostics = st.columns([2, 1])

with col_video:
    st.subheader("🎥 Live AI Stream")
    image_placeholder = st.empty()

with col_diagnostics:
    st.subheader("📊 System Stats")
    status_msg = st.empty()
    status_msg.info("System Ready. Check 'Start Webcam Feed' to begin.")
    
    st.markdown("""
    **Instructions:**
    1. **Mirror**: Check the Box to mirror the camera.
    2. **Invisible Cloak (Full Body)**: Select this mode, step completely out of frame, click **Calibrate Background Room**, and step back in to disappear!
    3. **Invisible Portal (Hand Controlled)**: 
       * Step out of frame and click **Calibrate Background Room**.
       * Hold up your hand. The portal circle is centered on your hand.
       * **Pinch/Expand your index and thumb** closer or further apart to decrease/increase the size of your invisibility portal!
    4. **Background Blur / Image**: Uses AI Selfie Segmentation to isolate you and blur or replace the background.
    """)

# Custom Background Loader
loaded_custom_bg = None
if custom_bg_file is not None:
    try:
        uploaded_img = Image.open(custom_bg_file)
        loaded_custom_bg = cv2.cvtColor(np.array(uploaded_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        st.error(f"Error loading background image: {e}")

# Webcam Loop
if run_cam:
    cap = cv2.VideoCapture(0)
    
    # Check if webcam opened successfully
    if not cap.isOpened():
        st.error("Error: Could not access the webcam.")
        run_cam = False

    while run_cam:
        ret, frame = cap.read()
        if not ret:
            st.error("Error: Failed to read frame from webcam.")
            break

        # Resize for consistent layout dimensions
        frame = cv2.resize(frame, (640, 480))
        h, w, c = frame.shape

        # Mirror Mode
        if mirror_mode:
            frame = cv2.flip(frame, 1)

        # Trigger calibration if button was pressed
        if getattr(st.session_state, "calibrate_request", False):
            st.session_state.calibrated_bg = frame.copy()
            st.session_state.calibrate_request = False
            st.toast("Room calibrated successfully!")

        # Wrap in MediaPipe Image format
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # 1. Processing Hand Tracking
        hand_results = st.session_state.hand_detector.detect(mp_image)

        # 2. Processing Selfie Segmentation Mask (if needed for blur/swap)
        segment_mask = None
        if bg_mode in ["AI Background Blur", "Custom Background Image"]:
            segmentation_results = st.session_state.segmenter.segment(mp_image)
            category_mask = segmentation_results.category_mask.numpy_view()
            # Squeeze to handle potential 4D/3D shapes from different SDK versions
            segment_mask = np.squeeze(category_mask) > 0.5

        # 3. Assemble Output Frame
        output_frame = frame.copy()

        # Handle full body cloak
        if bg_mode == "Invisible Cloak (Full Body)":
            if st.session_state.calibrated_bg is not None:
                output_frame = st.session_state.calibrated_bg.copy()
            else:
                st.warning("⚠️ Calibrate background first in the sidebar!")
        
        # Handle hand-controlled portal
        elif bg_mode == "Invisible Portal (Hand Controlled)":
            if st.session_state.calibrated_bg is not None:
                # Default to normal frame
                output_frame = frame.copy()
                
                # Check if hand detected to place and size the portal
                if hand_results.hand_landmarks:
                    for hand_landmarks in hand_results.hand_landmarks:
                        # Index tip is center of portal
                        index_tip = hand_landmarks[8]
                        cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                        
                        # Use distance between thumb (4) and index (8) to control radius
                        thumb_tip = hand_landmarks[4]
                        pinch_dist = np.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
                        
                        # Scale pinch distance to radius in pixels (min: 20px, max: 300px)
                        portal_radius = int(np.clip(pinch_dist * 600, 20, 300))
                        
                        # Create circular mask for portal
                        y_indices, x_indices = np.ogrid[:h, :w]
                        dist_from_center = (x_indices - cx)**2 + (y_indices - cy)**2
                        portal_mask = dist_from_center <= portal_radius**2
                        
                        # Replace area inside circular portal with calibrated background
                        output_frame = np.where(portal_mask[:, :, None], st.session_state.calibrated_bg, frame)
                        
                        # Draw a glowing green border around the portal
                        cv2.circle(output_frame, (cx, cy), portal_radius, (0, 255, 136), 2)
                        cv2.putText(output_frame, f"Portal Radius: {portal_radius}px", (cx - 50, cy - portal_radius - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 136), 1)
            else:
                st.warning("⚠️ Calibrate background first in the sidebar!")

        elif bg_mode == "AI Background Blur" and segment_mask is not None:
            # Blur the background
            blurred_bg = cv2.GaussianBlur(frame, (blur_amount, blur_amount), 0)
            output_frame = np.where(segment_mask[:, :, None], frame, blurred_bg)

        elif bg_mode == "Custom Background Image" and segment_mask is not None:
            if loaded_custom_bg is not None:
                # Resize custom background to match stream
                resized_custom_bg = cv2.resize(loaded_custom_bg, (w, h))
                output_frame = np.where(segment_mask[:, :, None], frame, resized_custom_bg)
            else:
                # Fallback to simple colored background
                fallback_bg = np.zeros_like(frame)
                fallback_bg[:] = [120, 30, 30] # deep slate blue/red
                output_frame = np.where(segment_mask[:, :, None], frame, fallback_bg)

        # 4. Draw Hand Landmarking Indicator
        if hand_results.hand_landmarks:
            for hand_landmarks in hand_results.hand_landmarks:
                index_tip = hand_landmarks[8]
                cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                cv2.circle(output_frame, (cx, cy), 8, (0, 255, 136), -1)

                # Open/Close Gesture Text
                thumb_tip = hand_landmarks[4]
                pinky_tip = hand_landmarks[20]
                dist = np.hypot(thumb_tip.x - pinky_tip.x, thumb_tip.y - pinky_tip.y)
                if dist > 0.4:
                    cv2.putText(output_frame, "PALM TRACKED: OPEN", (20, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 136), 2)
                    status_msg.success("Hand Gesture: Open Palm detected!")
                else:
                    status_msg.info("Hand Gesture: Tracking Palm...")
        else:
            status_msg.warning("No Hands Detected in frame.")

        # Convert back to RGB for display in Streamlit
        st_frame = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)
        image_placeholder.image(st_frame, channels="RGB")

    cap.release()
else:
    status_msg.info("Webcam feed stopped.")
