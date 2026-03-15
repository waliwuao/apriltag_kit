import cv2
import numpy as np

def draw_tag_info(image, tag_id, corners, rvec, tvec, mtx, dist, tag_size):
    pts = corners.astype(int)
    for i in range(4):
        cv2.line(image, tuple(pts[i]), tuple(pts[(i + 1) % 4]), (0, 255, 0), 2)

    cv2.putText(image, f"ID: {tag_id}", (pts[0][0], pts[0][1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    axis_len = tag_size
    axis_pts = np.float32([[0,0,0], [axis_len,0,0], [0,axis_len,0], [0,0,axis_len]]).reshape(-1, 3)
    img_pts, _ = cv2.projectPoints(axis_pts, rvec, tvec, mtx, dist)
    img_pts = img_pts.astype(int).reshape(-1, 2)

    origin = tuple(img_pts[0])
    cv2.line(image, origin, tuple(img_pts[1]), (0, 0, 255), 2)
    cv2.line(image, origin, tuple(img_pts[2]), (0, 255, 0), 2)
    cv2.line(image, origin, tuple(img_pts[3]), (255, 0, 0), 2)

    distance = np.linalg.norm(tvec)
    cv2.putText(image, f"Dist: {distance:.2f}m", (pts[0][0], pts[0][1] - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    return image
