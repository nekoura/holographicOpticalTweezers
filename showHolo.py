import os
import sys
import time
import subprocess

import cv2
import cupy as cp
from lib import libhologpu as libholo

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage

from colorama import init
init(autoreset=True)

# CONFIGS
maxIterNum = 100                                            # 最大迭代数
uniThres = 0.66                                             # 均匀度阈值
fps = 30.0                                                  # 输出视频帧率
codec = "libx264"                                           # 视频编码器
crf = 20                                                    # 视频码率

inputVid = './vids/output_gauss-R30.avi'                           # 输入视频文件
imgName = "point"                                           # 输出临时帧主文件名
imgFold = f'./frames/gauss{time.strftime("%Y%m%d%H%M%S")}/'    # 替换为包含要合成为视频的所有.tif图像的文件夹路径
outputVid = './vids/gaussphasevid.mp4'                           # 输出视频文件


# 窗体类
class VideoPlayer(QMainWindow):
    def __init__(self, video_path):
        super().__init__()

        self.video_path = video_path

        self.initUI()

    def initUI(self):
        # 创建标签用于显示图像
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.video_label)

        # 创建窗口
        self.setWindowTitle('Video Player')
        # self.setGeometry(10, 50, 1920 - 20, 1080 - 120)
        self.showMaximized()

        self.playVid()

    def playVid(self):
        self.cap = cv2.VideoCapture(self.video_path)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateFrame)
        self.timer.start(int(1000/fps))

    def updateFrame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.cap.release()
            self.showLastFrame()
        else:
            QFrame = self.cvtFrame2Qimg(frame)
            self.video_label.setPixmap(QPixmap.fromImage(QFrame))

    def showLastFrame(self):
        _, last_frame = self.cap.read()
        if last_frame is not None:
            QFrame = self.cvtFrame2Qimg(last_frame)
            self.video_label.setPixmap(QPixmap.fromImage(QFrame))

    def cvtFrame2Qimg(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        return QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

    def closeApp(self):
        self.close()


def loopCalcHoloGPU():
    """
    自动态路径视频生成全息图
    """
    cap = cv2.VideoCapture(inputVid)

    if not cap.isOpened():
        print("Cannot open video file")
        exit()

    if os.path.exists(imgFold):
        pass
    else:
        os.makedirs(imgFold)

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
        cv2.imwrite(f"{imgFold}{imgName}-{frameNum:03d}.tif", holo)

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


# def createVidFromImgs(imgFold, outputVid):
#     images = [img for img in os.listdir(imgFold) if img.endswith(".tif")]
#     if not images:
#         print("No .tif images found in the folder.")
#         return
#
#     frame = cv2.imread(os.path.join(imgFold, images[0]))
#     height, width, layers = frame.shape
#
#     fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 使用xvid编码器
#     video = cv2.VideoWriter(outputVid, fourcc, int(fps), (width, height))  # 30 FPS
#
#     for image in images:
#         video.write(cv2.imread(os.path.join(imgFold, image)))
#
#     cv2.destroyAllWindows()
#     video.release()


def createVidFromImgs():
    """
    将生成全息图帧合并为动态视频
    """
    # 获取当前文件夹的绝对路径并切换工作路径
    current_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(current_dir)

    images = [img for img in os.listdir(imgFold) if img.endswith(".tif")]
    if not images:
        print("No .tif images found in the folder.")
        return

    # 生成帧列表文件
    with open("frame_list.txt", "w") as f:
        for image in images:
            f.write(f"file '{os.path.join(imgFold, image)}'\n")

    frame = cv2.imread(os.path.join(imgFold, images[0]))
    height, width, layers = frame.shape

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",                       # 默认覆盖已有文件
        "-r", str(int(fps)),        # 指定帧率
        "-f", "concat",             # 使用-f concat合并文件
        "-safe", "0",               # 添加-safe 0参数
        "-i", "frame_list.txt",     # 帧列表
        "-c:v", codec,              # 编码器
        "-crf", str(crf),           # 码率控制
        "-pix_fmt", "yuv420p",      # 像素格式
        "-s", f"{width}x{height}",  # 帧尺寸
        outputVid
    ]

    # 打印要执行的命令
    # print(" ".join(ffmpeg_cmd))

    # 使用subprocess执行命令 将控制台输出打进log
    if os.path.exists("./log/"):
        pass
    else:
        os.makedirs("./log/")

    log_file = f"./log/ffmpeg_log_{time.strftime('%Y%m%d%H%M%S')}.txt"
    with open(log_file, "w") as log:
        subprocess.run(ffmpeg_cmd, stdout=log, stderr=log)

    # 转码结束后删除帧列表
    os.remove("frame_list.txt")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    globalTStart = time.time()
    loopCalcHoloGPU()
    createVidFromImgs()
    globalTEnd = time.time()

    print(f"\n\033[0;34mDuration: {round(globalTEnd - globalTStart, 2)}s\033[0m")

    player = VideoPlayer(outputVid)
    player.show()

    sys.exit(app.exec_())
