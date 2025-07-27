import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes

class Sample_container_win(WindowBase):
	def __init__(self,
				label="Sample Container",
				win_width=300,
				win_height=200,
				pos=(10, 10),
				uuid=None,
				outputs=None,
				visible=True): 

		super().__init__(label=label,pos=pos,win_width=win_width,win_height=win_height,uuid=uuid,outputs=outputs,visible=visible)

		self._persistent_fields = ["label"]
		self.accepted_input_types = [IOTypes.DATALIST]
		self.outputs = {
			"Data": IOTypes.DATALIST,
		}
		self.connections = {k: [] for k in self.outputs}
		
		self.clear_samples_tag = f"clear_samples_{self.UUID}"
		self.select_all_samples_tag = f"select_all_samples_{self.UUID}"
		self.deselect_all_samples_tag = f"deselect_all_samples_{self.UUID}"
		self.samples_group_tag = f"samples_group_{self.UUID}"

		self.samples_dict = {}
		self.samples_count = 0
	
		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):
	
			dpg.add_button(label="Clear samples", width=-1, tag=self.clear_samples_tag, callback=self.clear_samples_cb)
			dpg.add_button(label="Select all", width=-1, callback=self.select_all_samples_cb)
			dpg.add_button(label="Deselect all", width=-1, callback=self.deselect_all_samples_cb)

			dpg.add_group(tag=self.samples_group_tag)

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
		y = kwargs.get("y") or (args[0] if args and isinstance(args[0], list) else None)
		x = kwargs.get("x") or (args[1] if len(args) > 1 and isinstance(args[1], list) else None)
		name = kwargs.get("name", None)
		UUID = kwargs.get("uuid", None)

		if UUID is None:
			UUID = self.samples_count
			self.samples_count += 1
		
		if name is None:
			name = f"{UUID}"

		self.samples_dict[UUID] = {
			"y": y,
			"x": x,
			"name": name,
			"uuid": UUID
		}

		dpg.push_container_stack(self.samples_group_tag)
		with dpg.group(horizontal=True, tag=f"sample_group_{UUID}"):
			dpg.add_checkbox(tag=f"sample_checkbox_{UUID}", callback=self.sample_checkbox_cb, user_data=UUID)
			with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Right):
				dpg.add_menu_item(label="Delete", user_data=UUID, callback=self.delete_sample_cb)

			dpg.add_input_text(tag=f"sample_name_{UUID}", default_value=f"{name}", callback=self.sample_name_cb, user_data=UUID)
			with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Right):
				dpg.add_menu_item(label="Delete", user_data=UUID, callback=self.delete_sample_cb)
		dpg.pop_container_stack()

	def sample_checkbox_cb(self, sender, app_data, user_data):
		UUID = user_data

		if app_data:
			y = self.samples_dict[UUID]["y"]
			x = self.samples_dict[UUID]["x"]
			name = self.samples_dict[UUID]["name"]
			
			cmd = {
				"action": "add serie",
				"data": {
					"y": y,
					"x": x,
					"name": name,
					"uuid": UUID
				}
			}
			self.trigger_cb(cmd=cmd, data_type=IOTypes.CMD_DICT)
		else:
			cmd = {
				"action": "remove serie",
				"data": {
					"uuid": UUID
				}
			}
			self.trigger_cb(cmd=cmd, data_type=IOTypes.CMD_DICT)

	def sample_name_cb(self, sender, app_data, user_data):
		UUID = user_data
		new_name = app_data.strip()

		if new_name:
			self.samples_dict[UUID]["name"] = new_name

			cmd = {
				"action": "update serie name",
				"data": {
					"name": new_name,
					"uuid": UUID
				}
			}
			self.trigger_cb(cmd=cmd, data_type=IOTypes.CMD_DICT)

	def delete_sample_cb(self, sender, app_data, user_data):
		UUID = user_data
		if UUID in self.samples_dict:
			del self.samples_dict[UUID]
			dpg.delete_item(f"sample_checkbox_{UUID}")
			dpg.delete_item(f"sample_name_{UUID}")

			cmd = {
				"action": "remove serie",
				"data": {
					"uuid": UUID
				}
			}
			self.trigger_cb(cmd=cmd, data_type=IOTypes.CMD_DICT)

	def select_all_samples_cb(self, sender, app_data):
		for UUID in self.samples_dict:
			dpg.set_value(f"sample_checkbox_{UUID}", True)
			self.sample_checkbox_cb(f"sample_checkbox_{UUID}", True, UUID)

	def deselect_all_samples_cb(self, sender, app_data):
		for UUID in self.samples_dict:
			dpg.set_value(f"sample_checkbox_{UUID}", False)
			self.sample_checkbox_cb(f"sample_checkbox_{UUID}", False, UUID)

	def clear_samples_cb(self, sender, app_data):
		for UUID in list(self.samples_dict.keys()):
			dpg.delete_item(f"sample_checkbox_{UUID}")
			dpg.delete_item(f"sample_name_{UUID}")
			dpg.delete_item(f"sample_group_{UUID}")
			del self.samples_dict[UUID]

			self.sample_checkbox_cb(f"sample_checkbox_{UUID}", False, UUID)

	def trigger_cb(self, *args, **kwargs):
		"""Sends the last known status as STATUS_DICT to all outputs."""
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				if idx == 0:
					module.input_cb( *args, **kwargs)

EXPORTED_CLASS = Sample_container_win
EXPORTED_NAME = "Sample Container"
