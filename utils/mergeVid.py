import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
import cv2
import os
import time
import subprocess

fps = 30.0
codec = "libx264"
quality = 20

image_folder = './out/gauss/'  # 替换为包含要合成为视频的所有.tif图像的文件夹路径
output_video = './gaussphasevid.mp4'  # 更改输出视频文件的路径为.avi

class VideoPlayer(QMainWindow):
    def __init__(self, video_path):
        super().__init__()

        self.video_path = video_path
        self.frame_width = 0

        self.initUI()

    def initUI(self):
        # self.setWindowTitle("Video Player")
        # self.central_widget = QWidget(self)
        # self.setCentralWidget(self.central_widget)
        #
        # self.layout = QVBoxLayout(self.central_widget)
        # self.video_label = QLabel(self)
        # self.layout.addWidget(self.video_label)
        #
        # self.close_button = QPushButton("Close", self)
        # self.close_button.clicked.connect(self.close_app)
        # self.layout.addWidget(self.close_button)
        #
        # self.play_video()

        # 创建标签用于显示图像
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.video_label)

        # 创建窗口
        self.setWindowTitle('Video Player')
        self.setGeometry(10, 50, 1920 - 20, 1080 - 120)
        self.showMaximized()

        self.play_video()

    def play_video(self):
        self.cap = cv2.VideoCapture(self.video_path)
        self.frame_height = int(self.cap.get(4))
        self.frame_width = int(self.cap.get(3))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000/fps))

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            self.cap.release()
            self.show_last_frame()
        else:
            q_image = self.convert_frame_to_qimage(frame)
            self.video_label.setPixmap(QPixmap.fromImage(q_image))

    def show_last_frame(self):
        _, last_frame = self.cap.read()
        if last_frame is not None:
            q_image = self.convert_frame_to_qimage(last_frame)
            self.video_label.setPixmap(QPixmap.fromImage(q_image))

    def convert_frame_to_qimage(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        return QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

    def close_app(self):
        self.close()

# def create_video_from_images(image_folder, output_video):
#     images = [img for img in os.listdir(image_folder) if img.endswith(".tif")]
#     if not images:
#         print("No .tif images found in the folder.")
#         return
#
#     frame = cv2.imread(os.path.join(image_folder, images[0]))
#     height, width, layers = frame.shape
#
#     fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 使用xvid编码器
#     video = cv2.VideoWriter(output_video, fourcc, int(fps), (width, height))  # 30 FPS
#
#     for image in images:
#         video.write(cv2.imread(os.path.join(image_folder, image)))
#
#     cv2.destroyAllWindows()
#     video.release()

def create_video_from_images(image_folder, output_video):
    images = [img for img in os.listdir(image_folder) if img.endswith(".tif")]
    if not images:
        print("No .tif images found in the folder.")
        return

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape

    # 获取当前文件夹的绝对路径并切换工作路径
    current_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(current_dir)

    # 生成包含图像文件相对路径的image_list.txt文件
    with open("image_list.txt", "w") as f:
        for image in images:
            f.write(f"file '{os.path.join(image_folder, image)}'\n")

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-r", str(int(fps)),
        "-f", "concat",  # 使用-f concat选项
        "-safe", "0",  # 添加-safe 0参数
        "-i", "image_list.txt",  # 指定包含图像文件路径的文本文件
        "-c:v", codec,
        "-crf", str(quality),
        "-pix_fmt", "yuv420p",
        "-s", f"{width}x{height}",
        output_video
    ]

    # 打印要执行的命令
    # print(" ".join(ffmpeg_cmd))

    # 使用subprocess执行命令
    # subprocess.run(ffmpeg_cmd)
    log_file = f"ffmpeg_log_{time.strftime('%Y%m%d%H%M%S')}.txt"  # 日志文件名
    with open(log_file, "w") as log:
        subprocess.run(ffmpeg_cmd, stdout=log, stderr=log)

    os.remove("image_list.txt")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    create_video_from_images(image_folder, output_video)

    player = VideoPlayer(output_video)
    player.show()

    sys.exit(app.exec_())
