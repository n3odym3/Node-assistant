import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes
from modules.computer_vision.image_processing.image_processing import Image_processing

class Image_processing_win(WindowBase):
	def __init__(self,
				label="Image Processing",
				win_width=400,
				win_height=300,
				pos=(20, 20),
				uuid=None,
				outputs=None,
				visible=True): 

		super().__init__(label=label, pos=pos, win_width=win_width, win_height=win_height,
						uuid=uuid, outputs=outputs, visible=visible)

		self._persistent_fields = ["label"]
		self.accepted_input_types = [IOTypes.FRAME]
		self.outputs = {
			"Frame": IOTypes.FRAME,
		}
		self.connections = {k: [] for k in self.outputs}
		
		self.processor = Image_processing()

		self.contrast_tag = f"image_processing_contrast_{self.UUID}"
		self.contrast_checkbox_tag = f"image_processing_contrast_checkbox_{self.UUID}"

		self.brightness_tag = f"image_processing_brightness_{self.UUID}"
		self.brightness_checkbox_tag = f"image_processing_brightness_checkbox_{self.UUID}"

		self.negative_tag = f"image_processing_negative_{self.UUID}"
		

		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):
			
			with dpg.group(horizontal=True):
				dpg.add_text("Contrast")
				dpg.add_checkbox(tag=self.contrast_checkbox_tag, default_value=False)
				dpg.add_drag_int(tag=self.contrast_tag, default_value=0, min_value=-100, max_value=100)

			with dpg.group(horizontal=True):
				dpg.add_text("Brightness")
				dpg.add_checkbox(tag=self.brightness_checkbox_tag, default_value=False)
				dpg.add_drag_int(tag=self.brightness_tag, default_value=0, min_value=-100, max_value=100)

			with dpg.group(horizontal=True):
				dpg.add_text("Negative")
				dpg.add_checkbox(tag=self.negative_tag, default_value=False)


	def input_cb(self, data, *args, **kwargs):
		frame = data

		contrast_checkbox = dpg.get_value(self.contrast_checkbox_tag)
		contrast_value = 0
		brightness_checkbox = dpg.get_value(self.brightness_checkbox_tag)
		brightness_value = 0

		if contrast_checkbox or brightness_checkbox:
			if contrast_checkbox:
				contrast_value = dpg.get_value(self.contrast_tag)
			if brightness_checkbox:
				brightness_value = dpg.get_value(self.brightness_tag)
			
			frame = self.processor.change_contrast_brightness(frame, contrast_value, brightness_value)

		if dpg.get_value(self.negative_tag):
			frame = self.processor.negative(frame)
	
		self.trigger_cb(frame=frame)

	def is_ready(self):
		return True

	def is_outputs_ready(self):
		return True
	
	def trigger_cb(self,frame):
		"""Sends the last known status as STATUS_DICT to all outputs."""
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				if idx == 0:
					module.input_cb(data=frame, data_type=IOTypes.FRAME)

EXPORTED_CLASS = Image_processing_win
EXPORTED_NAME = "Image Processing"