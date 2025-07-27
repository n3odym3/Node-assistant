import numpy as np
import cv2
from typing import Any, Dict, Optional
from core.processing_base import ProcessingBase
from norfair import Tracker, Detection
import random 

class Point_tracker(ProcessingBase):
	def __init__(
		self,
		params: Optional[Dict[str, Any]] = None,
		*,
		buffer_size: int = 10,
		drop_policy: str = 'drop_new',
		daemon: bool = True,
		logger=None
	) -> None:
		
		super().__init__(
			params=params,
			buffer_size=buffer_size,
			drop_policy=drop_policy,
			daemon=daemon,
			logger=logger
		)

		self.tracker = Tracker(
				distance_function=params.get('distance_function', 'euclidean'),
				distance_threshold=params.get('distance_trheshold', 30),
			)
		self.tracking = {}   # {id :# {id : {points:[(x,y)], color:(r,g,b)}}}

	def _get_random_color(self):
		return tuple(random.randint(50, 255) for _ in range(3))
	
	def _process_data(self, data, p: Dict[str, Any]) -> Any:
		frame, point_list = data
		return self._track_points(frame,point_list, p)

	# def _track_points(self, frame: np.ndarray, point_list: list, p: Dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
	# 	detections = [Detection(np.array(center)) for center in point_list]
	# 	tracked_objects = self.tracker.update(detections)

	# 	trail_length = p.get("trail_length", 30)
	# 	show_trail = p.get("show_trail", False)
	# 	show_id = p.get("show_id", False)
	# 	show_centers = p.get("show_centers", False)
		
	# 	for obj in tracked_objects:
	# 		cx, cy = map(int, obj.estimate[0])
			
	# 		if obj.id not in self.tracking:
	# 			self.tracking[obj.id] = {
	# 				"color": self._get_random_color(),
	# 				"points": [],
	# 				"dim": []
	# 			}

	# 		self.tracking[obj.id]["points"].append((cx, cy))

	# 		while len(self.tracking[obj.id]["points"]) > trail_length:
	# 			self.tracking[obj.id]["points"].pop(0)
			
	# 		if show_trail:
	# 			trail = self.tracking[obj.id]["points"]
	# 			if len(trail) >= 2:
	# 				for i in range(1, len(trail)):
	# 					pt1 = trail[i - 1]
	# 					pt2 = trail[i]
	# 					cv2.line(frame, pt1, pt2, self.tracking[obj.id]["color"], 2, cv2.LINE_AA)

	# 		if show_id :
	# 			cv2.putText(frame, f"{obj.id}", (cx+4, cy-4),cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,255,0), 1,cv2.LINE_AA)
		
	# 	return frame, self.tracking
	

	def _track_points(self, frame: np.ndarray, point_list: list, p: Dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
		detections = [Detection(np.array(center)) for center in point_list]
		tracked_objects = self.tracker.update(detections)

		trail_length = p.get("trail_length", 30)
		show_trail = p.get("show_trail", False)
		show_id = p.get("show_id", False)
		show_age = p.get("show_age", False)
		show_distance = p.get("show_distance", False)
		show_speed = p.get("show_speed", False)

		for obj in tracked_objects:
			cx, cy = map(int, obj.estimate[0])

			if obj.id not in self.tracking:
				self.tracking[obj.id] = {
					"color": self._get_random_color(),
					"points": [],
					"dim": [],
					"distance": 0.0,
					"age": obj.age
				}

			# Mise à jour des données
			self.tracking[obj.id]["points"].append((cx, cy))
			self.tracking[obj.id]["distance"] += getattr(obj, "last_distance", 0.0)
			self.tracking[obj.id]["age"] = obj.age

			# Trail
			if show_trail:
				trail = self.tracking[obj.id]["points"][-trail_length:]
				if len(trail) >= 2:
					for i in range(1, len(trail)):
						pt1 = trail[i - 1]
						pt2 = trail[i]
						cv2.line(frame, pt1, pt2, self.tracking[obj.id]["color"], 2, cv2.LINE_AA)

			# Overlay texte
			text_lines = []
			if show_id:
				text_lines.append(f"ID:{obj.id}")
			if show_age:
				text_lines.append(f"Age:{obj.age}")
			if show_distance:
				text_lines.append(f"Dist:{self.tracking[obj.id]['distance']:.1f}")
			if show_speed and obj.age > 0:
				speed = self.tracking[obj.id]['distance'] / obj.age
				text_lines.append(f"Speed:{speed:.2f}")

			for i, line in enumerate(text_lines):
				cv2.putText(
					frame, line, (cx + 4, cy + 12 + i * 12),
					cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1, cv2.LINE_AA
				)

		return frame, self.tracking