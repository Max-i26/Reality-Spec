# RealityFrame // Reality-Spec 🌐

Reality-Spec is an interactive computer vision & augmented reality suite featuring real-time hand-tracking gestures, privacy invisibility cloaks, dynamically scalable portals, background blur, virtual backdrops, and virtual camera streaming.

The repository provides two complete implementations:
1. **Option A: Web Application Hub** (HTML5 + Three.js + MediaPipe Tasks Vision + Vite)
2. **Option B: Python Suite** (OpenCV + MediaPipe Tasks + Streamlit Web Dashboard + Virtual Camera)

---

## 🚀 Key Features

* **Invisible Portal**: Hover an invisibility lens over your hand and dynamically resize it by pinching or expanding your thumb and index fingers.
* **Full-Body Invisibility Cloak**: Disappear completely against a calibrated snapshot of your empty room.
* **AI Background Blur & Image Swap**: Real-time neural selfie segmentation isolating your silhouette.
* **3D AR Holograms & HUD**: High-tech sci-fi tracking matrices and 3D wireframes anchored to your hands.
* **Virtual Camera Streaming**: Send the processed feed directly to Zoom, Discord, Microsoft Teams, or Google Meet.

---

## 💻 Option A: Running the Web App (Vite)

### Prerequisites
* [Node.js](https://nodejs.org/) (Node 20.19.0 LTS or newer recommended)

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
*(Or specify host and port: `npx vite --port 8080 --host 127.0.0.1`)*

### 3. Open in Browser
Visit **[http://127.0.0.1:8080/](http://127.0.0.1:8080/)** or `http://localhost:5173/`.

### 4. Production Build
```bash
npm run build
```

---

## 🐍 Option B: Running the Python Suite

### Prerequisites
* [Python 3.9 - 3.13](https://www.python.org/downloads/)

### 1. Create and Activate Virtual Environment

* **Windows**:
  ```powershell
  python -m venv env
  .\env\Scripts\activate
  ```
* **macOS / Linux**:
  ```bash
  python3 -m venv env
  source env/bin/activate
  ```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Running Modes

#### Mode 1: Streamlit Interactive Web Dashboard (Recommended)
Features live sidebar controls, background calibration, hand-controlled resizing invisibility portal, and image uploads:
```bash
streamlit run streamlit_app.py
```
*Opens automatically at `http://localhost:8501`.*

#### Mode 2: Native OpenCV Window
Lightweight desktop window controlled via keyboard shortcuts:
```bash
python main.py
```
* **Keyboard Shortcuts**:
  * `m`: Toggle Mirror Mode
  * `c`: Calibrate empty room background
  * `i`: Toggle Invisibility Cloak
  * `b`: Toggle Virtual Background
  * `q`: Quit

#### Mode 3: Virtual Camera (For Zoom / Discord / Teams)
Streams the processed OpenCV feed as a fake webcam device:
```bash
python main2.py
```
*(Requires a virtual camera driver such as OBS Virtual Camera or Unity Capture).*

---

## 📁 Project Structure

```text
Reality-Spec/
├── index.html                 # Web Hub HTML entry point
├── package.json               # Node.js dependencies & scripts
├── requirements.txt           # Python dependencies
├── streamlit_app.py           # Streamlit AI Dashboard (Portal, Invisibility, Blur)
├── main.py                    # OpenCV + MediaPipe Tasks desktop app
├── main2.py                   # Virtual Camera streaming app
├── public/                    # Static assets & offline MediaPipe models
│   ├── favicon.svg
│   ├── icons.svg
│   └── models/
│       ├── hand_landmarker.task
│       ├── selfie_segmenter.task
│       └── selfie_segmenter.tflite
├── src/                       # Web Hub frontend modules
│   ├── ar.js                  # Three.js 3D & 2D HUD overlays
│   ├── background.js          # Background subtraction & composite canvas
│   ├── camera.js              # WebRTC MediaStream manager
│   ├── gestures.js            # MediaPipe landmark gesture rules
│   ├── main.js                # Core Web App coordinator
│   ├── recorder.js            # WebM Canvas recorder
│   └── style.css              # Cyberpunk glassmorphic design
├── tutorial_guide.md          # Web beginner teaching guide
└── tutorial_guide_python.md   # Python beginner teaching guide
```
