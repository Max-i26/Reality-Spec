/**
 * Background subtraction and blending engine.
 */

export class BackgroundManager {
  constructor() {
    this.width = 0;
    this.height = 0;
    
    // Background canvas
    this.bgCanvas = document.createElement('canvas');
    this.bgCtx = this.bgCanvas.getContext('2d');
    
    // Mask canvas
    this.maskCanvas = document.createElement('canvas');
    this.maskCtx = this.maskCanvas.getContext('2d');
    
    // Temp blending canvas
    this.tempCanvas = document.createElement('canvas');
    this.tempCtx = this.tempCanvas.getContext('2d');

    this.isCaptured = false;
    this.bgType = 'static'; // 'static', 'blur', 'cyber', 'custom'
    this.blurAmount = 0;
    this.customImage = null;
    
    // Cyber grid parameters
    this.gridOffset = 0;
  }

  init(width, height) {
    this.width = width;
    this.height = height;

    this.bgCanvas.width = width;
    this.bgCanvas.height = height;

    this.maskCanvas.width = width;
    this.maskCanvas.height = height;

    this.tempCanvas.width = width;
    this.tempCanvas.height = height;
    
    // Default background is solid dark gray before capture
    this.bgCtx.fillStyle = '#1e1e24';
    this.bgCtx.fillRect(0, 0, width, height);
  }

  /**
   * Captures background by averaging frames over a duration to reduce noise
   */
  async capture(videoElement, onProgress) {
    const totalFrames = 30;
    const intervalMs = 50;
    
    // Create temporary accumulator buffer
    const accumData = new Float32Array(this.width * this.height * 4);
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = this.width;
    tempCanvas.height = this.height;
    const tempCtx = tempCanvas.getContext('2d');

    for (let i = 0; i < totalFrames; i++) {
      tempCtx.drawImage(videoElement, 0, 0, this.width, this.height);
      const imgData = tempCtx.getImageData(0, 0, this.width, this.height);
      const data = imgData.data;

      // Accumulate pixel values
      for (let j = 0; j < data.length; j++) {
        accumData[j] += data[j];
      }

      if (onProgress) {
        onProgress(Math.round(((i + 1) / totalFrames) * 100));
      }
      
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }

    // Average the accumulated values
    const finalImgData = this.bgCtx.createImageData(this.width, this.height);
    for (let j = 0; j < accumData.length; j++) {
      finalImgData.data[j] = Math.round(accumData[j] / totalFrames);
    }
    
    this.bgCtx.putImageData(finalImgData, 0, 0);
    this.isCaptured = true;
  }

  /**
   * Set custom background image uploaded by user
   */
  setCustomImage(img) {
    this.customImage = img;
  }

  /**
   * Draw the Cyber Grid background
   */
  drawCyberGrid(ctx) {
    const w = this.width;
    const h = this.height;

    // Dark grid background
    ctx.fillStyle = '#050714';
    ctx.fillRect(0, 0, w, h);

    ctx.strokeStyle = 'rgba(0, 229, 255, 0.15)';
    ctx.lineWidth = 1;

    // Moving grid animation offset
    this.gridOffset = (this.gridOffset + 0.5) % 40;

    // Vertical lines
    for (let x = this.gridOffset; x < w; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }

    // Horizontal lines
    for (let y = this.gridOffset; y < h; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Glowing core gradient
    const gradient = ctx.createRadialGradient(w/2, h/2, 50, w/2, h/2, w/2);
    gradient.addColorStop(0, 'rgba(0, 255, 136, 0.05)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, w, h);
  }

  /**
   * Returns current active background image/pattern onto a destination context
   */
  renderActiveBackground(destCtx, originalVideo) {
    const w = this.width;
    const h = this.height;

    if (this.bgType === 'blur') {
      // Draw live frame, blur it
      destCtx.drawImage(originalVideo, 0, 0, w, h);
      this.applyBlur(destCtx, 20); // standard blur amount for blur mode
    } else if (this.bgType === 'cyber') {
      this.drawCyberGrid(destCtx);
    } else if (this.bgType === 'custom' && this.customImage) {
      destCtx.drawImage(this.customImage, 0, 0, w, h);
      if (this.blurAmount > 0) {
        this.applyBlur(destCtx, this.blurAmount);
      }
    } else {
      // Default: Static captured background
      destCtx.drawImage(this.bgCanvas, 0, 0, w, h);
      if (this.blurAmount > 0) {
        this.applyBlur(destCtx, this.blurAmount);
      }
    }
  }

  applyBlur(ctx, amount) {
    if (amount <= 0) return;
    ctx.filter = `blur(${amount}px)`;
    // Redraw canvas on itself to apply filter
    const temp = document.createElement('canvas');
    temp.width = this.width;
    temp.height = this.height;
    temp.getContext('2d').drawImage(ctx.canvas, 0, 0);
    ctx.clearRect(0, 0, this.width, this.height);
    ctx.drawImage(temp, 0, 0);
    ctx.filter = 'none'; // reset filter
  }

  /**
   * Process and blend portal invisibility
   */
  processPortal(outputCtx, videoElement, portalBox) {
    const w = this.width;
    const h = this.height;

    // 1. Draw webcam feed on output canvas
    outputCtx.drawImage(videoElement, 0, 0, w, h);

    if (!portalBox) return;

    // 2. Draw active background into our temp canvas
    this.renderActiveBackground(this.tempCtx, videoElement);

    // 3. Copy the portal region from background to output canvas
    const { x1, y1, width, height } = portalBox;
    
    // Draw with slight edge feathering using a sub-canvas if needed, 
    // but a clean copy is fast. Let's do a smooth feathered draw.
    outputCtx.save();
    
    // Feathered clipping region
    outputCtx.beginPath();
    outputCtx.rect(x1, y1, width, height);
    outputCtx.clip();
    
    outputCtx.drawImage(this.tempCanvas, 0, 0);
    outputCtx.restore();
  }

  /**
   * Process and blend full body invisibility
   * Replaces body segmentation area with background
   */
  processFullInvisibility(outputCtx, videoElement, segmentationMask) {
    const w = this.width;
    const h = this.height;

    // 1. Draw live camera frame on output canvas
    outputCtx.drawImage(videoElement, 0, 0, w, h);

    if (!segmentationMask) return;

    // 2. Render target background to temp canvas
    this.renderActiveBackground(this.tempCtx, videoElement);

    // 3. Write segmentation mask to maskCanvas
    this.maskCtx.clearRect(0, 0, w, h);
    
    // Create ImageData from MediaPipe mask
    const maskImgData = this.maskCtx.createImageData(w, h);
    const data = maskImgData.data;
    
    // MediaPipe mask contains float values [0, 1] representing confidence
    for (let i = 0; i < segmentationMask.length; i++) {
      const val = segmentationMask[i];
      const alpha = Math.round(val * 255);
      
      // We write white for person, transparent for background
      data[i * 4] = 255;
      data[i * 4 + 1] = 255;
      data[i * 4 + 2] = 255;
      data[i * 4 + 3] = alpha; // opacity matches segmentation confidence
    }
    
    this.maskCtx.putImageData(maskImgData, 0, 0);

    // 4. Clip background image with mask
    // We want the background to appear ONLY where the person is
    this.tempCtx.save();
    this.tempCtx.globalCompositeOperation = 'destination-in';
    this.tempCtx.drawImage(this.maskCanvas, 0, 0);
    this.tempCtx.restore();

    // 5. Draw the masked background cutout onto output canvas
    outputCtx.drawImage(this.tempCanvas, 0, 0);
  }

  /**
   * Process and blend virtual background (replaces background, keeps person)
   */
  processVirtualBackground(outputCtx, videoElement, segmentationMask) {
    const w = this.width;
    const h = this.height;

    if (!segmentationMask) {
      outputCtx.drawImage(videoElement, 0, 0, w, h);
      return;
    }

    // 1. Draw virtual background to output canvas
    this.renderActiveBackground(outputCtx, videoElement);

    // 2. Prepare person cutout from video feed using mask
    this.tempCtx.clearRect(0, 0, w, h);
    this.tempCtx.drawImage(videoElement, 0, 0, w, h);

    // Write segmentation mask to maskCanvas
    this.maskCtx.clearRect(0, 0, w, h);
    const maskImgData = this.maskCtx.createImageData(w, h);
    const data = maskImgData.data;
    for (let i = 0; i < segmentationMask.length; i++) {
      data[i * 4] = 255;
      data[i * 4 + 1] = 255;
      data[i * 4 + 2] = 255;
      data[i * 4 + 3] = Math.round(segmentationMask[i] * 255);
    }
    this.maskCtx.putImageData(maskImgData, 0, 0);

    // Keep only the person in tempCanvas
    this.tempCtx.save();
    this.tempCtx.globalCompositeOperation = 'destination-in';
    this.tempCtx.drawImage(this.maskCanvas, 0, 0);
    this.tempCtx.restore();

    // 3. Draw person cutout over background
    outputCtx.drawImage(this.tempCanvas, 0, 0);
  }
}
