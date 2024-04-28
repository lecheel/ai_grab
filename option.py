import tkinter as tk
from tkinter import ttk
import json

class OptionFrame(tk.Frame):
    def __init__(self, parent, handle_option, on_closing_callback=None, default_visibility=False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.handle_option = handle_option
        self.default_visibility = default_visibility
        self.is_visible = default_visibility
        self.config_data = {}  # Dictionary to hold configuration data
        self.workflow_options()  # Setup UI elements

    def workflow_options(self):
        
        # Group for CFG and Step sliders
        cfg_step_frame = ttk.LabelFrame(self, text="ksampler")
        cfg_step_frame.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        # Title and slider for CFG
        cfg_label = tk.Label(cfg_step_frame, text="CFG:")
        cfg_label.grid(row=0, column=0, padx=(5, 10), pady=5, sticky='e')

        self.cfg_slider = tk.Scale(cfg_step_frame, from_=0.1, to=10.0, resolution=0.1, orient=tk.HORIZONTAL)
        self.cfg_slider.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Title and slider for Step
        step_label = tk.Label(cfg_step_frame, text="Step:")
        step_label.grid(row=0, column=2, padx=(10, 5), pady=5, sticky='e')

        self.step_slider = tk.Scale(cfg_step_frame, from_=1, to=30, resolution=1, orient=tk.HORIZONTAL)
        self.step_slider.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        # Group for Lora sliders
        lora_frame = ttk.LabelFrame(self, text="Lora")
        lora_frame.grid(row=1, column=0, padx=5, pady=5, sticky='w')

        # Title and slider for Lora Strength Model
        lora_strength_model_label = tk.Label(lora_frame, text="Lora Strength Model:")
        lora_strength_model_label.grid(row=0, column=0, padx=(5, 10), pady=5, sticky='e')

        self.lora_strength_model_slider = tk.Scale(lora_frame, from_=0.1, to=10.0, resolution=0.1, orient=tk.HORIZONTAL)
        self.lora_strength_model_slider.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Title and slider for Lora Strength Clip
        lora_strength_clip_label = tk.Label(lora_frame, text="Lora Strength Clip:")
        lora_strength_clip_label.grid(row=0, column=2, padx=(10, 5), pady=5, sticky='e')

        self.lora_strength_clip_slider = tk.Scale(lora_frame, from_=0.1, to=10.0, resolution=0.1, orient=tk.HORIZONTAL)
        self.lora_strength_clip_slider.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        # Set initial slider values based on config data
        self.cfg_slider.set(self.config_data.get("cfg", 1.8))
        self.step_slider.set(self.config_data.get("step", 10))
        self.lora_strength_model_slider.set(self.config_data.get("lora_strength_model", 5.0))
        self.lora_strength_clip_slider.set(self.config_data.get("lora_strength_clip", 7.0))

        # Separator
        separator = ttk.Separator(self, orient='horizontal')
        separator.grid(row=3, columnspan=10, sticky='ew')

