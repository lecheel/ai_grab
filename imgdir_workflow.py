from PIL import Image, ImageTk
import websocket
import uuid
import json
import time
import queue
import glob
import io
import os
import urllib.request
import urllib.parse
from requests_toolbelt import MultipartEncoder


server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

class ImageBatch():
    def __init__(self, workflow_path='workflow.json'):
        self.load_workflow(workflow_path)
        self.setup_websocket()

    def batch_prompt(self):
        print('In Batch Progress')
        files = glob.glob('./data/*.jpg')
        for f in files:
            print(f)
            img = Image.open(f)
            self.prompt_img2img(img, "master piece")

    def load_workflow(self, workflow_path):
        print("Initializing workflow data... {}".format(workflow_path))
        try:
            with open(workflow_path, 'r') as file:
                workflow_content = json.load(file)
            self.wf = json.dumps(workflow_content)
            print("Loaded workflow:", workflow_path)
        except Exception as e:
            print("Error loading workflow:", e)
            self.wf = {}  # Reset workflow if loading fails

    def setup_websocket(self):
        server_address = "127.0.0.1:8188"
        self.client_id = str(uuid.uuid4())
        self.ws = websocket.WebSocket()
        self.ws.connect(f"ws://{server_address}/ws?clientId={self.client_id}")

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
                  # print('In K-Sampler -> Step: ', current_step, ' of: ', data['max'])
              if message['type'] == 'execution_cached':
                  data = message['data']
                  for itm in data['nodes']:
                      if itm not in finished_nodes:
                          finished_nodes.append(itm)
                          # print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
                          # Update the label with progress information
                          progress_text = f"Progress: {len(finished_nodes)}/{len(node_ids)} Tasks done"
              if message['type'] == 'executing':
                  data = message['data']
                  if data['node'] not in finished_nodes:
                      finished_nodes.append(data['node'])
                      # print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
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
              image.save(os.path.join(directory, itm['file_name']))
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



    def generate_image_by_prompt_and_image(self, prompt, output_path, image_data, filename, save_previews=False):
        self.upload_image_data(image_data, filename, server_address)  # Pass image data instead of a file path
        prompt_id = self.queue_promptX(prompt, self.client_id, server_address)['prompt_id']
        self.track_progress(prompt,prompt_id)
        images = self.get_imagesX(prompt_id, server_address, save_previews)
        self.save_imageX(images, output_path, save_previews)

    def prompt_img2img(self, img, save_previews=True):
        prompt = json.loads(self.wf)
        id_to_class_type = {id: details['class_type'] for id, details in prompt.items()}
        image_data = img
        filename = str(int(time.time())) + ".png"
        image_loader = [key for key, value in id_to_class_type.items() if value == 'LoadImage'][0]
        # using timestamp as filename
        filename = str(int(time.time())) + ".png"
        prompt.get(image_loader)['inputs']['image'] = filename
        self.generate_image_by_prompt_and_image(prompt, './output/img2img', image_data, filename, save_previews)

if __name__ == "__main__":
    app = ImageBatch("./workflows/sketch.json")
    app.batch_prompt()

