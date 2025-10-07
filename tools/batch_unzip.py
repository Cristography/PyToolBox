# tools/batch_unzip.py
import os
import zipfile
import customtkinter as ctk
from .tool_base import ToolBase


class BatchUnzipper(ToolBase):
    def __init__(self, app):
        super().__init__(app)
        # We need to store the state of our checkboxes
        self.delete_zip_var = ctk.BooleanVar(value=False)
        self.subfolder_var = ctk.BooleanVar(value=True)

    @property
    def name(self) -> str:
        return "Batch Unzipper"

    def create_ui(self, parent_frame):
        """Creates the UI for the Batch Unzipper."""
        label = ctk.CTkLabel(parent_frame, text="This tool finds and extracts all .zip files in a folder.")
        label.pack(pady=10, padx=10, anchor="w")

        subfolder_checkbox = ctk.CTkCheckBox(parent_frame,
                                             text="Extract each zip into its own subfolder",
                                             variable=self.subfolder_var)
        subfolder_checkbox.pack(pady=5, padx=20, anchor="w")

        delete_checkbox = ctk.CTkCheckBox(parent_frame,
                                          text="Delete original .zip file after successful extraction",
                                          variable=self.delete_zip_var)
        delete_checkbox.pack(pady=5, padx=20, anchor="w")

    def run(self, folder_path: str, progress_callback, log_callback):
        """The logic for unzipping files."""
        should_delete = self.delete_zip_var.get()
        use_subfolder = self.subfolder_var.get()

        try:
            # Find all zip files, case-insensitively
            zip_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.zip')]

            if not zip_files:
                log_callback("No .zip files found in the selected folder.")
                return

            total_files = len(zip_files)
            log_callback(f"Found {total_files} zip file(s) to extract.")

            for i, filename in enumerate(zip_files):
                zip_path = os.path.join(folder_path, filename)

                # Determine the extraction path
                if use_subfolder:
                    # Create a folder named after the zip file (e.g., 'archive.zip' -> 'archive/')
                    subfolder_name = os.path.splitext(filename)[0]
                    extract_path = os.path.join(folder_path, subfolder_name)
                    os.makedirs(extract_path, exist_ok=True)
                else:
                    extract_path = folder_path

                log_callback(f"Extracting '{filename}' to '{os.path.basename(extract_path)}/'...")

                # Extract the zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)

                # Optionally delete the original zip
                if should_delete:
                    os.remove(zip_path)
                    log_callback(f"Deleted '{filename}'.")

                # Update progress
                progress = int(((i + 1) / total_files) * 100)
                progress_callback(progress)

            log_callback("Batch extraction complete!")

        except Exception as e:
            log_callback(f"An error occurred: {e}")