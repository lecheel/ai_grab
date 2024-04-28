from tkinter import Frame, Canvas, Button, Toplevel, BOTH, YES
from PIL import Image, ImageTk
import pyautogui
import datetime
import io

class SnipRegion():
    def __init__(self, master, update_method):
        self.snip_surface = None
        self.master = master
        self.update_method = update_method
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.camera_x1 = None
        self.camera_y1 = None
        self.camera_x2 = None
        self.camera_y2 = None
        

        self.menu_frame = Frame(master)
        self.menu_frame.pack(fill=BOTH, expand=YES, padx=1, pady=1)

        self.buttonBar = Frame(self.menu_frame, bg="")
        self.buttonBar.pack()

        self.master_screen = Toplevel(master)
        self.master_screen.withdraw()
        self.master_screen.attributes("-transparent", "maroon3")
        self.picture_frame = Frame(self.master_screen, background="maroon3")
        self.picture_frame.pack(fill=BOTH, expand=YES)

    def create_screen_canvas(self):
        self.master_screen.deiconify()
        self.master.withdraw()

        self.snip_surface = Canvas(self.picture_frame, cursor="cross", bg="grey11")
        self.snip_surface.pack(fill=BOTH, expand=YES)

        self.snip_surface.bind("<ButtonPress-1>", self.on_button_press)
        self.snip_surface.bind("<B1-Motion>", self.on_snip_drag)
        self.snip_surface.bind("<ButtonRelease-1>", self.on_button_release)

        self.master_screen.attributes('-fullscreen', True)
        self.master_screen.attributes('-alpha', .3)
        self.master_screen.lift()
        self.master_screen.attributes("-topmost", True)

    def on_button_release(self, event):
        if self.start_x is not None and self.start_y is not None \
                and self.current_x is not None and self.current_y is not None:
            if self.start_x <= self.current_x and self.start_y <= self.current_y:
                self.take_bounded_screenshot(self.start_x, self.start_y, self.current_x - self.start_x, self.current_y - self.start_y)

            elif self.start_x >= self.current_x and self.start_y <= self.current_y:
                self.take_bounded_screenshot(self.current_x, self.start_y, self.start_x - self.current_x, self.current_y - self.start_y)

            elif self.start_x <= self.current_x and self.start_y >= self.current_y:
                self.take_bounded_screenshot(self.start_x, self.current_y, self.current_x - self.start_x, self.start_y - self.current_y)

            elif self.start_x >= self.current_x and self.start_y >= self.current_y:
                self.take_bounded_screenshot(self.current_x, self.current_y, self.start_x - self.current_x, self.start_y - self.current_y)
            self.exit_screenshot_mode()
        if event is not None:
            self.update_method(event, (self.camera_x1, self.camera_y1, self.camera_x2, self.camera_y2))
        return event,(self.camera_x1, self.camera_y1, self.camera_x2, self.camera_y2)

    def exit_screenshot_mode(self):
        self.snip_surface.destroy()
        self.master_screen.withdraw()
        self.master.deiconify()
        # self.camera_x = self.current_x
        # self.camera_y = self.current_y

    def on_button_press(self, event):
        self.start_x = self.snip_surface.canvasx(event.x)
        self.start_y = self.snip_surface.canvasy(event.y)
        self.snip_surface.create_rectangle(0, 0, 1, 1, outline='red', width=3, fill="maroon3")

    def on_snip_drag(self, event):
        self.current_x, self.current_y = (event.x, event.y)
        self.snip_surface.coords(1, self.start_x, self.start_y, self.current_x, self.current_y)

    def take_bounded_screenshot(self, x1, y1, x2, y2):
        # Convert coordinates to integers
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Capture screenshot
        screenshot = pyautogui.screenshot(region=(x1, y1, x2, y2))
        self.camera_x1 = x1
        self.camera_y1 = y1
        self.camera_x2 = x2
        self.camera_y2 = y2
        # print(f"camera viewport: ({x1}, {y1}, {x2}, {y2})")
        
        # Convert screenshot to bytes
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Optionally, return the bytes object for further processing
        return img_bytes
