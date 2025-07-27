import numpy as np
import cv2
from typing import Any, Dict, Optional, Tuple
from core.processing_base import ProcessingBase

class Contour_detection(ProcessingBase):
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

	def _process_data(self, data: Tuple[np.ndarray, np.ndarray], p: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
		frame, mask = data
		return self._detect_contours(frame, mask, p)

	def _detect_contours(self, frame: np.ndarray, mask: np.ndarray, params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
		lower_surface_thresh = int(params.get('lower_surface_thresh', 25))
		upper_surface_thresh = int(params.get('upper_surface_thresh', 100))
		show_blobs = params.get('show_blobs', True)
		isolate_selection = params.get('isolate_selection', True)
		show_boxes = params.get('show_boxes', True)
		show_centroids = params.get('show_centroids', True)
		visu_format = params.get('visu_format', 'Frame')

		calibration = 1.0
		detections = []

		if visu_format == 'Mask' and isolate_selection:
			orig_frame = frame.copy()
		if visu_format == 'Mask':
			frame = np.zeros_like(frame, dtype=np.uint8)

		cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
		calib_bounding_boxes = [cv2.minAreaRect(c) for c in cnts]
		calib_areas = [(box[1][0]) * (box[1][1]) for box in calib_bounding_boxes]

		if len(calib_areas) < 1:
			return frame, mask

		left_thresh = np.percentile(calib_areas, lower_surface_thresh)
		right_thresh = np.percentile(calib_areas, upper_surface_thresh)
		filtered_bounding_boxes = [
			box for box, area in zip(calib_bounding_boxes, calib_areas)
			if left_thresh <= area <= right_thresh
		]

		if show_blobs and mask is not None:
			frame[mask > 0] = (0, 0, 255)

		if isolate_selection and mask is not None:
			selection_mask = np.zeros_like(mask, dtype=np.uint8)

		for bounding_box in filtered_bounding_boxes:
			center = (int(bounding_box[0][0]), int(bounding_box[0][1]))
			dimensions = (bounding_box[1][0] * calibration, bounding_box[1][1] * calibration)

			detections.append(center)

			cell_length = max(dimensions)
			cell_width = min(dimensions)

			if mask is not None:
				box = np.array(cv2.boxPoints(bounding_box), dtype='int')

				if isolate_selection:
					cv2.fillPoly(selection_mask, [box], 255)

				if show_boxes:
					cv2.drawContours(frame, [box.astype('int')], -1, (0, 255, 0), 1, cv2.LINE_AA)

				if show_centroids:
					cv2.circle(frame, center, 2, (0, 0, 255), -1, cv2.LINE_AA)

		if isolate_selection and mask is not None:
			if visu_format == 'Mask':
				frame[selection_mask == 255] = orig_frame[selection_mask == 255]
			else:
				frame[selection_mask != 255] = 0

		return frame, mask, detections
