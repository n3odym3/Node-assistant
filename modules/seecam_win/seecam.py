from loguru import logger

from pygrabber.dshow_graph import FilterGraph,FilterType
from pygrabber.dshow_ids import MediaSubtypes, MediaTypes
from pygrabber.dshow_core import IAMCameraControlIID, IAMVideoProcAmpIID

import numpy as np
import time
import cv2 

from comtypes import COMError, CoInitialize
from ctypes import c_long, byref

CameraControl_Pan      = 0
CameraControl_Tilt     = 1
CameraControl_Roll     = 2
CameraControl_Zoom     = 3
CameraControl_Exposure = 4
CameraControl_Iris     = 5
CameraControl_Focus    = 6
CameraControl_Flags_Auto   = 0x0001
CameraControl_Flags_Manual = 0x0002

VideoProcAmp_Brightness            = 0
VideoProcAmp_Contrast              = 1
VideoProcAmp_Hue                   = 2
VideoProcAmp_Saturation            = 3
VideoProcAmp_Sharpness             = 4
VideoProcAmp_Gamma                 = 5
VideoProcAmp_ColorEnable           = 6
VideoProcAmp_WhiteBalance          = 7
VideoProcAmp_BacklightCompensation = 8
VideoProcAmp_Gain                  = 9
VideoProcAmp_Flags_Auto   = 0x0001
VideoProcAmp_Flags_Manual = 0x0002

class Seecam:
	def __init__(self):
		try:
			CoInitialize()
		except:
			pass

		self.defined = False
		self.graph = FilterGraph()
		self.last_frame = None
		self.frame_ready = False
		self.camera_filter = None
		self.cam_ctrl = None
		self.proc_amp = None
		self.max_exposure_check = 4
		self.exposure_check_count = 0

	def init(self, cam) :
		if type(cam) == str:
			camlist = self.list_devices()
			cam = camlist.index(cam)

		if cam >= 0:
			try :
				self.graph.add_video_input_device(cam)
				logger.trace(f"Setting format => {self.set_format(8)}")#720P Y16 90FPS
				logger.trace(f"Adding null render")
				self.graph.add_null_render()

				logger.trace(f"Adding sample grabber")
				self.graph.add_sample_grabber(self.frame_callback)
				sample_grabber = self.graph.filters[FilterType.sample_grabber]

				self.format, self.width, self.height = self.graph.get_input_device().get_current_format()

				logger.trace(f"Setting media type")
				match self.format:
					case "Y8":
						sample_grabber.set_media_type(MediaTypes.Video, MediaSubtypes.Y8)
					case "Y12":
						sample_grabber.set_media_type(MediaTypes.Video, MediaSubtypes.Y12)
					case "Y16":
						sample_grabber.set_media_type(MediaTypes.Video, MediaSubtypes.Y16)
				
				logger.trace(f"Preparing preview graph")
				self.graph.prepare_preview_graph()

				logger.trace(f"Running graph")
				self.graph.run()

			except Exception as e:
				print(e)
				return False, None
			
			self.camera_filter = self.graph.filters[FilterType.video_input].instance

			self.cam_ctrl = self.camera_filter.QueryInterface(IAMCameraControlIID)
			self.proc_amp = self.camera_filter.QueryInterface(IAMVideoProcAmpIID)

			self.defined = True
			return True, (self.format, self.width, self.height)

	def list_devices(self):
		return self.graph.get_input_devices()

	def list_formats(self):
		if self.defined:
			return self.graph.get_input_device().get_formats()
		return False

	def set_format(self, format_index):
		formats = self.graph.get_input_device().get_formats()
		for format in formats:
			if format_index == format['index']:
				self.graph.get_input_device().set_format(format_index)
				self.format = format['media_type_str']
				return True
		return False

	def frame_callback(self, buffer, blen):
		if self.format == "Y8":
			buffer_np = np.ctypeslib.as_array(buffer, shape=(blen,))
			buffer = buffer_np.view(dtype=np.uint8)
			frame = buffer.reshape((self.height, self.width))

		if self.format == "Y12":
			buffer_np = np.ctypeslib.as_array(buffer, shape=(blen,))
			triplets = buffer_np.reshape(-1, 3)

			pixel1 = ((triplets[:, 0].astype(np.uint16) << 4) | (triplets[:, 2] & 0x0F))
			pixel2 = ((triplets[:, 1].astype(np.uint16) << 4) | ((triplets[:, 2] >> 4) & 0x0F))

			pixels = np.empty((self.width * self.height,), dtype=np.uint16)
			pixels[0::2] = pixel1
			pixels[1::2] = pixel2

			frame = pixels.reshape(self.height, self.width)

		if self.format == "Y16":
			buffer_np = np.ctypeslib.as_array(buffer, shape=(blen,))
			buffer = buffer_np.view(dtype=np.uint16)
			frame = buffer.reshape((self.height, self.width))

		self.last_frame = frame
		self.frame_ready = True

	def close(self):
		pass

	def read(self,instant=False):
		frame = None
		self.frame_ready = False
		if self.defined:
			if self.graph.grab_frame() :
				if not instant:
					while not self.frame_ready:
						time.sleep(0.001)
				frame = self.last_frame
			return True, frame
		return False, frame

	def convert_to_8bit(self, frame, depth=12) :
		match depth :
			case 8:
				result = frame
			case 10 :
				result = (frame >> 2).astype(np.uint8)
			case 12 :
				result = (frame >> 4).astype(np.uint8)
			case 16 :
				result = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
		return result

	def convert_to_BGR(self, frame):
		return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

	def calc_exposure(self,frame):
		return np.mean(frame)

	def auto_expos(self, frame, target_exposure=200, threshold=50, min_exposure = -13, max_exposure=-6):
		frame_exposure = self.calc_exposure(frame)
		current_exposure = self.get_exposure()

		if frame_exposure < target_exposure - threshold:
			if self.exposure_check_count > self.max_exposure_check:
				if current_exposure <= max_exposure:
					self.set_exposure(current_exposure + 1)
					self.exposure_check_count = 0
			else:
				self.exposure_check_count += 1

		elif frame_exposure > target_exposure + threshold:
			if self.exposure_check_count > self.max_exposure_check:
				if current_exposure > min_exposure:
					self.set_exposure(current_exposure - 1)
					self.exposure_check_count = 0
			else:
				self.exposure_check_count += 1
		
		return self.get_exposure()

	def list_camera_parameters(self):
		if not self.cam_ctrl:
			return False
		
		camera_control_props = [
			(CameraControl_Pan,      "Pan"),
			(CameraControl_Tilt,     "Tilt"),
			(CameraControl_Roll,     "Roll"),
			(CameraControl_Zoom,     "Zoom"),
			(CameraControl_Exposure, "Exposure"),
			(CameraControl_Iris,     "Iris"),
			(CameraControl_Focus,    "Focus"),
		]

		result = {}

		for prop_id, prop_name in camera_control_props:

			min_val = c_long()
			max_val = c_long()
			step_val = c_long()
			default_val = c_long()
			caps_flags = c_long()

			try:
				hr = self.cam_ctrl.GetRange(
					prop_id,
					byref(min_val),
					byref(max_val),
					byref(step_val),
					byref(default_val),
					byref(caps_flags)
				)
				if hr == 0:
					result[prop_name] = {
						"min": min_val.value,
						"max": max_val.value,
						"step": step_val.value,
						"default": default_val.value,
						"caps": caps_flags.value
					}
				else:
					result[prop_name] = None
			except COMError:
				result[prop_name] = None

		return result

	def get_exposure_limits(self):
		cam_params = self.list_camera_parameters()
		if cam_params["Exposure"] is not None :
			return cam_params["Exposure"]["min"], cam_params["Exposure"]["max"]
		return None

	def set_exposure(self, exposure_value: int, manual: bool = True) -> bool:
		if not self.cam_ctrl:
			return False

		flags = CameraControl_Flags_Manual if manual else CameraControl_Flags_Auto
		try:
			hr = self.cam_ctrl.Set(
				CameraControl_Exposure,
				exposure_value,
				flags
			)
			if hr == 0:
				return True
			else:
				return False
		except COMError as e:
			return False

	def get_exposure(self):
		if not self.cam_ctrl:
			return None
			
		value = c_long()
		flags = c_long()
		try:
			hr = self.cam_ctrl.Get(CameraControl_Exposure, byref(value), byref(flags))
			if hr == 0:
				return value.value
		except COMError as e:
			return None
		return None

	def list_video_proc_parameters(self):

		if not self.proc_amp:
			return {}

		video_proc_amp_props = [
			(VideoProcAmp_Brightness,            "Brightness"),
			(VideoProcAmp_Contrast,              "Contrast"),
			(VideoProcAmp_Hue,                   "Hue"),
			(VideoProcAmp_Saturation,            "Saturation"),
			(VideoProcAmp_Sharpness,             "Sharpness"),
			(VideoProcAmp_Gamma,                 "Gamma"),
			(VideoProcAmp_ColorEnable,           "ColorEnable"),
			(VideoProcAmp_WhiteBalance,          "WhiteBalance"),
			(VideoProcAmp_BacklightCompensation, "BacklightComp"),
			(VideoProcAmp_Gain,                  "Gain"),
		]

		result = {}
		for prop_id, prop_name in video_proc_amp_props:
			min_val = c_long()
			max_val = c_long()
			step_val = c_long()
			default_val = c_long()
			caps_val = c_long()

			try:
				hr = self.proc_amp.GetRange(
					prop_id,
					byref(min_val),
					byref(max_val),
					byref(step_val),
					byref(default_val),
					byref(caps_val)
				)
				if hr == 0:
					result[prop_name] = {
						"min":     min_val.value,
						"max":     max_val.value,
						"step":    step_val.value,
						"default": default_val.value,
						"caps":    caps_val.value,
					}
				else:
					result[prop_name] = None
			except COMError:
				result[prop_name] = None

		return result

	def get_gain_limits(self):
		proc_params = self.list_video_proc_parameters()
		if proc_params["Brightness"] is not None :
			return proc_params["Brightness"]["min"], proc_params["Brightness"]["max"]
		return None

	def set_gain(self, gain_value: int, manual: bool = True) -> bool:
		if not self.proc_amp:
			return False

		flags = CameraControl_Flags_Manual
		try:
			hr = self.proc_amp.Set(
				VideoProcAmp_Brightness,
				gain_value,
				flags
			)
			if hr == 0:
				return True
			else:
				return False
		except COMError as e:
			return False

	def get_gain(self):
		if not self.proc_amp:
			return None
			
		value = c_long()
		flags = c_long()
		try:
			hr = self.proc_amp.Get(VideoProcAmp_Brightness, byref(value), byref(flags))
			if hr == 0:
				return value.value
		except COMError as e:
			return None
		return None
