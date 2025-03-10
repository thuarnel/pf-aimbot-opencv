import winsound
import win32api
import win32con
import win32gui
import numpy as np
import random
import time 
import cv2
import mss
from collections import deque

print("Initializing configuration...")
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
        self.region = {"top": self.capture_top, "left": self.capture_left, "width": self.uniformCaptureSize, "height": self.uniformCaptureSize}

config = Config()
screenCapture = mss.mss()

print("Loading reference image...")
template = cv2.imread("ref.png", cv2.IMREAD_UNCHANGED)
template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
w, h = template_gray.shape[::-1]

print("Generating scaled templates...")
scale_factors = [0.9, 1.0, 1.1]
templates = []
for scale in scale_factors:
    if scale == 1.0:
        templates.append(template_gray)
    else:
        width = int(template_gray.shape[1] * scale)
        height = int(template_gray.shape[0] * scale)
        scaled_template = cv2.resize(template_gray, (width, height), interpolation=cv2.INTER_AREA)
        templates.append(scaled_template)

centerW = w // 2
centerH = h // 2

crosshairU = config.crosshairUniform
regionC = config.region

robloxSensitivity = 0.84
PF_MouseSensitivity = 0.456
PF_AimSensitivity = 0.648

PF_sensitivity = PF_MouseSensitivity * PF_AimSensitivity
movementCompensation = 0.2
finalComputerSensitivityMultiplier = ((robloxSensitivity * PF_sensitivity) / 0.55) + movementCompensation

target_positions = deque(maxlen=3)
last_time = time.time()
prediction_enabled = False

MATCH_THRESHOLD = 0.85
target_fps = 60
frame_time = 1.0 / target_fps
min_consecutive_matches = 2
consecutive_matches = 0

def multi_scale_template_match(frame, templates, scale_factors):
    best_val = -1
    best_loc = None
    best_scale_idx = 0
    template = templates[1]
    result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= MATCH_THRESHOLD:
        best_val = max_val
        best_loc = max_loc
        best_scale_idx = 1
    else:
        for i, (template, scale) in enumerate(zip(templates, scale_factors)):
            if i == 1:
                continue
            result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_scale_idx = i
    
    w_scaled = int(w * scale_factors[best_scale_idx])
    h_scaled = int(h * scale_factors[best_scale_idx])
    center_w_scaled = w_scaled // 2
    center_h_scaled = h_scaled // 2
    
    return best_val, best_loc, center_w_scaled, center_h_scaled

def predict_target_position(positions, time_delta):
    if len(positions) < 2:
        return None
    last_pos = positions[-1]
    prev_pos = positions[-2]
    vel_x = (last_pos[0] - prev_pos[0]) / time_delta
    vel_y = (last_pos[1] - prev_pos[1]) / time_delta
    pred_x = int(last_pos[0] + vel_x * 0.05)
    pred_y = int(last_pos[1] + vel_y * 0.05)
    return (pred_x, pred_y)

print("Starting aim assist...")
while True:
    time.sleep(0.001)
    GameFrame = np.array(screenCapture.grab(regionC))
    GameFrame = cv2.cvtColor(GameFrame, cv2.COLOR_BGRA2GRAY)

    if win32api.GetAsyncKeyState(0x6) < 0:
        print("Exit key detected. Stopping...")
        winsound.Beep(1000, 10)
        break
    
    elif win32api.GetAsyncKeyState(0x02) < 0:
        max_val, max_loc, center_w, center_h = multi_scale_template_match(GameFrame, templates, scale_factors)
        
        if max_val >= MATCH_THRESHOLD:
            print("Target detected! Adjusting aim...")
            X = max_loc[0] + center_w
            Y = max_loc[1] + center_h
            target_positions.append((X, Y))
            time_delta = time.time() - last_time
            last_time = time.time()
            
            if prediction_enabled and len(target_positions) >= 2:
                predicted_pos = predict_target_position(target_positions, time_delta)
                if predicted_pos:
                    X, Y = predicted_pos
            
            nX = (-(crosshairU - X)) * finalComputerSensitivityMultiplier
            nY = (-(crosshairU - Y)) * finalComputerSensitivityMultiplier
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(nX), int(nY), 0, 0)
            
            consecutive_matches += 1
            if consecutive_matches >= min_consecutive_matches:
                win32api.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(random.uniform(0.01, 0.02))
                win32api.mouse_event(0x0004, 0, 0, 0, 0)
        else:
            target_positions.clear()
            consecutive_matches = 0
    else:
        target_positions.clear()
        consecutive_matches = 0
            
print("Script terminated.")