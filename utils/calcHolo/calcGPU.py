# -*- coding: utf-8 -*-

import cv2
import numpy as np
import cupy as cp
import matplotlib
import matplotlib.pyplot as plt
from lib import libhologpu as libholo
import time
matplotlib.use('Qt5Agg')


def genTargetImg():
    # 定义图像的宽度和高度
    width, height = 1920, 1080

    # 定义边距的大小
    wMargin = 50
    hMargin = 50

    # 创建一个空白的黑色图像，包括边距
    target = np.zeros((height, width), dtype=np.uint8)
    target[hMargin:height - hMargin, wMargin:width - wMargin] = 0  # 在边距区域填充黑色

    # 定义点阵的间隔和颜色
    wGridSpacing = 100  # 点阵的间隔
    hGridSpacing = 100
    gridColor = 255  # 点阵的颜色，这里是白色

    # 在图像上绘制点阵
    for x in range(wMargin, width - wMargin + wGridSpacing, wGridSpacing):
        for y in range(hMargin, height - hMargin + hGridSpacing, hGridSpacing):
            cv2.circle(target, (x, y), 2, gridColor, -1)  # 使用cv2.circle绘制点阵

    target = target.astype("uint8")
    return target


def main():
    imgName = "circle"
    # 迭代数
    maxIterNum = 100
    # 均匀度阈值
    uniThres = 0.66

    uniformity = []
    imgPath = f"../../utils/samples/{imgName}.jpg"

    period = 20

    # gratv = libholo.loadImg(f"../../grat_v{period}.tif")
    # gratv = gratv.astype("float")
    # grath = libholo.loadImg(f"../../grat_h{period}.tif")
    # grath = grath.astype("float")

    fresnel = libholo.loadImg("../../fresnellens.tif")
    fresnel = fresnel.astype("float")

    # grat = gratv + grath
    # grat = gratv
    # grat = grath
    target = libholo.loadImg(imgPath)

    # target = genTargetImg()
    # 阈值化
    target[target > 150] = 255
    # 归一化
    target = target / 255

    # CuPy类型转换(NumPy->CuPy)
    target = cp.asarray(target)

    Tstart = time.time()
    phase, normIntensity = libholo.GSiteration(maxIterNum, uniThres, target, uniformity)

    holo = libholo.genHologram(phase)
    # rec = libholo.reconstruct(normIntensity)

    # CuPy类型转换(CuPy->NumPy)
    holo = cp.asnumpy(holo)
    holo = holo.astype("float")
    # holo = holo + gratv
    # holo = holo + grath
    holo = holo + fresnel
    holo = holo.astype("uint8")

    # rec = cp.asnumpy(rec)

    holo = cv2.rotate(holo, cv2.ROTATE_90_CLOCKWISE)
    cv2.imwrite(f"../../{imgName}-{time.strftime('%Y%m%d%H%M%S')}-unif{round(uniformity[-1],4)}.tif", holo)

    Tend = time.time()
    # cv2.imwrite(f"img/weighted_rec-{imgName}-unif{round(uniformity[-1],4)}.bmp", rec)

    # cv2.imshow("holo", holo)
    # cv2.waitKey(0)

    # 性能
    print(f"Iteration: {len(uniformity)}")
    print(f"Duration: {round(Tend - Tstart, 2)}s")
    print(f"uniformity={uniformity[-1]}")
    efficiency = np.sum(normIntensity[target == 1]) / np.sum(target[target == 1])
    print(f"efficiency={efficiency}")

    # 预览
    # plt.figure(figsize=(10, 4))
    # ax1 = plt.subplot(131)
    # ax1.set_title("target")
    # plt.imshow(target, 'gray')
    # plt.axis('off')
    #
    # ax2 = plt.subplot(132)
    # ax2.set_title("Weighted Hologram\nDuration {} s".format(round(Tend - Tstart, 2)))
    # plt.imshow(holo, 'gray')
    # plt.axis('off')
    #
    # ax3 = plt.subplot(133)
    # ax3.set_title("Weighted Reconstruction")
    # plt.imshow(rec, 'gray')
    # plt.axis('off')
    #
    # plt.figure(figsize=(10, 8))
    # plt.plot(np.arange(1, len(uniformity) + 1), uniformity)
    # plt.xlabel("Iteration")
    # plt.ylabel("Uniformity")
    # plt.ylim(0, 1)

    del holo
    # del rec
    cp._default_memory_pool.free_all_blocks()

    plt.show()


if __name__ == "__main__":
    main()
