import cv2
import numpy as np
from pupil_apriltags import Detector

from .visualization import draw_tag_info


class BaseDetector:
    def __init__(self, calib_file, tag_size, family="tag36h11"):
        data = np.load(calib_file)
        self.mtx = data['mtx']
        self.dist = data['dist']
        self.tag_size = float(tag_size)
        self.detector = Detector(families=family, nthreads=1)
        self.obj_pts = np.array([
            [-self.tag_size / 2, -self.tag_size / 2, 0],
            [self.tag_size / 2, -self.tag_size / 2, 0],
            [self.tag_size / 2, self.tag_size / 2, 0],
            [-self.tag_size / 2, self.tag_size / 2, 0],
        ], dtype=np.float32)

    def detect_and_process(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        results = self.detector.detect(gray)
        detections = []

        for r in results:
            corners = np.array(r.corners, dtype=np.float32)
            success, rvec, tvec = cv2.solvePnP(self.obj_pts, corners, self.mtx, self.dist)
            if success:
                draw_tag_info(frame, r.tag_id, corners, rvec, tvec, self.mtx, self.dist, self.tag_size)
                detections.append({
                    'id': r.tag_id,
                    'rvec': rvec,
                    'tvec': tvec,
                    'center': np.array(r.center),
                    'distance': float(np.linalg.norm(tvec)),
                })
        return frame, detections

class StaticDetector(BaseDetector):
    def process_image(self, image_path):
        image = cv2.imread(image_path)
        if image is None: return None, []
        return self.detect_and_process(image)

class LiveDetector(BaseDetector):
    def start(self, camera_id=0):
        cap = cv2.VideoCapture(camera_id)
        while True:
            ret, frame = cap.read()
            if not ret: break

            processed_frame, info = self.detect_and_process(frame)
            cv2.imshow("AprilTag Live Detection", processed_frame)

            if info:
                print(f"Detected {len(info)} tags")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
