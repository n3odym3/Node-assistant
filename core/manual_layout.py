from modules.basic_ui.text_viewer_win import Text_viewer_win
from modules.basic_ui.Hello_world_win import HelloWorld_win

def create_windows():
    helloworld = HelloWorld_win(label="Hello World", pos=(50, 50), win_width=300, win_height=200)
    text_viewer = Text_viewer_win(label="Text Viewer", pos=(350, 50), win_width=400, win_height=300)

    helloworld.connect_to(text_viewer,0)



# from modules.computer_vision.binarize.binarise_win import Binarize_win
# from modules.computer_vision.contour_detection.contour_detection_win import Contour_detection_win
# from modules.computer_vision.tracker.tracker_win import Tracker_win

# def create_windows():
#     binarise = Binarize_win(label="Binarize", pos=(50, 50), win_width=300, win_height=200)
#     contour_detection = Contour_detection_win(label="Contour Detection", pos=(50, 50), win_width=400, win_height=300)
#     tracker = Tracker_win(label="Object Tracker", pos=(50, 50), win_width=400, win_height=300)

#     binarise.connect_to(contour_detection, 3)
#     contour_detection.connect_to(tracker, "Detections")

#     tracker.merge_into(contour_detection)
#     contour_detection.merge_into(binarise)
