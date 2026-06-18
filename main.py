import cv2
import mediapipe as mp
import numpy as np

from core.background import BackgroundModel
from vision.hand_tracker import HandTracker
from vision.portal_detector import PortalDetector
from vision.gesture import GestureController
from graphics.renderer import Renderer

from ar.target_tracker import TargetTracker
from ar.overlay_factory import OverlayFactory
from ar.ar_renderer import ARRenderer


focus_points = []


def mouse_callback(event, x, y, flags, param):
    global focus_points

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(focus_points) < 4:
            focus_points.append((x, y))


def make_person_mask(segmenter, frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = segmenter.process(rgb)

    mask = (result.segmentation_mask > 0.45).astype(np.uint8) * 255

    kernel = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.dilate(mask, kernel, iterations=2)

    return mask


def match_background_light(background, frame):
    bg = background.astype(np.float32)
    live = frame.astype(np.float32)

    for c in range(3):
        bg_mean = np.mean(bg[:, :, c])
        live_mean = np.mean(live[:, :, c])
        bg[:, :, c] = bg[:, :, c] + (live_mean - bg_mean)

    return np.clip(bg, 0, 255).astype(np.uint8)


def apply_full_invisibility(frame, background, person_mask):
    corrected_bg = match_background_light(background, frame)

    output = frame.copy()
    output[person_mask > 0] = corrected_bg[person_mask > 0]

    return output


def apply_portal_invisibility(frame, background, portal):
    output = frame.copy()

    if portal is None:
        return output

    corrected_bg = match_background_light(background, frame)

    x1, y1, x2, y2 = portal
    output[y1:y2, x1:x2] = corrected_bg[y1:y2, x1:x2]

    return output


def apply_focus_window(frame, background, box):
    if box is None:
        return frame

    corrected_bg = match_background_light(background, frame)

    x1, y1, x2, y2 = box

    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)

    # Smooth feather edge so the selected box does not look pasted
    mask = cv2.GaussianBlur(mask, (41, 41), 0)
    mask_3d = cv2.merge([mask, mask, mask]) / 255.0

    output = (frame * mask_3d + corrected_bg * (1 - mask_3d)).astype(np.uint8)

    return output


def draw_selecting_points(output):
    for point in focus_points:
        cv2.circle(output, point, 10, (0, 255, 255), -1)

    if len(focus_points) >= 2:
        for i in range(len(focus_points) - 1):
            cv2.line(output, focus_points[i], focus_points[i + 1], (0, 255, 255), 2)


def flip_corners_for_mirror(corners, frame_width):
    if corners is None:
        return None

    flipped = corners.copy()

    # Mirror x coordinates to match the flipped display frame
    flipped[:, 0] = frame_width - flipped[:, 0]

    # Fix corner order after horizontal flip
    flipped = np.array(
        [
            flipped[1],
            flipped[0],
            flipped[3],
            flipped[2]
        ],
        dtype=np.float32
    )

    return flipped


def draw_small_status(frame, text):
    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (20, 20),
        (430, 70),
        (0, 0, 0),
        -1
    )

    frame = cv2.addWeighted(frame, 0.78, overlay, 0.22, 0)

    cv2.putText(
        frame,
        text,
        (35, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    return frame


def main():
    global focus_points

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Camera not found")
        return

    cv2.namedWindow("RealityFrame")
    cv2.setMouseCallback("RealityFrame", mouse_callback)

    background_model = BackgroundModel()
    background_model.capture(cap, frames_count=150)
    background = background_model.get()

    hand_tracker = HandTracker()
    portal_detector = PortalDetector()
    gesture = GestureController()
    renderer = Renderer()

    target_tracker = TargetTracker(marker_id=0)
    ar_overlay = OverlayFactory.creeper_face(size=700)
    ar_renderer = ARRenderer(ar_overlay)

    invisible_mode = "PORTAL"

    focus_mode = False
    focus_box = None
    selecting_focus_points = False

    ar_mode = False
    show_tracking_frame = False

    mp_selfie = mp.solutions.selfie_segmentation

    with mp_selfie.SelfieSegmentation(model_selection=1) as segmenter:
        while True:
            ret, raw_frame = cap.read()

            if not ret:
                break

            raw_h, raw_w = raw_frame.shape[:2]

            # Display is mirrored, like your original project
            frame = cv2.flip(raw_frame, 1)

            hands = hand_tracker.find_hands(frame)

            if gesture.pinch_triggered(hands):
                if invisible_mode == "PORTAL":
                    invisible_mode = "FULL"
                else:
                    invisible_mode = "PORTAL"

            portal = portal_detector.detect(hands, frame.shape)

            if invisible_mode == "FULL":
                person_mask = make_person_mask(segmenter, frame)
                output = apply_full_invisibility(frame, background, person_mask)
                active_portal = None
            else:
                output = apply_portal_invisibility(frame, background, portal)
                active_portal = portal

            if selecting_focus_points and len(focus_points) == 4:
                xs = [p[0] for p in focus_points]
                ys = [p[1] for p in focus_points]

                focus_box = (min(xs), min(ys), max(xs), max(ys))
                selecting_focus_points = False

            if focus_mode and focus_box:
                output = apply_focus_window(output, background, focus_box)

            if ar_mode:
                # Detect marker from raw camera frame
                raw_corners = target_tracker.detect(raw_frame)

                # Convert marker corners to mirrored display coordinates
                corners = flip_corners_for_mirror(raw_corners, raw_w)

                # Draw creeper face locked to marker
                output = ar_renderer.draw_target_overlay(output, corners)

                if show_tracking_frame:
                    output = ar_renderer.draw_tracking_frame(output, corners)

                output = draw_small_status(output, "TARGET AR MODE")

            output = hand_tracker.draw_hands(output, hands)

            if invisible_mode == "PORTAL":
                output = renderer.draw_portal(output, active_portal)

            if selecting_focus_points:
                draw_selecting_points(output)

            renderer.draw_hud(output, invisible_mode, active_portal)

            cv2.imshow("RealityFrame", output)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            if key == ord("b"):
                background_model.capture(cap, frames_count=150)
                background = background_model.get()

            if key == ord("f"):
                if focus_box is not None:
                    focus_mode = not focus_mode

            if key == ord("r"):
                focus_points.clear()
                focus_box = None
                focus_mode = False
                selecting_focus_points = True

            if key == ord("a"):
                ar_mode = not ar_mode

            if key == ord("v"):
                show_tracking_frame = not show_tracking_frame

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()