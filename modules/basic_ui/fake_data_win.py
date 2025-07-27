import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
import numpy as np
from core.input_ouput_types import IOTypes

class Fakedata_win(WindowBase):
	"""
	A simple DearPyGui window that generates fake data on trigger.

	Features:
	- Outputs a list of 100 random integers between 0 and 100
	- Triggers manually via button or programmatically via input_cb
	"""

	def __init__(self,
				label="Button",
				win_width=-1,
				win_height=-1,
				pos=(10, 10),
				outputs=None,
				uuid=None,
				visible=True):

		super().__init__(label=label, pos=pos, win_width=win_width, win_height=win_height,
			uuid=uuid, outputs=outputs or [], visible=visible)

		# Persist window label only
		self._persistent_fields = ["label"]

		self.accepted_input_types = []
		self.outputs = {
			"Data" : IOTypes.DATALIST
		}
		self.connections = {k: [] for k in self.outputs}

		self.click_count = 0

		# Build UI
		with dpg.window(
			label=self.label,
			width=self.win_width,
			height=self.win_height,
			pos=self.pos,
			tag=self.winID,
			show=self.visible
		):
			dpg.add_button(label="Trigger", callback=self.trigger_cb)

	def input_cb(self, *args, **kwargs):
		"""
		Programmatic trigger: calls trigger_cb as if user clicked the button.
		"""
		self.trigger_cb(*args, **kwargs)

	def trigger_cb(self, *args, **kwargs):
		"""
		Generates and emits random data to connected outputs.
		Each output receives a dict with a 'y' key holding a list of 100 integers.
		"""
		self.click_count += 1
		
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				module.input_cb(y=list(np.random.randint(0, 101, size=100)), name=f"{self.click_count}", uuid=self.click_count)

EXPORTED_CLASS = Fakedata_win
EXPORTED_NAME = "Fake Data"
