import cv2
import HandTrackingModule as htm
import autopy #For controlling the mouse
import numpy as np
import time# Set resolution 
wCam, hCam = 1080, 720
frameR = 40
smoothening = 5
wScr, hScr = autopy.screen.size()  # 返回电脑屏幕的宽和高(1920.0, 1080.0)
#####################

cap = cv2.VideoCapture(0)  # Default camera on laptop: 0  External:1 or more
cap.set(3, wCam)  #Fix the w/h ratio to 3:4
cap.set(4, hCam) #and set the 分辨率
pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
frame = 0  # 初始化累计帧数
toggle = False
prev_state = [1, 1, 1, 1, 1]  # 初始化上一帧状态
current_state = [1, 1, 1, 1, 1]  # 初始化当前正状态

detector = htm.handDetector(maxHands = 2)

# print(wScr, hScr)


# class Drag(threading.Thread):

#     def __init__(self, *args, **kwargs):
#         super(Drag, self).__init__(*args, **kwargs)
#         self.__flag = threading.Event()     # 用于暂停线程的标识
#         self.__flag.set()       # 设置为True
#         self.__running = threading.Event()      # 用于停止线程的标识
#         self.__running.set()      # 将running设置为True

#     def run(self):
#         while self.__running.isSet():
#             self.__flag.wait()      # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回
#             # autopy.mouse.toggle(None, self._flag)
#             # print(self._tog)
#             autopy.mouse.toggle(autopy.mouse.Button.LEFT, True)


#     def pause(self):
#         self.__flag.clear()     # 设置为False, 让线程阻塞

#     def resume(self):
#         self.__flag.set()    # 设置为True, 让线程停止阻塞

#     def stop(self):
#         self.__flag.set()       # 将线程从暂停状态恢复, 如何已经暂停的话
#         self.__running.clear()        # 设置为False
    
#     def toggle(self):
#        self._tog = True

#     def release(self):
#        self._tog = False

# finger_drag = Drag()
# finger_drag.start()


while True:
    success, img_origin = cap.read() #按帧读取视频
                              #如果读取值是正确帧，success=True,如果读取到结尾，False
                              #img就是每一帧的图像，是个三维矩阵.在cv2里是BGR
    # 1. Detecting hand and return key points 坐标
    allhands,img = detector.findHands(img_origin, draw=True) #手部定位
    # 在图像窗口上创建一个矩形框，在该区域内移动鼠标
    cv2.rectangle(img, (frameR, frameR), (wCam - 4*frameR, hCam - 10*frameR), (0, 255, 0), 2,  cv2.FONT_HERSHEY_PLAIN)
    # finger_drag.pause()
    
######################################

    # 2. Detect 食指&中指
    if len(allhands) != 0:
        # x2, y2 = allhands[8][1:]
        # x3, y3 = allhands[12][1:]
        x1, y1 = allhands[0]['lmList'][4][0:2]
        x2, y2 = allhands[0]['lmList'][8][0:2]
        x3, y3 = allhands[0]['lmList'][12][0:2]
        fingers = detector.fingersUp(img, allhands)
        print(allhands) #fingers 返回一个list，[1,0,0,0,0]表示thumb伸出
        
        current_state = fingers
        # 记录相同状态的帧数
        if (prev_state == current_state):
            frame = frame + 1
        else:
            frame = 0
        prev_state = current_state

        # 3. 食指伸出 => Moving mode
        # if fingers[1] and fingers[2] == False:
        if fingers == [0,1,0,0,0]:
        # 4. Transfer to coordinate： 食指's coordinate in the window to mouse in the desktop
            # mouse's coordinate
            x = np.interp(x2, (frameR, wCam - 4*frameR), (0, wScr))
            y = np.interp(y2, (frameR, hCam - 10*frameR), (0, hScr))

            # smoothening values
            clocX = plocX + (x - plocX) / smoothening
            clocY = plocY + (y - plocY) / smoothening

            autopy.mouse.move(wScr - clocX, clocY)
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
            plocX, plocY = clocX, clocY

        # 5. 食指和中指都伸出 则检测指头距离 距离够短则对应鼠标点击
        if fingers == [0,1,1,0,0]:
            length, pointInfo, img = detector.FindDistance(x2,y2,x3,y3, img)
            if length < 35:
                cv2.circle(img_origin, (int(pointInfo[4]), int(pointInfo[5])),
                           15, (0, 255, 0), cv2.FILLED)
                #circle坐标只能是int，需要强制转换
                autopy.mouse.click()

        # 6. 若是Thumb和食指都伸出 则检测指头距离 距离够短则对应鼠标拖拽
        if fingers == [1,1,0,0,0]:
            # finger_drag.resume()
            x = np.interp(x2, (frameR, wCam - frameR), (0, wScr))
            y = np.interp(y2, (frameR, hCam - frameR), (0, hScr))
            # smoothening values
            clocX = plocX + (x - plocX) / (smoothening*0.5)
            clocY = plocY + (y - plocY) / (smoothening*0.5)

            length, pointInfo, img = detector.FindDistance(x1,y1,x2,y2, img)
            if length < 25:
                # finger_drag.toggle()
                if toggle == False and frame >= 2:
                    autopy.mouse.toggle(autopy.mouse.Button.LEFT, True)
                    # toggle = True
                autopy.mouse.move(wScr - clocX, clocY)
            
            else:
                # finger_drag.release()
                if toggle and frame >= 2:
                    autopy.mouse.toggle(autopy.mouse.Button.LEFT, False)
                    # toggle = False
  
            cv2.putText(img, "drag", (150, 50), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
            print("拖拽鼠标")
            

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    # img_copy = img.copy()
    cv2.putText(img_origin, f'fps:{int(fps)}', [15, 25],
                cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2) #Display Frames per second 每秒传输帧数
    cv2.imshow("Control system", img_origin)

    if cv2.waitKey(1) == ord('q'):
        break



# finger_drag.stop()
cap.release()
cv2.destroyAllWindows()


    
