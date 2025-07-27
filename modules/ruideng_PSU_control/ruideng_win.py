import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from loguru import logger
from modules.ruideng_PSU_control.ruideng_control import RuidengControl
from core.input_ouput_types import IOTypes


class Ruideng_control_win(WindowBase):
	"""
	A DearPyGui-based UI for controlling a Ruideng power supply unit (PSU).

	Features:
	- COM port discovery and connection
	- Set voltage, current, and output state
	- Monitor live voltage, current, input voltage, and temperature
	- React to incoming command dictionaries (CMD_DICT)
	"""

	def __init__(self,
				label="Ruideng Control",
				win_width=625,
				win_height=500,
				pos=(0, 50),
				uuid=None,
				outputs=None,
				visible=True):

		super().__init__(label=label, pos=pos, win_width=win_width,
			win_height=win_height, uuid=uuid, outputs=outputs or [], visible=visible)

		# Backend logic instance
		self.ruideng_control = RuidengControl()
		self.last_status = {}

		# UI element tags
		self.combo_tag = f"ruideng_combo_{self.UUID}"
		self.Vset_tag = f"ruideng_vset_{self.UUID}"
		self.Iset_tag = f"ruideng_iset_{self.UUID}"
		self.power_tag = f"ruideng_power_{self.UUID}"
		self.vout_tag = f"ruideng_vout_{self.UUID}"
		self.iout_tag = f"ruideng_iout_{self.UUID}"
		self.vin_tag = f"ruideng_vin_{self.UUID}"
		self.temp_tag = f"ruideng_temp_{self.UUID}"

		# I/O types
		self._persistent_fields = ["label"]
		self.accepted_input_types = [IOTypes.CMD_DICT]

		self.outputs = {
			"Status" : IOTypes.STATUS_DICT,
		}
		self.connections = {k: [] for k in self.outputs}

		# Build UI layout
		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):

			with dpg.group():
				with dpg.group(horizontal=True):
					dpg.add_button(label="Refresh Ports", callback=self.update_com_ports)
					dpg.add_combo(tag=self.combo_tag, callback=self.select_port_cb, width=100)
					dpg.add_button(label="Check Status", callback=lambda: self.update_status())

			with dpg.group(horizontal=True):
				dpg.add_text("Vset")
				dpg.add_input_float(tag=self.Vset_tag, default_value=0, min_value=0,
					min_clamped=True, max_value=60, max_clamped=True,
					format="%.2f", width=150, callback=self.config_cb)

				dpg.add_text("Iset")
				dpg.add_input_float(tag=self.Iset_tag, default_value=0, min_value=0,
					min_clamped=True, max_value=12, max_clamped=True,
					format="%.2f", width=150, callback=self.config_cb)

				dpg.add_text("Power")
				dpg.add_checkbox(tag=self.power_tag, default_value=False, callback=self.config_cb)

			dpg.add_separator()
			dpg.add_text("Vin : 0", tag=self.vin_tag)
			dpg.add_text("Vout : 0", tag=self.vout_tag)
			dpg.add_text("Iout : 0", tag=self.iout_tag)
			dpg.add_text("Temp : 0", tag=self.temp_tag)

	def input_cb(self, *args, **kwargs):
		"""
		Receives and interprets a CMD_DICT with optional 'volt', 'amp', and 'power' keys.
		Applies the corresponding commands to the Ruideng PSU.
		"""
		cmd = None
		if args and isinstance(args[0], dict):
			cmd = args[0]
		elif "cmd" in kwargs and isinstance(kwargs["cmd"], dict):
			cmd = kwargs["cmd"]
		else:
			logger.warning(f"{self.winID} input_cb: No valid dictionary provided")
			return

		if "volt" in cmd:
			try:
				value = float(cmd["volt"])
				dpg.set_value(self.Vset_tag, value)
				self.ruideng_control.set_voltage(value)
			except Exception as e:
				logger.warning(f"{self.winID} failed to set voltage: {e}")

		if "amp" in cmd:
			try:
				value = float(cmd["amp"])
				dpg.set_value(self.Iset_tag, value)
				self.ruideng_control.set_current(value)
			except Exception as e:
				logger.warning(f"{self.winID} failed to set current: {e}")

		if "power" in cmd:
			try:
				value = bool(cmd["power"])
				dpg.set_value(self.power_tag, value)
				self.ruideng_control.set_power(value)
			except Exception as e:
				logger.warning(f"{self.winID} failed to set power: {e}")

		self.update_status()

	def trigger_cb(self, *args, **kwargs):
		"""Sends the last known status as STATUS_DICT to all outputs."""
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				if idx == 0:
					module.input_cb(status=self.last_status)

	def update_com_ports(self, sender=None, app_data=None, user_data=None):
		"""Queries available COM ports and updates the combo box."""
		ports_infos = self.ruideng_control.list_com_ports()
		dpg.configure_item(self.combo_tag, items=list(ports_infos.keys()))

	def select_port_cb(self, sender, app_data, user_data=None):
		"""Tries to connect to the selected COM port and update status if successful."""
		success = self.ruideng_control.select_port(app_data)
		if success:
			self.update_status()
		else:
			logger.error(f"{self.winID} failed to connect to {app_data}")

	def config_cb(self, sender=None, app_data=None, user_data=None):
		"""
		Triggered when UI controls are changed.
		Applies current V/I/power settings to the PSU.
		"""
		vset = round(dpg.get_value(self.Vset_tag), 2)
		iset = round(dpg.get_value(self.Iset_tag), 2)
		power = dpg.get_value(self.power_tag)

		self.ruideng_control.set_voltage(vset)
		self.ruideng_control.set_current(iset)
		self.ruideng_control.set_power(power)

	def update_status(self):
		"""
		Fetches PSU status and updates UI values.
		Also stores the latest status in self.last_status.
		"""
		self.last_status = self.ruideng_control.check_status()

		if self.last_status:
			dpg.set_value(self.Vset_tag, self.last_status['vset'])
			dpg.set_value(self.Iset_tag, self.last_status['iset'])
			dpg.set_value(self.power_tag, self.last_status['power'])

			dpg.set_value(self.vout_tag, f"Vout  : {self.last_status['vout']}")
			dpg.set_value(self.iout_tag, f"Iout  : {self.last_status['iout']}")
			dpg.set_value(self.vin_tag, f"Vin   : {self.last_status['vin']}")
			dpg.set_value(self.temp_tag, f"Temp  : {self.last_status['temp']}")


EXPORTED_CLASS = Ruideng_control_win
EXPORTED_NAME = "Ruideng Control"
