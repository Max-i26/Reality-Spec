import cv2
import numpy as np


class Renderer:
    def draw_portal(self, frame, portal):
        if portal is None:
            return frame

        x1, y1, x2, y2 = portal

        line_layer = np.zeros_like(frame)

        corner = 45
        color = (0, 200, 255)
        thick = 6

        cv2.rectangle(line_layer, (x1, y1), (x2, y2), (255, 255, 255), 2)

        corners = [
            ((x1, y1), (x1 + corner, y1), (x1, y1 + corner)),
            ((x2, y1), (x2 - corner, y1), (x2, y1 + corner)),
            ((x1, y2), (x1 + corner, y2), (x1, y2 - corner)),
            ((x2, y2), (x2 - corner, y2), (x2, y2 - corner)),
        ]

        for main, p1, p2 in corners:
            cv2.line(line_layer, main, p1, color, thick)
            cv2.line(line_layer, main, p2, color, thick)

        glow = cv2.GaussianBlur(line_layer, (25, 25), 0)

        frame = cv2.addWeighted(frame, 1.0, glow, 0.35, 0)
        frame = cv2.addWeighted(frame, 1.0, line_layer, 1.0, 0)

        return frame

    def draw_text(self, frame, text, y):
        cv2.putText(
            frame,
            text,
            (30, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

    def draw_hud(self, frame, mode, portal):
        return frame