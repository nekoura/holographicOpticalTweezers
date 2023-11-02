import os
import sys
import getopt
import time

import cv2

from colorama import init
init(autoreset=True)


def getCliArgs(argv):
    """
    options, args = getopt.getopt(args, shortopts, longopts=[])

    :param args: 一般是sys.argv[1:]。过滤掉sys.argv[0]，它是执行脚本的名字，不算做命令行参数。
    :param shortopts: 短格式分析串。例如："hp:i:"，h后面没有冒号，表示后面不带参数；p和i后面带有冒号，表示后面带参数。
    :param longopts: 长格式分析串列表。例如：["help", "ip=", "port="]，help后面没有等号，表示后面不带参数；ip和port后面带冒号，表示后面带参数。

    :return: options是以元组为元素的列表，每个元组的形式为：(选项串, 附加参数)，如：('-i', '192.168.0.1')
    :return: args是个列表，其中的元素是那些不含'-'或'--'的参数。
    """
    try:
        opts, args = getopt.getopt(argv, "hi:o:n:", ["help", "username=", "outputFold=", "imgName="])
    except getopt.GetoptError:
        print('Error: invalid input \n')
        print('hints:')
        print('inputVid default path = ./vids/')
        print('outputImgs default format = ./frames/<outputFoldName>-YYYYmmddHHMMSS/<imgName>-nnn.tif \n')
        print('usage:')
        print('extractFrame.py -i <inputVid> -o <outputFoldName> -n <imgName>')
        print('extractFrame.py --username=<inputVid> --outputFold=<outputFoldName> --imgName=<imgName>')
        sys.exit(2)

    # 处理 返回值options是以元组为元素的列表。
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('hints:')
            print('inputVid default path = ../vids/')
            print('outputImgs default format = ../frames/<outputFoldName>-YYYYmmddHHMMSS/ \n')
            print('usage:')
            print('extractFrame.py -i <inputVid> -o <outputFoldName> -n <imgName>')
            print('extractFrame.py --username=<inputVid> --outputFold=<outputFoldName> --imgName=<imgName>')
            sys.exit()
        elif opt in ("-i", "--inputVid"):
            # 输入视频文件
            inputVid = f'../vids/{arg}'
        elif opt in ("-o", "--outputFoldName"):
            # 输出临时帧文件夹路径
            imgFold = f'../frames/{arg}-{time.strftime("%Y%m%d%H%M%S")}/'
        elif opt in ("-n", "--imgName"):
            # 输出临时帧主文件名
            imgName = arg

    return (inputVid, imgFold, imgName)


def main():
    inputVid, imgFold, imgName = getCliArgs(sys.argv[1:])

    cap = cv2.VideoCapture(inputVid)

    if not cap.isOpened():
        print("Cannot open video file")
        exit()

    if os.path.exists(imgFold):
        pass
    else:
        os.makedirs(imgFold)

    frameNum = 0

    # 逐帧读取视频并执行操作
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        cv2.imwrite(f"{imgFold}{imgName}-{frameNum:03d}.tif", frame)

        frameNum += 1

        print(f"\033[0;32mFrameNum: {frameNum - 1}\033[0m")

    # 释放资源并关闭窗口
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()