"""
Advanced Image Processor Tool for PyToolBox.

This tool allows for both single-image and batch processing with a real-time preview.
Features include adjustments for brightness, contrast, saturation, and resizing.
It operates independently of the main app's global folder selection for a more
integrated user experience.
"""
import os
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageEnhance, ImageTk

from .tool_base import ToolBase


class ImageAdjuster(ToolBase):
    def __init__(self, app):
        super().__init__(app)

        # --- State Management ---
        self.mode = None  # Tracks 'single' or 'batch' mode
        self.source_path = None  # Path to the single file or folder
        self.image_files_list = []  # List of image paths for batch mode

        # Store the original PIL image for fast, non-destructive previews
        self.original_pil_image = None
        # Store the Tkinter-compatible version for the UI label
        self.preview_tk_image = None

        # --- UI Widget References ---
        self.preview_label = None
        self.brightness_slider = None
        self.contrast_slider = None
        self.saturation_slider = None
        self.width_entry = None
        self.height_entry = None
        self.aspect_ratio_var = ctk.BooleanVar(value=True)

    @property
    def name(self) -> str:
        """The display name of the tool in the sidebar."""
        return "Advanced Image Processor"

    @property
    def requires_global_folder(self) -> bool:
        """
        Overrides the base class property.
        This tool handles its own file/folder loading, so it does not
        need the main app's global folder selection.
        """
        return False

    def on_preview_resize(self, event):
        """Callback function to re-render the preview when its container size changes."""
        self.update_preview()

    def create_ui(self, parent_frame):
        """Creates the entire UI for the image processor tool."""
        # --- Configure Grid Layout for the tool's main frame ---
        parent_frame.grid_columnconfigure(0, weight=3)  # Preview area takes more space
        parent_frame.grid_columnconfigure(1, weight=1)  # Controls area
        parent_frame.grid_rowconfigure(0, weight=1)

        # --- Left Side: Preview Panel ---
        preview_frame = ctk.CTkFrame(parent_frame)
        preview_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Bind the resize event of the frame to our handler function
        preview_frame.bind("<Configure>", self.on_preview_resize)

        self.preview_label = ctk.CTkLabel(preview_frame, text="Load an image or folder to begin", text_color="gray")
        self.preview_label.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Right Side: Controls Panel ---
        controls_frame = ctk.CTkFrame(parent_frame)
        controls_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")

        # --- File Loading Controls ---
        load_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        load_frame.pack(fill="x", padx=10, pady=10)
        load_frame.grid_columnconfigure((0, 1), weight=1)

        load_image_button = ctk.CTkButton(load_frame, text="Load Image", command=self.load_single_image)
        load_image_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        load_folder_button = ctk.CTkButton(load_frame, text="Load Folder", command=self.load_batch_folder)
        load_folder_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # --- Adjustment Controls ---
        ctk.CTkLabel(controls_frame, text="Brightness").pack(padx=10, anchor="w")
        self.brightness_slider = ctk.CTkSlider(controls_frame, from_=0.1, to=2.0, command=self.update_preview)
        self.brightness_slider.set(1.0)
        self.brightness_slider.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(controls_frame, text="Contrast").pack(padx=10, anchor="w")
        self.contrast_slider = ctk.CTkSlider(controls_frame, from_=0.1, to=2.0, command=self.update_preview)
        self.contrast_slider.set(1.0)
        self.contrast_slider.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(controls_frame, text="Saturation").pack(padx=10, anchor="w")
        self.saturation_slider = ctk.CTkSlider(controls_frame, from_=0.0, to=2.0, command=self.update_preview)
        self.saturation_slider.set(1.0)
        self.saturation_slider.pack(fill="x", padx=10, pady=(0, 20))

        # --- Resizing Controls ---
        ctk.CTkLabel(controls_frame, text="Resize (pixels)", font=ctk.CTkFont(weight="bold")).pack(padx=10,
                                                                                                   pady=(10, 5),
                                                                                                   anchor="w")
        resize_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        resize_frame.pack(fill="x", padx=10)
        resize_frame.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(resize_frame, text="W:").grid(row=0, column=0, padx=(0, 5))
        self.width_entry = ctk.CTkEntry(resize_frame, placeholder_text="auto")
        self.width_entry.grid(row=0, column=1, sticky="ew")
        self.width_entry.bind("<KeyRelease>", self.update_preview)

        ctk.CTkLabel(resize_frame, text="H:").grid(row=0, column=2, padx=5)
        self.height_entry = ctk.CTkEntry(resize_frame, placeholder_text="auto")
        self.height_entry.grid(row=0, column=3, sticky="ew")
        self.height_entry.bind("<KeyRelease>", self.update_preview)

        aspect_checkbox = ctk.CTkCheckBox(controls_frame, text="Maintain aspect ratio", variable=self.aspect_ratio_var)
        aspect_checkbox.pack(padx=10, pady=5, anchor="w")

        # --- Action Buttons ---
        save_button = ctk.CTkButton(controls_frame, text="Save Single Image", command=self.save_single_image_action)
        save_button.pack(fill="x", padx=10, pady=(20, 5))

        reset_button = ctk.CTkButton(controls_frame, text="Reset Adjustments", command=self.reset_adjustments,
                                     fg_color="gray")
        reset_button.pack(fill="x", padx=10, pady=(5, 10))

    def load_single_image(self):
        """Opens a file dialog to select a single image and sets up the tool for single mode."""
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")])
        if not path: return

        self.mode = 'single'
        self.source_path = path
        self.original_pil_image = Image.open(path)

        self.app.log_to_textbox(f"Loaded single image: {os.path.basename(path)}")
        self.update_preview()

    def load_batch_folder(self):
        """Opens a directory dialog and sets up the tool for batch mode."""
        path = filedialog.askdirectory()
        if not path: return

        supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
        self.image_files_list = [os.path.join(path, f) for f in os.listdir(path) if
                                 f.lower().endswith(supported_formats)]

        if not self.image_files_list:
            self.app.log_to_textbox("No supported images found in the selected folder.")
            self.original_pil_image = None
            self.preview_label.configure(image=None, text="No images found in folder")
            return

        self.mode = 'batch'
        self.source_path = path
        self.original_pil_image = Image.open(self.image_files_list[0])  # Load first image for preview

        self.app.log_to_textbox(f"Loaded folder with {len(self.image_files_list)} images. Previewing first image.")
        self.update_preview()

    def update_preview(self, _=None):
        """Re-applies transformations to the original image and updates the UI preview."""
        if not self.original_pil_image: return

        processed_image = self._apply_transformations(self.original_pil_image, is_preview=True)

        container = self.preview_label.master
        panel_width, panel_height = container.winfo_width(), container.winfo_height()

        if panel_width < 2 or panel_height < 2: return  # Avoid error if panel is not yet drawn

        display_image = processed_image.copy()
        display_image.thumbnail((panel_width - 20, panel_height - 20), Image.Resampling.LANCZOS)

        self.preview_tk_image = ImageTk.PhotoImage(display_image)
        self.preview_label.configure(image=self.preview_tk_image, text="")

    def reset_adjustments(self):
        """Resets all UI controls to their default values and updates the preview."""
        self.brightness_slider.set(1.0)
        self.contrast_slider.set(1.0)
        self.saturation_slider.set(1.0)
        self.width_entry.delete(0, 'end')
        self.height_entry.delete(0, 'end')
        self.aspect_ratio_var.set(True)
        self.update_preview()

    def run(self, _, progress_callback, log_callback):
        """
        The main processing logic triggered by the app's 'Start Batch Processing' button.
        This method is now dedicated exclusively to BATCH processing.
        """
        if self.mode != 'batch':
            log_callback("Error: The 'Start' button is for batch processing only.")
            log_callback("To save a single file, use the 'Save Single Image' button.")
            return

        self.process_batch(progress_callback, log_callback)

    def _apply_transformations(self, pil_image, is_preview=False):
        """Helper function to apply all current settings to a given PIL image."""
        img = pil_image.copy()

        img = ImageEnhance.Brightness(img).enhance(self.brightness_slider.get())
        img = ImageEnhance.Contrast(img).enhance(self.contrast_slider.get())
        img = ImageEnhance.Color(img).enhance(self.saturation_slider.get())

        try:
            w_str, h_str = self.width_entry.get(), self.height_entry.get()
            target_w = int(w_str) if w_str else None
            target_h = int(h_str) if h_str else None

            if target_w or target_h:
                if self.aspect_ratio_var.get():
                    img.thumbnail((target_w or 9999, target_h or 9999), Image.Resampling.LANCZOS)
                else:
                    new_size = (target_w or img.width, target_h or img.height)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
        except ValueError:
            if not is_preview:
                self.app.log_to_textbox("Warning: Invalid resize values. Skipping resize step.")

        return img

    def save_single_image_action(self):
        """Action for the tool's 'Save Single Image' button."""
        if self.mode != 'single' or not self.original_pil_image:
            self.app.log_to_textbox("Error: Please load a single image first.")
            return

        self.process_single_image(self.app.log_to_textbox)

    def process_single_image(self, log_callback):
        """Handles the logic for saving a single processed image."""
        log_callback("Processing single image...")
        processed_image = self._apply_transformations(self.original_pil_image)

        initial_name = os.path.basename(self.source_path)
        name, ext = os.path.splitext(initial_name)
        save_path = filedialog.asksaveasfilename(
            initialfile=f"{name}_edited{ext}",
            defaultextension=ext,
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("All Files", "*.*")]
        )
        if not save_path:
            log_callback("Save cancelled.")
            return

        processed_image.save(save_path)
        log_callback(f"Successfully saved image to: {save_path}")

    def process_batch(self, progress_callback, log_callback):
        """Handles processing a whole folder of images."""
        total_files = len(self.image_files_list)
        log_callback(f"Starting batch processing for {total_files} images...")

        output_folder = os.path.join(self.source_path, "processed_output")
        os.makedirs(output_folder, exist_ok=True)
        log_callback(f"Saving processed files to: {output_folder}")

        for i, image_path in enumerate(self.image_files_list):
            try:
                with Image.open(image_path) as img:
                    log_callback(f"Processing '{os.path.basename(image_path)}'...")
                    processed_image = self._apply_transformations(img)
                    save_name = os.path.basename(image_path)
                    processed_image.save(os.path.join(output_folder, save_name))
            except Exception as e:
                log_callback(f"Failed to process {os.path.basename(image_path)}: {e}")

            progress = int(((i + 1) / total_files) * 100)
            progress_callback(progress)

        log_callback("Batch processing complete!")