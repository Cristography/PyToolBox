# tools/tool_base.py
from abc import ABC, abstractmethod

class ToolBase(ABC):
    """Abstract base class for all tools."""

    def __init__(self, app):
        self.app = app

    # --- NEW PROPERTY ---
    @property
    def requires_global_folder(self) -> bool:
        """
        If True, the main 'Start Processing' button will require a folder to be selected.
        If False, the tool is responsible for its own data input (e.g., its own buttons).
        """
        return True # Default to True for simple batch tools

    @property
    @abstractmethod
    def name(self) -> str:
        """The display name of the tool."""
        pass

    @abstractmethod
    def create_ui(self, parent_frame):
        """Creates the tool-specific UI widgets inside the parent_frame."""
        pass

    @abstractmethod
    def run(self, folder_path: str, progress_callback, log_callback):
        """The core logic of the tool, to be run in a separate thread."""
        pass