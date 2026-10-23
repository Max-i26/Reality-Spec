import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

def draw_hud_box(img, x1, y1, x2, y2, color=(0, 229, 255), bracket_len=20, thickness=2):
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 1)
    # 4 Corner Brackets
    cv2.line(img, (x1, y1), (x1 + bracket_len, y1), color, thickness)
    cv2.line(img, (x1, y1), (x1, y1 + bracket_len), color, thickness)
    cv2.line(img, (x2, y1), (x2 - bracket_len, y1), color, thickness)
    cv2.line(img, (x2, y1), (x2, y1 + bracket_len), color, thickness)
    cv2.line(img, (x1, y2), (x1 + bracket_len, y2), color, thickness)
    cv2.line(img, (x1, y2), (x1, y2 - bracket_len), color, thickness)
    cv2.line(img, (x2, y2), (x2 - bracket_len, y2), color, thickness)
    cv2.line(img, (x2, y2), (x2, y2 - bracket_len), color, thickness)

def main():
    hand_model_path = 'public/models/hand_landmarker.task'
    segmenter_model_path = 'public/models/selfie_segmenter.task'

    # Initialize Hand Landmarker tracking 2 hands for dual-hand portal box
    hand_base_options = python.BaseOptions(model_asset_path=hand_model_path)
    hand_options = vision.HandLandmarkerOptions(
        base_options=hand_base_options,
        num_hands=2,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6
    )
    hand_detector = vision.HandLandmarker.create_from_options(hand_options)

    # Initialize Selfie Segmenter with continuous confidence masks
    seg_base_options = python.BaseOptions(model_asset_path=segmenter_model_path)
    seg_options = vision.ImageSegmenterOptions(
        base_options=seg_base_options,
        running_mode=vision.RunningMode.IMAGE,
        output_confidence_masks=True
    )
    segmenter = vision.ImageSegmenter.create_from_options(seg_options)

    cap = cv2.VideoCapture(0)

    # Modes: 'normal', 'invisibility', 'portal', 'virtual_bg'
    active_mode = 'normal'
    is_mirrored = True
    background_frame = None

    # Virtual Background Gradient
    virtual_bg = np.zeros((480, 640, 3), dtype=np.uint8)
    for y in range(480):
        virtual_bg[y, :] = [int(130 * (y / 480)), int(25 * (1 - y / 480)), int(180 * (y / 480))]

    print("\n=== Reality-Spec Desktop Engine ===")
    print("Keyboard Shortcuts:")
    print("  'm' : Toggle Mirror Mode")
    print("  'c' : Calibrate Room Background (Step out of view first)")
    print("  'i' : Full Face & Body Invisibility Cloak")
    print("  'p' : Dual-Hand Invisibility Portal Box (Spread hands to resize)")
    print("  'b' : Virtual Background")
    print("  'q' : Quit Application")
    print("===================================\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (640, 480))
        h, w, c = frame.shape

        if is_mirrored:
            frame = cv2.flip(frame, 1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # 1. Dual-Hand Tracking
        hand_results = hand_detector.detect(mp_image)

        # 2. Complete Face & Body Mask (Confidence > 0.42 + Morphological dilation)
        person_mask = None
        if active_mode in ['invisibility', 'virtual_bg']:
            seg_results = segmenter.segment(mp_image)
            conf_mask = np.squeeze(seg_results.confidence_masks[0].numpy_view())
            raw_mask = conf_mask > 0.42
            kernel = np.ones((5, 5), np.uint8)
            person_mask = cv2.dilate(raw_mask.astype(np.uint8), kernel, iterations=1).astype(bool)

        output_frame = frame.copy()

        # Mode: Full Invisibility (Face & Body)
        if active_mode == 'invisibility':
            if background_frame is not None and person_mask is not None:
                output_frame = np.where(person_mask[:, :, None], background_frame, frame)
            else:
                cv2.putText(output_frame, "PRESS 'C' TO CALIBRATE ROOM FIRST!", (40, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Mode: Dual-Hand / Single-Hand Invisibility Portal Box
        elif active_mode == 'portal':
            if background_frame is not None:
                bx1, by1, bx2, by2 = 0, 0, 0, 0
                portal_found = False
                num_hands = len(hand_results.hand_landmarks) if hand_results.hand_landmarks else 0

                if num_hands >= 2:
                    h1 = hand_results.hand_landmarks[0][8]
                    h2 = hand_results.hand_landmarks[1][8]
                    xa, ya = int(h1.x * w), int(h1.y * h)
                    xb, yb = int(h2.x * w), int(h2.y * h)

                    bx1 = max(0, min(xa, xb) - 15)
                    by1 = max(0, min(ya, yb) - 15)
                    bx2 = min(w, max(xa, xb) + 15)
                    by2 = min(h, max(ya, yb) + 15)
                    portal_found = True
                elif num_hands == 1:
                    hand = hand_results.hand_landmarks[0]
                    cx, cy = int(hand[8].x * w), int(hand[8].y * h)
                    pinch = np.hypot(hand[4].x - hand[8].x, hand[4].y - hand[8].y)
                    sz = int(np.clip(pinch * 800, 50, 360))
                    bx1 = max(0, cx - sz // 2)
                    by1 = max(0, cy - sz // 2)
                    bx2 = min(w, cx + sz // 2)
                    by2 = min(h, cy + sz // 2)
                    portal_found = True

                if portal_found and (bx2 > bx1 + 10) and (by2 > by1 + 10):
                    output_frame[by1:by2, bx1:bx2] = background_frame[by1:by2, bx1:bx2]
                    draw_hud_box(output_frame, bx1, by1, bx2, by2)
            else:
                cv2.putText(output_frame, "PRESS 'C' TO CALIBRATE ROOM FIRST!", (40, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Mode: Virtual Background
        elif active_mode == 'virtual_bg':
            if person_mask is not None:
                output_frame = np.where(person_mask[:, :, None], frame, virtual_bg)

        # Draw Hand Landmark Points
        if hand_results.hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(hand_results.hand_landmarks):
                color = (0, 229, 255) if hand_idx == 0 else (168, 85, 247)
                cx, cy = int(hand_landmarks[8].x * w), int(hand_landmarks[8].y * h)
                cv2.circle(output_frame, (cx, cy), 9, color, -1)

        # Bottom HUD Status
        status_txt = f"Mode: {active_mode.upper()} | Mirrored: {is_mirrored}"
        cv2.putText(output_frame, status_txt, (20, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        cv2.imshow("Reality-Spec Vision Engine", output_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            is_mirrored = not is_mirrored
        elif key == ord('c'):
            background_frame = frame.copy()
            print("Background room calibrated!")
        elif key == ord('i'):
            active_mode = 'normal' if active_mode == 'invisibility' else 'invisibility'
        elif key == ord('p'):
            active_mode = 'normal' if active_mode == 'portal' else 'portal'
        elif key == ord('b'):
            active_mode = 'normal' if active_mode == 'virtual_bg' else 'virtual_bg'

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
