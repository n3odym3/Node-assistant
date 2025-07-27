import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes
import numpy as np
import threading
from modules.computer_vision.contour_detection.contour_detection import Contour_detection
from modules.computer_vision.contour_detection.contour_detection_default_settings import DEFAULT_SETTINGS as DS	

class Contour_detection_win(WindowBase):
	def __init__(self,
				label="Detect Contours",
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
		self.accepted_input_types = [IOTypes.MASK,IOTypes.FRAME_MASK_PAIR]

		self.outputs = {
			"Frame" : IOTypes.FRAME,
			"Mask" : IOTypes.MASK,
			"Custom" : IOTypes.FRAME,
			"Pair" : IOTypes.FRAME_MASK_PAIR,
			"Detections" : IOTypes.POINT_LIST
		}
		self.connections = {k: [] for k in self.outputs}

		self.processor = Contour_detection(
			params={
				"lower_surface_thresh": DS.LOWER_SURFACE_THRESH, 
				"upper_surface_thresh": DS.UPPER_SURFACE_THRESH, 
				"show_blobs": DS.SHOW_BLOBS, 
				"show_boxes": DS.SHOW_BOXES, 
				"show_centroids": DS.SHOW_CENTROIDS, 
				"isolate_selection": DS.ISOLATE_SELECTION,
				"visu_format": DS.VISU_FORMAT
			},
			buffer_size=DS.BUFFER_SIZE,
			drop_policy=DS.DROP_POLICY
		)
		
		self.processor.start()

		self.lower_surface_thresh_tag = f"contour_lower_surface_thresh_{self.UUID}"
		self.upper_surface_thresh_tag = f"contour_upper_surface_thresh_{self.UUID}"
		self.show_blobs_tag = f"contour_show_blobs_{self.UUID}"
		self.isolate_selection_tag = f"isolate_show_selection_{self.UUID}"
		self.show_boxes_tag = f"contour_show_boxes_{self.UUID}"
		self.show_centroids_tag = f"contour_show_centroids_{self.UUID}"
		
		self.output_format_tag = f"contour_output_format_{self.UUID}"
		self.visu_format_tag = f"contour_visu_format_{self.UUID}"
		self.custom_output = ["Frame", "Mask"]

		self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
		self._monitor_thread_running = True
		self._monitor_thread.start()

		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):

			dpg.add_drag_int(label="Lower surface thresh", default_value=DS.LOWER_SURFACE_THRESH, min_value=0, max_value=100, callback=self._update_param_cb, tag=self.lower_surface_thresh_tag)
			dpg.add_drag_int(label="Upper surface thresh", default_value=DS.UPPER_SURFACE_THRESH, min_value=0, max_value=100, callback=self._update_param_cb, tag=self.upper_surface_thresh_tag)
			dpg.add_checkbox(label="Show blobs", default_value=DS.SHOW_BLOBS, callback=self._update_param_cb, tag=self.show_blobs_tag)
			dpg.add_checkbox(label="Isolate selection", default_value=DS.ISOLATE_SELECTION, callback=self._update_param_cb, tag=self.isolate_selection_tag)
			dpg.add_checkbox(label="Show boxes", default_value=DS.SHOW_BOXES, callback=self._update_param_cb, tag=self.show_boxes_tag)
			dpg.add_checkbox(label="Show centroids", default_value=DS.SHOW_CENTROIDS, callback=self._update_param_cb, tag=self.show_centroids_tag)

			with dpg.group(horizontal=True):
				dpg.add_text("Visu format") 
				dpg.add_combo(items=self.custom_output, default_value="Frame", tag=self.visu_format_tag,callback=self._update_param_cb)
			
			with dpg.group(horizontal=True):
				dpg.add_text("Output format")
				dpg.add_combo(items=self.custom_output,  default_value="Frame", tag=self.output_format_tag)


	def _update_param_cb(self, sender, app_data):
		"""Callback to update parameters when sliders or checkboxes are changed."""

		params = {
			"lower_surface_thresh": dpg.get_value(self.lower_surface_thresh_tag),
			"upper_surface_thresh": dpg.get_value(self.upper_surface_thresh_tag),
			"show_blobs": dpg.get_value(self.show_blobs_tag),
			"show_boxes": dpg.get_value(self.show_boxes_tag),
			"show_centroids": dpg.get_value(self.show_centroids_tag),
			"isolate_selection": dpg.get_value(self.isolate_selection_tag),
			"visu_format": dpg.get_value(self.visu_format_tag)
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

		return self.processor.submit((frame, mask))

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
							module.input_cb(data = result[1], data_type = IOTypes.MASK) #Mask
						elif idx == 2: 
							module.input_cb(data = result[self.custom_output.index(dpg.get_value(self.output_format_tag))]) #Custom output
						elif idx == 3:
							module.input_cb(data = [result[0],result[1]], data_type = IOTypes.FRAME_MASK_PAIR)
						elif idx == 4:
							module.input_cb(data = [result[0],result[2]], data_type = IOTypes.POINT_LIST)

EXPORTED_CLASS = Contour_detection_win
EXPORTED_NAME = "Contour Detection"
