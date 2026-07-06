/**
 * Media Recorder module to capture Canvas frames and save them as MP4/WebM video downloads.
 */

export class CanvasRecorder {
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.mediaRecorder = null;
    this.recordedChunks = [];
    this.isRecording = false;
  }

  /**
   * Start recording the canvas stream
   * @param {number} fps Frame rate of capture stream
   */
  start(fps = 30) {
    if (this.isRecording) return;
    
    this.recordedChunks = [];
    
    // Capture stream from canvas
    const stream = this.canvas.captureStream(fps);
    
    // Select supported video mimeType (prefer standard codecs)
    const options = { mimeType: 'video/webm;codecs=vp9' };
    
    try {
      this.mediaRecorder = new MediaRecorder(stream, options);
    } catch (e) {
      console.warn('VP9 video format not supported. Falling back to default WebM.', e);
      try {
        this.mediaRecorder = new MediaRecorder(stream);
      } catch (err) {
        console.error('MediaRecorder initialization failed.', err);
        throw new Error('Video recording not supported in this browser.');
      }
    }

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        this.recordedChunks.push(event.data);
      }
    };

    this.mediaRecorder.onstop = () => {
      this.saveVideo();
    };

    // Collect data slices every 1 second
    this.mediaRecorder.start(1000);
    this.isRecording = true;
  }

  /**
   * Stop recording
   */
  stop() {
    if (!this.isRecording) return;
    this.mediaRecorder.stop();
    this.isRecording = false;
  }

  /**
   * Bundles recorded chunks and triggers file download
   */
  saveVideo() {
    const blob = new Blob(this.recordedChunks, {
      type: 'video/webm'
    });
    
    const url = URL.createObjectURL(blob);
    
    // Create download link element
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `RealityFrame_Record_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '_')}.webm`;
    
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    setTimeout(() => {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 100);
  }
}
