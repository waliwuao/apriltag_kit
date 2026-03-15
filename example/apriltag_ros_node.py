import os
import sys

_font_paths = [
    "/usr/share/fonts/truetype",
    "/usr/share/fonts",
    "/usr/share/fonts/TTF"
]
for _path in _font_paths:
    if os.path.exists(_path):
        os.environ["QT_QPA_FONTDIR"] = _path
        break

os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.fonts.warning=false"

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import cv2
import numpy as np
import yaml
import math

if hasattr(cv2, 'setLogLevel'):
    cv2.setLogLevel(3)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from apriltag_kit.detection import BaseDetector

def euler_to_matrix(roll, pitch, yaw):
    r, p, y = map(math.radians, [roll, pitch, yaw])
    R_x = np.array([[1, 0, 0], [0, math.cos(r), -math.sin(r)], [0, math.sin(r), math.cos(r)]])
    R_y = np.array([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]])
    R_z = np.array([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]])
    return R_z @ R_y @ R_x

def matrix_to_quaternion(R):
    tr = np.trace(R)
    if tr > 0:
        S = math.sqrt(tr + 1.0) * 2
        qw = 0.25 * S
        qx = (R[2, 1] - R[1, 2]) / S
        qy = (R[0, 2] - R[2, 0]) / S
        qz = (R[1, 0] - R[0, 1]) / S
    elif (R[0, 0] > R[1, 1]) and (R[0, 0] > R[2, 2]):
        S = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        qw = (R[2, 1] - R[1, 2]) / S
        qx = 0.25 * S
        qy = (R[0, 1] + R[1, 0]) / S
        qz = (R[0, 2] + R[2, 0]) / S
    elif R[1, 1] > R[2, 2]:
        S = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        qw = (R[0, 2] - R[2, 0]) / S
        qx = (R[0, 1] + R[1, 0]) / S
        qy = 0.25 * S
        qz = (R[1, 2] + R[2, 1]) / S
    else:
        S = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        qw = (R[1, 0] - R[0, 1]) / S
        qx = (R[0, 2] + R[2, 0]) / S
        qy = (R[1, 2] + R[2, 1]) / S
        qz = 0.25 * S
    return qx, qy, qz, qw

class ApriltagRosNode(Node):
    def __init__(self):
        super().__init__('apriltag_pose_publisher')
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'tags_config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        settings = self.config['apriltag_settings']
        self.tag_size = float(settings['tag_size'])
        self.tags_map = {}
        for k, v in self.config['tags_world_coordinates'].items():
            R_w_t = euler_to_matrix(
                float(v.get('roll', 0)), float(v.get('pitch', 0)), float(v.get('yaw', 0))
            )
            t_w_t = np.array([float(v['x']), float(v['y']), float(v['z'])], dtype=np.float64).reshape(3, 1)
            self.tags_map[int(v['id'])] = (R_w_t, t_w_t)

        calib_file = os.path.join(os.path.dirname(__file__), '..', 'camera_calibration.npz')
        self.detector = BaseDetector(calib_file, self.tag_size, settings['family'])
        self.publisher_ = self.create_publisher(PoseStamped, settings['publish_topic'], 10)
        self.cap = cv2.VideoCapture(int(settings['camera_id']))
        self.timer = self.create_timer(0.03, self.process_frame)

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        processed_frame, detections = self.detector.detect_and_process(frame)
        for det in detections:
            tag_id = det['id']
            if tag_id not in self.tags_map:
                continue

            R_t_c, _ = cv2.Rodrigues(det['rvec'])
            t_t_c = np.asarray(det['tvec']).reshape(3, 1)
            R_c_t = R_t_c.T
            t_c_t = -R_c_t @ t_t_c

            R_w_t, t_w_t = self.tags_map[tag_id]
            R_w_c = R_w_t @ R_c_t
            t_w_c = R_w_t @ t_c_t + t_w_t

            qx, qy, qz, qw = matrix_to_quaternion(R_w_c)
            msg = PoseStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "world"
            msg.pose.position.x, msg.pose.position.y, msg.pose.position.z = t_w_c.flatten()
            msg.pose.orientation.x, msg.pose.orientation.y, msg.pose.orientation.z, msg.pose.orientation.w = qx, qy, qz, qw
            self.publisher_.publish(msg)

            cv2.putText(
                processed_frame,
                f"Cam XYZ: {t_w_c.flatten()[0]:.2f}, {t_w_c.flatten()[1]:.2f}, {t_w_c.flatten()[2]:.2f}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
            )
        cv2.imshow("ROS2 AprilTag Detection", processed_frame)
        cv2.waitKey(1)

    def destroy_node(self):
        self.cap.release()
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ApriltagRosNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
