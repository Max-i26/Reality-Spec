import math
import time


class GestureController:
    def __init__(self):
        self.last_pinch_time = 0
        self.cooldown = 1.0

    def distance(self, p1, p2):
        return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

    def is_pinch(self, hand):
        thumb_tip = hand.landmark[4]
        index_tip = hand.landmark[8]
        wrist = hand.landmark[0]
        middle_mcp = hand.landmark[9]

        pinch_dist = self.distance(thumb_tip, index_tip)
        hand_size = self.distance(wrist, middle_mcp)

        return pinch_dist < hand_size * 0.35

    def pinch_triggered(self, hands):
        now = time.time()

        if now - self.last_pinch_time < self.cooldown:
            return False

        for hand in hands:
            if self.is_pinch(hand):
                self.last_pinch_time = now
                return True

        return False