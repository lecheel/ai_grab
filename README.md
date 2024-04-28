# AI ImageGrab Application with Comfyui Workflow Adapter API

The AI ImageGrab application with Comfyui Workflow Adapter is a Python-based tool designed for image processing and manipulation. It provides a graphical user interface (GUI) for users to interact with and perform various image-related tasks. The application utilizes tkinter for the GUI, PIL for image handling, threading for concurrency, and websocket for communication with a server via Comfyui's workflow adapter.

## Features

- **Image Capture**: Captures images from a camera device in real-time.
- **Image Processing**: Processes captured images using predefined workflows and user prompts fetched via Comfyui's workflow adapter.
- **GUI Interface**: Provides an intuitive user interface with toolbar buttons, input fields, sliders, and canvas frames for image display.
- **WebSocket Communication**: Establishes communication with Comfyui's workflow adapter via WebSocket for fetching image data and processing instructions.

## Usage

1. **Installation**: Ensure Python and required libraries are installed.
2. **Server Availability**: Check if the server hosting Comfyui's workflow adapter is available for WebSocket communication.
3. **Run Application**: Execute the Python script to launch the AI ImageGrab application.
4. **Interact with GUI**: Use the GUI interface to capture images, input prompts, adjust parameters, and view processed images.
5. **Save Settings**: Optionally save application settings for future sessions.
6. **Exit Application**: Close the application when done.


## Installation

### Step 1: Create Conda Environment

Open your terminal or command prompt and navigate to your project directory.

Use the following command to create a new Conda environment named `aiimagegrab` and install the required packages:

```bash
conda create --name aigrab python=3.10 
```

This command will create a new Conda environment named `aiimagegrab` and install the packages listed in `requirements.txt`.

### Step 2: Activate Conda Environment

Activate the newly created Conda environment using the following command:

- **On Windows**:
  ```bash
  conda activate aigrab
  ```
### Step 3: Verify Installation

You can verify that the dependencies were installed successfully by running:

```bash
conda list
```

This command will display a list of installed packages in the `aiimagegrab` environment.

### Step 4: Run the Application

Now that your Conda environment is set up with the required dependencies, you can run your Python script using the `python` command as usual.

```bash
python main.py
```

That's it! Your environment should now be set up with the necessary dependencies for running the AI ImageGrab application using Conda.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- Credits to the developers and contributors of the libraries used in this project.
- Special thanks to [Comfyui](https://comfyui.com) for providing the workflow adapter and resources.

---

Feel free to adapt the README further to suit your preferences and requirements!
