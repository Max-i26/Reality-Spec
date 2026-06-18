import cv2
import numpy as np


class BackgroundModel:
    def __init__(self):
        self.background = None

    def capture(self, cap, frames_count=120):
        frames = []

        for _ in range(frames_count):
            ret, frame = cap.read()

            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            frames.append(frame)

            cv2.putText(
                frame,
                "Step OUT of frame - capturing background",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            cv2.imshow("RealityFrame", frame)
            cv2.waitKey(1)

        self.background = np.median(frames, axis=0).astype(np.uint8)

    def get(self):
        return self.background