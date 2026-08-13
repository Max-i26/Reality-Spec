# Tutorial: Build an Interactive AI Webcam Dashboard (Python)

This guide is designed to help you teach your friend how to build the computer vision privacy project in **Python** using **OpenCV** and **MediaPipe**. This guide is beginner-friendly and goes step-by-step from setting up the environment to drawing live AI overlays on the webcam stream.

---

## 📅 Roadmap Overview
1. **Environment & Setup**: Creating a Python virtual environment and installing packages.
2. **Open the Camera**: Building a simple OpenCV window to display the camera feed.
3. **Add Palm Tracking**: Integrating MediaPipe Hand Tracking to detect hands.
4. **Trigger Actions**:
   *   **Mirror Mode**: Mirroring the feed horizontally.
   *   **Invisibility**: Hiding yourself against a pre-captured background.
   *   **Virtual Background**: Swapping your background with an image.
5. **Streaming**: How to stream this output to Zoom, Teams, or Discord.

---

## Step 1: Environment Setup

### 1. Install Python
Make sure you have [Python 3.9 - 3.11](https://www.python.org/downloads/) installed. (MediaPipe works best with these versions).

### 2. Create and Activate a Virtual Environment (`venv`)
Open your terminal/command prompt and run:

*   **Windows**:
    ```bash
    python -m venv env
    .\env\Scripts\activate
    ```
*   **macOS / Linux**:
    ```bash
    python3 -m venv env
    source env/bin/activate
    ```

### 3. Install Dependencies
Install OpenCV for camera control and MediaPipe for AI hand tracking:
```bash
pip install opencv-python mediapipe numpy
```

---

## Step 2: Open the Camera (Hello World of CV)

Create a file named `main.py` and add this code to make sure the webcam opens and displays successfully:

```python
import cv2

def main():
    # 0 is usually the default built-in webcam
    cap = cv2.VideoCapture(0)

    print("Press 'q' on your keyboard to exit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Display the live feed
        cv2.imshow("AI Webcam Control", frame)

        # Exit when the user presses 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
```
Run it in your terminal:
```bash
python main.py
```

---

## Step 3: Integrating Palm Tracking

We will add hand detection using **MediaPipe**. Update your `main.py` to:

```python
import cv2
import mediapipe as mp

def main():
    cap = cv2.VideoCapture(0)

    # Initialize MediaPipe Hand solutions
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # MediaPipe requires RGB images, but OpenCV reads in BGR
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        # If a hand is detected
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw the full hand skeletons on the screen
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Get specific landmark coordinates (e.g., Index Finger Tip is index 8)
                h, w, c = frame.shape
                index_tip = hand_landmarks.landmark[8]
                cx, cy = int(index_tip.x * w), int(index_tip.y * h)

                # Draw a glowing green circle on the index fingertip
                cv2.circle(frame, (cx, cy), 15, (0, 255, 136), -1)

        cv2.imshow("AI Webcam Control", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
```

---

## Step 4: Logic for Features (Invisibility & Background Swaps)

Now, let's create a complete interactive script. We will add keys to control modes:
*   `m` to toggle **Mirror Mode**
*   `c` to **Calibrate / Capture Room Background**
*   `i` to toggle **Invisibility**
*   `b` to toggle **Virtual Background Image**

Save this code in `main.py`:

```python
import cv2
import mediapipe as mp
import numpy as np

def main():
    cap = cv2.VideoCapture(0)

    # MediaPipe Setup
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

    # App States
    is_mirrored = False
    is_invisible = False
    use_bg_image = False
    
    background_frame = None  # Captured background
    virtual_bg = None        # Loaded custom image

    # Create a dummy colored background (or load an image with cv2.imread('bg.jpg'))
    # Creating a cyber blue screen:
    virtual_bg = np.zeros((480, 640, 3), dtype=np.uint8)
    virtual_bg[:] = [100, 20, 20]  # dark red/blue color

    print("Keyboard Controls:")
    print(" 'm' - Toggle Mirror")
    print(" 'c' - Capture Background (Stand out of frame first)")
    print(" 'i' - Toggle Invisibility")
    print(" 'b' - Toggle Virtual Background")
    print(" 'q' - Exit")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Resize to standard size
        frame = cv2.resize(frame, (640, 480))
        h, w, c = frame.shape

        # Mirror Option
        if is_mirrored:
            frame = cv2.flip(frame, 1)

        # AI tracking processing
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        # Base output frame setup
        output_frame = frame.copy()

        if is_invisible and background_frame is not None:
            # Full invisibility: replace output frame with the captured background
            output_frame = background_frame.copy()
        elif use_bg_image and virtual_bg is not None:
            # Swapped Virtual Background
            output_frame = virtual_bg.copy()

        # Handle Palm / Hand Tracking Overlays
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Find Index Tip coordinates
                index_tip = hand_landmarks.landmark[8]
                cx, cy = int(index_tip.x * w), int(index_tip.y * h)
                
                # Draw tracking dot
                cv2.circle(output_frame, (cx, cy), 12, (0, 255, 136), -1)

                # Simple Gesture logic: Detect if Hand is Open
                thumb_tip = hand_landmarks.landmark[4]
                pinky_tip = hand_landmarks.landmark[20]
                dist = np.hypot(thumb_tip.x - pinky_tip.x, thumb_tip.y - pinky_tip.y)
                
                if dist > 0.4:
                    cv2.putText(output_frame, "OPEN PALM ACTIVE", (20, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 136), 2)

        # Draw current mode status text
        status_text = f"Mirror: {is_mirrored} | Invisibility: {is_invisible} | BgImage: {use_bg_image}"
        cv2.putText(output_frame, status_text, (20, 450), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Show Output
        cv2.imshow("AI Webcam Control", output_frame)

        # Handle Key Inputs
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            is_mirrored = not is_mirrored
        elif key == ord('c'):
            # Stand out of frame and capture the empty room
            background_frame = frame.copy()
            print("Background room captured!")
        elif key == ord('i'):
            if background_frame is None:
                print("Error: Capture background first by pressing 'c'!")
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
```

---

## Step 5: Streaming to Zoom/Discord (Virtual Camera)

To turn this Python output into a virtual camera that Zoom, Teams, or Discord can recognize:

1. Install the `pyvirtualcam` package:
   ```bash
   pip install pyvirtualcam
   ```
2. Note: You will need to install a virtual camera driver:
   * **Windows**: Install [OBS Studio](https://obsproject.com/) (which installs a virtual camera driver) or [Unity Capture](https://github.com/schellingb/UnityCapture).
   * **macOS**: Install [OBS Studio](https://obsproject.com/).
3. Update your Python script to output to `pyvirtualcam`:
   ```python
   import pyvirtualcam

   # Inside your loop:
   with pyvirtualcam.Camera(width=640, height=480, fps=30) as cam:
       # ...
       # Send RGB frame to virtual camera
       rgb_out = cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB)
       cam.send(rgb_out)
       cam.sleep_until_next_frame()
   ```
