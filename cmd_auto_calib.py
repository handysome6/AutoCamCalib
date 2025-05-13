from PySide6.QtWidgets import QApplication

from pts.auto_pts import scan_positions
from hik.hik_sync_cam import HikSyncedCameras


app = QApplication([])
cam = HikSyncedCameras()
cam.initialize_camera_group()
cam.frame_signal.connect(lambda frame_type, frame: print(frame_type, frame.shape))

for position_info in scan_positions(h_fov=40, v_fov=40, h_count=9, v_count=9, port="COM4"):
    if position_info['success']:
        print(f"成功到达位置 {position_info['index']}")
        cam.capture_dual_camera()
    else:
        print(f"位置 {position_info['index']} 移动失败")

app.exec()

