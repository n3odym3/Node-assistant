import dearpygui.dearpygui as dpg
import numpy as np
import threading
import time
import cv2
import os

from core.window_base import WindowBase
from modules.image_viewer.clipboard_injector import clipboardinjector
from core.input_ouput_types import IOTypes


class Image_viewer_win(WindowBase):
	"""
	Image_viewer_win:
	A DearPyGui-based modular window to display images with support for:
	- grayscale rescaling
	- color palette application
	- FPS measurement
	- annotated scale overlay
	- clipboard/image export
	- input handling from various sources (file, folder, ndarray)
	"""

	def __init__(self,
				label="Image Viewer",
				win_width=1280,
				win_height=900,
				pos=(100, 100),
				uuid=None,
				outputs=None,
				visible=True,
				colorize=True,
				intensity_rescaling=True,
				fps_counter=True,
				image_export=True,
				image_depth="12bit"):

		super().__init__(label=label, pos=pos, win_width=win_width, win_height=win_height,
			uuid=uuid, outputs=outputs or [], visible=visible)

		# FPS tracking
		self.fps = 0
		self.now = time.time()
		self.last = self.now

		# Lock for threaded updates
		self.lock = threading.Lock()

		# Last image reference
		self.last_image = None

		# Display options
		self.negative = False
		self.palette = "Inferno"
		self.imgcount = 0

		# Texture state
		self.texture_width = 0
		self.texture_height = 0

		# DPG element tags
		self.texture_tag = f"viewer_texture_{self.UUID}"
		self.plot_tag = f"viewer_plot_{self.UUID}"
		self.fps_tag = f"viewer_fps_{self.UUID}"
		self.name_tag = f"viewer_name_{self.UUID}"
		self.count_tag = f"viewer_count_{self.UUID}"
		self.save_btn = f"viewer_save_{self.UUID}"
		self.auto_remap_tag = f"viewer_autoremap_{self.UUID}"
		self.inf_tag = f"viewer_inf_{self.UUID}"
		self.sup_tag = f"viewer_sup_{self.UUID}"

		# Config flags
		self.colorize = colorize
		self.intensity_rescaling = intensity_rescaling
		self.fps_counter = fps_counter
		self.image_export = image_export
		self.image_depth = image_depth

		# Persistence and IO setup
		self._persistent_fields = [
			"label", "colorize", "intensity_rescaling",
			"fps_counter", "image_export", "image_depth"
		]
		self.accepted_input_types = [IOTypes.FRAME, IOTypes.FILE_PATH]
		self.output_types = [IOTypes.FRAME]

		self.outputs = {
			"Frame" : IOTypes.FRAME
		}
		self.connections = {k: [] for k in self.outputs}

		self._build_interface(win_width, win_height, pos)

	def _build_interface(self, win_width, win_height, pos):
		"""Creates the DearPyGui layout."""
		with dpg.window(label=self.label, width=win_width, height=win_height,
			pos=pos, tag=self.winID, show=self.visible):

			with dpg.group(horizontal=True):
				if self.colorize:
					dpg.add_combo(("Normal", "Negative"), width=120, default_value="Normal", callback=self.set_mode)
					dpg.add_combo(("B&W", "Inferno", "Jet", "HSV"), width=120, default_value=self.palette, callback=self.set_mode)

				if self.intensity_rescaling:
					dpg.add_text("Auto:")
					dpg.add_checkbox(default_value=True, tag=self.auto_remap_tag, callback=self.update_image_callback)
					dpg.add_text("Inf:")
					dpg.add_drag_int(default_value=0, min_value=0, max_value=255, width=100, tag=self.inf_tag, callback=self.update_image_callback)
					dpg.add_text("Sup:")
					dpg.add_drag_int(default_value=255, min_value=0, max_value=255, width=100, tag=self.sup_tag, callback=self.update_image_callback)

				if self.fps_counter:
					dpg.add_text("| FPS:")
					dpg.add_text("0", tag=self.fps_tag)

			if self.image_export:
				with dpg.group(horizontal=True):
					dpg.add_button(label="Clipboard", callback=self.copy_to_clipboard)
					dpg.add_input_text(default_value="Image", width=150, tag=self.name_tag, callback=self.reset_counter)
					dpg.add_text("count: 0", tag=self.count_tag)
					dpg.add_button(label="Save", tag=self.save_btn, callback=self.save_image)

			self.init_viewer(1000, 1000)

	def input_cb(self, *args, **kwargs):
		"""Receives and processes image input from args or kwargs (supports ndarray or filepath)."""
		frame = kwargs["data"] if "data" in kwargs else (args[0] if args else None) #Numpy compatible evaluation

		if isinstance(frame, str) and os.path.exists(frame):
			frame = cv2.imread(frame, cv2.IMREAD_UNCHANGED)
			if frame is not None and frame.ndim == 3 and frame.shape[2] == 3:
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		if isinstance(frame, np.ndarray):
			self.update_image(frame)

	def convert_to_lowdepth(self, frame: np.ndarray) -> np.ndarray:
		"""Converts high bit-depth image to 8-bit based on image_depth."""
		match self.image_depth:
			case "8bit":
				return frame
			case "12bit":
				return (frame >> 4).astype(np.uint8)
			case "16bit_norm":
				return cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
			case "16bit_abs":
				return (frame >> 8).astype(np.uint8)

	def get_minmax_values(self, frame: np.ndarray) -> tuple[int, int]:
		"""Returns min and max intensity values from non-zero pixels."""
		non_zero = frame[frame > 0]
		min_val = np.min(non_zero) if non_zero.size else 0
		match self.image_depth:
			case "8bit":
				max_val = np.max(non_zero) if non_zero.size else 255
			case "12bit":
				max_val = np.max(non_zero) if non_zero.size else 4096
			case _:
				max_val = np.max(non_zero) if non_zero.size else 65535
		return min_val, max_val

	def remap_pixel_intensity(self, frame: np.ndarray, low: float, high: float) -> np.ndarray:
		"""Normalizes frame between [low, high] and scales to 8-bit."""
		normalized = np.clip((frame.astype(np.float32) - low) / (high - low), 0, 1)
		return (normalized * 255).astype(np.uint8)

	def add_intensity_scale(self, img: np.ndarray, scale_width=30, position='left') -> np.ndarray:
		"""Adds vertical or horizontal intensity scale bar to image."""
		h = img.shape[0]
		gradient = np.linspace(255, 0, h).reshape((h, 1)).astype(np.uint8)
		scale = np.tile(gradient, (1, scale_width))
		overlay = img.copy()

		match position:
			case 'right': overlay[:, -scale_width:] = scale
			case 'left': overlay[:, :scale_width] = scale
			case 'top': overlay[:scale_width, :] = scale.T
			case 'bottom': overlay[-scale_width:, :] = scale.T

		return overlay

	def calc_fps(self) -> float:
		"""Computes current FPS from timestamps."""
		self.now = time.time()
		delta = self.now - self.last
		if delta > 0:
			self.fps = 1 / delta
			self.last = self.now
		return self.fps

	def convert_to_texture(self, frame: np.ndarray) -> list:
		"""Converts 3-channel image to flattened RGB float array for DearPyGui."""
		return (np.flip(frame, 2).ravel() / 255.0).astype('f')

	def init_viewer(self, width: int, height: int):
		"""Initializes DearPyGui image display area."""
		if dpg.does_item_exist(self.texture_tag):
			dpg.delete_item(self.texture_tag)
		if dpg.does_item_exist(self.plot_tag):
			dpg.delete_item(self.plot_tag)

		default_img = np.zeros((height, width, 3), dtype=np.uint8)
		texture = self.convert_to_texture(default_img)

		dpg.push_container_stack(self.winID)
		with dpg.plot(tag=self.plot_tag, no_menus=True, no_title=True, width=-1, height=-1):
			with dpg.texture_registry(show=False):
				dpg.add_raw_texture(width, height, default_value=texture, tag=self.texture_tag, format=dpg.mvFormat_Float_rgb)
			dpg.add_plot_legend()
			dpg.add_plot_axis(dpg.mvXAxis, no_gridlines=True, no_tick_labels=True, no_tick_marks=True)
			with dpg.plot_axis(dpg.mvYAxis, no_gridlines=True, no_tick_labels=True, no_tick_marks=True):
				dpg.add_image_series(self.texture_tag, [0, 0], [width, height])
		dpg.pop_container_stack()
		self.texture_width = width
		self.texture_height = height

	def colorize_frame(self, frame: np.ndarray) -> np.ndarray:
		"""Applies negative or colormap to the 8-bit image."""
		if self.negative:
			frame = 255 - frame
		match self.palette:
			case 'B&W': return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
			case 'Inferno': return cv2.applyColorMap(frame, cv2.COLORMAP_INFERNO)
			case 'Jet': return cv2.applyColorMap(frame, cv2.COLORMAP_JET)
			case 'HSV': return cv2.applyColorMap(frame, cv2.COLORMAP_HSV)
		return frame

	def remap_and_annotate(self, frame, min_val=None, max_val=None):
		"""Remaps intensities, adds scale bar and min/max text."""
		if dpg.get_value(self.auto_remap_tag):
			min_val = np.percentile(frame, 1)
			max_val = np.percentile(frame, 100)
			dpg.set_value(self.sup_tag, max_val)

		frame = self.remap_pixel_intensity(frame, dpg.get_value(self.inf_tag), dpg.get_value(self.sup_tag))
		frame = self.add_intensity_scale(frame)

		if min_val is None or max_val is None:
			min_val, max_val = self.get_minmax_values(frame)

		frame = self.colorize_frame(frame)
		cv2.putText(frame, f"{max_val:.0f}", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
		cv2.putText(frame, f"{min_val:.0f}", (30, frame.shape[0]-15), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

		return frame

	def process_lowdepth(self, frame, min_val=None, max_val=None, mask=None):
		"""Processes image before rendering and adds overlay if mask is provided."""
		frame = self.remap_and_annotate(frame, min_val, max_val)
		if mask is not None:
			frame[mask] = [0, 0, 255]
		return frame

	def update_image(self, frame):
		"""Triggers image display update in a background thread."""
		self.last_image = frame
		lowdepth = self.convert_to_lowdepth(self.last_image)

		if frame is not None and not self.lock.locked():
			def task():
				with self.lock:
					if frame.shape[0] != self.texture_height or frame.shape[1] != self.texture_width:
						self.init_viewer(frame.shape[1], frame.shape[0])

					minval, maxval = self.get_minmax_values(frame)
					processed = self.process_lowdepth(lowdepth, minval, maxval)
					texture = self.convert_to_texture(processed)
					dpg.set_value(self.texture_tag, texture)
					dpg.set_value(self.fps_tag, str(int(self.calc_fps())))
			threading.Thread(target=task).start()

	def update_image_callback(self):
		"""Callback to trigger update from UI."""
		self.update_image(self.last_image)

	def set_mode(self, sender, app_data):
		"""Handles UI mode changes (negative toggle or palette switch)."""
		if app_data in ["Normal", "Negative"]:
			self.negative = (app_data == "Negative")
		else:
			self.palette = app_data
		self.update_image(self.last_image)

	def copy_to_clipboard(self):
		"""Copies the processed image to clipboard using the custom injector."""
		if self.last_image is not None:
			minval, maxval = self.get_minmax_values(self.last_image)
			lowdepth = self.convert_to_lowdepth(self.last_image)
			image = self.remap_and_annotate(lowdepth, minval, maxval)
			clipboardinjector.send_image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

	def save_image(self):
		"""Saves both raw and processed images to PNG with indexed names."""
		if self.last_image is not None:
			minval, maxval = self.get_minmax_values(self.last_image)
			raw = self.last_image
			lowdepth = self.convert_to_lowdepth(raw)
			processed = self.remap_and_annotate(lowdepth, minval, maxval)

			name = dpg.get_value(self.name_tag)
			cv2.imwrite(f"{name}_RAW_{self.imgcount}.png", raw)
			cv2.imwrite(f"{name}_Processed_{self.imgcount}.png", processed)

			dpg.set_value(self.count_tag, f"count : {self.imgcount}")
			self.imgcount += 1

	def reset_counter(self):
		"""Resets the saved image counter to zero."""
		self.imgcount = 0
		dpg.set_value(self.count_tag, f"count: {self.imgcount}")


EXPORTED_CLASS = Image_viewer_win
EXPORTED_NAME = "Image Viewer"
