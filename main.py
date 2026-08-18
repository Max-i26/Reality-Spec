import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

def main():
    # Path to the pre-downloaded hand landmarker task file
    model_path = 'public/models/hand_landmarker.task'
    
    # Initialize the MediaPipe Hand Landmarker Tasks API
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        min_hand_detection_confidence=0.7
    )
    detector = vision.HandLandmarker.create_from_options(options)

    # 0 is usually the default built-in webcam
    cap = cv2.VideoCapture(0)

    # App States
    is_mirrored = False
    is_invisible = False
    use_bg_image = False
    
    background_frame = None  # Captured room background
    virtual_bg = None        # Loaded custom background image

    # Create a custom digital background (solid deep-space blue/red color)
    # You can also load an image using: virtual_bg = cv2.imread('your_image.jpg')
    virtual_bg = np.zeros((480, 640, 3), dtype=np.uint8)
    virtual_bg[:] = [80, 20, 20]  # dark blue/red tone

    print("\n=== AI Webcam Control Center ===")
    print("Keyboard Controls:")
    print("  'm' : Toggle Mirror Mode")
    print("  'c' : Calibrate (Capture empty room background - step out of frame first!)")
    print("  'i' : Toggle Invisibility Shield")
    print("  'b' : Toggle Virtual Background")
    print("  'q' : Quit Application")
    print("===============================\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Unable to fetch webcam feed.")
            break

        # Resize for consistent dimensions
        frame = cv2.resize(frame, (640, 480))
        h, w, c = frame.shape

        # 1. Mirror Mode
        if is_mirrored:
            frame = cv2.flip(frame, 1)

        # Convert frame to RGB and wrap inside MediaPipe Image format
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Detect hand landmarks
        results = detector.detect(mp_image)

        # Determine target background mode
        output_frame = frame.copy()
        if is_invisible and background_frame is not None:
            # Full invisibility: replace output frame pixels with captured background
            output_frame = background_frame.copy()
        elif use_bg_image and virtual_bg is not None:
            # Swap background completely
            output_frame = virtual_bg.copy()

        # 2. Draw Hand Landmark Indicators
        if results.hand_landmarks:
            for hand_landmarks in results.hand_landmarks:
                # Find Index Tip coordinates (landmark index 8)
                index_tip = hand_landmarks[8]
                cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                
                # Draw a green tracking circle on fingertip
                cv2.circle(output_frame, (cx, cy), 12, (0, 255, 136), -1)

                # Simple Gesture logic: Detect if hand is fully open
                thumb_tip = hand_landmarks[4]
                pinky_tip = hand_landmarks[20]
                dist = np.hypot(thumb_tip.x - pinky_tip.x, thumb_tip.y - pinky_tip.y)
                
                if dist > 0.4:
                    cv2.putText(output_frame, "PALM TRACKED: OPEN", (20, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 136), 2)

        # 3. Render Status Overlay text at the bottom
        status_text = f"Mirror: {is_mirrored} | Invisibility: {is_invisible} | VirtualBg: {use_bg_image}"
        cv2.putText(output_frame, status_text, (20, 450), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Display final output frame
        cv2.imshow("AI Webcam Control", output_frame)

        # Listen for key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            is_mirrored = not is_mirrored
        elif key == ord('c'):
            # Copy current clean frame
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
