class PortalDetector:
    def detect(self, hands, frame_shape):
        if len(hands) < 2:
            return None

        h, w, _ = frame_shape

        points = []

        for hand in hands:
            for lm_id in [4, 8]:
                lm = hand.landmark[lm_id]
                points.append((int(lm.x * w), int(lm.y * h)))

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)

        if (x2 - x1) < 120 or (y2 - y1) < 80:
            return None

        return x1, y1, x2, y2