import time
from collections import deque

class FPSCounter:
	def __init__(self, smoothing_window=10):
		self.last_time = None
		self.raw_fps = 0.0
		self.smoothed_fps = 0.0
		self.samples = deque(maxlen=smoothing_window)
		self.smoothing_window = smoothing_window
		self.call_count = 0

	def tick(self) -> tuple[float, float]:
		"""Call this once per frame. Returns (raw_fps, smoothed_fps)."""
		now = time.time()

		if self.last_time is not None:
			delta = now - self.last_time
			if delta > 0:
				self.raw_fps = 1.0 / delta
				self.samples.append(self.raw_fps)
				self.call_count += 1
				
				if self.call_count % self.smoothing_window == 0 and len(self.samples) == self.smoothing_window:
					self.smoothed_fps = sum(self.samples) / self.smoothing_window

		self.last_time = now
		return self.raw_fps, self.smoothed_fps