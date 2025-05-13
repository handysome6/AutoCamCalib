import cv2
import numpy as np
from pathlib import Path
from loguru import logger
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QMessageBox

from auto_gui_ui import Ui_MainWIndow
from hik.hik_sync_cam import HikSyncedCameras, FrameType
from pts.auto_pts import scan_positions, PTSPositionGenerator
from pts.pts_controller import PTSController


ROOT_DIR = Path.home() / "DCIM"
DEFAULT_EXP = 220000
DEFAULT_GAIN = 5

DEFAULT_H_FOV = 55
DEFAULT_H_COUNT = 10
DEFAULT_V_FOV = 35
DEFAULT_V_COUNT = 10
DEFAULT_PORT = "COM4"


class ScanThread(QThread):
    position_reached = Signal(dict)  # 发送位置信息
    scan_finished = Signal()         # 扫描完成信号
    
    def __init__(self, camera_group: HikSyncedCameras, port: str = "COM4", h_fov: float = 40, v_fov: float = 40, h_count: int = 9, v_count: int = 9):
        super().__init__()
        self.camera_group = camera_group
        self.port = port
        self.h_fov = h_fov
        self.v_fov = v_fov
        self.h_count = h_count
        self.v_count = v_count
        self._is_running = True
        
    def stop(self):
        self._is_running = False
        
    def run(self):
        try:
            for position_info in scan_positions(h_fov=self.h_fov, v_fov=self.v_fov, h_count=self.h_count, v_count=self.v_count, port=self.port):
                if not self._is_running:
                    break
                    
                self.position_reached.emit(position_info)
                QThread.msleep(1500)
                self.camera_group.capture_dual_camera()
                QThread.msleep(1000)

            self.scan_finished.emit()
        except Exception as e:
            logger.error(f"Scan process error: {str(e)}")
            self.scan_finished.emit()


class AutoGui(QMainWindow, Ui_MainWIndow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._init_graphics_view()
        self._set_default_values()
        self.camera_group = None
        self.scan_thread = None

        self.left_frame_captured = False
        self.right_frame_captured = False

        self.actionConnnect_Cameras.triggered.connect(self.connect_camera)
        self.pushButton_start.clicked.connect(self.start_scan_process)

        self.lineEdit_savingPath.setText(str(ROOT_DIR))

    def _set_default_values(self):
        self.lineEdit_hFov.setText(str(DEFAULT_H_FOV))
        self.lineEdit_hCount.setText(str(DEFAULT_H_COUNT))
        self.lineEdit_vFov.setText(str(DEFAULT_V_FOV))
        self.lineEdit_vCount.setText(str(DEFAULT_V_COUNT))
        self.lineEdit_serialPort.setText(str(DEFAULT_PORT))
        self.lineEdit_expTime.setText(str(DEFAULT_EXP))
        self.lineEdit_gain.setText(str(DEFAULT_GAIN))

        self.position_generator = PTSPositionGenerator(
            center_pan=90,
            center_tilt=30,
            h_fov=DEFAULT_H_FOV,
            v_fov=DEFAULT_V_FOV,
            h_count=DEFAULT_H_COUNT,
            v_count=DEFAULT_V_COUNT
        )

        self.lineEdit_hFov.textChanged.connect(self.update_position_generator)
        self.lineEdit_hCount.textChanged.connect(self.update_position_generator)
        self.lineEdit_vFov.textChanged.connect(self.update_position_generator)
        self.lineEdit_vCount.textChanged.connect(self.update_position_generator)

        self.pushButton_botLeft.clicked.connect(self.move_bot_left)
        self.pushButton_botRight.clicked.connect(self.move_bot_right)
        self.pushButton_topRight.clicked.connect(self.move_top_right)
        self.pushButton_topLeft.clicked.connect(self.move_top_left)

    def update_position_generator(self):
        self.position_generator.update_params(
            h_fov=float(self.lineEdit_hFov.text()),
            v_fov=float(self.lineEdit_vFov.text()),
            h_count=int(self.lineEdit_hCount.text()),
            v_count=int(self.lineEdit_vCount.text())
        )

    def move_bot_left(self):
        position = self.position_generator.bottom_left()
        logger.info(f"移动到位置: {position}")
        pts_controller = PTSController(port=self.lineEdit_serialPort.text())
        pts_controller.set_pan_tilt(position[0], position[1])
        pts_controller.close()
    
    def move_bot_right(self):
        position = self.position_generator.bottom_right()
        logger.info(f"移动到位置: {position}")
        pts_controller = PTSController(port=self.lineEdit_serialPort.text())
        pts_controller.set_pan_tilt(position[0], position[1])
        pts_controller.close()

    def move_top_right(self):
        position = self.position_generator.top_right()
        logger.info(f"移动到位置: {position}")
        pts_controller = PTSController(port=self.lineEdit_serialPort.text())
        pts_controller.set_pan_tilt(position[0], position[1])
        pts_controller.close()
        
    def move_top_left(self):
        position = self.position_generator.top_left()
        logger.info(f"移动到位置: {position}")
        pts_controller = PTSController(port=self.lineEdit_serialPort.text())
        pts_controller.set_pan_tilt(position[0], position[1])
        pts_controller.close()

    def _init_graphics_view(self):
        self.graphicsView_left.setScene(QGraphicsScene(self))
        self.graphicsView_right.setScene(QGraphicsScene(self))
        self.left_pixmap = QGraphicsPixmapItem()
        self.right_pixmap = QGraphicsPixmapItem()
        self.graphicsView_left.scene().addItem(self.left_pixmap)
        self.graphicsView_right.scene().addItem(self.right_pixmap)

    def connect_camera(self):
        self.camera_group = HikSyncedCameras()
        self.camera_group.initialize_camera_group()
        self.camera_group.frame_signal.connect(self.update_frame)
        self.camera_group.frame_signal.connect(self.save_frame)

        # set default exp and gain
        self.camera_group.set_exp(DEFAULT_EXP)
        self.camera_group.set_gain(DEFAULT_GAIN)

        self.lineEdit_expTime.textChanged.connect(lambda: self.camera_group.set_exp(int(self.lineEdit_expTime.text())))
        self.lineEdit_gain.textChanged.connect(lambda: self.camera_group.set_gain(int(self.lineEdit_gain.text())))

        self.actionCapture_Camera.triggered.connect(self.camera_group.capture_dual_camera)

    def start_scan_process(self):
        if not self.camera_group:
            QMessageBox.warning(self, "警告", "请先连接相机")
            return
            
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
            self.scan_thread.wait()
            
        self.scan_thread = ScanThread(
            self.camera_group, 
            port=self.lineEdit_serialPort.text(),
            h_fov=float(self.lineEdit_hFov.text()),
            v_fov=float(self.lineEdit_vFov.text()),
            h_count=int(self.lineEdit_hCount.text()),
            v_count=int(self.lineEdit_vCount.text())
        )
        self.scan_thread.position_reached.connect(self.on_position_reached)
        self.scan_thread.scan_finished.connect(self.on_scan_finished)
        self.scan_thread.start()
        
        self.pushButton_start.setEnabled(False)
        
    def on_position_reached(self, position_info):
        logger.info(f"到达位置 {position_info['index']}")
        
    def on_scan_finished(self):
        self.pushButton_start.setEnabled(True)
        logger.info("扫描过程完成")

    def update_frame(self, type: FrameType, frame: np.ndarray):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        if type == FrameType.LEFT:
            self.left_pixmap.setPixmap(QPixmap.fromImage(q_image))
            self.graphicsView_left.fitInView(self.left_pixmap, Qt.KeepAspectRatio)
        elif type == FrameType.RIGHT:
            self.right_pixmap.setPixmap(QPixmap.fromImage(q_image))
            self.graphicsView_right.fitInView(self.right_pixmap, Qt.KeepAspectRatio)

    def save_frame(self, type: FrameType, frame: np.ndarray):
        if type == FrameType.LEFT:
            self.left_frame_captured = True
        elif type == FrameType.RIGHT:
            self.right_frame_captured = True

        if self.left_frame_captured and self.right_frame_captured:
            self.camera_group.save_frames(self.lineEdit_savingPath.text())
            # reset flag
            self.left_frame_captured = False
            self.right_frame_captured = False

    def closeEvent(self, event):
        if self.camera_group:
            self.camera_group._deinit_cameras()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = AutoGui()
    window.show()
    sys.exit(app.exec())
