import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes
import numpy as np
import threading
from modules.demo.binarise_frame import Binarize_Frame

class Binarize_demo_win(WindowBase):
	def __init__(self,
				label="Binarize",
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
		self.accepted_input_types = [IOTypes.FRAME]

		self.outputs = {
			"Frame" : IOTypes.FRAME,
			"Mask" : IOTypes.MASK
		}
		self.connections = {k: [] for k in self.outputs}

		self.processor = Binarize_Frame(
			params={
				"block_size": 25, 
				"bin_thresh": 15
				},

			buffer_size=1,
			drop_policy="drop_new"
		)
		self.processor.start()

		self.block_size_tag = f"binarize_block_size_{self.UUID}"
		self.bin_thresh_tag = f"binarize_bin_thresh_{self.UUID}"

		self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
		self._monitor_thread_running = True
		self._monitor_thread.start()

		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):

			dpg.add_drag_int(label="Block size", default_value=25, min_value=3, max_value=51, callback=self._update_param_cb, tag=self.block_size_tag)
			dpg.add_drag_int(label="Bin thresh", default_value=15, min_value=0, max_value=50, callback=self._update_param_cb, tag=self.bin_thresh_tag)


	def _update_param_cb(self, sender, app_data):
		block_size = dpg.get_value(self.block_size_tag)
		if block_size % 2 == 0:
			block_size += 1
			dpg.set_value(self.block_size_tag, block_size)

		params = {
			"block_size": dpg.get_value(self.block_size_tag),
			"bin_thresh": dpg.get_value(self.bin_thresh_tag),
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
		frame = kwargs.get("data") if "data" in kwargs else (args[0] if args else None)
		if frame is None or not isinstance(frame, np.ndarray):
			return False
		return self.processor.submit(frame)

	def _monitor_loop(self):
		while self._monitor_thread_running:
			result = self.processor.get()
			if result is not None:
				for idx, output_key in enumerate(self.outputs):
					connected_modules = self.connections.get(output_key, [])
					for module in connected_modules:
						if idx == 0: 
							module.input_cb(data = result[0], data_type = IOTypes.FRAME)
						elif idx == 1:
							module.input_cb(data = result[1], data_type = IOTypes.MASK)
							

EXPORTED_CLASS = Binarize_demo_win