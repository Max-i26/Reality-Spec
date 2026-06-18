# RealityFrame

RealityFrame is a real-time computer vision project built with Python, OpenCV, and MediaPipe. It combines gesture recognition, background reconstruction, selective invisibility, and AR effects to create an interactive privacy and visual effects system.

## Features

* Gesture-controlled invisibility modes
* Partial invisibility using pinch/snap gesture
* Full invisibility using L-hand gesture
* Custom focus area selection
* Real-time background reconstruction
* AR overlay support
* Smooth blending and masking effects

## Practical Uses

### Online Meetings

Keep only your workspace visible while hiding distractions around you. This can prevent people walking behind you from appearing on camera and helps maintain privacy during calls.

### Content Creation

Create unique visual effects and selective visibility regions without requiring a green screen.

### Privacy Enhancement

Hide unwanted areas of a room while keeping important objects or workspaces visible.

## Controls

| Action                | Control              |
| --------------------- | -------------------- |
| Partial Invisibility  | Pinch / Snap Gesture |
| Full Invisibility     | L-Hand Gesture       |
| Start Focus Selection | F                    |
| Select Visible Region | 4 Mouse Clicks       |
| Reset Selection       | R                    |
| Quit Application      | Q                    |

## Project Structure

```text
RealityFrame/
│
├── ar/
│   ├── ar_renderer.py
│   ├── overlay_factory.py
│   └── target_tracker.py
│
├── assets/
│   └── marker_0.png
│
├── core/
│   └── background.py
│
├── graphics/
│   └── renderer.py
│
├── tools/
│   ├── generate_marker.py
│   └── test_marker.py
│
├── vision/
│   ├── gesture.py
│   ├── hand_tracker.py
│   └── portal_detector.py
│
├── main.py
└── requirements.txt
```

## Technologies Used

* Python
* OpenCV
* MediaPipe
* NumPy
* Computer Vision
* Image Processing
* Gesture Recognition

## Installation

```bash
git clone https://github.com/yourusername/RealityFrame.git
cd RealityFrame
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Future Improvements

* Advanced AR object placement
* Multi-user tracking
* Additional gesture controls
* Improved segmentation quality
* Object-specific invisibility modes

Built as an exploration of real-time computer vision, gesture interaction, privacy-focused camera systems, and augmented reality concepts.
