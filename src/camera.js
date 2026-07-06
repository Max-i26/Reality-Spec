/**
 * Camera module to initialize and manage the user's webcam feed.
 */

export class CameraManager {
  constructor(videoElement) {
    this.video = videoElement;
    this.stream = null;
    this.width = 0;
    this.height = 0;
  }

  /**
   * Request webcam access and assign stream to video element
   * @returns {Promise<{width: number, height: number}>} resolution details
   */
  async start() {
    if (this.stream) {
      this.stop();
    }

    const constraints = {
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: 'user',
        frameRate: { ideal: 30 }
      },
      audio: false
    };

    try {
      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      // Wait for metadata to load to get actual resolution
      await new Promise((resolve) => {
        // Check if metadata is already loaded
        if (this.video.videoWidth > 0 && this.video.videoHeight > 0) {
          this.width = this.video.videoWidth;
          this.height = this.video.videoHeight;
          this.video.play().catch(e => console.warn("video.play error:", e));
          resolve();
          return;
        }

        this.video.onloadedmetadata = () => {
          this.width = this.video.videoWidth;
          this.height = this.video.videoHeight;
          this.video.play().catch(e => console.warn("video.play error in listener:", e));
          resolve();
        };

        // Assign stream AFTER listener is set
        this.video.srcObject = this.stream;
      });

      return { width: this.width, height: this.height };
    } catch (err) {
      console.error('Error opening webcam: ', err);
      throw new Error('Camera access denied or device unavailable.');
    }
  }

  /**
   * Stop all video tracks
   */
  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.video.srcObject = null;
      this.stream = null;
    }
  }
}
