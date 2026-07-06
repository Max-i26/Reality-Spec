import { FilesetResolver, HandLandmarker, ImageSegmenter } from '@mediapipe/tasks-vision';
import { CameraManager } from './camera.js';
import { GestureDetector } from './gestures.js';
import { BackgroundManager } from './background.js';
import { ARManager } from './ar.js';
import { CanvasRecorder } from './recorder.js';
import './style.css';

// DOM elements
const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas-output');
const ctx = canvas.getContext('2d');

const systemStatus = document.getElementById('system-status');
const resolutionDisplay = document.getElementById('resolution-display');
const fpsDisplay = document.getElementById('fps-display');
const latencyVal = document.getElementById('latency-val');
const activeModeVal = document.getElementById('active-mode-val');
const gestureVal = document.getElementById('gesture-val');
const portalLockVal = document.getElementById('portal-lock-val');

// Buttons
const btnModeNormal = document.getElementById('btn-mode-normal');
const btnModePortal = document.getElementById('btn-mode-portal');
const btnModeFull = document.getElementById('btn-mode-full');
const btnRecalibrate = document.getElementById('btn-recalibrate');
const btnScreenshot = document.getElementById('btn-screenshot');
const btnRecord = document.getElementById('btn-record');
const recordingStatus = document.getElementById('recording-status');

// Sliders and Uploads
const blurSlider = document.getElementById('blur-slider');
const blurVal = document.getElementById('blur-val');
const customBgInput = document.getElementById('custom-bg-input');

// Calibration Overlay
const calibrationOverlay = document.getElementById('calibration-overlay');
const calibrationCountdown = document.getElementById('calibration-countdown');
const calibrationTitle = document.getElementById('calibration-title');
const calibrationSubtitle = document.getElementById('calibration-subtitle');

// Gesture dropdowns
const selectThumbsUp = document.getElementById('select-thumbs-up');
const selectFist = document.getElementById('select-fist');
const selectVictory = document.getElementById('select-victory');

// Instances
const cameraManager = new CameraManager(video);
const gestureDetector = new GestureDetector();
const backgroundManager = new BackgroundManager();
const arManager = new ARManager();
const recorder = new CanvasRecorder(canvas);

// State variables
let handLandmarker = null;
let imageSegmenter = null;
let systemInitialized = false;

let activeMode = 'normal'; // 'normal', 'portal', 'full'
let portalBox = null; // { x1, y1, x2, y2, width, height }
let manualDrawing = false;
let manualStart = null;

// Timing stats
let lastFrameTime = 0;
let frameCount = 0;
let fpsIntervalTime = 0;
let activeFPS = 0;

// Gesture cooldowns
const gestureCooldowns = {
  arToggle: 0,
  screenshot: 0,
  modeToggle: 0,
  recalibrate: 0
};
const COOLDOWN_DURATION = 1500; // ms

// Trigger action helpers
function triggerAction(actionName) {
  const now = Date.now();
  
  if (actionName === 'ar-toggle' && now - gestureCooldowns.arToggle > COOLDOWN_DURATION) {
    gestureCooldowns.arToggle = now;
    cycleARFilter();
  } else if (actionName === 'screenshot' && now - gestureCooldowns.screenshot > COOLDOWN_DURATION) {
    gestureCooldowns.screenshot = now;
    takeScreenshot();
  } else if (actionName === 'mode-toggle' && now - gestureCooldowns.modeToggle > COOLDOWN_DURATION) {
    gestureCooldowns.modeToggle = now;
    togglePrivacyMode();
  } else if (actionName === 'recalibrate' && now - gestureCooldowns.recalibrate > COOLDOWN_DURATION) {
    gestureCooldowns.recalibrate = now;
    triggerRecalibrate();
  } else if (actionName === 'privacy-mask') {
    // Instant Privacy Mask (temporarily forces full invisibility)
    if (activeMode !== 'full') {
      setPrivacyMode('full');
      showTempToast("Fist detected: Privacy Shield engaged.");
    }
  }
}

// Show a temporary HUD message overlay
function showTempToast(message) {
  systemStatus.textContent = message.toUpperCase();
  systemStatus.parentNode.querySelector('.status-dot').style.backgroundColor = '#ff3366';
  
  setTimeout(() => {
    if (systemInitialized) {
      systemStatus.textContent = 'SYSTEM ONLINE';
      systemStatus.parentNode.querySelector('.status-dot').style.backgroundColor = '#00ff88';
    }
  }, 3000);
}

// Cycle between AR filters
function cycleARFilter() {
  const filters = ['none', 'creeper', 'cyberhud', 'orbit3d'];
  let currentIdx = filters.indexOf(arManager.activeFilter);
  let nextIdx = (currentIdx + 1) % filters.length;
  setARFilter(filters[nextIdx]);
}

function setARFilter(filterName) {
  arManager.activeFilter = filterName;
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.ar === filterName);
  });
  showTempToast(`AR Filter: ${filterName}`);
}

// Cycle privacy modes
function togglePrivacyMode() {
  const modes = ['normal', 'portal', 'full'];
  let currentIdx = modes.indexOf(activeMode);
  let nextIdx = (currentIdx + 1) % modes.length;
  setPrivacyMode(modes[nextIdx]);
}

function setPrivacyMode(modeName) {
  activeMode = modeName;
  activeModeVal.textContent = modeName.toUpperCase();
  
  btnModeNormal.classList.toggle('active', modeName === 'normal');
  btnModePortal.classList.toggle('active', modeName === 'portal');
  btnModeFull.classList.toggle('active', modeName === 'full');
  
  showTempToast(`Mode: ${modeName}`);
}

/**
 * STEPPER WIZARD UPDATE HELPER
 */
function updateStepper(activeStepId, completedStepIds, progressWidth, instructionText) {
  document.querySelectorAll('.step-item').forEach(item => {
    item.classList.remove('active', 'complete');
  });

  if (activeStepId) {
    document.getElementById(activeStepId).classList.add('active');
  }

  completedStepIds.forEach(id => {
    document.getElementById(id).classList.add('complete');
  });

  document.getElementById('stepper-progress-line').style.width = `${progressWidth}%`;
  document.getElementById('stepper-instruction').textContent = instructionText;
}

/**
 * INITIALIZATION FLOW
 */
async function initializeSystem() {
  try {
    // Start step 1 active
    updateStepper('step-1', [], 0, 'Downloading vision network files... (15MB first-time download)');
    systemStatus.textContent = 'LOADING MODELS...';
    
    // 1. Load MediaPipe Fileset Resolver
    const vision = await FilesetResolver.forVisionTasks(
      'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.8/wasm'
    );

    // 2. Parallel build Hand Landmarker & Image Segmenter
    const handPromise = HandLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: '/models/hand_landmarker.task',
        delegate: 'GPU'
      },
      runningMode: 'VIDEO',
      numHands: 2,
      minHandDetectionConfidence: 0.65,
      minHandPresenceConfidence: 0.65
    });

    const segmentPromise = ImageSegmenter.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: '/models/selfie_segmenter.task',
        delegate: 'GPU'
      },
      runningMode: 'VIDEO',
      outputConfidenceMasks: true
    });

    [handLandmarker, imageSegmenter] = await Promise.all([handPromise, segmentPromise]);
    
    updateStepper('step-1', [], 15, 'Requesting camera access permissions... Please click "Allow" when prompted.');
    systemStatus.textContent = 'STARTING CAMERA...';

    // 3. Start Camera
    const resolution = await cameraManager.start();
    canvas.width = resolution.width;
    canvas.height = resolution.height;
    resolutionDisplay.textContent = `${resolution.width}x${resolution.height}`;

    // 4. Initialize Subsystems
    backgroundManager.init(resolution.width, resolution.height);
    arManager.init(resolution.width, resolution.height);

    systemInitialized = true;
    systemStatus.textContent = 'SYSTEM ONLINE';
    systemStatus.parentNode.querySelector('.status-dot').style.backgroundColor = '#00ff88';

    // Webcam is loaded, mark Step 1 complete and advance to Step 2
    updateStepper('step-2', ['step-1'], 50, 'Camera loaded. Step out of the frame and click "Calibrate Background Backplate" below.');

    // 5. Automatic Initial Calibration
    await triggerRecalibrate();

    // 6. Start Loop
    lastFrameTime = performance.now();
    fpsIntervalTime = lastFrameTime;
    requestAnimationFrame(renderLoop);

  } catch (err) {
    console.error('Initialization failed: ', err);
    systemStatus.textContent = 'CRITICAL ERROR';
    systemStatus.parentNode.querySelector('.status-dot').style.backgroundColor = '#ff3366';
    updateStepper('step-1', [], 0, `Initialization error: ${err.message}. Please reload and check camera connections.`);
    alert(`System initialization failed: ${err.message}. Please check your camera permissions.`);
  }
}

/**
 * CALIBRATION PROCESS
 */
async function triggerRecalibrate() {
  calibrationOverlay.classList.remove('overlay-hidden');
  calibrationTitle.textContent = 'CALIBRATING BACKGROUND';
  calibrationSubtitle.textContent = 'Please step out of the camera view...';
  
  updateStepper('step-2', ['step-1'], 50, 'CALIBRATION ACTIVE: Please step completely out of the camera view.');

  // 3 second countdown
  for (let c = 3; c > 0; c--) {
    calibrationCountdown.textContent = c;
    await new Promise(r => setTimeout(r, 1000));
  }

  calibrationCountdown.textContent = '⚡';
  calibrationTitle.textContent = 'LEARNING ENVIRONMENT';
  calibrationSubtitle.textContent = 'Scanning room colors...';

  // Perform average accumulation
  await backgroundManager.capture(video, (progress) => {
    calibrationSubtitle.textContent = `Scanning: ${progress}%`;
  });

  calibrationOverlay.classList.add('overlay-hidden');
  showTempToast('Calibration Successful');

  // Mark step 2 complete and transition to Step 3 active (complete)
  updateStepper('step-3', ['step-1', 'step-2', 'step-3'], 100, 'System ready! Select a privacy filter or raise a hand to test AR effects.');
}

/**
 * SCREENSHOT EXPORT
 */
function takeScreenshot() {
  const link = document.createElement('a');
  link.download = `RealityFrame_${Date.now()}.png`;
  link.href = canvas.toDataURL('image/png');
  link.click();
  showTempToast('Screenshot Captured');
}

/**
 * MAIN PROCESSING AND RENDERING LOOP
 */
function renderLoop(now) {
  if (!systemInitialized) return;

  const startProcessing = performance.now();

  // 1. Calculate FPS
  frameCount++;
  if (now - fpsIntervalTime >= 1000) {
    activeFPS = Math.round((frameCount * 1000) / (now - fpsIntervalTime));
    fpsDisplay.textContent = activeFPS;
    frameCount = 0;
    fpsIntervalTime = now;
  }

  // 2. Perform Detection if video is ready
  let handsList = [];
  let bodyMaskArray = null;

  if (video.readyState >= 2) {
    const timestamp = now;

    // Detect Hands
    const handResult = handLandmarker.detectForVideo(video, timestamp);
    if (handResult && handResult.landmarks) {
      handsList = handResult.landmarks;
    }

    // Detect Gestures
    const detectedGesture = gestureDetector.detect(handsList);
    gestureVal.textContent = detectedGesture;

    // Route gesture trigger bindings
    if (detectedGesture !== 'NONE') {
      if (detectedGesture === 'THUMBS_UP') {
        triggerAction(selectThumbsUp.value);
      } else if (detectedGesture === 'FIST') {
        triggerAction(selectFist.value);
      } else if (detectedGesture === 'VICTORY') {
        triggerAction(selectVictory.value);
      }
    }

    // Portal Box resizing gesture loop
    if (activeMode === 'portal') {
      const pinchPortal = gestureDetector.getPortalBox(handsList, canvas.width, canvas.height);
      if (pinchPortal) {
        portalBox = pinchPortal;
        portalLockVal.textContent = 'RESIZING (PINCH)';
        portalLockVal.style.color = '#00ff88';
      } else if (portalBox) {
        portalLockVal.textContent = 'LOCKED';
        portalLockVal.style.color = '#00e5ff';
      } else {
        portalLockVal.textContent = 'INACTIVE';
        portalLockVal.style.color = '#a0a0c0';
      }
    } else {
      portalLockVal.textContent = 'INACTIVE';
      portalLockVal.style.color = '#a0a0c0';
    }

    // Run Segmentation if in full body invisibility or virtual background mode
    if (activeMode === 'full' || backgroundManager.bgType === 'blur' || backgroundManager.bgType === 'cyber' || (backgroundManager.bgType === 'custom' && backgroundManager.customImage)) {
      const segmentResult = imageSegmenter.segmentForVideo(video, timestamp);
      if (segmentResult && segmentResult.confidenceMasks) {
        bodyMaskArray = segmentResult.confidenceMasks[0].getAsFloat32Array();
      }
    }
  }

  // 3. Render base visual stream
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (activeMode === 'portal') {
    backgroundManager.processPortal(ctx, video, portalBox);
  } else if (activeMode === 'full') {
    backgroundManager.processFullInvisibility(ctx, video, bodyMaskArray);
  } else {
    // Normal Mode (check if virtual background override is selected)
    if (backgroundManager.bgType !== 'static') {
      backgroundManager.processVirtualBackground(ctx, video, bodyMaskArray);
    } else {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    }
  }

  // 4. Render AR overlays
  arManager.process(ctx, handsList);

  // 5. Draw HUD annotations in 2D Canvas (Futuristic portal corners, manual drawing boxes)
  drawHUDAnnotations();

  // 6. Draw hand skeletal tracking on canvas if debugging/recalibrating (lightly translucent)
  if (handsList.length > 0) {
    drawHandSkeletons(handsList);
  }

  // 7. Calculate process latency
  const latency = Math.round(performance.now() - startProcessing);
  latencyVal.textContent = `${latency} ms`;

  requestAnimationFrame(renderLoop);
}

/**
 * Draw hand skeletal connections in 2D canvas (subtle neon lines)
 */
function drawHandSkeletons(handsList) {
  ctx.save();
  ctx.strokeStyle = 'rgba(0, 255, 136, 0.25)';
  ctx.fillStyle = 'rgba(0, 229, 255, 0.4)';
  ctx.lineWidth = 1.5;

  handsList.forEach(hand => {
    // Draw landmarks
    hand.forEach(lm => {
      ctx.beginPath();
      ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw skeletal connections
    const connections = [
      [0, 1], [1, 2], [2, 3], [3, 4], // Thumb
      [0, 5], [5, 6], [6, 7], [7, 8], // Index
      [5, 9], [9, 10], [10, 11], [11, 12], // Middle
      [9, 13], [13, 14], [14, 15], [15, 16], // Ring
      [13, 17], [17, 18], [18, 19], [19, 20], // Pinky
      [0, 17] // Palm bottom
    ];

    connections.forEach(([s, e]) => {
      const start = hand[s];
      const end = hand[e];
      ctx.beginPath();
      ctx.moveTo(start.x * canvas.width, start.y * canvas.height);
      ctx.lineTo(end.x * canvas.width, end.y * canvas.height);
      ctx.stroke();
    });
  });
  ctx.restore();
}

/**
 * Draw 2D Sci-Fi corner HUD on portal boxes
 */
function drawHUDAnnotations() {
  if (activeMode !== 'portal' || !portalBox) return;

  const { x1, y1, width, height } = portalBox;
  const x2 = x1 + width;
  const y2 = y1 + height;

  ctx.save();
  
  // Base rectangle outline
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
  ctx.lineWidth = 1;
  ctx.strokeRect(x1, y1, width, height);

  // Futuristic glowing corners
  ctx.strokeStyle = '#00e5ff';
  ctx.lineWidth = 4;
  ctx.shadowBlur = 10;
  ctx.shadowColor = 'rgba(0, 229, 255, 0.7)';

  const cornerSize = Math.min(25, width * 0.2, height * 0.2);

  // Top Left
  ctx.beginPath();
  ctx.moveTo(x1 + cornerSize, y1); ctx.lineTo(x1, y1); ctx.lineTo(x1, y1 + cornerSize);
  ctx.stroke();

  // Top Right
  ctx.beginPath();
  ctx.moveTo(x2 - cornerSize, y1); ctx.lineTo(x2, y1); ctx.lineTo(x2, y1 + cornerSize);
  ctx.stroke();

  // Bottom Left
  ctx.beginPath();
  ctx.moveTo(x1 + cornerSize, y2); ctx.lineTo(x1, y2); ctx.lineTo(x1, y2 - cornerSize);
  ctx.stroke();

  // Bottom Right
  ctx.beginPath();
  ctx.moveTo(x2 - cornerSize, y2); ctx.lineTo(x2, y2); ctx.lineTo(x2, y2 - cornerSize);
  ctx.stroke();

  // Draw manual drag indicator if mouse is near
  if (manualDrawing) {
    ctx.fillStyle = '#00ff88';
    ctx.font = '700 9px "Orbitron"';
    ctx.fillText('PORTAL DRAWN', x1 + 5, y1 - 5);
  }

  ctx.restore();
}

/**
 * EVENT LISTENERS SETUP
 */

// Tab switching click bindings
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    btn.classList.add('active');
    const tabId = `tab-${btn.dataset.tab}`;
    document.getElementById(tabId).classList.add('active');
    showTempToast(`Navigated to: ${btn.dataset.tab.toUpperCase()}`);
  });
});

// Sidebar collapse click binding (Immersive Mode)
const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
const appGrid = document.getElementById('app-grid');

btnToggleSidebar.addEventListener('click', () => {
  appGrid.classList.toggle('sidebar-collapsed');
  if (appGrid.classList.contains('sidebar-collapsed')) {
    btnToggleSidebar.textContent = '⚡ Control Deck';
    btnToggleSidebar.classList.add('active');
    showTempToast('IMMERSIVE DISPLAY ENGAGED');
  } else {
    btnToggleSidebar.textContent = '⚡ Immersive View';
    btnToggleSidebar.classList.remove('active');
    showTempToast('CONTROL DECK ENABLED');
  }
});

// Privacy mode button bindings
btnModeNormal.addEventListener('click', () => setPrivacyMode('normal'));
btnModePortal.addEventListener('click', () => setPrivacyMode('portal'));
btnModeFull.addEventListener('click', () => setPrivacyMode('full'));

btnRecalibrate.addEventListener('click', triggerRecalibrate);
btnScreenshot.addEventListener('click', takeScreenshot);

// Background select click routing
document.querySelectorAll('.bg-thumb-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    document.querySelectorAll('.bg-thumb-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    const type = btn.dataset.bg;
    if (type === 'custom') {
      customBgInput.click();
    } else {
      backgroundManager.bgType = type;
      showTempToast(`Background: ${type}`);
    }
  });
});

customBgInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        backgroundManager.setCustomImage(img);
        backgroundManager.bgType = 'custom';
        showTempToast('Custom Background Loaded');
        // Set custom button active
        document.querySelectorAll('.bg-thumb-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('[data-bg="custom"]').classList.add('active');
      };
      img.src = event.target.result;
    };
    reader.readAsDataURL(file);
  }
});

// Blur slider binding
blurSlider.addEventListener('input', (e) => {
  const val = parseInt(e.target.value);
  blurVal.textContent = `${val}px`;
  backgroundManager.blurAmount = val;
});

// AR Filter selector click routing
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    setARFilter(btn.dataset.ar);
  });
});

// Video Recorder toggle binding
btnRecord.addEventListener('click', () => {
  if (recorder.isRecording) {
    recorder.stop();
    btnRecord.textContent = '🔴 Start Recording';
    btnRecord.classList.remove('active');
    recordingStatus.textContent = 'Video saved, downloading...';
    recordingStatus.className = 'recording-desc-idle';
    setTimeout(() => {
      recordingStatus.textContent = 'Ready to record output';
    }, 3000);
  } else {
    recorder.start();
    btnRecord.textContent = '⏹ Stop Recording';
    btnRecord.classList.add('active');
    recordingStatus.textContent = '• RECORDING LIVE CANVAS STREAM';
    recordingStatus.className = 'recording-desc-active';
  }
});

// Manual canvas mouse portal dragging (fallback)
canvas.addEventListener('mousedown', (e) => {
  if (activeMode !== 'portal') return;
  const rect = canvas.getBoundingClientRect();
  // Map mouse coordinate to source canvas width/height
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  
  // Note: the output is horizontally mirrored, so we mirror the mouse coordinates too!
  const mouseX = canvas.width - ((e.clientX - rect.left) * scaleX);
  const mouseY = (e.clientY - rect.top) * scaleY;

  manualDrawing = true;
  manualStart = { x: mouseX, y: mouseY };
  portalBox = { x1: mouseX, y1: mouseY, x2: mouseX, y2: mouseY, width: 0, height: 0 };
});

canvas.addEventListener('mousemove', (e) => {
  if (!manualDrawing || activeMode !== 'portal') return;
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const mouseX = canvas.width - ((e.clientX - rect.left) * scaleX);
  const mouseY = (e.clientY - rect.top) * scaleY;

  const x1 = Math.min(manualStart.x, mouseX);
  const y1 = Math.min(manualStart.y, mouseY);
  const x2 = Math.max(manualStart.x, mouseX);
  const y2 = Math.max(manualStart.y, mouseY);

  portalBox = { x1, y1, x2, y2, width: x2 - x1, height: y2 - y1 };
});

window.addEventListener('mouseup', () => {
  if (manualDrawing) {
    manualDrawing = false;
    showTempToast('Portal Locked');
  }
});

// Start initialization on load
window.addEventListener('DOMContentLoaded', initializeSystem);

