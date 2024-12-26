import os
import sys
from pynput import keyboard
from termcolor import colored
import cv2
import json
import math
import mss
import os
import sys
import time
import torch
import numpy as np
from termcolor import colored
from ultralytics import YOLO
import interception
import win32con
import win32gui
import win32api
import threading
import tkinter as tk

pixel_increment = 1 #controls how many pixels the mouse moves for each relative movement
aimbot_status = colored("ENABLED", 'green')

smooth = 1.6 #controls the size of the detection box (equaling the width and height)
box_constant = 350 #controls the size of the detection box (equaling the width and height)
delay = 0 #controls the size of the detection box (equaling the width and height)

aim_height = 3 # The lower the number, the higher the aim_height. For example: 2 would be the head and 100 would be the feet.

confidence = 0.55 # How confident the AI needs to be for it to lock on to the player. Default is 45%

use_trigger_bot = False # Will shoot if crosshair is locked on the player

class Overlay(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def callback(self):
        self.root.quit()

    def run(self):
        # Create the main window
        self.root = tk.Tk()

        # Set the window attributes to make it fully transparent
        self.root.config(bg="white")
        self.root.wm_attributes("-transparentcolor", "white")
        self.root.wm_attributes("-fullscreen", "True")
        self.root.wm_attributes("-topmost", "True")
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate the center of the screen
        self.center_x = screen_width // 2
        self.center_y = screen_height // 2

        # Create a canvas widget to draw the circle
        self.canvas = tk.Canvas(
            self.root,
            width=screen_width,
            height=screen_height,
            bg="#000000",
            highlightthickness=0,
        )
        hwnd = self.canvas.winfo_id()
        colorkey = win32api.RGB(0, 0, 0)  # full black in COLORREF structure
        wnd_exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        new_exstyle = wnd_exstyle | win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_exstyle)
        win32gui.SetLayeredWindowAttributes(hwnd, colorkey, 255, win32con.LWA_COLORKEY)
        self.canvas.pack()

        self.circle_radius = box_constant/2

        # Start the Tkinter main loop
        self.root.mainloop()

    def hide(self):
        self.canvas.delete(self.oval)

    def show(self):
        self.oval = self.canvas.create_oval(
            self.center_x - self.circle_radius,
            self.center_y - self.circle_radius,
            self.center_x + self.circle_radius,
            self.center_y + self.circle_radius,
            outline="white",
        )


# overlay = Overlay()

interception.auto_capture_devices()

screensize = {'X': 1920, 'Y': 1080}

screen_res_x = screensize['X']
screen_res_y = screensize['Y']

screen_x = int(screen_res_x / 2)
screen_y = int(screen_res_y / 2)

screen = mss.mss()

model = YOLO('yolov11.pt')
# if torch.cuda.is_available():
#     print(colored("CUDA ACCELERATION [ENABLED]", "green"))
# else:
#     print(colored("[!] CUDA ACCELERATION IS UNAVAILABLE", "red"))
#     print(colored("[!] Check your PyTorch installation, else performance will be poor", "red"))

def update_status_aimbot():
    global aimbot_status
    if aimbot_status == colored("ENABLED", 'green'):
        aimbot_status = colored("DISABLED", 'red')
        # overlay.hide()
    else:
        aimbot_status = colored("ENABLED", 'green')
        # overlay.show()
    sys.stdout.write("\033[K")
    print(f"[!] AIMBOT IS [{aimbot_status}]", end = "\r")

def sleep(duration, get_now = time.perf_counter):
    if duration == 0: return
    now = get_now()
    end = now + duration
    while now < end:
        now = get_now()

def is_aimbot_enabled():
    return aimbot_status == colored("ENABLED", 'green')

def is_shooting():
    return True

def is_targeted():
    return True

def is_target_locked(x, y):
    #plus/minus 5 pixel threshold
    threshold = 5
    return screen_x - threshold <= x <= screen_x + threshold and screen_y - threshold <= y <= screen_y + threshold

def move_crosshair(x, y):
    # if is_targeted():
    #     scale = sens_config["targeting_scale"]
    # else:
    #     return

    # for rel_x, rel_y in interpolate_coordinates_from_center((x, y), scale):
    #     # ii_.mi = MouseInput(rel_x, rel_y, 0, 0x0001, 0, ctypes.pointer(extra))
    #     # input_obj = Input(ctypes.c_ulong(0), ii_)
    #     # ctypes.windll.user32.SendInput(1, ctypes.byref(input_obj), ctypes.sizeof(input_obj))
    #     # rzctl.mouse_move(int(rel_x), int(rel_y), True)
    interception.move_relative(int((x - 960)/smooth), int((y - 540)/smooth))
    sleep(0.000001 * delay)
        # sleep(mouse_delay)

#generator yields pixel tuples for relative movement
def interpolate_coordinates_from_center(absolute_coordinates, scale):
    diff_x = (absolute_coordinates[0] - screen_x) * scale/pixel_increment
    diff_y = (absolute_coordinates[1] - screen_y) * scale/pixel_increment
    length = int(math.dist((0,0), (diff_x, diff_y)))
    if length == 0: return
    unit_x = (diff_x/length) * pixel_increment
    unit_y = (diff_y/length) * pixel_increment
    x = y = sum_x = sum_y = 0
    for k in range(0, length):
        sum_x += x
        sum_y += y
        x, y = round(unit_x * k - sum_x), round(unit_y * k - sum_y)
        yield x, y
        

def main():
    print("havoc priv")

    half_screen_width = 1920/2
    half_screen_height = 1080/2
    detection_box = {'left': int(half_screen_width - box_constant//2), #x1 coord (for top-left corner of the box)
                        'top': int(half_screen_height - box_constant//2), #y1 coord (for top-left corner of the box)
                        'width': int(box_constant),  #width of the box
                        'height': int(box_constant)} #height of the box
    sleep(1)
    # overlay.show()
    update_status_aimbot()
    while True:
        start_time = time.perf_counter()
        frame = np.array(screen.grab(detection_box))
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        boxes = model.predict(source=frame, verbose=False, conf=confidence, iou=0.80, half=True)
        result = boxes[0]
        if len(result.boxes.xyxy) != 0: #player detected
            least_crosshair_dist = closest_detection = player_in_frame = False
            for box in result.boxes.xyxy: #iterate over each player detected
                x1, y1, x2, y2 = map(int, box)
                x1y1 = (x1, y1)
                x2y2 = (x2, y2)
                height = y2 - y1
                relative_head_X, relative_head_Y = int((x1 + x2)/2), int((y1 + y2)/2 - height/aim_height) 
                own_player = x1 < 15 or (x1 < box_constant/5 and y2 > box_constant/1.2) 
                crosshair_dist = math.dist((relative_head_X, relative_head_Y), (box_constant/2, box_constant/2))

                if not least_crosshair_dist: least_crosshair_dist = crosshair_dist 

                if crosshair_dist <= least_crosshair_dist and not own_player:
                    least_crosshair_dist = crosshair_dist
                    closest_detection = {"x1y1": x1y1, "x2y2": x2y2, "relative_head_X": relative_head_X, "relative_head_Y": relative_head_Y}

                if own_player:
                    own_player = False
                    if not player_in_frame:
                        player_in_frame = True

            if closest_detection: 
                absolute_head_X, absolute_head_Y = closest_detection["relative_head_X"] + detection_box['left'], closest_detection["relative_head_Y"] + detection_box['top']
                x1, y1 = closest_detection["x1y1"]
                # if win32api.GetAsyncKeyState(0x02) != 0:
                if is_aimbot_enabled():
                    move_crosshair(absolute_head_X, absolute_head_Y)

def clean_up():
    screen.close()
    os._exit(0)

def on_release(key):
    try:
        if key == keyboard.KeyCode.from_char('r'):
            update_status_aimbot()
        if key == keyboard.Key.f2:
            clean_up()
    except NameError:
        pass


listener = keyboard.Listener(on_release=on_release)
listener.start()


main()