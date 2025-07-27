import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes

class Text_viewer_win(WindowBase):
	"""
	A DearPyGui window for displaying incoming text in a read-only multiline field.

	Features:
	- Displays a string passed via input
	- Stores content persistently for export
	"""

	def __init__(self,
				label="Text Viewer",
				win_width=400,
				win_height=300,
				pos=(10, 10),
				uuid=None,
				outputs=None,
				content="(No content)",
				visible=True):

		super().__init__(label=label, pos=pos, win_width=win_width, win_height=win_height,
			uuid=uuid, outputs=outputs or [], visible=visible)

		# Persist label and text content
		self._persistent_fields = ["label"]

		# Define input and output types
		self.accepted_input_types = [IOTypes.TEXT, IOTypes.CMD_DICT, IOTypes.TRIGGER]
		
		self.outputs = {}
		self.connections = {k: [] for k in self.outputs}

		# Initial content
		self.content = content

		# Internal tag for the text field
		self.text_tag = f"text_viewer_content_{self.UUID}"

		# Build UI
		with dpg.window(label=self.label, width=self.win_width, height=self.win_height, pos=self.pos, tag=self.winID, show=self.visible):

			dpg.add_input_text(
				multiline=True,
				readonly=True,
				tag=self.text_tag,
				default_value=self.content,
				width=self.win_width - 20,
				height=self.win_height - 40
			)

	def input_cb(self, *args, **kwargs):
		"""
		Updates the text display with new content received from upstream.
		Accepts a plain string or 'content' keyword in kwargs.
		"""
		text_input = str(kwargs.get("data") or args[0])

		dpg.set_value(self.text_tag, text_input)
		self.content = text_input  # Used for persistence/export


EXPORTED_CLASS = Text_viewer_win
EXPORTED_NAME = "Text viewer"
