import cv2
import numpy as np
from PySide6.QtCore import QPoint, Signal, Slot, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QPushButton, QWidget, QGraphicsScene, QGraphicsPixmapItem

from .hikcap_ui import Ui_HIKCapture
from ..hik_sync_cam import HikSyncedCameras, FrameType

class HIKCaptureMain(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_HIKCapture()
        self.ui.setupUi(self)
        self.ui.lineEdit_exposure.setText("80000")
        self.ui.lineEdit_gain.setText("0")

        self._init_graphics_view()
        self.ui.pushButton_swtich.setEnabled(False)
        self.ui.pushButton_save_bmp.setEnabled(False)
        self.ui.pushButton_stream_mode.setEnabled(False)

        self.camera_group = HikSyncedCameras()

        self.ui.pushButton_detect.clicked.connect(self.detect_cameras)
        self.ui.pushButton_connect.clicked.connect(self.connect_cameras)
        self.ui.pushButton_capture.clicked.connect(self.camera_group.capture_dual_camera)
        self.ui.pushButton_save_jpg.clicked.connect(self.save_frames)
        self.ui.pushButton_setexpparams.clicked.connect(self.setexpgain)
        self.camera_group.frame_signal.connect(self.update_frame)

        # floating_button = QPushButton("Floating", self.ui.graphicsView_left)
        # pos = self.ui.graphicsView_left.pos()
        # pos = pos + QPoint(100, 50)
        # floating_button.move(pos.x(), pos.y())

    def _init_graphics_view(self):
        self.ui.graphicsView_left.setScene(QGraphicsScene(self))
        self.ui.graphicsView_right.setScene(QGraphicsScene(self))
        self.left_pixmap = QGraphicsPixmapItem()
        self.right_pixmap = QGraphicsPixmapItem()
        self.ui.graphicsView_left.scene().addItem(self.left_pixmap)
        self.ui.graphicsView_right.scene().addItem(self.right_pixmap)

    def detect_cameras(self):
        device_list = self.camera_group._enum_device_list()
        self.ui.comboBox_leftcam.clear()
        self.ui.comboBox_rightcam.clear()
        self.ui.comboBox_leftcam.addItems(device_list)
        self.ui.comboBox_rightcam.addItems(device_list)

        left_cam_id, right_cam_id = self.camera_group._infer_LR_by_name()
        self.ui.comboBox_leftcam.setCurrentIndex(left_cam_id)
        self.ui.comboBox_rightcam.setCurrentIndex(right_cam_id)

        # self.ui.pushButton_detect.setEnabled(False)

    def get_selected_cameras(self):
        left_cam = self.ui.comboBox_leftcam.currentIndex()
        right_cam = self.ui.comboBox_rightcam.currentIndex()
        return left_cam, right_cam 
    
    def setexpgain(self):
        self.camera_group.set_exp_gain(self.ui.lineEdit_exposure.text(), self.ui.lineEdit_gain.text())

    def connect_cameras(self):
        left_cam, right_cam = self.get_selected_cameras()
        if left_cam == right_cam:
            print("Please select different cameras!")
            return
        self.camera_group._set_cameras(left_cam, right_cam)
        self.camera_group._init_cameras()
        self.setexpgain()

        # UPDATE UIs
        self.ui.comboBox_leftcam.setEnabled(False)
        self.ui.comboBox_rightcam.setEnabled(False)
        self.ui.pushButton_connect.setEnabled(False)

    def update_frame(self, type: FrameType, frame: np.ndarray):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        if type == FrameType.LEFT:
            self.left_pixmap.setPixmap(QPixmap.fromImage(q_image))
            self.ui.graphicsView_left.fitInView(self.left_pixmap, Qt.KeepAspectRatio)
        elif type == FrameType.RIGHT:
            self.right_pixmap.setPixmap(QPixmap.fromImage(q_image))
            self.ui.graphicsView_right.fitInView(self.right_pixmap, Qt.KeepAspectRatio)

    def save_frames(self):
        self.camera_group.save_frames()
        from win11toast import notify
        notify("Captured images!")

    def closeEvent(self, event) -> None:
        self.camera_group._deinit_cameras()
        return super().closeEvent(event)



if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = HIKCaptureMain()
    window.show()
    sys.exit(app.exec())