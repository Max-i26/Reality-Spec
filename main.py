import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

def main():
    # Model paths
    hand_model_path = 'public/models/hand_landmarker.task'
    segmenter_model_path = 'public/models/selfie_segmenter.task'

    # Initialize Hand Landmarker
    hand_base_options = python.BaseOptions(model_asset_path=hand_model_path)
    hand_options = vision.HandLandmarkerOptions(
        base_options=hand_base_options,
        num_hands=1,
        min_hand_detection_confidence=0.7
    )
    hand_detector = vision.HandLandmarker.create_from_options(hand_options)

    # Initialize Selfie Segmenter
    seg_base_options = python.BaseOptions(model_asset_path=segmenter_model_path)
    seg_options = vision.ImageSegmenterOptions(
        base_options=seg_base_options,
        running_mode=vision.RunningMode.IMAGE,
        output_category_mask=True
    )
    segmenter = vision.ImageSegmenter.create_from_options(seg_options)

    cap = cv2.VideoCapture(0)

    # App States
    is_mirrored = False
    is_invisible = False
    use_bg_image = False

    background_frame = None

    # Custom digital background gradient
    virtual_bg = np.zeros((480, 640, 3), dtype=np.uint8)
    for y in range(480):
        virtual_bg[y, :] = [int(120 * (y / 480)), int(30 * (1 - y / 480)), int(180 * (y / 480))]

    print("\n=== AI Webcam Control Center ===")
    print("Keyboard Controls:")
    print("  'm' : Toggle Mirror Mode")
    print("  'c' : Calibrate (Capture empty room background - step out of frame first!)")
    print("  'i' : Toggle True Body Invisibility (Only your body disappears!)")
    print("  'b' : Toggle Virtual Background (Replaces room background with backdrop)")
    print("  'q' : Quit Application")
    print("===============================\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Unable to fetch webcam feed.")
            break

        frame = cv2.resize(frame, (640, 480))
        h, w, c = frame.shape

        if is_mirrored:
            frame = cv2.flip(frame, 1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # 1. Hand Tracking
        hand_results = hand_detector.detect(mp_image)

        # 2. Body Segmentation Mask (computed when Invisibility or Virtual Background is active)
        segment_mask = None
        if is_invisible or use_bg_image:
            seg_results = segmenter.segment(mp_image)
            cat_mask = seg_results.category_mask.numpy_view()
            segment_mask = np.squeeze(cat_mask) > 0.5

        output_frame = frame.copy()

        # True Body Invisibility: Only the person's body disappears into the calibrated room
        if is_invisible and background_frame is not None and segment_mask is not None:
            output_frame = np.where(segment_mask[:, :, None], background_frame, frame)

        # Virtual Background: Only the background is replaced; the person stays visible
        elif use_bg_image and segment_mask is not None:
            output_frame = np.where(segment_mask[:, :, None], frame, virtual_bg)

        # Hand Tracking Overlay
        if hand_results.hand_landmarks:
            for hand_landmarks in hand_results.hand_landmarks:
                index_tip = hand_landmarks[8]
                cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                cv2.circle(output_frame, (cx, cy), 10, (0, 255, 136), -1)

                thumb_tip = hand_landmarks[4]
                pinky_tip = hand_landmarks[20]
                dist = np.hypot(thumb_tip.x - pinky_tip.x, thumb_tip.y - pinky_tip.y)
                if dist > 0.4:
                    cv2.putText(output_frame, "PALM: OPEN", (20, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 136), 2)

        # Status text
        status_text = f"Mirror: {is_mirrored} | Body Invisibility: {is_invisible} | VirtualBg: {use_bg_image}"
        cv2.putText(output_frame, status_text, (20, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        cv2.imshow("AI Webcam Control", output_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            is_mirrored = not is_mirrored
        elif key == ord('c'):
            background_frame = frame.copy()
            print("Room background calibrated/captured!")
        elif key == ord('i'):
            if background_frame is None:
                print("Warning: Press 'c' first to capture the room background!")
            else:
                is_invisible = not is_invisible
                use_bg_image = False
        elif key == ord('b'):
            use_bg_image = not use_bg_image
            is_invisible = False

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
