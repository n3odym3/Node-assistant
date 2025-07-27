import dearpygui.dearpygui as dpg
import numpy as np
import threading
from queue import Queue
import cv2

from core.window_base import WindowBase
from core.input_ouput_types import IOTypes
from modules.video_reader.fps_counter import FPSCounter

class Video_viewer_win(WindowBase):
	def __init__(self,
				label="Video Viewer",
				win_width=800,
				win_height=600,
				pos=(100, 100),
				uuid=None,
				outputs=None,
				visible=True,
				fps_counter=True):

		super().__init__(label=label, pos=pos, win_width=win_width, win_height=win_height,
			uuid=uuid, outputs=outputs or [], visible=visible)

		self.texture_tag = f"video_viewer_texture_{self.UUID}"
		self.plot_tag = f"video_viewer_plot_{self.UUID}"
		self.texture_width = 0
		self.texture_height = 0
		self.lock = threading.Lock()

		# FPS tracking
		self.fps_counter = fps_counter
		self.fps_display_tag = f"video_viewer_display_fps_{self.UUID}"
		self.fps_read_tag = f"video_viewer_read_fps_{self.UUID}"
		
		self.display_fps_counter = FPSCounter(smoothing_window=10)
		self.read_fps_counter = FPSCounter(smoothing_window=10)

		self.accepted_input_types = [IOTypes.FRAME, IOTypes.MASK]
		self.outputs = {
			"Frame": IOTypes.FRAME,
			"Mask": IOTypes.MASK
		}
		self.connections = {k: [] for k in self.outputs}

		self._build_interface(win_width, win_height, pos)

		# Frame queue and render thread
		self.frame_queue = Queue(maxsize=1)
		self.worker_thread = threading.Thread(target=self._render_loop, daemon=True)
		self.worker_thread.start()

	def _build_interface(self, width, height, pos):
		with dpg.window(label=self.label, width=width, height=height, pos=pos, tag=self.winID, show=self.visible):
			if self.fps_counter:
				with dpg.group(horizontal=True):
					dpg.add_text("Read FPS: ")
					dpg.add_text("0", tag=self.fps_read_tag)
					dpg.add_text("Display FPS: ")
					dpg.add_text("0", tag=self.fps_display_tag)
			self.init_viewer(1280, 720)

	def update_image(self, frame):
		dpg.set_value(self.fps_read_tag, f"{self.read_fps_counter.get_fps()[1]:.1f}")
		if frame is None:
			return

		try:
			self.frame_queue.put_nowait(frame)
		except:
			pass

	def _render_loop(self):
		while True:
			frame = self.frame_queue.get()
			self._update_texture(frame)

	def _update_texture(self, frame):
		h, w = frame.shape[:2]
		if h != self.texture_height or w != self.texture_width:
			self.init_viewer(w, h)

		texture_data = self.convert_to_texture(frame)
		dpg.set_value(self.texture_tag, texture_data)
		dpg.set_value(self.fps_display_tag, f"{self.display_fps_counter.get_fps()[1]:.1f}")

	def convert_to_texture(self, frame: np.ndarray) -> np.ndarray:
		rgb_frame = frame[..., ::-1]  # BGR to RGB (no copy)
		return (rgb_frame.astype(np.float32) / 255.0).flatten()

	def init_viewer(self, width, height):
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

	def input_cb(self, *args, **kwargs):
		frame = kwargs.get("data") if "data" in kwargs else (args[0] if args else None)

		if frame is not None and (len(frame.shape) == 2 or (len(frame.shape) == 3 and frame.shape[2] == 1)):
			frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

		self.update_image(frame)


EXPORTED_CLASS = Video_viewer_win
EXPORTED_NAME = "Video Viewer"
