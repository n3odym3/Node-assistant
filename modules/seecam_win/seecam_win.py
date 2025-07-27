import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes
from modules.seecam_win.seecam import Seecam
import threading

class Seecam_win(WindowBase):
	def __init__(self,
				label="Seecam",
				win_width=300,
				win_height=200,
				pos=(10, 10),
				uuid=None,
				outputs=None,
				visible=True): 

		super().__init__(label=label,pos=pos,win_width=win_width,win_height=win_height,uuid=uuid,outputs=outputs,visible=visible)

		self.refresh_tag = "seecam_refresh" + self.UUID
		self.camlist_tag = "seecam_camlist" + self.UUID
		self.camstatus_tag = "seecam_status" + self.UUID
		self.caminfo_tag = "seecam_info" + self.UUID
		self.webcam_gain_tag = "seecam_gain" + self.UUID
		self.webcam_exposure_tag = "seecam_exposure" + self.UUID
		self.contrast_tag = "seecam_contrast" + self.UUID
		self.frame_avg_tag = "seecam_frame_avg" + self.UUID
		self.auto_exposure_tag = "seecam_auto_exposure" + self.UUID
		self.view_webcam_tag = "seecam_view_webcam" + self.UUID

		self.camlist = []
		self.cam_running = False
		self.cam_thread = None

		self.seecam = Seecam()

		self._persistent_fields = ["label"]
		self.accepted_input_types = [IOTypes.CMD_DICT]
		self.outputs = {
			"8bit RGB": IOTypes.FRAME,
			"16bit gray": IOTypes.FRAME16
		}
		self.connections = {k: [] for k in self.outputs}
		
		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):
	
			with dpg.group(horizontal=True):
				dpg.add_button(label="Refresh", tag=self.refresh_tag ,callback=self.refresh_cam)
				dpg.add_combo(items=self.camlist, tag= self.camlist_tag, width=200, callback=self.select_cam)

			dpg.add_text("Status : not initialized", tag=self.camstatus_tag)
			dpg.add_text("Info : NA", tag=self.caminfo_tag)

			with dpg.group(horizontal=True):
				dpg.add_slider_int(label="Lum.", default_value=0, min_value=0, max_value=0, tag=self.webcam_gain_tag, callback=self.set_gain)

			with dpg.group(horizontal=True):
				dpg.add_slider_int(label= "Exp.", default_value=0, min_value=0, max_value=0, tag=self.webcam_exposure_tag, callback=self.set_exposure)

			with dpg.group(horizontal=True):
				dpg.add_text("Frame avg. : 0", tag=self.frame_avg_tag)
			
			with dpg.group(horizontal=True):
				dpg.add_text("Auto exp ")
				dpg.add_checkbox(default_value=False, tag=self.auto_exposure_tag)

			# with dpg.group(horizontal=True):
			# 	dpg.add_text("View webcam")
			# 	dpg.add_checkbox(tag= self.view_webcam_tag, default_value=True, callback=self.webcam_view_cb)

			self.auto_select_cam()


	def refresh_cam(self):
		self.camlist = self.seecam.list_devices()
		filtered_camlist = [cam for cam in self.camlist if "See3" in cam]
		dpg.configure_item(self.camlist_tag, items=filtered_camlist)

	def select_cam(self, sender, cam_name):
		ret, infos = self.seecam.init(cam_name)
		self.cam_running = ret

		if ret :
			dpg.set_value(self.camstatus_tag, "Status : running")
			dpg.set_value(self.caminfo_tag, f"Status : {infos[0]} {infos[1]}x{infos[2]}")

			gain_limits = self.seecam.get_gain_limits()

			if gain_limits:
				dpg.configure_item(self.webcam_gain_tag, min_value = gain_limits[0] ,max_value= gain_limits[1])

				current_gain = self.seecam.get_gain()
				dpg.set_value(self.webcam_gain_tag, current_gain)

			exposure_limits = self.seecam.get_exposure_limits()
			if exposure_limits:
				dpg.configure_item(self.webcam_exposure_tag, min_value = exposure_limits[0] ,max_value= exposure_limits[1])
				current_gain = self.seecam.get_gain()
				dpg.set_value(self.webcam_gain_tag, current_gain)

			exposure_limits = self.seecam.get_exposure_limits()
			if exposure_limits:
				dpg.configure_item(self.webcam_exposure_tag, min_value = exposure_limits[0] ,max_value= exposure_limits[1])

				current_exposure = self.seecam.get_exposure()
				dpg.set_value(self.webcam_exposure_tag, current_exposure)

			self.start_webcam_thread()

	def auto_select_cam(self):
		self.refresh_cam()
		for camname in self.camlist:
			if "See3" in camname:
				dpg.set_value(self.camlist_tag, camname)
				self.select_cam(None, camname)
				break

	def set_gain(self, sender,app_data):
		self.seecam.set_gain(app_data)
	
	def set_exposure(self, sender, app_data):
		self.seecam.set_exposure(app_data)

	def start_webcam_thread(self):
		if self.cam_thread and self.cam_thread.is_alive():
			self.cam_running = False
			self.cam_thread.join()

		self.cam_running = True

		def task():
			while self.cam_running:
				ret,frame = self.seecam.read()
				if frame is not None:
					frame8_bit = self.seecam.convert_to_8bit(frame, depth=10)
					frame8_bit = self.seecam.convert_to_BGR(frame8_bit)

					self.trigger_cb(frame, frame8_bit)

					if dpg.get_value(self.auto_exposure_tag):
						dpg.set_value(self.webcam_exposure_tag, self.seecam.auto_expos(frame8_bit))
					
					dpg.set_value(self.frame_avg_tag, f"Frame avg. : {self.seecam.calc_exposure(frame8_bit):.0f}")


		self.cam_thread = threading.Thread(target=task)
		self.cam_thread.start()

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
					module.input_cb(args[1])
				if idx == 1:
					module.input_cb(args[0])

EXPORTED_CLASS = Seecam_win
EXPORTED_NAME = "Seecam"
