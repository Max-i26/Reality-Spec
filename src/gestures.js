/**
 * Gesture detection helper for MediaPipe Hand Landmarks.
 */

export class GestureDetector {
  constructor() {
    this.cooldown = 1000; // ms
    this.lastTriggeredTime = 0;
  }

  // Calculate Euclidean distance between two 3D landmarks
  distance(p1, p2) {
    return Math.sqrt(
      Math.pow(p1.x - p2.x, 2) +
      Math.pow(p1.y - p2.y, 2) +
      Math.pow(p1.z - p2.z, 2)
    );
  }

  // Check if finger is extended (distance from tip to wrist is greater than MCP to wrist)
  isFingerExtended(tip, mcp, wrist) {
    return this.distance(tip, wrist) > this.distance(mcp, wrist) * 1.15;
  }

  // Detect individual gestures
  isPinch(hand) {
    const thumbTip = hand[4];
    const indexTip = hand[8];
    const wrist = hand[0];
    const middleMcp = hand[9];

    const pinchDist = this.distance(thumbTip, indexTip);
    const handSize = this.distance(wrist, middleMcp);

    // If pinch distance is less than 32% of hand size
    return pinchDist < handSize * 0.32;
  }

  isFist(hand) {
    const wrist = hand[0];
    // Check if index, middle, ring, pinky are folded (tips close to wrist)
    const fingerTips = [hand[8], hand[12], hand[16], hand[20]];
    const fingerMcps = [hand[5], hand[9], hand[13], hand[17]];

    let foldedCount = 0;
    for (let i = 0; i < 4; i++) {
      const tipToWrist = this.distance(fingerTips[i], wrist);
      const mcpToWrist = this.distance(fingerMcps[i], wrist);
      // If the tip is closer to the wrist than the base (MCP) joint
      if (tipToWrist < mcpToWrist * 0.95) {
        foldedCount++;
      }
    }
    return foldedCount === 4;
  }

  isThumbsUp(hand) {
    const wrist = hand[0];
    const thumbTip = hand[4];
    const thumbIp = hand[3];
    const thumbMcp = hand[2];
    const indexMcp = hand[5];
    const pinkyMcp = hand[17];

    // Check if other fingers are folded (fist-like)
    const otherTips = [hand[8], hand[12], hand[16], hand[20]];
    const otherMcps = [hand[5], hand[9], hand[13], hand[17]];
    let foldedCount = 0;
    for (let i = 0; i < 4; i++) {
      if (this.distance(otherTips[i], wrist) < this.distance(otherMcps[i], wrist) * 1.0) {
        foldedCount++;
      }
    }

    // Thumb pointing upward (y-coord of tip is smaller than MCP in screen coords)
    const isPointingUp = thumbTip.y < thumbIp.y && thumbIp.y < thumbMcp.y;
    // Thumb is also extended away from index finger
    const thumbExt = this.distance(thumbTip, indexMcp) > this.distance(pinkyMcp, indexMcp) * 0.45;

    return foldedCount >= 3 && isPointingUp && thumbExt;
  }

  isVictory(hand) {
    const wrist = hand[0];
    const indexTip = hand[8];
    const indexMcp = hand[5];
    const middleTip = hand[12];
    const middleMcp = hand[9];
    
    // Index and Middle extended
    const indexExt = this.isFingerExtended(indexTip, indexMcp, wrist);
    const middleExt = this.isFingerExtended(middleTip, middleMcp, wrist);

    // Ring and Pinky folded
    const ringTip = hand[16];
    const ringMcp = hand[13];
    const pinkyTip = hand[20];
    const pinkyMcp = hand[17];
    const ringFolded = this.distance(ringTip, wrist) < this.distance(ringMcp, wrist);
    const pinkyFolded = this.distance(pinkyTip, wrist) < this.distance(pinkyMcp, wrist);

    // Spread between index and middle
    const spread = this.distance(indexTip, middleTip);
    const handSize = this.distance(wrist, middleMcp);

    return indexExt && middleExt && ringFolded && pinkyFolded && spread > handSize * 0.25;
  }

  /**
   * Evaluates hand landmark results and returns detected gesture
   * @param {Array} handsList MediaPipe Landmarker multi-hand landmarks
   * @returns {string} detected gesture label
   */
  detect(handsList) {
    if (!handsList || handsList.length === 0) return 'NONE';

    // If double hand is detected, check for double pinch
    if (handsList.length >= 2) {
      if (this.isPinch(handsList[0]) && this.isPinch(handsList[1])) {
        return 'DOUBLE_PINCH';
      }
    }

    // Single hand detection
    const primaryHand = handsList[0];
    if (this.isFist(primaryHand)) return 'FIST';
    if (this.isThumbsUp(primaryHand)) return 'THUMBS_UP';
    if (this.isVictory(primaryHand)) return 'VICTORY';
    if (this.isPinch(primaryHand)) return 'PINCH';

    return 'NONE';
  }

  /**
   * Reconstruct portal box coordinates from two hands (Thumb + Index tips)
   * @param {Array} handsList 
   * @param {number} width 
   * @param {number} height 
   * @returns {Object|null} portal bounding box
   */
  getPortalBox(handsList, width, height) {
    if (!handsList || handsList.length < 2) return null;

    const points = [];
    for (let i = 0; i < 2; i++) {
      const hand = handsList[i];
      // Index Tip (8) and Thumb Tip (4)
      const indexTip = hand[8];
      const thumbTip = hand[4];

      points.push({ x: indexTip.x * width, y: indexTip.y * height });
      points.push({ x: thumbTip.x * width, y: thumbTip.y * height });
    }

    const xs = points.map(p => p.x);
    const ys = points.map(p => p.y);

    const x1 = Math.min(...xs);
    const y1 = Math.min(...ys);
    const x2 = Math.max(...xs);
    const y2 = Math.max(...ys);

    // Minimum size requirements
    if ((x2 - x1) < 80 || (y2 - y1) < 60) {
      return null;
    }

    return { x1, y1, x2, y2, width: x2 - x1, height: y2 - y1 };
  }
}
