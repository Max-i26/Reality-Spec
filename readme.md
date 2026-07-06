# RealityFrame // Web Hub 🌐

RealityFrame Web is a futuristic, hardware-accelerated computer vision and augmented reality webcam privacy dashboard running directly in the browser. Rebuilt from the ground up from the original command-line Python tools, it brings robust real-time hand-tracking gestures, virtual privacy filters (such as Portal and Full-body invisibility), custom 3D Three.js HUDs, and video capture directly to the web.

---

## 🚀 Key Features

*   **Real-Time Privacy Modes**:
    *   **Normal**: Clean pass-through webcam output.
    *   **Portal Invisibility**: Interactively define a window in your view where you are rendered invisible against a captured room background.
    *   **Full Invisibility**: Disappear entirely from the camera's sight while retaining full movement capabilities.
*   **Augmented Reality (AR) Overlays**:
    *   **Creeper Pixel Mask**: Retro-pixelated face mask.
    *   **Cyber HUD**: High-tech sci-fi tracking overlay on your hands.
    *   **Orbit 3D**: Dynamic 3D holographic wireframes orbiting your palms, rendered via Three.js.
*   **Gesture Control Bindings**:
    *   Bind specific gestures (like Thumbs Up, Victory, Fist, Pinch) to trigger instant actions (toggle AR filters, take screenshots, toggle privacy modes).
*   **Built-in Media Recorder**:
    *   Record and download your customized webcam canvas stream instantly.

---

## 🛠️ How to Run Locally

### Prerequisites
Make sure you have [Node.js](https://nodejs.org/) installed (recommended: Node 20.19.0 LTS or newer).

### Installation

1. Clone this repository (or copy the files) and navigate into the project directory:
   ```bash
   cd Reality-Spec
   ```

2. Install the package dependencies:
   ```bash
   npm install
   ```

### Running the Development Server

1. Start the local development server:
   ```bash
   npm run dev
   ```
   *Alternatively, run on a specific port and IPv4 binding:*
   ```bash
   npx vite --port 8080 --host 127.0.0.1
   ```

2. Open your web browser and go to:
   **[http://127.0.0.1:8080/](http://127.0.0.1:8080/)**

---

## 📦 Production Build

To compile and minify the project for production deployment, run:
```bash
npm run build
```
This generates a highly optimized production bundle inside the `dist/` directory.
