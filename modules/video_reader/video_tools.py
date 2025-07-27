import cv2
import time 

class Video_tools() :
	def __init__(self):
		self.video = None
		self.last_frame = None

		self.fps = 30
		self.playback_fps = 30
		self.last_read_ts = time.perf_counter()

	def set_video(self, path):
		self.video = cv2.VideoCapture(path, cv2.CAP_FFMPEG)

	def read(self):
		if self.video is not None:
			return self.video.read()
		return False, None

	def read_first_frame(self, file) :
		'''Get the first frame of the video'''
		video = cv2.VideoCapture(file, cv2.CAP_FFMPEG)
		ret , frame = video.read()
		return frame

video = Video_tools() 