import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes
from modules.sequence_processor.sequence_processor import sequence_processor

class Sequence_writer_win(WindowBase):
	def __init__(self,
				label="Sequence writer",
				win_width=300,
				win_height=200,
				pos=(10, 10),
				uuid=None,
				outputs=None,
				visible=True): 

		super().__init__(label=label,pos=pos,win_width=win_width,win_height=win_height,uuid=uuid,outputs=outputs,visible=visible)

		self._persistent_fields = ["label"]
		self.accepted_input_types = [IOTypes.TEXT]
		self.outputs = {
			"CMD list": IOTypes.CMD_LIST,
		}
		self.connections = {k: [] for k in self.outputs}
		
		self.validate_seq_tag = f"seq_writer_validate_{self.UUID}"
		self.sequence_input_tag = f"seq_writer_input_{self.UUID}"

		self.cmd_list = []

		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):

			dpg.add_button(label="Validate sequence", width= -1, tag=self.validate_seq_tag, callback=self._validate_sequence_cb)
			dpg.add_input_text(
				tag=self.sequence_input_tag, 
				width=-1, height=300, multiline=True, 
				on_enter=True, 
				callback=self._validate_sequence_cb,
				payload_type="sequence", 
				drop_callback=lambda s,a :dpg.set_value(s, dpg.get_value(self.sequence_input_tag)+a))

	def is_ready(self):
		"""Check if the window is ready to process inputs."""
		return True
	
	def is_outputs_ready(self):
		for output in self.outputs:
			is_ready = getattr(output, "is_ready", None)
			if callable(is_ready) and not is_ready():
				return False
		return True
	
	def input_cb(self, *args, **kwargs):
		print(f"{self.winID} received input: args={args}, kwargs={kwargs}")

	def trigger_cb(self, *args, **kwargs):
		"""Sends the last known status as STATUS_DICT to all outputs."""
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				if idx == 0:
					module.input_cb(self.cmd_list)

	def _validate_sequence_cb(self, sender, app_data):
		sequence = dpg.get_value(self.sequence_input_tag)
		self.cmd_list = sequence_processor.get_commands(sequence)
		self.trigger_cb()

EXPORTED_CLASS = Sequence_writer_win
EXPORTED_NAME = "Sequence Writer"
