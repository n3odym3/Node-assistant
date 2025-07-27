import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes

class Template_win(WindowBase):
	"""
	A basic example module window using the WindowBase system.

	This template demonstrates:
	- Declaring input/output types
	- Handling incoming data
	- Sending messages to downstream connected modules
	- Saving persistent fields (e.g., label)
	"""

	def __init__(self,
				label="Template",
				win_width=300,
				win_height=200,
				pos=(10, 10),
				uuid=None,
				outputs=None,
				visible=True,
				default_number=10): 
		"""
		Initialize a new Template window with optional label, size, and position.

		Args:
			label (str): The window title and base ID.
			win_width (int): Width of the window.
			win_height (int): Height of the window.
			pos (tuple): Initial position of the window.
			uuid (str): Optional fixed UUID for serialization.
			outputs (dict): Optional output dictionary (overridden here).
			visible (bool): Whether the window is shown on creation.
		"""
		super().__init__(label=label, pos=pos, win_width=win_width, win_height=win_height, uuid=uuid, outputs=outputs, visible=visible)

		self._persistent_fields = ["label","default_number"]

		self.accepted_input_types = [IOTypes.TEXT]
		self.outputs = {
			"TEXT": IOTypes.TEXT,
			"NUMBER": IOTypes.NUMBER
		}

		self.connections = {k: [] for k in self.outputs}

		self.text_tag = f"template_text_{self.UUID}"
		self.number_tag = f"template_number_{self.UUID}"

		self.default_number = default_number

		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):

			dpg.add_button(label="Hello world", callback=self.trigger_cb)
			dpg.add_input_int(tag=self.number_tag,default_value=self.default_number, callback=lambda sender, value: setattr(self, "default_number", value))

	def input_cb(self, *args, **kwargs):
		"""
		Default input callback: logs incoming arguments to stdout.
		Override for custom behavior.
		"""
		print(f"{self.winID} received input: args={args}, kwargs={kwargs}")

	def trigger_cb(self, *args, **kwargs):
		"""
		Triggered when the button is pressed.
		Sends a fixed message ("Hello World") to the first output only.
		"""
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				if idx == 0:
					module.input_cb("Hello World")
				if idx == 1:
					module.input_cb(self.default_number)

EXPORTED_CLASS = Template_win
EXPORTED_NAME = "Template"

