import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import websocket
import uuid
import json
import urllib.request
import urllib.parse
import io
import random
import time
import pyautogui
import bettercam
import time
import cv2
import os
import sys

# from rich import print
import queue
from region import SnipRegion
from option import OptionFrame


import winclip32
from requests_toolbelt import MultipartEncoder

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

class TextRedirector:
    def __init__(self, text_widget, tag):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, msg):
        self.text_widget.config(state="normal")
        self.text_widget.insert("end", msg, (self.tag,))
        self.text_widget.config(state="disabled")
        self.text_widget.see("end")  # Automatically scroll to the end

    def flush(self):
        pass

class ImageViewer(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("AI ImageGrab")
        self.iconbitmap("./icons/ai_imagegrab.ico")
        self.geometry("830x600")
        self.imgLock = False

#        self.img_lock = threading.Lock()

        self.full_image = None
        self.current_image_index = 0
        self.imageX = None
        self.image1 = None
        self.image1_copy = None
        self.image2 = None
        self.last_seed = None

        self.ws = None
        self.camera = None
        self.camera = bettercam.create()
        self.capture_thread_stop_queue = queue.Queue()

        self.camera_x = 0
        self.camera_y = 0
		
        self.load_settings()
        self.setup_ui()
        self.setup_websocket()
        self.setup_camera()
         
        """ 
        # Create a text widget to display console logs
        self.log_text = tk.Text(self, wrap="word", state="disabled")
        self.log_text.pack(expand=True, fill="both")

        # Create a scrollbar and attach it to the text widget
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.log_text.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=self.scrollbar.set)

        # Redirect stdout and stderr to the text widget
        sys.stdout = TextRedirector(self.log_text, "stdout")
        sys.stderr = TextRedirector(self.log_text, "stderr")

        # Start a thread to periodically check for updates to the text widget
        self.update_console_thread = threading.Thread(target=self.update_console)
        self.update_console_thread.daemon = True
        self.update_console_thread.start()
        """


    def update_console(self):
        # Periodically update the text widget to check for new logs
        while True:
            self.log_text.see("end")
            time.sleep(0.5)

    def clear_log(self):
        # Clear the log_text widget
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def setup_ui(self):

        default_visibility = False
        # Create a toolbar frame
        self.toolbar_frame = tk.Frame(self, bd=1, relief=tk.RAISED)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        # Define toolbar buttons with corresponding icon indices
        self.icon_names = ["i_option", "i_top", "i_preview", "i_region", "i_quit"]
        self.icon_names_toggled = ["i_option_on", "i_top_on", "i_preview_on", "i_region_on", "i_quit_on"]  # Toggled icons
        self.button_functions = [self.Option, self.Top_fun, self.Preview_fun, self.Region_fun, self.Quit_fun]
        self.button_statuses = [False] * len(self.icon_names)  # Initialize button statuses to False
        self.toolbar_buttons = []  # To keep references to toolbar buttons
        
        for i, (icon_name, button_func) in enumerate(zip(self.icon_names, self.button_functions)):
            # Load the image from the resource file
            icon_image = self.load_icon_from_resource(icon_name, self.button_statuses[i])
            # Scale the image to 24x24
            icon_image = icon_image.resize((24, 24), Image.Resampling.LANCZOS)
            icon_photo = ImageTk.PhotoImage(icon_image)
            # Create the button with the image
            button = tk.Button(self.toolbar_frame, image=icon_photo, command=lambda i=i: self.toggle_button(i), borderwidth=0)
            button.image = icon_photo  # Keep a reference to avoid garbage collection
            button.pack(side=tk.LEFT, padx=2, pady=2)
            self.toolbar_buttons.append(button)

        self.options_frame = OptionFrame(self, self.handle_option, default_visibility=default_visibility)
        if default_visibility:
            self.options_frame.pack(side=tk.TOP, fill=tk.NONE, expand=False)
        self.is_options_visible = default_visibility

        # Create the option frame
        #self.options_frame = tk.Frame(self, bd=1, relief=tk.RAISED)
        #self.options_frame.pack(side=tk.TOP, fill=tk.X)

        top_frame = tk.Frame(self)
        top_frame.pack()

        bottom_frame = tk.Frame(self)
        bottom_frame.pack()

        self.camera_x = self.settings.get("camera_x", 0)
        self.camera_y = self.settings.get("camera_y", 0)

        self.prompt_button = tk.Button(top_frame, text="Prompt", command=lambda: \
                self.prompt_img2img(workflow, self.text_input.get(), self.slider.get(), save_previews=True))
        self.prompt_button.pack(side=tk.LEFT)

        # Create an input text field
        self.text_input = tk.Entry(top_frame, width=80)
        self.text_input.pack(side=tk.LEFT)
        self.text_input.insert(0, self.settings.get("remark", ""))

        # Create a slider
        self.slider = tk.Scale(top_frame, from_=0.0, to=1.0, resolution=0.02, orient=tk.HORIZONTAL)
        self.slider.pack(side=tk.LEFT)
        self.slider.set(self.settings.get("strength", 0.1))

        self.is_options_visible = False
        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack()
        self.canvas1 = tk.Canvas(self.canvas_frame, width=300, height=400)
        self.canvas1.pack(side=tk.LEFT)
        self.canvas2 = tk.Canvas(self.canvas_frame, width=600, height=400)
        self.canvas2.pack(side=tk.LEFT)

        # Keep the window always on top
        self.attributes('-topmost', False)

    def toggle_button(self, index):
        # Toggle the button status
        self.button_statuses[index] = not self.button_statuses[index]
        # Update the toolbar icon based on the toggle status
        icon_name = self.icon_names[index] if not self.button_statuses[index] else self.icon_names_toggled[index]
        icon_image = self.load_icon_from_resource(icon_name)
        # Scale the image to 24x24
        icon_image = icon_image.resize((24, 24), Image.Resampling.LANCZOS)
        icon_photo = ImageTk.PhotoImage(icon_image)
        # Update the button's image
        self.toolbar_buttons[index].config(image=icon_photo)
        self.toolbar_buttons[index].image = icon_photo  # Keep a reference to avoid garbage collection
        # Call the corresponding function
        self.button_functions[index]()

    def load_icon_from_resource(self, icon_name, is_toggled=False):
        # Determine the appropriate icon name based on the toggle status
        if is_toggled:
            icon_name += "_on"  # Append "_on" suffix for toggled state
        # Load the image from the resource file
        icon_path = f"icons/{icon_name}.png"  # Assuming icons are stored in a directory named 'icons'
        icon_image = Image.open(icon_path)
        return icon_image

    def Top_fun(self):
        # Toggle topmost attribute
        self.attributes('-topmost', not self.attributes('-topmost'))

    def Quit_fun(self):
        self.quit_app()

    def Option(self):
        self.toggle_options()

    def toggle_options(self):
        if not self.is_options_visible:
            # Pack the options frame before the canvas frame to ensure it follows the toolbar
            self.options_frame.pack(side=tk.TOP, fill=tk.NONE, expand=False, before=self.canvas_frame)
        else:
            self.options_frame.pack_forget()
        self.is_options_visible = not self.is_options_visible

    def handle_option(self, name, value):
        pass

    def Preview_fun(self):
        # Toggle the visibility of canvas1
        if self.canvas1.winfo_ismapped():
            self.canvas1.pack_forget()
        else:
            self.canvas1.pack(side=tk.LEFT, before=self.canvas2)


    def setup_camera(self):
        # print(bettercam.device_info())
        x = self.camera_x
        y = self.camera_y
        # adjust x,y +512 less then 1920,1080
        if x + 512 > 1920:
            x = 1920 - 512
        if y + 512 > 1080:
            y = 1080 - 512
        self.camera.start(target_fps=1, region=(x, y, x+512, y+512))
        self.camera.is_capturing = True
        self.capture_thread = threading.Thread(target=self.capture_and_display, daemon=True)
        self.capture_thread.start()


    def update_camera_position(self, event, camera_position):
        print(f"Camera position: {camera_position}")
        self.camera_x = camera_position[0] 
        self.camera_y = camera_position[1]
        # self.capture_thread_stop_queue.put(True)
        self.camera.stop()
        self.setup_camera()

    def Region_fun(self):
        self.snipRegion = SnipRegion(self, self.update_camera_position)
        self.snipRegion.create_screen_canvas()
        self.snipRegion.on_button_release(None)

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            self.settings = {"remark": "", "strength": 0.1, "camera_x": 0, "camera_y": 0}

    def save_settings(self):
        self.settings["remark"] = self.text_input.get()
        self.settings["strength"] = self.slider.get()
        self.settings["camera_x"] = self.camera_x
        self.settings["camera_y"] = self.camera_y
        with open("settings.json", "w") as f:
            json.dump(self.settings, f)

    def setup_websocket(self):
        server_address = "127.0.0.1:8188"
        self.client_id = str(uuid.uuid4())
        self.ws = websocket.WebSocket()
        self.ws.connect(f"ws://{server_address}/ws?clientId={self.client_id}")
		

    def copy_image_to_clipboard(self,imgIO):
        # Convert image to bytes
        image_byte = io.BytesIO()
        imgIO.convert("RGB").save(image_byte, "BMP")
        data = image_byte.getvalue()[14:]
        image_byte.close()
        winclip32.set_clipboard_data(winclip32.BITMAPINFO_STD_STRUCTURE, data)

    def upload_image_data(self, image_data, name, server_address, image_type="input", overwrite=False):
        # Convert the Image object to bytes
        img_byte_arr = io.BytesIO()
        image_data.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        multipart_data = MultipartEncoder(
            fields={
                'image': (name, img_byte_arr.read(), 'image/png'),  # Pass the bytes buffer
                'type': image_type,
                'overwrite': str(overwrite).lower()
            }
        )

        data = multipart_data.to_string()
        headers = {'Content-Type': multipart_data.content_type}
        request = urllib.request.Request("http://{}/upload/image".format(server_address), data=data, headers=headers)
        with urllib.request.urlopen(request) as response:
            return response.read()

    def capture_and_display(self):
        while True:
            if not self.capture_thread_stop_queue.empty():  # Check if stop signal is received
                print("Capture thread stopped --<queue>")
                break

            frame = self.camera.get_latest_frame()

            if not self.imgLock:
                self.full_image = Image.fromarray(frame.copy())
            # Convert the frame to a PIL Image
            image = Image.fromarray(frame)

            # Resize the image to fit the canvas
            image1 = image.resize((300, 300))
            self.image1_copy = image
            self.image1 = ImageTk.PhotoImage(image1)
            self.canvas1.create_image(0, 0, anchor=tk.NW, image=self.image1)

            # Sleep for a short time to control the frame rate
            time.sleep(0.001)

    def unlock_button(self):
        # Clear the lock bit
        self.imgLock = False
        print("Button unlocked.")

    def update_canvas2(self):
        if self.imageX:
            if not self.imgLock:
                self.image2 = ImageTk.PhotoImage(self.imageX)
                self.canvas2.create_image(0, 0, anchor=tk.NW, image=self.image2)
                self.copy_image_to_clipboard(self.imageX)
                # self.update_idletasks()
                self.imgLock = True

                # self.progress_bar.stop()
                # self.progress_bar['value'] = 0

    def get_images(self, prompt):
        prompt_id = self.queue_prompt(prompt)['prompt_id']
        # print(prompt_id)
        current_node = ""
        while True:
            out = self.ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['prompt_id'] == prompt_id:
                        if data['node'] is None:
                            break  # Execution is done
                        else:
                            current_node = data['node']
            else:
                if current_node == 'save_image_websocket_node':
                    # Clear the canvas before displaying the new image
                    self.imageX = Image.open(io.BytesIO(out[8:]))
                    self.update_canvas2()

    def queue_prompt(self, prompt):
        p = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)
        return json.loads(urllib.request.urlopen(req).read())

    def prompt_image(self):
        # Check if the lock bit is set
        if self.last_seed is None:
            self.last_seed = random.randint(10**14, 10**15 - 1)
        self.imgLock = False
        with open("prompt.json", "r") as file:
            prompt = json.load(file)
        prompt["3"]["inputs"]["seed"] = self.last_seed 

        print(prompt["3"]["inputs"]["seed"])
        self.get_images(prompt)

    def get_history(self,prompt_id, server_address):
      with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
          return json.loads(response.read())

    def queue_promptX(self,prompt, client_id, server_address):
      p = {"prompt": prompt, "client_id": client_id}
      headers = {'Content-Type': 'application/json'}
      data = json.dumps(p).encode('utf-8')
      req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data, headers=headers)
      return json.loads(urllib.request.urlopen(req).read())

    def track_progress(self,prompt,prompt_id):
      node_ids = list(prompt.keys())
      finished_nodes = []

      while True:
          out = self.ws.recv()
          if isinstance(out, str):
              message = json.loads(out)
              if message['type'] == 'progress':
                  data = message['data']
                  current_step = data['value']
                  max_step = data['max']
                  # progress_text = f"Progress: {current_step}/{max_step}"
                  print('In K-Sampler -> Step: ', current_step, ' of: ', data['max'])
              if message['type'] == 'execution_cached':
                  data = message['data']
                  for itm in data['nodes']:
                      if itm not in finished_nodes:
                          finished_nodes.append(itm)
                          print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
                          # Update the label with progress information
                          progress_text = f"Progress: {len(finished_nodes)}/{len(node_ids)} Tasks done"
              if message['type'] == 'executing':
                  data = message['data']
                  if data['node'] not in finished_nodes:
                      finished_nodes.append(data['node'])
                      print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
                      # Update the label with progress information
                      progress_text = f"Progress: {len(finished_nodes)}/{len(node_ids)} Tasks done"

                  if data['node'] is None and data['prompt_id'] == prompt_id:
                      break #Execution is done
              # time.sleep(0.01)
          else:
              continue
      return

    def get_image(self,filename, subfolder, folder_type, server_address):
      data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
      url_values = urllib.parse.urlencode(data)
      with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
          return response.read()

    def save_imageX(self, images, output_path, save_previews):
      for itm in images:
          directory = os.path.join(output_path, 'temp/') if itm['type'] == 'temp' and save_previews else output_path
          os.makedirs(directory, exist_ok=True)
          try:
              image = Image.open(io.BytesIO(itm['image_data']))
              self.imgLock = False
              self.imageX = image
              self.update_canvas2()
              # image.save(os.path.join(directory, itm['file_name']))
          except Exception as e:
              print(f"Failed to save image {itm['file_name']}: {e}")

    def get_imagesX(self,prompt_id, server_address, allow_preview = False):
      output_images = []

      history = self.get_history(prompt_id, server_address)[prompt_id]
      for node_id in history['outputs']:
          node_output = history['outputs'][node_id]
          output_data = {}
          if 'images' in node_output:
              for image in node_output['images']:
                  if allow_preview and image['type'] == 'temp':
                      preview_data = self.get_image(image['filename'], image['subfolder'], image['type'], server_address)
                      output_data['image_data'] = preview_data
                  if image['type'] == 'output':
                      image_data = self.get_image(image['filename'], image['subfolder'], image['type'], server_address)
                      output_data['image_data'] = image_data
          output_data['file_name'] = image['filename']
          output_data['type'] = image['type']
          output_images.append(output_data)

      return output_images

    def generate_image_by_prompt_and_image(self, prompt, output_path, image_data, filename, save_previews=False):
        self.upload_image_data(image_data, filename, server_address)  # Pass image data instead of a file path
        prompt_id = self.queue_promptX(prompt, self.client_id, server_address)['prompt_id']
        self.track_progress(prompt,prompt_id)
        images = self.get_imagesX(prompt_id, server_address, save_previews)
        self.save_imageX(images, output_path, save_previews)

    def image_to_bytes(self, image):
        # Convert the PIL Image to bytes (PNG format)
        with BytesIO() as buffer:
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()
        return image_bytes

    def photo_image_to_pil(self, photo_image):
        # Render the PhotoImage on a canvas and capture the content as an image
        width, height = photo_image.width(), photo_image.height()
        canvas = tk.Canvas(self, width=width, height=height)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo_image)
        canvas.update()
        pil_image = Image.new("RGB", (width, height))
        pil_image.paste(canvas, (0, 0))
        return pil_image   

    def prompt_img2img(self, workflow, positve_prompt, strength, negative_prompt='', save_previews=False):
        prompt = json.loads(workflow)
        image_data = self.image1_copy
        id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
        k_sampler = [key for key, value in id_to_class_type.items() if value == 'KSampler'][0]
        prompt.get(k_sampler)['inputs']['seed'] = random.randint(10**14, 10**15 - 1)
        postive_input_id = prompt.get(k_sampler)['inputs']['positive'][0]
        prompt.get(postive_input_id)['inputs']['text'] = positve_prompt
        prompt.get(k_sampler)['inputs']['denoise'] = strength
        
        if negative_prompt != '':
            negative_input_id = prompt.get(k_sampler)['inputs']['negative'][0]
            prompt.get(negative_input_id)['inputs']['text'] = negative_prompt
        
        image_loader = [key for key, value in id_to_class_type.items() if value == 'LoadImage'][0]
        # using timestamp as filename
        filename = str(int(time.time())) + ".png"
        prompt.get(image_loader)['inputs']['image'] = filename
        
        self.generate_image_by_prompt_and_image(prompt, './output/img2img', image_data, filename, save_previews)

    def quit_app(self):
        self.save_settings()
        self.ws.close()  # Close WebSocket connection
        self.destroy()   # Quit the application

def load_workflow(workflow_path):
  try:
      with open(workflow_path, 'r') as file:
          workflow = json.load(file)
          return json.dumps(workflow)
  except FileNotFoundError:
      print(f"The file {workflow_path} was not found.")
      return None
  except json.JSONDecodeError:
      print(f"The file {workflow_path} contains invalid JSON.")
      return None


def check_server_availability(server_address):
    try:
        # Attempt to connect to the server
        ws = websocket.WebSocket()
        ws.connect(server_address)
        ws.close()
        return True
    except ConnectionRefusedError:
        return False

def open_websocket_connection():
    server_address = 'ws://127.0.0.1:8188/ws?clientId={}'.format(uuid.uuid4())
    return server_address

def main():
    ret = True
    print("Checking server availability...")
    server_address = open_websocket_connection()
    server_available = check_server_availability(server_address)
    if server_available:
        print("Comfyui Server is available [OK]")
    else:
        ret = False
        print("Comfyui Server is not available [NG]")
    return ret

if __name__ == "__main__":
    if main():
        workflow = load_workflow('./workflows/sketch_api.json')
        app = ImageViewer()
        option_frame = OptionFrame(None, handle_option=None)
        # option_frame.pack()
        app.mainloop()

"""
+-----------------------+
| toolbar |  |  |       +
+-----------------------+
| option                |
|    option1            |
|    option2            |
+-----------------------+
| input_text, slider    |
+-----------------------+
| canvas1 | cancas2     |
+-----------------------+



"""