import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes
from modules.sequence_processor.sequence_processor import sequence_processor
from loguru import logger
import datetime
import time
import threading 

class Sequence_processor_win(WindowBase):
	def __init__(self,
				label="Sequence processor",
				win_width=300,
				win_height=200,
				pos=(10, 10),
				uuid=None,
				outputs=None,
				visible=True): 

		super().__init__(label=label,pos=pos,win_width=win_width,win_height=win_height,uuid=uuid,outputs=outputs,visible=visible)

		self._persistent_fields = ["label"]
		self.accepted_input_types = [IOTypes.CMD_LIST]
		self.outputs = {
			"CMD dict": IOTypes.CMD_DICT,
			"Trigger": IOTypes.TRIGGER,
		}
		self.connections = {k: [] for k in self.outputs}
		
		self.sequence_input_tag = f"seq_writer_input_{self.UUID}"
		self.table_tag = f"seq_writer_table_{self.UUID}"
		self.run_seq_tag = f"seq_run_{self.UUID}"
		self.kill_seq_tag = f"seq_kill_{self.UUID}"
		self.seq_remaining_tag = f"seq_remaining_{self.UUID}"
		self.table_group_tag = f"seq_table_group_{self.UUID}"

		self.task = None
		self.cmd_list = []
		self.total_duration = 0
		self.seq_running = False
		self.seq_error = False
		self.check_delay = 5 # Check every 5 seconds if the task is still running
		
		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):

				with dpg.group(tag=self.table_group_tag):
					pass

				with dpg.group(horizontal=True) :
					dpg.add_button(label="Run seq.", tag = self.run_seq_tag,  callback=self.run_sequence)
					dpg.add_button(label="KILL seq.", tag = self.kill_seq_tag,  callback=self.kill_sequence)

				dpg.add_text("Remaining : 00:00:00", tag=self.seq_remaining_tag)

	def is_ready(self):
		"""Check if the window is ready to process inputs."""
		return True
	
	def is_outputs_ready(self):
		for output in self.outputs:
			is_ready = getattr(output, "is_ready", None)
			if callable(is_ready) and not is_ready():
				return False
		return True
	
	def validate_sequence(self, cmd_list):
		self.seq_error = False
		if self.merged_into is not None:
			dpg.show_item(self.winID)
			dpg.focus_item(self.winID)

		dpg.push_container_stack(self.table_group_tag)
		dpg.delete_item(self.table_tag)
		
		with dpg.table(header_row=True, resizable=True, tag=self.table_tag, borders_innerH=True, borders_innerV=True, borders_outerH=True, borders_outerV=True,policy=dpg.mvTable_SizingStretchProp):
			dpg.add_table_column(label="Cmd")
			dpg.add_table_column(label="Descr")
			self.total_duration = 0
			self.last_sequence = []
			for i,cmd in enumerate(cmd_list):
				with dpg.table_row():
					dpg.add_text(cmd)
					cmd_result = sequence_processor.trad_cmd(cmd)

					if not cmd_result["valid"]:
						dpg.highlight_table_row(self.table_tag, i,  [255,0,0,50])
						self.seq_error = True
						logger.error(f"Invalid command at index {i} ! Please correct : {cmd}")

					self.total_duration += cmd_result["duration"]
					dpg.add_text(cmd_result["description"])
			dpg.set_value(self.seq_remaining_tag, f"Remaining : {datetime.timedelta(seconds=int(self.total_duration))}")

			if not self.seq_error:
				logger.info(f"Sequence validated with {len(cmd_list)} commands, total duration: {self.total_duration} seconds")
				self.last_sequence = cmd_list

		dpg.pop_container_stack()

	def run_sequence(self, *args, **kwargs):
		
		if not self.seq_error :

			def task() :
				duration = 0
				for i, cmd in enumerate(self.last_sequence):

					if not self.seq_running :
						logger.info("Sequence aborted")
						dpg.set_value(self.seq_remaining_tag, f"Duration : ABORTED")
						return

					self.total_duration -= duration
					dpg.set_value(self.seq_remaining_tag, f"Duration : {datetime.timedelta(seconds=int(self.total_duration))}")

					dpg.highlight_table_row(self.table_tag, i,  [0,0,255,50])

					cmd_response = sequence_processor.trad_cmd(cmd)

					self.trigger_cb(0,cmd_response["cmd"])

					duration = cmd_response["duration"]
					if duration > 0:
						remaining_time = duration
						while remaining_time > 0:
							sleep_time = min(self.check_delay, remaining_time)
							time.sleep(sleep_time)
							remaining_time -= self.check_delay

							if not self.seq_running:
								logger.info("Sequence aborted")
								self.trigger_cb(1,"KILLED")
								dpg.set_value(self.seq_remaining_tag, f"Duration : ABORTED")
								return

					dpg.highlight_table_row(self.table_tag, i,  [0,255,0,50])

				dpg.set_value(self.seq_remaining_tag, f"Duration : DONE")
				self.trigger_cb(1,"DONE")
				self.seq_running = False

			if  not self.seq_running:
				self.set_table_color((0, 0, 0, 0))
				self.trigger_cb(1,"START")
				self.seq_running = True
				self.task = threading.Thread(target=task)
				self.task.start()
			else :
				logger.warning("A sequence is already running, please wait for it to finish or kill it before starting a new one.")
		else:
			logger.error("Cannot run a sequence that contains errors. Please validate the sequence first.")
			dpg.set_value(self.seq_remaining_tag, f"Duration : ERROR")

	def set_table_color(self, rgba=(0, 0, 0, 0)):
		rows = dpg.get_item_children(self.table_tag, 1)
		for i in range(len(rows)):
			dpg.highlight_table_row(self.table_tag, i, rgba)

	def kill_sequence(self, *args, **kwargs):
		self.seq_running = False
		self.set_table_color((255, 0, 0, 50))

	def input_cb(self, *args, **kwargs):
		cmd_list = kwargs.get("data") if "data" in kwargs else (args[0] if args else None)
		self.validate_sequence(cmd_list)

	def trigger_cb(self,out_idx=0, cmd = {}):
		"""Sends the last known status as STATUS_DICT to all outputs."""
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				if idx == 0 and out_idx == 0:
					module.input_cb(cmd)
				if idx == 1 and out_idx == 1:
					module.input_cb(cmd)

EXPORTED_CLASS = Sequence_processor_win
EXPORTED_NAME = "Sequence processor"
