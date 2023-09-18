import cv2
import os
import numpy as np
import cupy as cp
from lib import libhologpu as libholo
import time

imgName = "point"
maxIterNum = 100    # 最大迭代数
uniThres = 0.66     # 均匀度阈值

# 输入视频文件
video_path = 'output_gauss-R30.avi'
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("无法打开视频文件")
    exit()

# 输出文件夹
dir_path = "./out/gauss/"
if os.path.exists(dir_path):
    pass
else:
    os.makedirs(dir_path)

uniformity = []
frameNum = 0

# 逐帧读取视频并执行操作
while True:
    ret, frame = cap.read()

    if not ret:
        break

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    target = gray_frame
    # 阈值化
    target[target > 150] = 255
    # 归一化
    target = target / 255

    # -----开始计时-----
    Tstart = time.time()

    # CuPy类型转换(NumPy->CuPy)
    target = cp.asarray(target)

    # 计算全息图
    phase, normIntensity = libholo.GSiteration(maxIterNum, uniThres, target, uniformity)
    holo = libholo.genHologram(phase)

    # CuPy类型转换(CuPy->NumPy)
    holo = cp.asnumpy(holo)

    # 写图
    cv2.imwrite(f"./out/gauss/{imgName}-{frameNum:03d}.tif", holo)

    # -----结束计时-----
    Tend = time.time()

    frameNum += 1

    # 性能
    print(f"\033[0;32mFrameNum: {frameNum - 1}\033[0m")
    print(f"Iteration: {len(uniformity)}")
    print(f"Duration: {round(Tend - Tstart, 2)}s")
    print(f"uniformity={round(uniformity[-1], 4)}")
    efficiency = cp.sum(normIntensity[target == 1]) / cp.sum(target[target == 1])
    print(f"efficiency={round(float(efficiency), 4)}")

    uniformity = []
    del holo

# 释放资源并关闭窗口
cp._default_memory_pool.free_all_blocks()
cap.release()
cv2.destroyAllWindows()
