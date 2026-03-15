import cv2
import numpy as np
import glob
import os

class CameraCalibrator:
    def __init__(self, square_size):
        self.square_size = square_size
        self.common_sizes = [(9, 6), (8, 6), (7, 5), (10, 7), (11, 8)]

    def _auto_find_chessboard(self, gray):
        for size in self.common_sizes:
            ret, corners = cv2.findChessboardCorners(gray, size, None)
            if ret:
                return ret, corners, size
        return False, None, None

    def calibrate(self, image_folder, output_path="camera_calibration.npz"):
        images = glob.glob(os.path.join(image_folder, "*.png")) + glob.glob(os.path.join(image_folder, "*.jpg"))
        if not images:
            return False

        objpoints = []
        imgpoints = []
        detected_size = None
        img_shape = None

        for fname in images:
            img = cv2.imread(fname)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img_shape = gray.shape[::-1]

            ret, corners, size = self._auto_find_chessboard(gray)
            if ret:
                if detected_size is None:
                    detected_size = size
                elif detected_size != size:
                    continue

                objp = np.zeros((size[0] * size[1], 3), np.float32)
                objp[:, :2] = np.mgrid[0:size[0], 0:size[1]].T.reshape(-1, 2)
                objp *= self.square_size

                objpoints.append(objp)
                imgpoints.append(corners)

        if not objpoints:
            return False

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img_shape, None, None)
        if ret:
            np.savez(output_path, mtx=mtx, dist=dist)
            return True
        return False
