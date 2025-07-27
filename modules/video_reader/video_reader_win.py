import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes
from modules.video_reader.video_tools import video
from modules.video_reader.folder_tools import folder_tools
import threading, os, time
from loguru import logger

class VideoReader_win(WindowBase):
	def __init__(self,
				label="Video Reader",
				win_width=300,
				win_height=200,
				pos=(10, 10),
				uuid=None,
				outputs=None,
				visible=True):

		super().__init__(label=label,pos=pos,win_width=win_width,win_height=win_height,uuid=uuid,outputs=outputs,visible=visible)

		self._persistent_fields = ["label"]
		self.accepted_input_types = [IOTypes.FOLDER_PATH, IOTypes.FILE_PATH]

		self.outputs = {
			"Frame": IOTypes.FRAME,
			"Trigger": IOTypes.TRIGGER,
		}
		self.connections = {k: [] for k in self.outputs}

		self.winID = f"video_reader_win_{self.UUID}"
		self.table_tag = f"video_reader_table_{self.UUID}"
		self.child_win_table_tag = f"video_reader_child_table_{self.UUID}"
		self.fps_tag = f"video_reader_fps_{self.UUID}"
		self.start_tag = f"video_reader_start_{self.UUID}"
		self.stop_tag = f"video_reader_stop_{self.UUID}"
		self.video_group_tag = f"video_reader_group_{self.UUID}"

		self.last_selectable = None
		self.last_video_selected = None
		self.enabled = False
		self.folder = ""

		self.currentvid = 0
		self.video_running = False
		self.video_thread = None

		self.path_index = 0
		self.video_keys = []  # ordered list of video base names
		self.videos = {}      # dict: base_name -> {path, data}

		self.playback_fps = 30  # default value
		self.frame_interval = 1.0 / self.playback_fps

		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):

			with dpg.group(horizontal=True):
				dpg.add_button(label="START", tag=self.start_tag, callback=self.start_video)
				dpg.add_button(label="STOP", tag=self.stop_tag, callback=lambda s, a: setattr(self, "video_running", False))
				dpg.add_input_int(label="FPS", tag=self.fps_tag, default_value=30, min_value=1, min_clamped=True, width=-1, callback=self.set_playback_fps)

			with dpg.group(tag=self.video_group_tag):
				with dpg.child_window(tag=self.child_win_table_tag):
					with dpg.table(header_row=True, resizable=True, tag=self.table_tag):
						dpg.add_table_column(label="Filename")

	def update_file_list(self, path):
		self.last_selectable = None
		self.last_video_selected = None

		filepaths, filenames = folder_tools.list_files(path, file_extension="mp4", sort_by="name")
		self.videos = {name: {"path": fp} for name, fp in zip(filenames, filepaths)}
		self.video_keys = list(self.videos.keys())

		dpg.delete_item(self.child_win_table_tag)

		dpg.push_container_stack(self.video_group_tag)
		with dpg.child_window(tag=self.child_win_table_tag):
			with dpg.table(header_row=True, resizable=True, tag=self.table_tag,
						borders_innerH=True, borders_innerV=True,
						borders_outerH=True, borders_outerV=True,
						row_background=True, policy=dpg.mvTable_SizingStretchProp):

				dpg.add_table_column(label="Name")

				for i, name in enumerate(self.video_keys):
					with dpg.table_row():
						dpg.add_selectable(label=name, callback=self.on_row_click, user_data=i)
		
		dpg.pop_container_stack()

	def on_row_click(self, sender, app_data, user_data):
		if self.last_selectable is not None:
			dpg.set_value(self.last_selectable, False)

		self.last_selectable = sender
		name = self.video_keys[user_data]
		self.last_video_selected = self.videos[name]["path"]
		self.frame_cb(frame=video.read_first_frame(self.last_video_selected))

	def play_loop(self):
		next_frame_time = time.perf_counter()

		while self.video_running:
			if not self.is_outputs_ready():
				time.sleep(0.001)
				continue

			now = time.perf_counter()
			if now < next_frame_time:
				time.sleep(next_frame_time - now)
				continue

			ret, frame = video.read()
			if not ret:
				break
			if frame is not None:
				self.frame_cb(frame=frame)

			frame_interval = self.frame_interval
			next_frame_time += frame_interval

			if next_frame_time < time.perf_counter():
				next_frame_time = time.perf_counter()

		self.trigger_cb(event="STOP")
		self.video_running = False
		self.video_thread = None

	def start_video(self):
		if not self.last_video_selected:
			logger.warning(f"{self.winID} No video selected to play.")
			return

		self.trigger_cb(event="START")
		video.set_video(self.last_video_selected)
		self.video_running = True

		if self.video_thread is None or not self.video_thread.is_alive():
			self.video_thread = threading.Thread(target=self.play_loop, daemon=True)
			self.video_thread.start()

	def set_playback_fps(self, sender, app_data):
		self.playback_fps = app_data
		self.frame_interval = 1.0 / max(1, self.playback_fps)

	def input_cb(self, *args, **kwargs):
		path = kwargs.get("data") or (args[0] if args else None)
		if isinstance(path, str) and os.path.isdir(path):
			self.folder = path
			self.update_file_list(path)
			self.enabled = True
			self.video_running = False
			self.processing_required = False
			self.processing_running = False

	def frame_cb(self,frame):
		"""Sends the last known status as STATUS_DICT to all outputs."""
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				if idx == 0:
					module.input_cb(data=frame)

	def trigger_cb(self, event = None):
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				if idx == 1:
					module.input_cb(event)

EXPORTED_CLASS = VideoReader_win
EXPORTED_NAME = "Video Reader"
