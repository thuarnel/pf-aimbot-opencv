import winsound
import win32api
import win32con
import win32gui
import numpy as np
import random
import time 
import cv2
import mss

#Config class to store important info about program capture
class Config:
    def __init__(self):
        
        self.width = 1920
        self.height = 1080
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        self.uniformCaptureSize = 240
        self.crosshairUniform = self.uniformCaptureSize // 2
        self.capture_left = self.center_x - self.crosshairUniform
        self.capture_top = self.center_y - self.crosshairUniform
        
        self.region = {"top": self.capture_top,"left": self.capture_left,"width": self.uniformCaptureSize,"height": self.uniformCaptureSize}
        
config = Config()
screenCapture = mss.mss()

template = cv2.imread("enemyIndic3.png", cv2.IMREAD_UNCHANGED)
template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
w, h = template_gray.shape[::-1]

#template matching will give us top left corner coords which is not what we
#want as we must hit the center of the rhombus, so we get half of template size
#to offset coords towards the center of template (rhombus)
centerW = w//2
centerH = h//2

#copy values of these 2 vars as to make access faster (accessing attribute from fn is slower than direct variable)
crosshairU = config.crosshairUniform
regionC = config.region

#change sensitivity here
robloxSensitivity = 0.55
PF_MouseSensitivity = 0.5
PF_AimSensitivity=1

PF_sensitivity = PF_MouseSensitivity*PF_AimSensitivity
movementCompensation = 0.2 #keep it in 0 to 1 range
finalComputerSensitivityMultiplier = ((robloxSensitivity*PF_sensitivity)/0.55) + movementCompensation

while True:
    time.sleep(0.001)
    GameFrame = np.array(screenCapture.grab(regionC))
    GameFrame = cv2.cvtColor(GameFrame, cv2.COLOR_BGRA2GRAY)

    #change to 0x12 if you wanna close program with ALT
    #cv2.waitKey(1) & 0xFF == ord('q') or 
    if win32api.GetAsyncKeyState(0x6) < 0:
            winsound.Beep(1000, 10)
            break
        
    elif win32api.GetAsyncKeyState(0x02) < 0:
        result = cv2.matchTemplate(GameFrame, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        #if aim is acting out too much try 0.85 (avoid false positives)
        if max_val >=0.8:

            X=max_loc[0]+centerW
            Y=max_loc[1]+centerH
            nX = (-(crosshairU - X))*finalComputerSensitivityMultiplier
            nY = (-(crosshairU - Y))*finalComputerSensitivityMultiplier
                
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(nX), int(nY), 0, 0)

            win32api.mouse_event(0x0002, 0, 0, 0, 0)
            time.sleep(random.uniform(0.01, 0.03))
            win32api.mouse_event(0x0004, 0, 0, 0, 0)
            
    #cv2.imshow("test", GameFrame)
print("bye")
