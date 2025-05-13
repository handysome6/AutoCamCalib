# hik_sync_cam.py

import cv2
import sys
import time
import numpy as np
from ctypes import *
from pathlib import Path
from loguru import logger
from PySide6.QtCore import Signal, QObject, QThread, QThreadPool, QRunnable

from hik.utils import load_hik_sdk, buffer2numpy
load_hik_sdk()
from MvCameraControl_class import * 


HIK_SYNC = 1
ROOT_DIR = Path.home() / "DCIM"
MASTER_CFG_PATH = Path(__file__).parent / "camera_config" / "master.cfg"
SLAVE_CFG_PATH = Path(__file__).parent / "camera_config" / "slave.cfg"

LEFT_CAM_TYPE = "SLAVE"
RIGHT_CAM_TYPE = "MASTER"


from enum import Enum
class FrameType(Enum):
    LEFT = 0
    RIGHT = 1

class HikSyncedCameras(QObject):
    """
        This class is used to control HIK robotics cameras connection in QT way
    """
    frame_signal = Signal(FrameType, np.ndarray)
    def __init__(self):
        super().__init__()
        self.left_cam = None
        self.right_cam = None
        self.left_frame = None
        self.right_frame = None

        self.left_cam_thread = None
        self.right_cam_thread = None
        self.master_cam = None
        self.slave_cam = None
        self.devList = []

    def _enum_device_list(self) -> list[str]:
        """
            This function enumerate all connect HIK robotics cameras
        
        Returns:
        --------------------
            return a list of device info
        """
        logger.info("enumerating devices")

        self.device_list = MV_CC_DEVICE_INFO_LIST()
        self.tlayer_type = MV_GIGE_DEVICE | MV_USB_DEVICE
        ret = MvCamera.MV_CC_EnumDevices(self.tlayer_type, self.device_list)
        if ret != 0:
            print("enum devices fail! ret[0x%x]" % ret)
            sys.exit()
        if self.device_list.nDeviceNum == 0:
            logger.error("find no device!")

        self.devList = []
        for i in range(0, self.device_list.nDeviceNum):
            mvcc_dev_info = cast(self.device_list.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                print("\ngige device: [%d]" % i)
                chUserDefinedName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName:
                    if 0 == per:
                        break
                    chUserDefinedName = chUserDefinedName + chr(per)
                print("device user define name: %s" % chUserDefinedName)

                chModelName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                    if 0 == per:
                        break
                    chModelName = chModelName + chr(per)

                print("device model name: %s" % chModelName)

                nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
                self.devList.append(
                    "[" + str(i) + "]GigE: " + chUserDefinedName + " " + chModelName + "(" + str(nip1) + "." + str(
                        nip2) + "." + str(nip3) + "." + str(nip4) + ")")
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print("\nu3v device: [%d]" % i)
                chUserDefinedName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chUserDefinedName:
                    if per == 0:
                        break
                    chUserDefinedName = chUserDefinedName + chr(per)
                print("device user define name: %s" % chUserDefinedName)

                chModelName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                    if 0 == per:
                        break
                    chModelName = chModelName + chr(per)
                print("device model name: %s" % chModelName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)
                self.devList.append("[" + str(i) + "]USB: " + chUserDefinedName + " " + chModelName
                               + "(" + str(strSerialNumber) + ")")

        return self.devList
    
    def _set_cameras(self, left_cam_id, right_cam_id):
        """
            This function set the left and right camera index

        Args:
        --------------------
            left_cam_id: int, selected left camera index in enum_device_list
            right_cam_id: int, selected right camera index in enum_device_list
        """
        self.left_cam_id = left_cam_id
        self.right_cam_id = right_cam_id

    def _infer_LR_by_name(self):
        """
            This function infer the left and right camera index by camera name
        """

        for i, dev_info in enumerate(self.devList):
            if "left" in dev_info.lower():
                self.left_cam_id = i
            elif "right" in dev_info.lower():
                self.right_cam_id = i
        if self.left_cam_id is None or self.right_cam_id is None:
            logger.error("Failed to infer left and right camera index")
            sys.exit()
        self._set_cameras(self.left_cam_id, self.right_cam_id)
        logger.debug(f"inferred left and right camera index: {self.left_cam_id}, {self.right_cam_id}")

        return self.left_cam_id, self.right_cam_id

    def _determine_master_slave(self):
        """
            This function determine the master and slave cameras

        Returns:
        --------------------
            master_cam: MvCamera, master camera
            slave_cam: MvCamera, slave camera
        """
        if LEFT_CAM_TYPE == "MASTER":
            self.master_cam = self.left_cam
            self.slave_cam = self.right_cam
            logger.debug("left cam is master, right cam is slave")
        else:
            self.master_cam = self.right_cam
            self.slave_cam = self.left_cam
            logger.debug("right cam is master, left cam is slave")
        
        return self.master_cam, self.slave_cam

    def _init_cameras(self):
        logger.info("initializing cameras...")
        self.left_cam = self._connect_camera(self.device_list, self.left_cam_id)
        self.right_cam = self._connect_camera(self.device_list, self.right_cam_id)

        self.master_cam, self.slave_cam = self._determine_master_slave()
        
        self._set_master_camera_params(self.master_cam)
        self._set_slave_camera_params(self.slave_cam)
        
        self._start_grab_camera(self.left_cam)
        self._start_grab_camera(self.right_cam)

        # Start thread for each camera
        self.left_cam_thread = CamRunThread(self.left_cam, FrameType.LEFT)
        self.right_cam_thread = CamRunThread(self.right_cam, FrameType.RIGHT)

        self.left_cam_thread.signals.captured_frame.connect(self._fetch_captured_images)
        self.right_cam_thread.signals.captured_frame.connect(self._fetch_captured_images)
        self.left_cam_thread.setAutoDelete(False)
        self.right_cam_thread.setAutoDelete(False)
        QThreadPool.globalInstance().start(self.left_cam_thread)
        QThreadPool.globalInstance().start(self.right_cam_thread)
        logger.info("initializing cameras done")

    def _connect_camera(self, device_list, n_connection_num):
        if int(n_connection_num) >= device_list.nDeviceNum:
            print("intput error!")
            sys.exit()

        cam = MvCamera()
        # ch:选择设备并创建句柄 | en:Select device and create handle
        stDeviceList = cast(device_list.pDeviceInfo[int(n_connection_num)], POINTER(MV_CC_DEVICE_INFO)).contents
        ret = cam.MV_CC_CreateHandle(stDeviceList)
        if ret != 0:
            print("create handle fail! ret[0x%x]" % ret)
            sys.exit()
        ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            print("open device fail! ret[0x%x]" % ret)
            sys.exit()

        return cam
    
    def _set_master_camera_params(self, cam: MvCamera):
        # load config
        ret = cam.MV_CC_FeatureLoad(str(MASTER_CFG_PATH))
        if ret != 0:
            print("load config fail! ret[0x%x]" % ret)
            sys.exit()

    def _set_slave_camera_params(self, cam: MvCamera):
        # ret = cam.MV_CC_FeatureSave("slave.cfg")

        ret = cam.MV_CC_FeatureLoad(str(SLAVE_CFG_PATH))
        if ret != 0:
            print("load config fail! ret[0x%x]" % ret)
            sys.exit()

    def _get_device_info(self, device_list, i):
        mvcc_dev_info = cast(device_list.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
            print("\ngige device: [%d]" % i)
            str_mode_name = ""
            for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                if per == 0:
                    break
                str_mode_name = str_mode_name + chr(per)
            print("device model name: %s" % str_mode_name)
            nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
            nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
            nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
            nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
        elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
            print("\nusb device: [%d]" % i)
            str_mode_name = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                if per == 0:
                    break
                str_mode_name = str_mode_name + chr(per)
            print("device model name: %s" % str_mode_name)
        else:
            print("\nUnkown device: [%d]" % i)

    def _start_grab_camera(self, cam: MvCamera):
        # ch:开始取流 | en:Start grab image
        ret = cam.MV_CC_StartGrabbing()
        if ret != 0:
            print("start grabbing fail! ret[0x%x]" % ret)
            sys.exit()

    def _stop_grab_camera(self, cam: MvCamera):
        # ch:停止取流 | en:Stop grab image
        if cam is None:
            return
        ret = cam.MV_CC_StopGrabbing()
        if ret != 0:
            print("stop grabbing fail! ret[0x%x]" % ret)
            sys.exit()

    def _disconnect_camera(self, cam: MvCamera):
        # ch:关闭设备 | Close device
        if cam is None:
            return
        ret = cam.MV_CC_CloseDevice()
        if ret != 0:
            print("close deivce fail! ret[0x%x]" % ret)
            sys.exit()

        # ch:销毁句柄 | Destroy handle
        ret = cam.MV_CC_DestroyHandle()
        if ret != 0:
            print("destroy handle fail! ret[0x%x]" % ret)
            sys.exit()

    def _fetch_captured_images(self, frameType: FrameType, frame: np.ndarray):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if frameType == FrameType.LEFT:
            self.left_frame = frame
            self.frame_signal.emit(FrameType.LEFT, frame)
        elif frameType == FrameType.RIGHT:
            self.right_frame = frame
            self.frame_signal.emit(FrameType.RIGHT, frame)

    def _deinit_cameras(self):
        if self.left_cam_thread:
            self.left_cam_thread.stop()
        if self.right_cam_thread:
            self.right_cam_thread.stop()

        self._stop_grab_camera(self.left_cam)
        self._stop_grab_camera(self.right_cam)
        
        self._disconnect_camera(self.left_cam)
        self._disconnect_camera(self.right_cam)
        
        self.left_cam = None
        self.right_cam = None
        
        logger.info("Cameras deinitialized.")


    def initialize_camera_group(self):
        self._enum_device_list()
        self._infer_LR_by_name()
        self._init_cameras()

    def set_exp_gain(self, exp, gain):
        ret0 = self.left_cam.MV_CC_SetFloatValue("ExposureTime", float(exp))
        ret1 = self.left_cam.MV_CC_SetFloatValue("Gain", float(gain))
        ret2 = self.right_cam.MV_CC_SetFloatValue("ExposureTime", float(exp))
        ret3 = self.right_cam.MV_CC_SetFloatValue("Gain", float(gain))

        if ret0 or ret1 or ret2 or ret3:
            logger.error("set exp / gain failed")
        else:
            logger.success("set exp / gain successful")

    def set_exp(self, value):
        """value in unit us, which is 1E-6 s"""
        logger.debug("setting exp time"+str(value))
        ret0 = self.left_cam.MV_CC_SetFloatValue("ExposureTime", float(value))
        ret2 = self.right_cam.MV_CC_SetFloatValue("ExposureTime", float(value))
        if ret0 or ret2:
            logger.info("set exp  failed")
        else:
            logger.info("set exp successful")

    def set_gain(self, value):
        """value in unit us, which is 1E-6 s"""
        logger.debug("setting gain"+str(value))
        ret1 = self.left_cam.MV_CC_SetFloatValue("Gain", float(value))
        ret3 = self.right_cam.MV_CC_SetFloatValue("Gain", float(value))
        if ret1 or ret3:
            logger.info("set gain failed")
        else:
            logger.info("set gain successful")

    def capture_dual_camera(self):
        """
            This function capture images from both cameras, either synced or not
        """
        self.left_frame = None
        self.right_frame = None

        # trigger master camera or both
        self.master_cam.MV_CC_SetCommandValue("TriggerSoftware")
        if not HIK_SYNC:
            self.slave_cam.MV_CC_SetCommandValue("TriggerSoftware")

        logger.info("sent trigger command")
        self.left_cam_thread.start_capture()
        self.right_cam_thread.start_capture()

    def save_frames(self, saving_path: str | Path = ROOT_DIR):
        """
            This function save images from both cameras, using timestamp as filename and save to ROOT_DIR

        Args:
        --------------------
            saving_path: str or Path, saving path

        Returns:
        --------------------
            left_name: str, left camera image name
            right_name: str, right camera image name
        """
        saving_path = Path(saving_path)
        timestamp = int(time.time() * 1e7)
        left_name = saving_path / f"A_{timestamp}.jpg"
        right_name = saving_path / f"D_{timestamp}.jpg"
        self.left_cam_thread.Save_jpg(left_name)
        self.right_cam_thread.Save_jpg(right_name)
        logger.info("successfully saved images")

        return left_name, right_name


class CameraSignals(QObject):
    captured_frame = Signal(FrameType, np.ndarray)

class CamRunThread(QRunnable):
    def __init__(self, cam: MvCamera, frameType):
        super().__init__()
        self.signals = CameraSignals()
        self.cam = cam
        self.capture = False
        self.exit = False
        self.frameType = frameType

        self.buf_save_image = None
        self.stFrameInfo = MV_FRAME_OUT_INFO_EX()

    def start_capture(self):
        self.capture = True

    def run(self):
        stOutFrame = MV_FRAME_OUT()
        memset(byref(stOutFrame), 0, sizeof(stOutFrame))
        while True:
            if self.exit:
                break
            if self.capture:
                str_id = "LEFT" if self.frameType==FrameType.LEFT else "RIGHT"
                logger.info(str_id+" cam Thread captureing...")
                # 获取影像缓冲数据
                ret = self.cam.MV_CC_GetImageBuffer(stOutFrame, 10000)
                self.stFrameInfo = stOutFrame.stFrameInfo

                if None != stOutFrame.pBufAddr and 0 == ret:
                    # 输出影像长、宽等信息
                    logger.debug(str(self.frameType)[10:] + "\tget one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
                        self.stFrameInfo.nWidth, self.stFrameInfo.nHeight, self.stFrameInfo.nFrameNum))

                    # 将缓冲数据的内存地址赋给 self.buf_grab_image
                    self.buf_save_image = (c_ubyte * self.stFrameInfo.nFrameLen)()
                    import platform
                    if platform.system() == 'Windows':
                        cdll.msvcrt.memcpy(byref(self.buf_save_image), stOutFrame.pBufAddr, self.stFrameInfo.nFrameLen)
                    else:
                        memmove(byref(self.buf_save_image), stOutFrame.pBufAddr, self.stFrameInfo.nFrameLen)

                    n_save_image_size = self.stFrameInfo.nWidth * self.stFrameInfo.nHeight * 3 + 2048
                    img_buff = (c_ubyte * n_save_image_size)()

                    # 转换像素格式为RGB
                    stConvertParam = MV_CC_PIXEL_CONVERT_PARAM()
                    memset(byref(stConvertParam), 0, sizeof(stConvertParam))
                    stConvertParam.nWidth = self.stFrameInfo.nWidth
                    stConvertParam.nHeight = self.stFrameInfo.nHeight
                    stConvertParam.pSrcData = cast(self.buf_save_image, POINTER(c_ubyte))
                    stConvertParam.nSrcDataLen = self.stFrameInfo.nFrameLen
                    stConvertParam.enSrcPixelType = self.stFrameInfo.enPixelType
                    nConvertSize = self.stFrameInfo.nWidth * self.stFrameInfo.nHeight * 3
                    stConvertParam.enDstPixelType = PixelType_Gvsp_RGB8_Packed
                    stConvertParam.pDstBuffer = (c_ubyte * nConvertSize)()
                    stConvertParam.nDstBufferSize = nConvertSize
                    self.cam.MV_CC_ConvertPixelType(stConvertParam)

                    # 将转换后的RGB数据拷贝给img_buff
                    import platform
                    if platform.system() == 'Windows':
                        cdll.msvcrt.memcpy(byref(img_buff), stConvertParam.pDstBuffer, nConvertSize)
                    else:
                        memmove(byref(img_buff), stConvertParam.pDstBuffer, nConvertSize)

                    # 将二进制的img_buff转换为numpy矩阵
                    numArray = buffer2numpy(img_buff, self.stFrameInfo.nWidth, self.stFrameInfo.nHeight)
                    # logger.info(f"frame shape: {numArray.shape} from {self.frameType} cam")
                    self.signals.captured_frame.emit(self.frameType, numArray)

                    nRet = self.cam.MV_CC_FreeImageBuffer(stOutFrame)
                self.capture = False
            QThread.msleep(100)
    
    def stop(self):
        self.exit = True

    # 存jpg图像
    def Save_jpg(self, file_path):
        if self.buf_save_image is None:
            return

        c_file_path = str(file_path).encode('ascii')
        print(c_file_path)
        stSaveParam = MV_SAVE_IMAGE_TO_FILE_PARAM_EX()
        stSaveParam.enPixelType = self.stFrameInfo.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
        stSaveParam.nWidth = self.stFrameInfo.nWidth  # ch:相机对应的宽 | en:Width
        stSaveParam.nHeight = self.stFrameInfo.nHeight  # ch:相机对应的高 | en:Height
        stSaveParam.nDataLen = self.stFrameInfo.nFrameLen
        stSaveParam.pData = cast(self.buf_save_image, POINTER(c_ubyte))
        stSaveParam.enImageType = MV_Image_Jpeg  # ch:需要保存的图像类型 | en:Image format to save
        stSaveParam.nQuality = 90
        stSaveParam.pcImagePath = ctypes.create_string_buffer(c_file_path)
        stSaveParam.iMethodValue = 2
        ret = self.cam.MV_CC_SaveImageToFileEx(stSaveParam)

        return ret


#region
##########################################################################
# Manually set master and slave cameras paramerters
##########################################################################
# FAILED cases
# if ret != 0: 
#     print("set trigger mode fail! ret[0x%x]" % ret)
#     sys.exit()

##########################################################################
# MASTER PARAMETERS:
# # set TriggerMode to ON
# ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_ON)

# # set TriggerSource to Software
# ret = cam.MV_CC_SetEnumValue("TriggerSource", MV_TRIGGER_SOURCE_SOFTWARE)

# # LineSelector to Line1
# ret = cam.MV_CC_SetEnumValue("LineSelector", 2)

# # LineMode to strobe
# ret = cam.MV_CC_SetEnumValue("LineMode", 8)

# # LineSource to ExposureStartActive
# ret = cam.MV_CC_SetEnumValue("LineSource", 0)

# # StrobeEnable to True
# ret = cam.MV_CC_SetBoolValue("StrobeEnable", True)

# # StrobeLineDuration to 500
# ret = cam.MV_CC_SetIntValue("StrobeLineDuration", 500)

# # StrobeLineDelay to 0
# ret = cam.MV_CC_SetIntValue("StrobeLineDelay", 0)

# # ReverseX and ReverseY to True
# ret = cam.MV_CC_SetBoolValue("ReverseX", False)
# ret = cam.MV_CC_SetBoolValue("ReverseY", False)

# save config
# ret = cam.MV_CC_FeatureSave("master.cfg")

##########################################################################
# SLAVE PARAMETERS:
# # set TriggerSelector to FrameBurstStart 
# ret = cam.MV_CC_SetEnumValue("TriggerSelector", 6)
# # set TriggerMode to ON
# ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_ON)
# # set TriggerSource to line0
# ret = cam.MV_CC_SetEnumValue("TriggerSource", 12)
# if not HIK_SYNC:
#     ret = cam.MV_CC_SetEnumValue("TriggerSource", MV_TRIGGER_SOURCE_SOFTWARE)
# # set TriggerDelay to 0
# ret = cam.MV_CC_SetFloatValue("TriggerDelay", 0.0)
# # set ExposureTime to off
# ret = cam.MV_CC_SetEnumValue("ExposureAuto", MV_EXPOSURE_AUTO_MODE_OFF)
# # # set Gain to off
# # ret = cam.MV_CC_SetEnumValue("GainAuto", MV_GAIN_MODE_OFF)
# # ReverseX and ReverseY to True
# ret = cam.MV_CC_SetBoolValue("ReverseX", False)
# ret = cam.MV_CC_SetBoolValue("ReverseY", False)
#endregion