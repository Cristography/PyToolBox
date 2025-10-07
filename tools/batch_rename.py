# tools/batch_rename.py
import os
import re  # Import the regular expressions module
import customtkinter as ctk
from .tool_base import ToolBase


class BatchRenamer(ToolBase):
    def __init__(self, app):
        super().__init__(app)
        self.prefix_entry = None
        self.padding_entry = None
        self.start_number_entry = None

    @property
    def name(self) -> str:
        return "Batch Renamer"

    def create_ui(self, parent_frame):
        """Creates the enhanced UI for the Batch Renamer."""

        # --- Prefix Section ---
        prefix_label = ctk.CTkLabel(parent_frame, text="File Prefix:")
        prefix_label.pack(pady=(10, 2), padx=20, anchor="w")

        self.prefix_entry = ctk.CTkEntry(parent_frame, placeholder_text="e.g., 'vacation_2023_'")
        self.prefix_entry.pack(pady=(0, 10), padx=20, fill="x")

        # --- Numbering Options Section in a Frame ---
        options_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=10)
        options_frame.grid_columnconfigure((1, 3), weight=1)

        # --- Leading Zeros (Padding) ---
        padding_label = ctk.CTkLabel(options_frame, text="Digits (padding):")
        padding_label.grid(row=0, column=0, padx=(0, 5), sticky="w")

        self.padding_entry = ctk.CTkEntry(options_frame)
        self.padding_entry.insert(0, "4")  # Default to 4 digits
        self.padding_entry.grid(row=0, column=1, sticky="ew")

        # --- Start Number ---
        start_num_label = ctk.CTkLabel(options_frame, text="Start Number:")
        start_num_label.grid(row=0, column=2, padx=(15, 5), sticky="w")

        self.start_number_entry = ctk.CTkEntry(options_frame, placeholder_text="auto")
        self.start_number_entry.grid(row=0, column=3, sticky="ew")

        info_label = ctk.CTkLabel(parent_frame,
                                  text="Leave 'Start Number' blank to automatically continue from existing files with the same prefix.",
                                  wraplength=350, justify="left", text_color="gray")
        info_label.pack(padx=20, pady=10, anchor="w")

    def run(self, folder_path: str, progress_callback, log_callback):
        """The enhanced logic for renaming files with advanced options."""

        # --- 1. Get and Validate User Input ---
        prefix = self.prefix_entry.get()
        if not prefix:
            log_callback("Error: Prefix cannot be empty.")
            return

        try:
            padding = int(self.padding_entry.get())
            if padding < 1:
                log_callback("Error: Digits (padding) must be 1 or greater.")
                return
        except ValueError:
            log_callback("Error: Digits (padding) must be a valid number.")
            return

        start_num_str = self.start_number_entry.get()
        all_files_in_dir = os.listdir(folder_path)

        # --- 2. Determine the Starting Counter ---
        start_counter = 1

        if start_num_str:  # Manual start number provided
            try:
                start_counter = int(start_num_str)
                log_callback(f"Using manual start number: {start_counter}")
            except ValueError:
                log_callback("Error: Start Number is not a valid number. Aborting.")
                return
        else:  # Automatic mode: find the next number
            max_num = 0
            # Use regex to safely find files that match the "prefix + number" pattern
            # re.escape handles special characters in the prefix
            pattern = re.compile(f"^{re.escape(prefix)}(\d+)")

            for filename in all_files_in_dir:
                match = pattern.match(filename)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

            if max_num > 0:
                start_counter = max_num + 1
                log_callback(f"Detected existing files. Automatically continuing from number: {start_counter}")
            else:
                log_callback("No existing files with this prefix found. Starting from 1.")

        # --- 3. Filter Files That Need Renaming ---
        # We only want to rename files that DO NOT already start with the prefix
        files_to_rename = [f for f in all_files_in_dir
                           if os.path.isfile(os.path.join(folder_path, f)) and not f.startswith(prefix)]

        if not files_to_rename:
            log_callback("No files to rename. (Files may already have the correct prefix).")
            progress_callback(100)  # Show completion
            return

        total_files = len(files_to_rename)
        log_callback(f"Found {total_files} file(s) to rename.")

        # --- 4. The Main Renaming Loop ---
        for i, filename in enumerate(files_to_rename):
            _, extension = os.path.splitext(filename)

            # Dynamically create the format string for padding
            # e.g., if padding is 4, this becomes {:04d}
            number_format = f"{{:0{padding}d}}"

            # The current number is the starting counter plus the loop index
            current_number = start_counter + i

            # Build the new name
            new_name = f"{prefix}{number_format.format(current_number)}{extension}"

            source = os.path.join(folder_path, filename)
            destination = os.path.join(folder_path, new_name)

            try:
                os.rename(source, destination)
                log_callback(f"Renamed '{filename}' -> '{new_name}'")
            except Exception as e:
                log_callback(f"Error renaming '{filename}': {e}")

            # Update progress
            progress = int(((i + 1) / total_files) * 100)
            progress_callback(progress)

        log_callback("Batch renaming complete!")