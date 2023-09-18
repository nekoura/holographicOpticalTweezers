import cv2
import numpy as np
import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

# 设置图像的宽度和高度
width, height = 1920, 1080
fps = 30.0
step = 5
radius = 8
center_radius = 5

# 创建一个类来存储点的信息和状态
class PointInfo:
    def __init__(self):
        self.x = None  # 初始位置
        self.y = None
        self.center_x = width // 2  # 图像中心
        self.center_y = height // 2
        self.stop_generation = False


point = PointInfo()


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建标签用于显示图像
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.image_label)

        # 创建窗口
        self.setWindowTitle('Image Viewer')
        self.setGeometry(10, 50, width - 20, height - 120)
        self.showMaximized()
        # self.show()

        # 初始化帧
        self.frame = np.zeros((height, width, 3), dtype=np.uint8)

        # 创建视频写入对象
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(f'output{fps}fps.avi', self.fourcc, fps, (width, height))

        # 鼠标点击事件处理函数
        def mousePressEvent(event):
            if not point.stop_generation:
                point.x, point.y = event.x(), event.y()
                self.timer.start(int(1000/fps))  # 开始定时器以生成图像序列

        self.image_label.mousePressEvent = mousePressEvent

        # 初始化鼠标样式
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

        # 创建定时器以定期生成和显示图像序列
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)

    def update_image(self):
        # 创建黑色背景图像
        self.frame = np.zeros((height, width, 3), dtype=np.uint8)

        # 在图像上绘制白色点
        cv2.circle(self.frame, (point.x, point.y), radius, (255, 255, 255), -1)

        # 计算点移动的方向
        x_direction, y_direction = self.calculate_direction(point.x, point.y)

        # 更新点的位置
        point.x += x_direction
        point.y += y_direction

        distance_to_center = np.sqrt((point.x - point.center_x) ** 2 + (point.y - point.center_y) ** 2)

        # 如果点到达图像中心，停止生成图像

        if distance_to_center < center_radius:
            point.stop_generation = True
            self.timer.stop()  # 停止定时器

        # 将当前帧写入视频文件
        self.out.write(self.frame)

        # -------PyQt-------
        # 将 OpenCV 图像转换为 QImage
        h, w, c = self.frame.shape
        q_image = QImage(self.frame.data, w, h, w * c, QImage.Format_RGB888)

        # 显示图像
        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)
        self.image_label.repaint()
        # ------------------

        if point.stop_generation:
            self.out.release()

    def calculate_direction(self, x, y):
        x_direction = 0
        y_direction = 0

        if x < point.center_x:
            x_direction = step
        elif x > point.center_x:
            x_direction = -step

        if y < point.center_y:
            y_direction = step
        elif y > point.center_y:
            y_direction = -step

        # 如果点接近中心点，减小步长
        if abs(x - point.center_x) < 10:
            x_direction //= 2
        if abs(y - point.center_y) < 10:
            y_direction //= 2

        return x_direction, y_direction


if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    sys.exit(app.exec_())
