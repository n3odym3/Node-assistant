import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes
import threading
from modules.computer_vision.tracker.tracker import Point_tracker
from modules.computer_vision.tracker.tracker_default_settings import DEFAULT_SETTINGS as DS

class Tracker_win(WindowBase):
	def __init__(self,
				label="Tracker",
				win_width=300,
				win_height=200,
				pos=(10, 10),
				uuid=None,
				outputs=None,
				visible=True):

		if outputs is None:
			outputs = []

		super().__init__(label=label, pos=pos, win_width=win_width, win_height=win_height, uuid=uuid, outputs=outputs, visible=visible)

		self._persistent_fields = ["label"]
		
		self.accepted_input_types = [IOTypes.POINT_LIST]

		self.outputs = {
			"Frame" : IOTypes.FRAME,
			"Tracking" : IOTypes.TRACKING,
		}
		self.connections = {k: [] for k in self.outputs}

		self.processor = Point_tracker(
			params={
				"trail_length": DS.TRAIL_LENGTH,
				"distance_function": DS.DISTANCE_FUNCTION, 
				"distance_threshold": DS.DISTANCE_TRESHOLD,
			},
			buffer_size=DS.BUFFER_SIZE,
			drop_policy=DS.DROP_POLICY
		)
		
		self.processor.start()

		self.trail_length_tag = f"tracker_trail_length{self.UUID}"
		self.trace_length_tag = f"tracker_trace_length_{self.UUID}"
		self.show_trail_tag = f"tracker_show_trail_{self.UUID}"
		self.show_id_tag = f"tracker_show_id_{self.UUID}"
		self.show_age_tag = f"tracker_show_age_{self.UUID}"
		self.show_distance_tag = f"tracker_show_distance_{self.UUID}"
		self.show_speed_tag = f"tracker_show_speed_{self.UUID}"

		self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
		self._monitor_thread_running = True
		self._monitor_thread.start()

		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):
			
			dpg.add_checkbox(label="Show ID", default_value=False, callback=self._update_param_cb, tag=self.show_id_tag)
			dpg.add_checkbox(label="Show trail", default_value=False, callback=self._update_param_cb, tag=self.show_trail_tag)
			dpg.add_drag_int(label="Trail length", default_value=DS.DISTANCE_TRESHOLD, min_value=0, max_value=100, callback=self._update_param_cb, tag=self.trail_length_tag)
			dpg.add_checkbox(label="Show age", default_value=False, callback=self._update_param_cb, tag=self.show_age_tag)
			dpg.add_checkbox(label="Show distance", default_value=False, callback=self._update_param_cb, tag=self.show_distance_tag)
			dpg.add_checkbox(label="Show speed", default_value=False, callback=self._update_param_cb, tag=self.show_speed_tag)

	def _update_param_cb(self, sender, app_data):
		"""Callback to update parameters when sliders or checkboxes are changed."""

		params = {
			"trail_length": int(dpg.get_value(self.trail_length_tag)),
			"show_trail": dpg.get_value(self.show_trail_tag),
			"show_id": dpg.get_value(self.show_id_tag),
			"show_age": dpg.get_value(self.show_age_tag),
			"show_distance": dpg.get_value(self.show_distance_tag),		
			"show_speed": dpg.get_value(self.show_speed_tag)
		}
		self.processor.update_params(**params)

	def on_close(self):
		self._monitor_thread_running = False
		if self._monitor_thread.is_alive():
			self._monitor_thread.join()
		self.processor.stop()

	def is_ready(self):
		return self.processor.is_ready()

	def input_cb(self, *args, **kwargs):
		if "data_type" in kwargs:
			data_type = kwargs["data_type"]
		
		if "data" in kwargs:
			if data_type == IOTypes.FRAME_MASK_PAIR:
				frame, mask = kwargs["data"]
			elif data_type == IOTypes.MASK:
				frame = kwargs["data"]
				mask = kwargs["data"]
			elif data_type == IOTypes.POINT_LIST:
				data = kwargs["data"]
				frame = data[0]
				point_list = data[1]
				return self.processor.submit((frame, point_list))

		# return self.processor.submit((frame))

	def _monitor_loop(self):
		while self._monitor_thread_running:
			result = self.processor.get()
			
			if result is not None:
				for idx, output_key in enumerate(self.outputs):
					connected_modules = self.connections.get(output_key, [])
					for module in connected_modules:
						if idx == 0:
							module.input_cb(data = result[0], data_type = IOTypes.FRAME) #Frame
						elif idx == 1:
							module.input_cb(data = result[1], data_type = IOTypes.TRACKING) #Tracking

EXPORTED_CLASS = Tracker_win
EXPORTED_NAME = "Tracker"
