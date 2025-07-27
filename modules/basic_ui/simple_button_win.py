import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes

class Button_win(WindowBase):
	"""
	A simple DearPyGui button module that acts as a trigger source.

	Features:
	- Emits a 'trigger' to connected modules when clicked
	- Can also be triggered programmatically via input_cb
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

		# Persistent label for layout saving
		self._persistent_fields = ["label"]

		# No input types accepted
		self.accepted_input_types = []

		self.outputs = {
			"Trig" : IOTypes.TRIGGER,
		}
		self.connections = {k: [] for k in self.outputs}

		# UI layout
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
		Allows external code to trigger the button programmatically.
		Equivalent to clicking the button.
		"""
		self.trigger_cb(*args, **kwargs)

	def trigger_cb(self, *args, **kwargs):
		"""
		Forwards the trigger to all connected output modules.
		"""
		for output_key, targets in self.connections.items():
			for module in targets:
				module.input_cb(*args, **kwargs)


EXPORTED_CLASS = Button_win
EXPORTED_NAME = "Trigger Button"
