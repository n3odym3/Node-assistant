import tkinter as tk
from tkinter import filedialog
import dearpygui.dearpygui as dpg
import os

from core.window_base import WindowBase
from core.input_ouput_types import IOTypes

class File_browser_win(WindowBase):
	"""
	A simple DearPyGui window that allows the user to browse and select
	a file or a folder, and then propagates the selected path downstream.

	Features:
	- UI combo box to select between file/folder mode
	- File/folder browsing using native Tkinter dialogs
	- Propagation of selected path to all outputs
	"""

	def __init__(self,
				label="File browser",
				win_width=300,
				win_height=200,
				pos=(10, 10),
				outputs=None,
				uuid=None,
				visible=True):

		super().__init__(label=label, pos=pos, win_width=win_width, win_height=win_height, uuid=uuid, outputs=outputs, visible=visible)

		# Persistent fields saved in layouts
		self._persistent_fields = ["label"]

		self.accepted_input_types = [IOTypes.TRIGGER]
		self.outputs = {
			"File" : IOTypes.FILE_PATH,
			"Folder" : IOTypes.FOLDER_PATH
		}
		self.connections = {k: [] for k in self.outputs}

		# UI element tag
		self.browser_type_tag = f"browser_type_tag{self.UUID}"

		# Build window content
		with dpg.window(label=self.label, width=self.win_width, height=self.win_height,
			pos=self.pos, tag=self.winID, show=self.visible):

			dpg.add_text("Select a file or folder")

			dpg.add_combo(
				items=["file", "folder"],
				label="Browser Type",
				default_value="file",
				tag=self.browser_type_tag,
		)

			dpg.add_button(label="Browse", callback=self.trigger_cb)

	def input_cb(self, *args, **kwargs):
		"""
		Handles trigger-type inputs. If a path is provided via kwargs or args,
		it will be used as the starting directory. Otherwise, default browsing is triggered.
		"""
		path = kwargs.get("path") or (args[0] if args else None)

		if path and isinstance(path, str) and os.path.exists(path):
			if os.path.isdir(path):
				self.trigger_cb(initial_path=path)
			else:
				self.trigger_cb(initial_path=os.path.dirname(path))
		else:
			self.trigger_cb()

	def format_filetypes(self, ext_list):
		"""
		Helper to create filetype filter list for file dialogs.
		Example: ['png', 'tif'] -> [('Files', '*.png *.tif')]
		"""
		pattern = " ".join([f"*.{ext}" for ext in ext_list])
		return [("Files", pattern)]

	def browse_file(self, default_folder=None, filetypes=None):
		"""
		Opens a file selection dialog.
		Returns the selected file path as a string.
		"""
		root = tk.Tk()
		root.withdraw()

		if isinstance(filetypes, list):
			ft = self.format_filetypes(filetypes)
		else:
			ft = [("All files", "*.*")]

		return filedialog.askopenfilename(
			title="Select File",
			initialdir=default_folder or ".",
			filetypes=ft,
		)

	def browse_folder(self, default_folder=None):
		"""
		Opens a folder selection dialog.
		Returns the selected folder path as a string.
		"""
		root = tk.Tk()
		root.withdraw()
		root.call('wm', 'attributes', '.', '-topmost', True)

		return filedialog.askdirectory(
			title="Select Folder",
			initialdir=default_folder or ".",
		)
	
	def trigger_cb(self, *args, **kwargs):
		"""
		Opens a file or folder browser depending on the selected mode,
		then propagates the selected path to connected outputs.
		Routing is based on output index.
		"""
		browser_type = dpg.get_value(self.browser_type_tag)
		initial_path = kwargs.get("initial_path", None)
		path = None

		if browser_type == "file":
			path = self.browse_file(default_folder=initial_path)
		elif browser_type == "folder":
			path = self.browse_folder(default_folder=initial_path)

		if path:
			# Utiliser les index de sortie pour router correctement
			output_keys = list(self.outputs.keys())

			for idx, output_key in enumerate(output_keys):
				for module in self.connections.get(output_key, []):
						if browser_type == "file" and idx == 0:
							module.input_cb(path)
						elif browser_type == "folder" and idx == 1:
							module.input_cb(path)

EXPORTED_CLASS = File_browser_win
EXPORTED_NAME = "File browser"
