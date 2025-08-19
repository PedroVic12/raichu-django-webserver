# main.py
import cv2
import time
import math
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
import threading

# OPTIONAL: serial to Arduino
try:
    import serial
except Exception:
    serial = None

# ---------------------------
# Util functions
# ---------------------------
def angle_between_points(a, b, c):
    """Return angle ABC (in degrees)"""
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cosang = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cosang = np.clip(cosang, -1, 1)
    return np.degrees(np.arccos(cosang))

def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

# ---------------------------
# PoseCounter: conta pushups
# ---------------------------
class PoseCounter:
    """
    Usa MediaPipe Pose. Para pushups, medimos o ângulo do ombro-cotovelo-pulso (ou ombro-cotovelo).
    Lógica simples: quando o ângulo cai abaixo de threshold_down -> 'baixo'; quando sobe acima de threshold_up -> 'subida' (conta +1).
    """
    def __init__(self, threshold_down=90, threshold_up=160, smoothing=3):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.state = 'up'  # 'up' ou 'down'
        self.count = 0
        self.threshold_down = threshold_down
        self.threshold_up = threshold_up
        self.smoothing = smoothing
        self.angle_history = []

    def process(self, image_rgb):
        results = self.pose.process(image_rgb)
        if not results.pose_landmarks:
            return None, None
        lm = results.pose_landmarks.landmark
        h = results.pose_landmarks.landmark[0].y  # just to ensure list exists
        # landmarks indexes: shoulder=11 (left) / 12(right), elbow=13/14, wrist=15/16
        # We'll average left & right elbow angles if both available
        angles = []
        for side in [('left',11,13,15), ('right',12,14,16)]:
            _, s_idx, e_idx, w_idx = side
            try:
                shoulder = (lm[s_idx].x, lm[s_idx].y)
                elbow   = (lm[e_idx].x, lm[e_idx].y)
                wrist   = (lm[w_idx].x, lm[w_idx].y)
                ang = angle_between_points(shoulder, elbow, wrist)
                angles.append(ang)
            except Exception:
                pass
        if not angles:
            return results, None
        angle = np.mean(angles)
        # smoothing
        self.angle_history.append(angle)
        if len(self.angle_history) > self.smoothing:
            self.angle_history.pop(0)
        angle_smooth = float(np.mean(self.angle_history))

        # state machine
        if self.state == 'up' and angle_smooth < self.threshold_down:
            self.state = 'down'
        elif self.state == 'down' and angle_smooth > self.threshold_up:
            self.state = 'up'
            self.count += 1

        return results, round(angle_smooth,1)

    def reset(self):
        self.count = 0
        self.state = 'up'
        self.angle_history = []

# ---------------------------
# BallDetector: conta embaixadinhas
# ---------------------------
class BallDetector:
    """
    Usa YOLO para detectar bola (classe 'sports ball'). Para contar 'touches' (embaixadinhas):
    - Detecta bbox do objeto bola (centro).
    - Usa pose landmarks (nariz para cabeça, tornozelos/ankles para pés) para medir proximidade.
    - Se bola estiver perto do nariz ou perto do pé (distance < threshold) e houver transição cooldown -> conta +1.
    - Evita múltiplas contagens com cooldown_time (s).
    """
    def __init__(self, model_name='yolov8n.pt', conf=0.35, iou=0.45, cooldown_time=0.35):
        self.model = YOLO(model_name)
        self.conf = conf
        self.iou = iou
        self.last_touch_t = 0
        self.count = 0
        self.cooldown_time = cooldown_time

    def detect_ball(self, frame_bgr):
        # ultralytics model expects BGR or RGB, it handles both
        # returns list of detections with .boxes.xyxy and .boxes.cls and .boxes.conf
        results = self.model(frame_bgr, imgsz=640, conf=self.conf, iou=self.iou, verbose=False)
        # take first result (per frame), find sports ball class (usually 32 in COCO)
        if len(results) == 0:
            return None, results
        r = results[0]
        boxes = r.boxes
        if boxes is None or len(boxes) == 0:
            return None, results
        # find boxes with class name 'sports ball'
        for box in boxes:
            cls = int(box.cls[0])
            # ultralytics uses COCO labels; sports ball typically class 32 — but we will match by name if available
            # safer: check model.names
            name = r.names.get(cls, '')
            if 'ball' in name.lower() or 'sports' in name.lower() or 'soccer' in name.lower():
                xyxy = box.xyxy[0].cpu().numpy()  # [x1,y1,x2,y2]
                x1,y1,x2,y2 = xyxy
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                return (int(cx), int(cy), int(x1), int(y1), int(x2), int(y2)), results
        # none matching
        return None, results

    def try_count_touch(self, ball_center, pose_landmarks, frame_shape):
        """
        ball_center: (cx,cy,x1,y1,x2,y2) in pixel coords
        pose_landmarks: mediapipe result.pose_landmarks.landmark (normalized coords)
        frame_shape: (h,w)
        """
        if ball_center is None or pose_landmarks is None:
            return False
        now = time.time()
        if now - self.last_touch_t < self.cooldown_time:
            return False
        cx, cy, x1, y1, x2, y2 = ball_center
        h, w = frame_shape[:2]
        # map pose landmarks to pixel coords
        try:
            # nose index 0, left ankle 27, right ankle 28 (MediaPipe Pose has 33 landmarks)
            nose = pose_landmarks.landmark[0]
            la = pose_landmarks.landmark[27]
            ra = pose_landmarks.landmark[28]
            nose_pt = (int(nose.x * w), int(nose.y * h))
            la_pt = (int(la.x * w), int(la.y * h))
            ra_pt = (int(ra.x * w), int(ra.y * h))
        except Exception:
            return False

        ball_pt = (int(cx), int(cy))
        # distances
        d_nose = dist(ball_pt, nose_pt)
        d_la = dist(ball_pt, la_pt)
        d_ra = dist(ball_pt, ra_pt)

        # dynamic threshold based on frame size
        threshold_head = h * 0.08  # adjustable
        threshold_foot = h * 0.10

        # if ball near nose (head touch) OR near either ankle (foot touch) -> count
        if d_nose < threshold_head or d_la < threshold_foot or d_ra < threshold_foot:
            self.count += 1
            self.last_touch_t = now
            return True
        return False

# ---------------------------
# VideoApp: loop principal
# ---------------------------
class VideoApp:
    def __init__(self, cam_index=0, use_arduino=False, arduino_port='COM3', baud=9600):
        self.cam_index = cam_index
        self.cap = cv2.VideoCapture(cam_index)
        self.pose_counter = PoseCounter()
        self.ball_detector = BallDetector()
        self.use_arduino = use_arduino and serial is not None
        self.serial_conn = None
        if self.use_arduino:
            try:
                self.serial_conn = serial.Serial(arduino_port, baud, timeout=0.5)
                print(f"[Arduino] connected to {arduino_port} @ {baud}")
            except Exception as e:
                print("[Arduino] couldn't connect:", e)
                self.use_arduino = False

        # drawing colors
        self.color_bg = (18,18,18)
        self.last_send_t = 0

    def send_to_arduino(self, pushups, embaixadas):
        if not self.use_arduino or not self.serial_conn:
            return
        now = time.time()
        if now - self.last_send_t < 0.5:
            return
        try:
            msg = f"P,{pushups},{embaixadas}\n"
            self.serial_conn.write(msg.encode())
            self.last_send_t = now
        except Exception as e:
            print("[Arduino] send failed:", e)

    def run(self):
        prev_time = time.time()
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Camera not available")
                break
            frame = cv2.flip(frame, 1)  # mirror
            h, w = frame.shape[:2]
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Pose processing
            pose_res, elbow_angle = self.pose_counter.process(image_rgb)
            # Ball detection
            ball_center, _ = self.ball_detector.detect_ball(frame)

            # if pose landmarks exist, try to count ball touches
            if pose_res and pose_res.pose_landmarks:
                touched = self.ball_detector.try_count_touch(ball_center, pose_res.pose_landmarks, frame.shape)
                if touched:
                    print("Embaixada! total:", self.ball_detector.count)

            # overlay: draw ball bbox & center
            if ball_center is not None:
                cx, cy, x1, y1, x2, y2 = ball_center
                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,200,255), 2)
                cv2.circle(frame, (cx,cy), 6, (0,200,255), -1)

            # draw pose landmarks
            if pose_res and pose_res.pose_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, pose_res.pose_landmarks, self.pose_counter.mp_pose.POSE_CONNECTIONS,
                    mp.solutions.drawing_utils.DrawingSpec(color=(80,200,120), thickness=2, circle_radius=2),
                    mp.solutions.drawing_utils.DrawingSpec(color=(80,120,200), thickness=1, circle_radius=1)
                )

            # text overlays
            # pushups
            pu_count = self.pose_counter.count
            em_count = self.ball_detector.count
            angle_text = f"{elbow_angle}°" if elbow_angle is not None else "--"
            cv2.putText(frame, f"PUSHUPS: {pu_count}", (12,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200,200,50), 2)
            cv2.putText(frame, f"ELBOW ANGLE: {angle_text}", (12,60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180,180,180), 2)
            cv2.putText(frame, f"EMBAIXADAS: {em_count}", (12,95), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50,200,200), 2)

            # fps
            now = time.time()
            fps = 1.0 / (now - prev_time + 1e-8)
            prev_time = now
            cv2.putText(frame, f"FPS: {int(fps)}", (w-120,30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)

            cv2.imshow("Pushups + Embaixadinhas Counter", frame)

            # optionally send counts to Arduino once in a while
            self.send_to_arduino(pu_count, em_count)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            if key == ord('r'):
                self.pose_counter.reset()
                self.ball_detector.count = 0
                print("Reset counts")

        self.cap.release()
        cv2.destroyAllWindows()
        if self.serial_conn:
            self.serial_conn.close()

# ---------------------------
# Entrypoint
# ---------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cam", type=int, default=0, help="webcam index")
    parser.add_argument("--arduino", action='store_true', help="enable arduino serial")
    parser.add_argument("--port", type=str, default="COM3", help="arduino serial port (COMx or /dev/ttyUSBx)")
    parser.add_argument("--baud", type=int, default=115200, help="serial baud")
    args = parser.parse_args()

    app = VideoApp(cam_index=args.cam, use_arduino=args.arduino, arduino_port=args.port, baud=args.baud)
    app.run()
