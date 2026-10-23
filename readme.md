# Reality-Spec: AI-Powered Real-Time Computer Vision Privacy & Augmented Reality System 🔮

> ### Project: Reality-Spec – AI-Powered Real-Time Computer Vision Privacy & Augmented Reality System
>
> The Reality-Spec AI-Powered Real-Time Computer Vision Privacy & Augmented Reality System is a technology-based project designed to transform standard webcam feeds using advanced computer vision and neural segmentation. The system detects human hands, tracks finger landmarks, isolates human silhouettes, and removes or modifies video backgrounds in real time to provide privacy, invisibility cloaks, and interactive augmented reality effects.
>
> By presenting seamless background replacement, dynamic hand-controlled invisibility portals, and virtual camera streaming, the system aims to demonstrate how artificial intelligence and computer vision can enhance personal privacy in video communication, support interactive remote collaboration, and deliver futuristic camera experiences without expensive hardware.

---

## 🚀 Key Features

* **Complete Face & Body Invisibility Cloak**:
  Uses neural selfie segmentation combined with continuous confidence masks and edge dilation to make 100% of your body and face vanish into a calibrated snapshot of your empty room, while keeping the live environment completely active in real time.
* **Dual-Hand & Mouse Resizable Invisibility Portal Box**:
  A futuristic rectangular portal box with sci-fi corner brackets. Raise both hands to stretch and resize the box between your index fingertips, pinch with a single hand, or adjust its position and dimensions manually using mouse sliders.
* **Ghost & Predator Camouflage Slider**:
  Adjust transparency between 10% and 100% to blend between live visibility, translucent holographic camouflage, or full disappearance.
* **Instant Virtual Backgrounds**:
  Replace your room background with built-in procedural sci-fi backdrops (Cyberpunk Neon, Deep Space, Modern Studio) or any uploaded JPG/PNG file without leaving artifacts around your hair.
* **AI Background Blur**:
  Smoothly blur the background with adjustable intensity while keeping your face and body sharply focused.
* **Virtual Camera Loopback**:
  Broadcast your augmented, privacy-filtered video stream directly into Zoom, Discord, Google Meet, or Microsoft Teams as a recognized webcam device.

---

## 🛠️ Step-by-Step Implementation & Running Guide

The repository includes two complete implementations:
* **Option 1: Streamlit & Python Suite** (Interactive web app + native OpenCV desktop engine + Virtual Camera)
* **Option 2: Web Hub** (Hardware-accelerated browser client built with Three.js & Vite)

---

### Option 1: Streamlit & Python Suite (Recommended)

#### Step 1: Clone the Repository & Open Terminal
```powershell
git clone https://github.com/Max-i26/Reality-Spec.git
cd Reality-Spec
```

#### Step 2: Set Up Virtual Environment
* **Windows (PowerShell)**:
  ```powershell
  python -m venv env
  .\env\Scripts\activate
  ```
* **macOS / Linux**:
  ```bash
  python3 -m venv env
  source env/bin/activate
  ```

#### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

#### Step 4: Run the Application

##### Mode A: Streamlit Interactive Web Dashboard (Best UI/UX)
```powershell
python -m streamlit run streamlit_app.py
```
* **Browser Access**: Automatically opens at **`http://localhost:8501`**.
* **How to use Invisibility**:
  1. Select **Body Invisibility Cloak** or **Invisible Portal** from the sidebar dropdown.
  2. Step completely out of camera view for 2 seconds.
  3. Click **📸 Calibrate Empty Room** in the sidebar.
  4. Step back into view: your face and body will completely vanish into the live room!
  5. For the **Invisible Portal Box**, raise both hands and move them apart to resize the portal, or toggle **Mouse / Manual Sliders** to adjust it using your mouse pointer.

##### Mode B: Native OpenCV Desktop App
```powershell
python main.py
```
* **Keyboard Shortcuts**:
  * `c` : Calibrate empty room background (*step out of view first*)
  * `i` : Toggle Full Face & Body Invisibility Cloak
  * `p` : Toggle Dual-Hand Invisibility Portal Box
  * `b` : Toggle Virtual Background
  * `m` : Toggle Mirror Mode
  * `q` : Exit

##### Mode C: Virtual Camera Streaming (For Zoom / Discord / Teams)
```powershell
python main2.py
```
*(Requires a virtual camera driver such as OBS Virtual Camera or Unity Capture installed on Windows).*

---

### Option 2: Web Hub (HTML5 + Three.js + Vite)

#### Step 1: Install Node.js Dependencies
```bash
npm install
```

#### Step 2: Start Development Server
```bash
npm run dev
```

#### Step 3: Open in Browser
Visit **[http://127.0.0.1:8080/](http://127.0.0.1:8080/)** in Google Chrome or Microsoft Edge.

#### Step 4: Production Build
```bash
npm run build
```

---

## 📁 Clean Repository Structure

```text
Reality-Spec/
├── index.html                 # Web Hub HTML entry point
├── package.json               # Node.js dependencies & scripts
├── package-lock.json          # Node.js locked dependency tree
├── vite.config.js             # Vite server config & watcher ignore rules
├── requirements.txt           # Python library dependencies
├── streamlit_app.py           # Futuristic Streamlit AI Privacy Dashboard
├── main.py                    # OpenCV + MediaPipe Tasks desktop application
├── main2.py                   # Virtual Camera streaming application
├── public/                    # Offline MediaPipe AI model bundles
│   ├── favicon.svg            # App icon
│   ├── icons.svg              # UI SVG sprite symbols
│   └── models/
│       ├── hand_landmarker.task     # 21-point dual-hand tracking model
│       ├── selfie_segmenter.task    # Neural human segmentation model
│       └── selfie_segmenter.tflite  # Float16 optimized model weights
├── src/                       # Web Hub frontend modules
│   ├── ar.js                  # Three.js 3D spatial holograms & 2D HUD
│   ├── background.js          # Canvas composite & noise-reduced averaging
│   ├── camera.js              # HTML5 WebRTC MediaStream manager
│   ├── gestures.js            # Landmark gesture recognition engine
│   ├── main.js                # Core Web Hub coordinator
│   ├── recorder.js            # In-browser WebM video recorder
│   └── style.css              # Cyberpunk glassmorphic design system
└── readme.md                  # Complete project documentation & guide
```

---

## 🔧 Troubleshooting

* **`ModuleNotFoundError: No module named 'mediapipe'` or `'toml'`**:
  Always execute Streamlit using `python -m streamlit run streamlit_app.py` after activating your virtual environment. This guarantees the interpreter uses the local `env` package path.
* **Webcam Access Error**:
  Ensure no other video conferencing app (such as Zoom, Teams, or Skype) is currently using your webcam before starting the script.
* **Virtual Camera not appearing in Zoom/Discord**:
  Ensure you have installed [OBS Studio](https://obsproject.com/) (and clicked "Start Virtual Camera" once to register the Windows driver) or [Unity Capture](https://github.com/schellingb/UnityCapture).
