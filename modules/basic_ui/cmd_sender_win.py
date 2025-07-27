import dearpygui.dearpygui as dpg
from loguru import logger

from core.window_base import WindowBase
from core.input_ouput_types import IOTypes


class CMDSender_win(WindowBase):
	"""
	A modular window that allows the user to build a dictionary interactively
	and send it downstream on trigger. Useful for sending command-like
	messages with key-value pairs.
	"""

	def __init__(self,
				label="CMD Sender",
				win_width=-1,
				win_height=-1,
				pos=(10, 10),
				outputs=None,
				uuid=None,
				visible=True,
				status=None):

		super().__init__(label=label, pos=pos, win_width=win_width,
						win_height=win_height, uuid=uuid,
						outputs=outputs or [], visible=visible)

		# Fields to persist in layout save
		self._persistent_fields = ["label", "status"]

		# Optional initial dictionary
		self.status = status if status is not None else {}

		# IO types
		self.accepted_input_types = [IOTypes.TRIGGER]
		self.output_types = [IOTypes.CMD_DICT]

		self.outputs = {
			"Dict" : IOTypes.CMD_DICT,
			"TXT" : IOTypes.TEXT
		}
		self.connections = {k: [] for k in self.outputs}

		# Internal structures
		self._rows = {}  # tag -> (key_tag, value_tag)
		self._row_counter = 0

		self.rows_container_tag = f"rows_container_{self.UUID}"
		self.add_key_btn_tag = f"add_key_btn_{self.UUID}"

		# Build UI
		with dpg.window(label=self.label, width=self.win_width, height=self.win_height,
						pos=self.pos, tag=self.winID, show=self.visible):

			with dpg.group(horizontal=True):
				dpg.add_button(label="Add Key", tag=self.add_key_btn_tag,
								callback=lambda: self._add_key_row())
				dpg.add_button(label="Send", callback=self.trigger_cb)

			with dpg.group(tag=self.rows_container_tag):
				pass  # Starts empty

		# Populate with initial values (if any)
		for key, value in self.status.items():
			self._add_key_row(key=key, value=value)

	def input_cb(self, *args, **kwargs):
		"""
		Propagate upstream trigger as-is.
		"""
		self.trigger_cb(*args, **kwargs)

	def trigger_cb(self, *args, **kwargs):
		"""
		Collect key-value entries into a dictionary and send to downstream modules.
		"""
		cmd: dict[str, str] = {}

		for key_tag, value_tag in self._rows.values():
			key = dpg.get_value(key_tag).strip()
			value = dpg.get_value(value_tag).strip()
			if key:
				cmd[key] = value

		logger.debug(f"{self.winID} sending cmd={cmd}")

		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				if idx == 0: 
					module.input_cb(cmd)
				elif idx == 1:  
					module.input_cb(str(cmd))
				else:
					logger.warning(f"[{self.label}] Unsupported output index {idx}")

	def _add_key_row(self, key: str = "", value: str = ""):
		"""
		Add a new key/value input row with delete capability.
		"""
		row_idx = self._row_counter
		self._row_counter += 1

		row_tag = f"{self.winID}_row_{row_idx}"
		key_tag = f"{row_tag}_key"
		value_tag = f"{row_tag}_value"
		delete_tag = f"{row_tag}_del"

		with dpg.group(horizontal=True, parent=self.rows_container_tag, tag=row_tag):
			dpg.add_input_text(tag=key_tag, width=120, hint="key",
							   callback=lambda *_: self._update_status(),
								default_value=key)
			dpg.add_input_text(tag=value_tag, width=120, hint="value",
							   callback=lambda *_: self._update_status(),
								default_value=value)
			dpg.add_button(label="Delete", tag=delete_tag,
							callback=lambda: self._delete_row(row_tag))

		self._rows[row_tag] = (key_tag, value_tag)

	def _delete_row(self, row_tag: str):
		"""
		Delete a row and update internal state accordingly.
		"""
		if row_tag in self._rows:
			dpg.delete_item(row_tag)
			del self._rows[row_tag]
			logger.debug(f"{self.winID} removed row {row_tag}")
			self._update_status()

	def _update_status(self):
		"""
		Refresh self.status to reflect current key/value inputs.
		"""
		current = {}
		for key_tag, value_tag in self._rows.values():
			key = dpg.get_value(key_tag).strip()
			value = dpg.get_value(value_tag).strip()
			if key:
				current[key] = value
		self.status = current


EXPORTED_CLASS = CMDSender_win
EXPORTED_NAME = "Dict Sender"
