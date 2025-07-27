import dearpygui.dearpygui as dpg
from core.window_base import WindowBase
from core.input_ouput_types import IOTypes
import cv2
import numpy as np

class Tracking_processor_win(WindowBase):
	def __init__(self,
				label="Tracking Processor",
				win_width=400,
				win_height=300,
				pos=(20, 20),
				uuid=None,
				outputs=None,
				visible=True): 

		super().__init__(label=label, pos=pos, win_width=win_width, win_height=win_height,
						uuid=uuid, outputs=outputs, visible=visible)

		self._persistent_fields = ["label"]
		self.accepted_input_types = [IOTypes.TRACKING]
		self.outputs = {
			"Trace": IOTypes.FRAME,
			"Sample data": IOTypes.TRACKING
		}
		self.connections = {k: [] for k in self.outputs}

		self.table_tag = f"tracking_processor_table_{self.UUID}"
		self.distance_threshold_tag = f"tracking_processor_distance_threshold_{self.UUID}"
		self.reset_selection_tag = f"tracking_processor_reset_selection_{self.UUID}"

		self.last_selection = None
		self.tracking_data = {}


		with dpg.window(label=self.label,
						width=self.win_width,
						height=self.win_height,
						pos=self.pos,
						tag=self.winID,
						show=self.visible):
			with dpg.group(horizontal=True):
				dpg.add_text("Distance Threshold:")
				dpg.add_drag_int(tag=self.distance_threshold_tag, default_value=100, min_value=0, max_value=1000, width=100)

				dpg.add_button(label="Reset Selection", tag=self.reset_selection_tag, callback=self._reset_selection_cb)

			with dpg.table(header_row=True, tag=self.table_tag,
							resizable=True, policy=dpg.mvTable_SizingStretchProp,
							borders_innerH=True, borders_outerH=True,
							borders_innerV=True, borders_outerV=True, sortable=True,callback=self._sort_callback):

				for col in ["ID","Speed","Distance","Age"]:
					dpg.add_table_column(label=col)

	def input_cb(self, data, *args, **kwargs):
		self.tracking_data = data
		self._refresh_table()

	def _sort_callback(self, sender, sort_specs):
		return 
		if sort_specs is None:
			return

		col_index, direction = sort_specs[0]
		reverse = direction < 0

		rows = dpg.get_item_children(sender, 1)
		row_data = []

		for row in rows:
			cells = dpg.get_item_children(row, 1)
			if col_index >= len(cells):
				continue

			value = dpg.get_value(cells[col_index])

			try:
				value = float(value)
			except ValueError:
				pass

			row_data.append((row, value))

		row_data.sort(key=lambda x: x[1], reverse=reverse)
		new_order = [row[0] for row in row_data]

		dpg.reorder_items(sender, 1, new_order)

	def _refresh_table(self):
		for tag in dpg.get_item_children(self.table_tag)[1]:
			dpg.delete_item(tag)
	
		threshold = dpg.get_value(self.distance_threshold_tag)

		for obj_id, info in self.tracking_data.items():
			age = info.get("age", 0)
			dist = info.get("distance", 0.0)
			speed = dist / age if age > 0 else 0.0

			if dist < threshold:
					continue
			
			with dpg.table_row(parent=self.table_tag, tag=f"row_{obj_id}"):
				dpg.add_selectable(label=str(obj_id), callback=self._row_select_cb, user_data=obj_id, span_columns=True)
				dpg.add_text(f"{speed:.2f}")
				dpg.add_text(f"{dist:.2f}")
				dpg.add_text(str(age))

	def _reset_selection_cb(self, sender, app_data):
		self.last_selection = None
		rows = dpg.get_item_children(self.table_tag, 1)

		for row in rows:
			cells = dpg.get_item_children(row, 1)
			if not cells:
				continue
			selectable = cells[0]
			dpg.set_value(selectable, False)

		self.trigger_cb(frame=None, tracking={})

	def _row_select_cb(self, sender, app_data, user_data):
		output_data = []

		rows = dpg.get_item_children(self.table_tag, 1)
		
		for row in rows:
			cells = dpg.get_item_children(row, 1)
			if not cells:
				continue

			selectable = cells[0]
			if dpg.get_value(selectable):
				
				obj_id = int(dpg.get_item_label(selectable))
				info = self.tracking_data.get(obj_id, {})

				dist = info.get("distance", 0.0)
				age = info.get("age", 0)
				speed = dist / age if age > 0 else 0.0
				points = info.get("points", [])
				color = info.get("color", (0, 255, 0))

				output_data.append({
					"id": obj_id,
					"age": age,
					"distance": dist,
					"speed": speed,
					"points": points,
					"color": color
				})

		frame = np.zeros((720, 1280, 3), dtype=np.uint8)

		for obj in output_data:
			points = obj["points"]
			color = obj["color"]
			obj_id = obj["id"]

			if len(points) >= 2:
				for i in range(1, len(points)):
					pt1 = tuple(map(int, points[i - 1]))
					pt2 = tuple(map(int, points[i]))
					cv2.line(frame, pt1, pt2, color, 2, cv2.LINE_AA)

			if points:
				cx, cy = map(int, points[-1])
				cv2.putText(frame, f"ID:{obj_id}", (cx + 4, cy - 4),
							cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)


		self.trigger_cb(frame=frame, tracking=output_data)

	def is_ready(self):
		return True

	def is_outputs_ready(self):
		return True
	
	def trigger_cb(self,frame, tracking):
		"""Sends the last known status as STATUS_DICT to all outputs."""
		for idx, output_key in enumerate(self.outputs):
			connected_modules = self.connections.get(output_key, [])
			for module in connected_modules:
				if idx == 0:
					module.input_cb(data=frame, data_type=IOTypes.FRAME)
				if idx == 1:
					module.input_cb(tracking, data_type=IOTypes.TRACKING)

EXPORTED_CLASS = Tracking_processor_win
EXPORTED_NAME = "Tracking Processor"