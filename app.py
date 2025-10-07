# app.py
"""
The main application class for PyToolBox.
This file is responsible for creating the main window, loading all the tools,
managing the UI layout, and handling the execution of tool logic in a
separate thread to keep the GUI responsive.
"""

import os
import customtkinter as ctk
from tkinter import filedialog
import threading

# --- Import all available tools from the 'tools' package ---
# This is the central place to register new tools.
from tools.batch_rename import BatchRenamer
from tools.batch_unzip import BatchUnzipper
from tools.image_adjuster import ImageAdjuster

# --- Global Application Settings ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Configuration ---
        self.title("PyToolBox")
        self.geometry("1000x700")  # A larger size for the image processor

        # --- Configure Grid Layout ---
        # Column 0 for sidebar, Column 1 for main content (expands).
        self.grid_columnconfigure(1, weight=1)
        # Row 0 for tool frame (expands), Row 4 for log box (expands).
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # --- Sidebar Frame ---
        self.sidebar_frame = ctk.CTkFrame(self, width=150, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=5, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)  # Pushes buttons to the top

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="PyToolBox", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- Tool Frame (Main Content Area) ---
        self.tool_frame = ctk.CTkFrame(self, corner_radius=5)
        self.tool_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # --- Common Controls (Below Tool Frame) ---
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=1, padx=20, pady=(0, 10), sticky="ew")

        self.folder_path_var = ctk.StringVar(value="No folder selected")
        self.folder_label = ctk.CTkLabel(self.controls_frame, textvariable=self.folder_path_var)
        self.folder_label.pack(side="left", padx=10, pady=5)

        self.select_folder_button = ctk.CTkButton(self.controls_frame, text="Select Folder", command=self.select_folder)
        self.select_folder_button.pack(side="right", padx=10, pady=5)

        self.start_button = ctk.CTkButton(self, text="Start Batch Processing", command=self.start_processing)
        self.start_button.grid(row=2, column=1, padx=20, pady=10, sticky="ew")

        # --- Progress Bar and Logging Textbox ---
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=3, column=1, padx=20, pady=(0, 5), sticky="ew")

        self.log_textbox = ctk.CTkTextbox(self, state="disabled")
        self.log_textbox.grid(row=4, column=1, padx=20, pady=(0, 20), sticky="nsew")

        # --- Tool Initialization and Registration ---
        # To add a new tool, import its class and add it to this dictionary.
        self.tools = {
            "Batch Renamer": BatchRenamer(self),
            "Batch Unzipper": BatchUnzipper(self),
            "Advanced Image Processor": ImageAdjuster(self),
        }
        self.current_tool = None
        self.create_tool_buttons()
        # Select a default tool to show on startup
        self.select_tool("Advanced Image Processor")

    def create_tool_buttons(self):
        """Dynamically creates buttons for each registered tool."""
        for i, name in enumerate(self.tools.keys()):
            button = ctk.CTkButton(self.sidebar_frame, text=name,
                                   command=lambda n=name: self.select_tool(n))
            button.grid(row=i + 1, column=0, padx=20, pady=10, sticky="ew")

    def select_tool(self, name: str):
        """Clears the tool frame and loads the UI for the selected tool."""
        # Clear the old tool's UI from the frame
        for widget in self.tool_frame.winfo_children():
            widget.destroy()

        self.current_tool = self.tools.get(name)
        if self.current_tool:
            # Tell the new tool to create its specific UI inside the frame
            self.current_tool.create_ui(self.tool_frame)
            self.log_to_textbox(f"Switched to '{name}'.")

    def select_folder(self):
        """Opens a dialog to select a folder and updates the label."""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path_var.set(folder)
            self.log_to_textbox(f"Selected folder: {folder}")

    def log_to_textbox(self, message: str):
        """Safely appends a message to the log textbox from any thread."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")  # Auto-scroll to the bottom

    def update_progress(self, value: int):
        """Updates the progress bar. Value should be 0-100."""
        self.progress_bar.set(value / 100)

    def start_processing(self):
        """Starts the processing logic for the currently selected tool."""
        if not self.current_tool:
            self.log_to_textbox("Error: No tool selected.")
            return

        folder_path = self.folder_path_var.get()

        # Check if the tool requires the global folder, and if so, validate it.
        # This allows tools like the Image Processor to bypass this check.
        if self.current_tool.requires_global_folder:
            if not os.path.isdir(folder_path):
                self.log_to_textbox("Error: Please select a valid folder for this tool.")
                return

        # Disable button to prevent multiple runs while processing
        self.start_button.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)

        # Run the tool's core logic in a separate thread to avoid freezing the GUI
        thread = threading.Thread(
            target=self.run_tool_thread,
            args=(self.current_tool, folder_path)
        )
        thread.daemon = True  # Allows the app to close even if the thread is running
        thread.start()

    def run_tool_thread(self, tool, folder_path: str):
        """
        Wrapper function that executes the tool's run method in a thread.
        It uses a try/finally block to ensure the GUI is re-enabled after completion.
        """
        try:
            # Pass thread-safe callbacks to the tool using `self.after`
            # This schedules the GUI updates to run on the main thread.
            tool.run(
                folder_path,
                progress_callback=lambda p: self.after(0, self.update_progress, p),
                log_callback=lambda m: self.after(0, self.log_to_textbox, m)
            )
        except Exception as e:
            # Log any unexpected errors from the tool's run method
            self.after(0, self.log_to_textbox, f"FATAL ERROR in tool '{tool.name}': {e}")
        finally:
            # This will always run, even if the tool crashes
            self.after(0, self.processing_finished)

    def processing_finished(self):
        """Resets the start button to its normal state."""
        self.start_button.configure(state="normal", text="Start Batch Processing")
        self.log_to_textbox("-----------------")