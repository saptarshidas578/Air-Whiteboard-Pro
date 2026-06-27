import cv2
import mediapipe as mp
import numpy as np
import math
import time
import os
import threading
from collections import deque
from enum import Enum, auto
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
import requests

NGROK_URL = "https://existing-entryway-demise.ngrok-free.dev/ocr"
# ---------------- MULTITHREADED CAMERA ----------------
class VideoStream:
    """Runs the webcam on a separate CPU thread to boost FPS."""
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.grabbed, self.frame = self.cap.read()
        self.stopped = False

    def start(self):
        # Run the update loop in a background daemon thread
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            self.grabbed, self.frame = self.cap.read()

    def read(self):
        return self.grabbed, self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()
    
    

# ---------------- ENUMS ----------------
class Mode(Enum):
    IDLE = auto()
    DRAW = auto()
    LINE = auto()
    ERASE = auto()
    PAUSE = auto()

# ---------------- MAIN APPLICATION ----------------
class AirWhiteboard:
    def __init__(self):
        # Mediapipe Setup
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.ocr_text = ""
        # Start Multithreaded Camera
        self.stream = VideoStream(0).start()
        time.sleep(1) # Give the camera a second to warm up
        success, frame = self.stream.read()
        
        if not success or frame is None:
            print("Error: Could not read from webcam.")
            exit()
            
        self.h, self.w, _ = frame.shape

        # State Variables
        self.canvas = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        self.pages = [self.canvas.copy()]
        self.current_page = 0
        self.undo_stack = deque(maxlen=20) 
        
        # Smoothing & Coordinates
        self.smooth_x, self.smooth_y = 0, 0
        self.alpha = 0.6 # Smoothing factor (lower = smoother but slightly delayed)
        self.prev_x, self.prev_y = 0, 0
        self.line_start = None
        
        self.mode = Mode.IDLE
        self.color = (255, 255, 255)
        self.color_name = "WHITE"
        self.thickness = 5
        
        self.show_camera = True
        self.presentation_mode = False
        self.recognized_shape = ""

    # ---------------- HELPERS ----------------
    def finger_up(self, lm, tip, pip):
        return lm[tip].y < lm[pip].y

    def save_current_page(self):
        self.pages[self.current_page] = self.canvas.copy()

    def detect_shape(self, contour):
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        vertices = len(approx)

        if vertices == 3: return "Triangle"
        if vertices == 4: return "Rectangle"
        if vertices > 6: return "Circle"
        return "Unknown"

    def export_pdf(self):
        pdf = pdf_canvas.Canvas("notes.pdf")
        filename = "temp_page.png"
        
        for page in self.pages:
            temp = cv2.cvtColor(page, cv2.COLOR_BGR2RGB)
            cv2.imwrite(filename, temp)
            pdf.drawImage(ImageReader(filename), 0, 0, width=595, height=842)
            pdf.showPage()
            
        pdf.save()
        if os.path.exists(filename):
            os.remove(filename)
        print("PDF saved as notes.pdf")
    def recognize_text(self):

        filename = "ocr_temp.png"
        cv2.imwrite(filename, self.canvas)

        try:
            with open(filename, "rb") as img:
                files = {"image": img}

                response = requests.post(
                    NGROK_URL,
                    files=files,
                    timeout=30
                )

            if os.path.exists(filename):
                os.remove(filename)

            data = response.json()
            return data["text"]

        except Exception as e:
            print(e)

            if os.path.exists(filename):
                os.remove(filename)

            return "OCR Failed"

    # ---------------- CORE LOGIC ----------------
    def process_hands(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        self.mode = Mode.IDLE

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            lm = hand.landmark

            raw_x, raw_y = int(lm[8].x * self.w), int(lm[8].y * self.h)
            thumb_x, thumb_y = int(lm[4].x * self.w), int(lm[4].y * self.h)
            
            # Apply Exponential Moving Average (EMA) for smooth drawing
            if self.smooth_x == 0 and self.smooth_y == 0:
                self.smooth_x, self.smooth_y = raw_x, raw_y
            else:
                self.smooth_x = int((self.alpha * raw_x) + ((1 - self.alpha) * self.smooth_x))
                self.smooth_y = int((self.alpha * raw_y) + ((1 - self.alpha) * self.smooth_y))

            # Brush size based on pinch distance
            dist = math.hypot(thumb_x - raw_x, thumb_y - raw_y)
            if dist < 40: self.thickness = 3
            elif dist < 80: self.thickness = 7
            else: self.thickness = 12

            # Finger states
            index = self.finger_up(lm, 8, 6)
            middle = self.finger_up(lm, 12, 10)
            ring = self.finger_up(lm, 16, 14)
            pinky = self.finger_up(lm, 20, 18)

            # === COLOR BAR SELECTION ===
            if self.smooth_y < 60 and not self.presentation_mode:
                self.prev_x, self.prev_y = 0, 0
                self.line_start = None
                step = self.w // 4

                if self.smooth_x < step:
                    self.color, self.color_name = (0, 0, 255), "RED"
                elif self.smooth_x < step * 2:
                    self.color, self.color_name = (0, 255, 0), "GREEN"
                elif self.smooth_x < step * 3:
                    self.color, self.color_name = (255, 0, 0), "BLUE"
                else:
                    self.color, self.color_name = (255, 255, 255), "WHITE"

            # === ERASE ===
            elif index and middle and ring and pinky:
                self.mode = Mode.ERASE
                cv2.circle(self.canvas, (self.smooth_x, self.smooth_y), 40, (0, 0, 0), -1)
                self.prev_x, self.prev_y = 0, 0
                self.line_start = None

            # === LINE TOOL ===
            elif index and middle and ring and not pinky:
                self.mode = Mode.LINE
                if self.line_start is None:
                    self.line_start = (self.smooth_x, self.smooth_y)
                else:
                    cv2.line(self.canvas, self.line_start, (self.smooth_x, self.smooth_y), self.color, self.thickness)
                    self.line_start = None
                self.prev_x, self.prev_y = 0, 0

            # === DRAW ===
            elif index and not middle:
                self.mode = Mode.DRAW
                if self.prev_x == 0 and self.prev_y == 0:
                    self.undo_stack.append(self.canvas.copy())
                    self.prev_x, self.prev_y = self.smooth_x, self.smooth_y

                cv2.line(self.canvas, (self.prev_x, self.prev_y), (self.smooth_x, self.smooth_y), self.color, self.thickness)
                self.prev_x, self.prev_y = self.smooth_x, self.smooth_y
                self.line_start = None

            # === PAUSE ===
            elif index and middle:
                self.mode = Mode.PAUSE
                self.prev_x, self.prev_y = 0, 0
                self.line_start = None

            else:
                self.prev_x, self.prev_y = 0, 0
                self.line_start = None

            self.mp_draw.draw_landmarks(frame, hand, self.mp_hands.HAND_CONNECTIONS)
        else:
            # Reset smooth coordinates if hand leaves frame
            self.smooth_x, self.smooth_y = 0, 0

    def draw_ui(self, frame):
        # Mask-based blending for cleaner drawing overlays
        if self.show_camera and not self.presentation_mode:
            gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
            mask_inv = cv2.bitwise_not(mask)
            
            frame_bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
            canvas_fg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
            output = cv2.add(frame_bg, canvas_fg)
        else:
            output = self.canvas.copy()

        # Draw Hover Cursor if in Idle Mode
        if self.mode == Mode.IDLE and self.smooth_x != 0 and self.smooth_y != 0:
            cv2.circle(output, (self.smooth_x, self.smooth_y), self.thickness, self.color, 1)

        if not self.presentation_mode:
            step = self.w // 4
            # Top Color Bar
            cv2.rectangle(output, (0, 0), (step, 60), (0, 0, 255), -1)
            cv2.rectangle(output, (step, 0), (step*2, 60), (0, 255, 0), -1)
            cv2.rectangle(output, (step*2, 0), (step*3, 60), (255, 0, 0), -1)
            cv2.rectangle(output, (step*3, 0), (self.w, 60), (255, 255, 255), -1)

            cv2.putText(output, f"Color: {self.color_name}", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

            # Bottom Control Bar
            cv2.rectangle(output, (0, self.h - 50), (self.w, self.h), (30, 30, 30), -1)
            controls = "N:New P:Prev M:Next C:Clear S:Save E:PDF K:Shot U:Undo H:Shape T:Pres O:OCR ESC:Exit"
            cv2.putText(output, controls, (10, self.h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

            # Info Text
            cv2.putText(output, f"Page {self.current_page + 1}/{len(self.pages)} | Brush {self.thickness}",
                        (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(output, f"Shape: {self.recognized_shape}",
                        (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(output,f"OCR: {self.ocr_text}",(10, 150),cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,(0,255,0),2)
        return output

    def handle_keyboard(self, frame):
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27: # ESC
            return False
            
        elif key == ord('n'):
            self.save_current_page()
            self.canvas = np.zeros((self.h, self.w, 3), dtype=np.uint8)
            self.pages.append(self.canvas.copy())
            self.current_page = len(self.pages) - 1
            
        elif key == ord('p'):
            self.save_current_page()
            if self.current_page > 0:
                self.current_page -= 1
                self.canvas = self.pages[self.current_page].copy()
                
        elif key == ord('m'):
            self.save_current_page()
            if self.current_page < len(self.pages) - 1:
                self.current_page += 1
                self.canvas = self.pages[self.current_page].copy()
                
        elif key == ord('c'):
            self.undo_stack.append(self.canvas.copy())
            self.canvas[:] = 0
            
        elif key == ord('s'):
            cv2.imwrite(f"drawing_{int(time.time())}.png", self.canvas)
            print("Canvas saved.")
            
        elif key == ord('k'):
            cv2.imwrite(f"screenshot_{int(time.time())}.png", frame)
            print("Screenshot saved.")
            
        elif key == ord('v'):
            self.show_camera = not self.show_camera
            
        elif key == ord('u'):
            if self.undo_stack:
                self.canvas = self.undo_stack.pop()
                
        elif key == ord('t'):
            self.presentation_mode = not self.presentation_mode
            
        elif key == ord('e'):
            self.save_current_page()
            self.export_pdf()
            
        elif key == ord('h'):
            self.apply_shape_recognition()
        
        elif key == ord('o'):
            print("Recognizing...")
            self.ocr_text = self.recognize_text()
            print(self.ocr_text)
            
        return True

    def apply_shape_recognition(self):
        self.undo_stack.append(self.canvas.copy())
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            if cv2.contourArea(cnt) > 1000:
                self.recognized_shape = self.detect_shape(cnt)
                x, y, w_box, h_box = cv2.boundingRect(cnt)
                
                # Erase rough shape
                cv2.drawContours(self.canvas, [cnt], -1, (0, 0, 0), -1)

                if self.recognized_shape == "Rectangle":
                    cv2.rectangle(self.canvas, (x, y), (x + w_box, y + h_box), self.color, self.thickness)
                elif self.recognized_shape == "Circle":
                    center = (x + w_box // 2, y + h_box // 2)
                    radius = max(w_box, h_box) // 2
                    cv2.circle(self.canvas, center, radius, self.color, self.thickness)
                elif self.recognized_shape == "Triangle":
                    epsilon = 0.04 * cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, epsilon, True)
                    cv2.drawContours(self.canvas, [approx], -1, self.color, self.thickness)
                break

    def run(self):
        while True:
            success, frame = self.stream.read()
            if not success or frame is None:
                continue

            frame = cv2.flip(frame, 1)
            self.process_hands(frame)
            output = self.draw_ui(frame)
            
            cv2.imshow("AIR WHITEBOARD PRO", output)
            
            if not self.handle_keyboard(frame):
                break

        self.stream.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = AirWhiteboard()
    app.run()