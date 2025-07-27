import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
import numpy as np
from core.input_ouput_types import IOTypes

class Lineplot_win(WindowBase):
	def __init__(self,
				label="Lineplot",
				win_width=300,
				win_height=200,
				pos=(10, 10),
				uuid=None,
				outputs=None,
				visible=True):

		if outputs is None:
			outputs = [] 

		super().__init__(label=label,pos=pos,win_width=win_width,win_height=win_height,uuid=uuid,outputs=outputs,visible=visible)

		self.plot_tag = "lineplot_plot" + self.UUID
		self.anot_check_tag = "lieplot_anot_check" + self.UUID
		self.xaxis_tag = "lineplot_x_axis" + self.UUID
		self.yaxis_tag = "lineplot_y_axis" + self.UUID
		self.dragline_tag = "lineplot_dragline" + self.UUID
		self.closest_point_anot_tag = "closest_point_anot" + self.UUID
		self.handler_tag = "lineplot_handler" + self.UUID


		self._persistent_fields = ["label"]
		self.accepted_input_types = [IOTypes.POSITION,IOTypes.DATALIST,IOTypes.CMD_DICT]
		self.output_types = ["str"]

		self.outputs = {
			"Datalist" : IOTypes.DATALIST,
			"Position" : IOTypes.POSITION,
			"CMD" : IOTypes.CMD_DICT
		}

		self.descriptions = {
			"Datalist" : "Outputs the data as a list of points",
			"Position" : "Outputs the position of the mouse in the plot",
			"CMD" : "Outputs a command dictionary with the action to perform"
		}
		
		self.connections = {k: [] for k in self.outputs}

		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):
			
			#Create an empty plot that will be filled by the plot_callback
			dpg.add_checkbox(label="Anotation", tag=self.anot_check_tag, default_value=True)

			with dpg.plot(label="Line Serie", height=-1, width=-1, tag=self.plot_tag):
				dpg.add_plot_legend()

				dpg.add_plot_axis(dpg.mvXAxis, label="Time", tag=self.xaxis_tag)
				dpg.add_plot_axis(dpg.mvYAxis, label="Intensity", tag=self.yaxis_tag)

				dpg.add_drag_line(label="dline1", tag=self.dragline_tag, color=[255, 0, 0, 255], callback=self.dragline_callback)

			#Add mouse handlers to the plot to automatically update the crop values when the user zooms in/out
			with dpg.handler_registry(tag=self.handler_tag):
				dpg.add_mouse_move_handler(callback=self.plot_change_callback)
				# dpg.add_mouse_wheel_handler(callback=self.plot_change_callback)
				# dpg.add_mouse_drag_handler(callback=self.plot_change_callback, button=dpg.mvMouseButton_Left)
				# dpg.add_mouse_drag_handler(callback=self.plot_change_callback, button=dpg.mvMouseButton_Right)

			#Edit the plot settings
			dpg.configure_item(self.plot_tag, anti_aliased=True)
			dpg.configure_item(self.plot_tag, crosshairs=True)

	def find_closest_point(self, mouse_x, mouse_y, x_data, y_data):
		x_scale = 1 / x_data.ptp()
		y_scale = 1 / y_data.ptp()
		distances = np.hypot((x_data - mouse_x) * x_scale,(y_data - mouse_y) * y_scale)
		return np.argmin(distances)
	
	def select_serie(self, sender, app_data, user_data):
		'''Select the serie that will be tracked/anotated'''
		self.selected_serie = user_data

	def plot_change_callback(self,sender, app_data):
		if dpg.is_item_hovered(self.plot_tag) : #If the mouse is over the plot
			if dpg.does_item_exist(self.closest_point_anot_tag) :
				dpg.delete_item(self.closest_point_anot_tag) #Delete the previous anotation

			if dpg.get_value(self.anot_check_tag) : #If the anotation checkbox is checked
				axis = dpg.get_item_children(self.yaxis_tag, 1)
				
				if len(axis) > 0: #If there is a plot in the preview window
					if self.selected_serie is not None and dpg.does_item_exist(self.selected_serie) and dpg.get_item_type(self.selected_serie) == "mvAppItemType::mvLineSeries" :
						plot = dpg.get_value(self.selected_serie) #Get the selected serie
					else :
						plot = dpg.get_value(axis[0]) #Get the first by default

					xplot = plot[0] #get the X data
					yplot = plot[1] #get the Y data
					
					mouse_x, mouse_y = dpg.get_plot_mouse_pos() #get the mouse position
					point_index = self.find_closest_point(mouse_x, mouse_y, np.array(xplot), np.array(yplot)) #Find the closest point between the mouse and the plot

					annot = f"Index : {point_index}\nX : {xplot[point_index]}\nY : {yplot[point_index]}"
					dpg.add_plot_annotation(tag=self.closest_point_anot_tag, label=annot, default_value=(xplot[point_index], yplot[point_index]), offset=(25, -25), color=[255, 255, 0, 255], parent=self.plot_tag)   

	def autofit_axis(self,x=True,y=True):
		if x :
			dpg.fit_axis_data(self.xaxis_tag)
		if y :
			dpg.fit_axis_data(self.yaxis_tag)

	def clear_plot(self):
		children = dpg.get_item_children(self.yaxis_tag, 1)
		for child in children:
			if dpg.get_item_type(child) == "mvAppItemType::mvLineSeries":
				dpg.delete_item(child)

	def move_dragline(self, x):
		dpg.set_value(self.dragline_tag, x)
	
	def dragline_callback(seklf, sender, app_data):
		pass

	def plot_data(self, x =None, y =None, name="Serie", UUID=None):
		if x is None :
			x = list(range(len(y)))

		serie_id = f"prevplot_{UUID}"

		if dpg.does_item_exist(serie_id) :
			dpg.configure_item(serie_id, x=x, y=y)
			self.autofit_axis()
		else :
			dpg.add_line_series(x=x, y=y, label=name, parent=self.yaxis_tag, tag=serie_id)
			dpg.add_button(label="Select serie", user_data =dpg.last_item() , parent=dpg.last_item(), callback=self.select_serie)

			if len(dpg.get_item_children(self.yaxis_tag)[1]) < 2 :
				self.autofit_axis()

		self.select_serie(None,None, serie_id)

	def input_cb(self, *args, **kwargs):
		if kwargs.get("data_type") == IOTypes.CMD_DICT:
			cmd = kwargs.get("cmd")

			if cmd and cmd.get("action") == "add serie":
				data = cmd.get("data", {})
				self.plot_data(x=data.get("x", None), y=data.get("y", None), name=data.get("name", None), UUID=data.get("uuid", None))

			if cmd and cmd.get("action") == "remove serie":
				data = cmd.get("data", {})
				UUID = data.get("uuid", None)
				if UUID is not None:
					dpg.delete_item(f"prevplot_{UUID}")
			
			if cmd and cmd.get("action") == "update serie name":
				data = cmd.get("data", {})
				UUID = data.get("uuid", None)
				new_name = data.get("name", None)
				if UUID is not None and new_name is not None:
					if dpg.does_item_exist(f"prevplot_{UUID}"):
						dpg.set_item_label(f"prevplot_{UUID}", new_name)
			return

		y = kwargs.get("y") or (args[0] if args and isinstance(args[0], list) else None)
		x = kwargs.get("x") or (args[1] if len(args) > 1 and isinstance(args[1], list) else None)
		name = kwargs.get("name", "Serie")
		UUID = kwargs.get("uuid", None)
		self.plot_data(x=x, y=y, name=name, UUID=UUID)

	def trigger_cb(self, *args, **kwargs):
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				pass
			#TODO: Implement the trigger callback logic

EXPORTED_CLASS = Lineplot_win
EXPORTED_NAME = "Lineplot"
