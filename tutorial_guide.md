# Tutorial: Build an Interactive AI Webcam Dashboard (JavaScript)

This guide is designed to help you teach your friend how to build a simplified version of **RealityFrame**. Since they don't know Python, this project is built entirely using **HTML, CSS, and modern JavaScript (Web APIs)**. It runs directly in any web browser and leverages **MediaPipe** for real-time hand tracking.

---

## 📅 Roadmap Overview
1. **Setup & Environment**: Scaffold the project using Vite and install required packages.
2. **Open the Camera**: Access the user's webcam using the browser's native `navigator.mediaDevices` API.
3. **Add Palm Tracking**: Integrate MediaPipe Hand Landmarker to locate hands in real-time.
4. **Trigger Actions based on Hands**:
   *   **Mirror Mode**: Flip the screen.
   *   **Invisibility**: Hide yourself against a pre-captured background.
   *   **Virtual Background**: Replace the background with an image.
5. **Streaming**: How to output/stream the canvas feed.

---

## Step 1: Environment Setup

### 1. Install Node.js
First, ensure [Node.js](https://nodejs.org/) is installed on your computer.

### 2. Scaffold a New Project with Vite
Open your terminal and run:
```bash
# Initialize a new Vanilla JS project in a folder named 'ai-webcam'
npx -y create-vite@latest ai-webcam --template vanilla
cd ai-webcam
```

### 3. Install MediaPipe Tasks
Install Google's official MediaPipe tasks library for web:
```bash
npm install @mediapipe/tasks-vision
```

### 4. Project Structure
Your folder structure should look like this:
```text
ai-webcam/
├── index.html          # Main HTML structure
├── style.css           # Styling
├── main.js             # Core logic
└── package.json        # Project metadata & scripts
```

---

## Step 2: Designing the Interface (`index.html`)

Let's create a clean layout with a video viewer, output canvas, and buttons to trigger actions.

Replace the contents of `index.html` with:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Webcam Control Center</title>
  <link rel="stylesheet" href="./style.css">
</head>
<body>
  <div class="app">
    <h1>AI Webcam Control Center</h1>
    
    <div class="video-container">
      <!-- Hidden raw webcam feed -->
      <video id="webcam" autoplay playsinline muted style="display: none;"></video>
      
      <!-- Display Canvas (where we draw our effects) -->
      <canvas id="output-canvas"></canvas>
    </div>

    <div class="controls">
      <button id="btn-mirror">Toggle Mirror</button>
      <button id="btn-calibrate">Capture Room Background</button>
      <button id="btn-invisible">Toggle Invisibility</button>
      <button id="btn-background">Swap Background Image</button>
    </div>
  </div>

  <script type="module" src="./main.js"></script>
</body>
</html>
```

---

## Step 3: Setting Up Styles (`style.css`)

Create a dark, futuristic UI using CSS:
```css
body {
  margin: 0;
  padding: 0;
  background-color: #0b0b14;
  color: #fff;
  font-family: sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.app {
  text-align: center;
}

.video-container {
  margin: 20px auto;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid #00ff88;
  max-width: 640px;
  aspect-ratio: 4/3;
  background-color: #000;
}

canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.controls {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 20px;
}

button {
  background: #151528;
  color: #fff;
  border: 1px solid #00ff88;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: 0.3s ease;
}

button:hover {
  background: #00ff88;
  color: #000;
}
```

---

## Step 4: Writing the Logic (`main.js`)

Now, let's build the interactive JavaScript logic step-by-step. 

Replace the content in `main.js` with this comprehensive template:

```javascript
import { FilesetResolver, HandLandmarker } from '@mediapipe/tasks-vision';

// DOM Elements
const video = document.getElementById('webcam');
const canvas = document.getElementById('output-canvas');
const ctx = canvas.getContext('2d');

// State Variables
let handLandmarker = null;
let isMirrored = false;
let isInvisible = false;
let useBgImage = false;
let backgroundImage = null; // Captured room background
let virtualBgImage = new Image(); // Swapped background image

// Load Virtual Background Image
virtualBgImage.src = 'https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=640&auto=format&fit=crop'; // Example abstract bg

// Initialize Camera
async function startWebcam() {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { width: 640, height: 480 }
  });
  video.srcObject = stream;
  video.onloadedmetadata = () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    video.play();
    requestAnimationFrame(renderLoop);
  };
}

// Initialize Hand Tracking
async function loadAIModel() {
  const vision = await FilesetResolver.forVisionTasks(
    'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.8/wasm'
  );
  handLandmarker = await HandLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task'
    },
    runningMode: 'VIDEO',
    numHands: 1
  });
  console.log("Hand Tracking Model Loaded!");
  startWebcam();
}

// Draw Loop (Executed every frame)
function renderLoop() {
  ctx.save();

  // Handle Mirror Effect
  if (isMirrored) {
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
  }

  // Draw Core background layers
  if (isInvisible && backgroundImage) {
    // Render the captured clean background (Making user invisible)
    ctx.putImageData(backgroundImage, 0, 0);
  } else if (useBgImage) {
    // Render Virtual Background image
    ctx.drawImage(virtualBgImage, 0, 0, canvas.width, canvas.height);
  } else {
    // Default Camera Feed
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  }

  // Process Hand Landmarks
  if (handLandmarker && video.readyState === 4) {
    const startTimeMs = performance.now();
    const result = handLandmarker.detectForVideo(video, startTimeMs);

    if (result.landmarks && result.landmarks.length > 0) {
      const landmarks = result.landmarks[0]; // First detected hand
      
      // Draw a tracking indicator on the index finger tip (Landmark index 8)
      const indexTip = landmarks[8];
      const x = indexTip.x * canvas.width;
      const y = indexTip.y * canvas.height;

      // Draw a glowing tracking point
      ctx.beginPath();
      ctx.arc(x, y, 15, 0, 2 * Math.PI);
      ctx.fillStyle = "#00ff88";
      ctx.fill();
      
      // OPTIONAL Palm-based triggering logic
      detectGestures(landmarks);
    }
  }

  ctx.restore();
  requestAnimationFrame(renderLoop);
}

// Simple Gesture Triggering Logic
function detectGestures(landmarks) {
  // Let's measure distance between thumb tip (4) and pinky tip (20) to detect open/close palm
  const thumb = landmarks[4];
  const pinky = landmarks[20];
  const distance = Math.hypot(thumb.x - pinky.x, thumb.y - pinky.y);

  if (distance > 0.4) {
    // Open Palm action: Example, temporarily swap background or mirror
    console.log("Open Palm detected!");
  }
}

// Actions
document.getElementById('btn-mirror').onclick = () => {
  isMirrored = !isMirrored;
};

document.getElementById('btn-calibrate').onclick = () => {
  // Temporarily grab a static frame of the room when the user isn't in view
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  backgroundImage = ctx.getImageData(0, 0, canvas.width, canvas.height);
  alert("Room background captured! You can now turn on Invisibility.");
};

document.getElementById('btn-invisible').onclick = () => {
  if (!backgroundImage) {
    alert("Please capture the room background first!");
    return;
  }
  isInvisible = !isInvisible;
  useBgImage = false;
};

document.getElementById('btn-background').onclick = () => {
  useBgImage = !useBgImage;
  isInvisible = false;
};

// Start the Application
loadAIModel();
```

---

## Step 5: Streaming to meeting apps (Virtual Camera)
To stream the interactive canvas output into Zoom, Teams, or Discord:

1. **Direct WebRTC Stream**: You can use the canvas capture stream directly in another WebRTC app:
   ```javascript
   const stream = canvas.captureStream(30); // 30 FPS stream
   ```
2. **OBS Virtual Camera**:
   * Open **OBS Studio**.
   * Add a **Window Capture** source and select your browser tab running the project.
   * Click **Start Virtual Camera** in OBS. You can now choose "OBS Virtual Camera" as your video input in Zoom, Google Meet, or Discord.
