
def load_hik_sdk():
    import os
    import sys
    import platform
    from pathlib import Path

    if platform.system() == 'Linux':
        MVS_PATH = os.getenv('MVCAM_SDK_PATH')
        if platform.processor() == 'aarch64':
            MV_IMPORT_PATH = Path(MVS_PATH) / "Samples/aarch64/Python/MvImport"
        else:
            MV_IMPORT_PATH = Path(MVS_PATH) / "Samples/64/Python/MvImport"
    elif platform.system() == 'Windows':
        MVS_PATH = os.getenv('MVCAM_COMMON_RUNENV')
        MV_IMPORT_PATH = Path(MVS_PATH) / "Samples/Python/MvImport"

    if not MV_IMPORT_PATH.exists():
        print(f"MV_IMPORT_PATH not found: {MV_IMPORT_PATH}")
        sys.exit()

    sys.path.append(str(MV_IMPORT_PATH))

    try:
        import MvCameraControl_class
        print(f"MvCameraControl_class imported successfully from {MV_IMPORT_PATH}")
    except Exception as e:
        print(f"Error importing MvCameraControl_class: {e}")
        sys.exit()


# 将二进制的影像数据转换成numpy的矩阵，方便后处理
def buffer2numpy(data, nWidth, nHeight):
    import numpy as np
    data_ = np.frombuffer(data, count=int(nWidth * nHeight * 3), dtype=np.uint8, offset=0)
    data_r = data_[0:nWidth * nHeight * 3:3]
    data_g = data_[1:nWidth * nHeight * 3:3]
    data_b = data_[2:nWidth * nHeight * 3:3]

    data_r_arr = data_r.reshape(nHeight, nWidth)
    data_g_arr = data_g.reshape(nHeight, nWidth)
    data_b_arr = data_b.reshape(nHeight, nWidth)
    numArray = np.zeros([nHeight, nWidth, 3], "uint8")

    numArray[:, :, 0] = data_r_arr
    numArray[:, :, 1] = data_g_arr
    numArray[:, :, 2] = data_b_arr
    return numArray

