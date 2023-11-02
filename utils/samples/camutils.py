import numpy as np
from lib import nncam
import cv2
import threading

class hCam():
    def __init__(self, resolution, log):
        # threading.Thread.__init__(self)
        self.device = None
        self.buf = None

        self.total = 0
        self.nparray = None
        self.frame = None
        self.captured = None
        self.imgWidth = None
        self.imgHeight = None

        self.log = log
        self.resolution = resolution

# the vast majority of callbacks come from nncam.dll/so/dylib internal threads
    @staticmethod
    def camEvtHandler(nEvent, ctx):
        if nEvent == nncam.NNCAM_EVENT_IMAGE:
            ctx.getDynImgCallback(nEvent)
        elif nEvent == nncam.NNCAM_EVENT_STILLIMAGE:
            ctx.getStillImgCallback(nEvent)

    def getDynImgCallback(self, nEvent):
        try:
            self.device.PullImageV3(self.buf, 0, 24, 0, None)
        except nncam.HRESULTException as ex:
            print('pull image failed, hr=0x{:x}'.format(ex.hr & 0xffffffff))
        else:
            self.total += 1

            if self.log:
                print('pull image ok, total = {}'.format(self.total))

            self.nparray = np.frombuffer(self.buf, np.uint8).reshape((self.imgHeight, self.imgWidth, 3))
            self.frame = cv2.cvtColor(self.nparray, cv2.COLOR_RGBA2BGR)

    def getStillImgCallback(self, nEvent):
        try:
            self.device.PullImageV3(self.buf, 1, 24, 0, None)  # peek
        except nncam.HRESULTException as ex:
            print('pull image failed, hr=0x{:x}'.format(ex.hr & 0xffffffff))
        else:
            self.nparray = np.frombuffer(self.buf, np.uint8).reshape((self.imgHeight, self.imgWidth, 3))
            self.captured = cv2.cvtColor(self.nparray, cv2.COLOR_RGBA2BGR)

    def initCam(self):
        devlist = nncam.Nncam.EnumV2()
        if len(devlist) > 0:
            print('{}: flag = {:#x}, preview = {}, still = {}'.format(devlist[0].displayname, devlist[0].model.flag, devlist[0].model.preview, devlist[0].model.still))
            for r in devlist[0].model.res:
                print('\t = [{} x {}]'.format(r.width, r.height))
            self.device = nncam.Nncam.Open(devlist[0].id)
            if self.device:
                try:
                    self.device.put_AutoExpoEnable(1)
                    # resolution
                    self.device.put_eSize(self.resolution)
                    self.imgWidth, self.imgHeight = self.device.get_Size()
                    bufsize = nncam.TDIBWIDTHBYTES(self.imgWidth * 24) * self.imgHeight
                    print('image size: {} x {}, bufsize = {}'.format(self.imgWidth, self.imgHeight, bufsize))
                    self.buf = bytes(bufsize)

                    if self.buf:
                        try:
                            self.device.StartPullModeWithCallback(self.camEvtHandler, self)
                        except nncam.HRESULTException as ex:
                            print('failed to start camera, hr=0x{:x}'.format(ex.hr & 0xffffffff))
                    input('press ENTER to exit\n')
                finally:
                    self.device.Close()
                    self.device = None
                    self.buf = None
            else:
                print('failed to open camera')
        else:
            print('no camera found')

    def captureImg(self):
        self.device.Snap(0xffffffff)