import * as THREE from 'three';

/**
 * AR Manager integrating 2D Canvas HUD overlays and 3D Three.js spatial overlays.
 */
export class ARManager {
  constructor() {
    this.width = 0;
    this.height = 0;
    this.activeFilter = 'none'; // 'none', 'creeper', 'cyberhud', 'orbit3d'

    // Three.js setup for 3D overlay
    this.threeCanvas = document.createElement('canvas');
    this.renderer = null;
    this.scene = null;
    this.camera = null;
    
    // 3D Objects
    this.holoGroup = null;
    this.torusKnot = null;
    this.particleSystem = null;

    // Animation variables
    this.clock = new THREE.Clock();
  }

  /**
   * Initializes the Three.js rendering pipeline
   */
  init(width, height) {
    this.width = width;
    this.height = height;

    this.threeCanvas.width = width;
    this.threeCanvas.height = height;

    // 1. Create WebGL Renderer
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.threeCanvas,
      alpha: true, // transparent background to overlay on webcam
      antialias: true
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // 2. Create Scene
    this.scene = new THREE.Scene();

    // 3. Create Perspective Camera (matching typical webcam FOV)
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.camera.position.z = 5;

    // 4. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x00e5ff, 2, 50);
    pointLight.position.set(0, 5, 5);
    this.scene.add(pointLight);

    // 5. Create Hologram Group
    this.holoGroup = new THREE.Group();
    
    // Torus Knot geometry (futuristic glowing ring)
    const torusGeo = new THREE.TorusKnotGeometry(0.5, 0.15, 100, 16);
    const torusMat = new THREE.MeshBasicMaterial({
      color: 0x00ff88,
      wireframe: true,
      transparent: true,
      opacity: 0.8
    });
    this.torusKnot = new THREE.Mesh(torusGeo, torusMat);
    this.holoGroup.add(this.torusKnot);

    // Inner core sphere
    const sphereGeo = new THREE.SphereGeometry(0.25, 16, 16);
    const sphereMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      wireframe: true,
      transparent: true,
      opacity: 0.6
    });
    const coreSphere = new THREE.Mesh(sphereGeo, sphereMat);
    this.holoGroup.add(coreSphere);

    // Hologram particles orbiting
    const particleCount = 60;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      // Random coordinates around sphere
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 0.7 + Math.random() * 0.3; // radius between 0.7 and 1.0
      
      positions[i] = r * Math.sin(phi) * Math.cos(theta);
      positions[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i + 2] = r * Math.cos(phi);
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({
      color: 0x00e5ff,
      size: 0.05,
      transparent: true,
      opacity: 0.9
    });
    this.particleSystem = new THREE.Points(particleGeo, particleMat);
    this.holoGroup.add(this.particleSystem);

    this.scene.add(this.holoGroup);
    this.holoGroup.visible = false;
  }

  /**
   * Main update entrypoint
   */
  process(ctx, handsList) {
    if (this.activeFilter === 'none') {
      this.holoGroup.visible = false;
      return;
    }

    const hasHand = handsList && handsList.length > 0;

    if (this.activeFilter === 'orbit3d') {
      this.render3DOverlay(handsList);
      // Draw Three.js WebGL canvas on top of 2D context
      ctx.save();
      // Mirror the ThreeJS canvas overlay as well so it aligns with hand tracking
      ctx.scale(-1, 1);
      ctx.drawImage(this.threeCanvas, -this.width, 0);
      ctx.restore();
    } else {
      this.holoGroup.visible = false;
    }

    if (hasHand) {
      if (this.activeFilter === 'cyberhud') {
        this.drawCyberHUD(ctx, handsList[0]);
      } else if (this.activeFilter === 'creeper') {
        this.drawCreeperMask(ctx, handsList[0]);
      }
    }
  }

  /**
   * Map 2D normalized MediaPipe coordinates to ThreeJS 3D space
   */
  mapTo3DSpace(x, y, zDepth) {
    // Map x, y from [0, 1] to NDC [-1, 1]
    // Note: mirror mapping is handled by renderer canvas flip
    const ndcX = (x * 2) - 1;
    const ndcY = -(y * 2) + 1; // invert Y

    // Unproject to 3D coordinates based on camera frustum
    const vector = new THREE.Vector3(ndcX, ndcY, 0.5);
    vector.unproject(this.camera);
    
    // Extrapolate vector based on a constant distance
    // Scale depth based on z coordinate from hand tracking (which is relative depth)
    const distance = 4 - (zDepth * 3); // Map depth around 3 to 5 units away
    const dir = vector.sub(this.camera.position).normalize();
    
    return this.camera.position.clone().add(dir.multiplyScalar(distance));
  }

  /**
   * Renders the Three.js 3D Scene
   */
  render3DOverlay(handsList) {
    const elapsed = this.clock.getElapsedTime();

    if (handsList && handsList.length > 0) {
      this.holoGroup.visible = true;

      // Get palm location (landmark 9 - Middle Finger MCP)
      const palm = handsList[0][9];
      const wrist = handsList[0][0];
      const thumbBase = handsList[0][2];
      
      // Calculate hand size for 3D scale
      const handSize = Math.sqrt(
        Math.pow(palm.x - wrist.x, 2) + Math.pow(palm.y - wrist.y, 2)
      );

      // Map coordinates to 3D space
      const pos3D = this.mapTo3DSpace(palm.x, palm.y, palm.z);
      
      // Update position
      this.holoGroup.position.copy(pos3D);

      // Scale based on hand size
      const scale = handSize * 7.5; // multiplier to match hand dimensions
      this.holoGroup.scale.set(scale, scale, scale);

      // Rotate objects
      this.torusKnot.rotation.x = elapsed * 0.8;
      this.torusKnot.rotation.y = elapsed * 0.5;
      this.particleSystem.rotation.y = -elapsed * 0.3;
    } else {
      this.holoGroup.visible = false;
    }

    // Clear WebGL buffer and render frame
    this.renderer.clear();
    this.renderer.render(this.scene, this.camera);
  }

  /**
   * Draw a futuristic Sci-Fi cyber hud around hand landmarks
   */
  drawCyberHUD(ctx, hand) {
    const palm = hand[9];
    const px = palm.x * this.width;
    const py = palm.y * this.height;

    // Get hand span size
    const wrist = hand[0];
    const handSize = Math.sqrt(
      Math.pow(palm.x - wrist.x, 2) + Math.pow(palm.y - wrist.y, 2)
    ) * this.width;

    const r = handSize * 0.9;
    const elapsed = this.clock.getElapsedTime();

    ctx.save();
    
    // Draw concentric rotating rings
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.8)';
    ctx.shadowBlur = 10;
    ctx.shadowColor = 'rgba(0, 229, 255, 0.5)';

    // Outer bracket brackets
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(px, py, r, elapsed, elapsed + Math.PI * 0.4);
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(px, py, r, elapsed + Math.PI, elapsed + Math.PI * 1.4);
    ctx.stroke();

    // Inner dashed ring
    ctx.strokeStyle = 'rgba(0, 255, 136, 0.6)';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 8]);
    ctx.beginPath();
    ctx.arc(px, py, r * 0.7, -elapsed * 1.2, -elapsed * 1.2 + Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]); // Reset

    // Lock-on brackets
    const size = r * 0.4;
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.9)';
    ctx.lineWidth = 2;

    const drawBracket = (x, y, dx, dy) => {
      ctx.beginPath();
      ctx.moveTo(x + dx * size, y);
      ctx.lineTo(x, y);
      ctx.lineTo(x, y + dy * size);
      ctx.stroke();
    };

    drawBracket(px - r, py - r, 1, 1);   // Top Left
    drawBracket(px + r, py - r, -1, 1);  // Top Right
    drawBracket(px - r, py + r, 1, -1);  // Bottom Left
    drawBracket(px + r, py + r, -1, -1); // Bottom Right

    // Diagnostic text
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#00e5ff';
    ctx.font = '700 9px "Orbitron"';
    ctx.fillText('TARGET LOCK // TRK_ID: 0A', px + r + 10, py - 10);
    ctx.fillStyle = '#00ff88';
    ctx.fillText(`X: ${palm.x.toFixed(2)} Y: ${palm.y.toFixed(2)}`, px + r + 10, py + 5);
    ctx.fillStyle = '#a0a0c0';
    ctx.fillText(`RANGE: ${(1 - palm.z).toFixed(2)}m`, px + r + 10, py + 20);

    // Center crosshair
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.4)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(px - 10, py); ctx.lineTo(px + 10, py);
    ctx.moveTo(px, py - 10); ctx.lineTo(px, py + 10);
    ctx.stroke();

    ctx.restore();
  }

  /**
   * Draw pixelated Creeper Mask on hand (handheld shield/prop)
   */
  drawCreeperMask(ctx, hand) {
    const palm = hand[9];
    const px = palm.x * this.width;
    const py = palm.y * this.height;

    const wrist = hand[0];
    const handSize = Math.sqrt(
      Math.pow(palm.x - wrist.x, 2) + Math.pow(palm.y - wrist.y, 2)
    ) * this.width;

    const size = handSize * 1.5;
    const elapsed = this.clock.getElapsedTime();

    ctx.save();
    ctx.translate(px, py);
    // Dynamic floating animation
    ctx.translate(0, Math.sin(elapsed * 4) * 8);

    // Draw Minecraft base shield
    ctx.fillStyle = '#45aa41';
    ctx.fillRect(-size/2, -size/2, size, size);

    // Pixel blocks drawing (Minecraft noise texture)
    const block = size / 8;
    
    // Fixed noise representation
    const greenShades = ['#3f9c3b', '#48b244', '#388e35', '#45aa41'];
    
    // Draw 8x8 pixel texture grid
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 8; x++) {
        // Creeper Face layout (0: green noise, 1: black facial features)
        let isFaceFeature = false;
        
        // Eyes
        if ((y === 2 && (x === 1 || x === 2 || x === 5 || x === 6))) isFaceFeature = true;
        // Nose & Mouth
        if ((y === 3 && (x === 3 || x === 4))) isFaceFeature = true;
        if ((y === 4 && (x === 2 || x === 3 || x === 4 || x === 5))) isFaceFeature = true;
        if ((y === 5 && (x === 2 || x === 5))) isFaceFeature = true;

        if (isFaceFeature) {
          ctx.fillStyle = '#111811';
        } else {
          // Semi-random shade based on grid coordinates
          const idx = (x + y * 7) % greenShades.length;
          ctx.fillStyle = greenShades[idx];
        }

        ctx.fillRect(-size/2 + x * block, -size/2 + y * block, block + 0.5, block + 0.5);
      }
    }

    // Glowing border outline
    ctx.strokeStyle = '#00ff88';
    ctx.lineWidth = 2;
    ctx.shadowBlur = 10;
    ctx.shadowColor = '#00ff88';
    ctx.strokeRect(-size/2, -size/2, size, size);

    ctx.restore();
  }
}
