from enum import Enum
from typing import Any


class IOTypes(str, Enum):
    """
    Enum class to define standard I/O data types for modules.
    Each member has:
        - value: string key used in communication
        - dtype: string description of the data type
        - description: human-readable explanation
    """

    def __new__(cls, value: str, dtype: str, description: str) -> 'IOTypes':
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.dtype = dtype
        obj.description = description
        return obj

    TRIGGER = ("trigger", "str or None", "Trigger event, no data")
    FILE_PATH = ("file_path", "str", "Path to a file, e.g., image or video")
    FOLDER_PATH = ("folder_path", "str", "Path to a folder")
    FRAME = ("frame", "np.ndarray", "Image frame, typically a numpy array")
    FRAME16 = ("frame16", "np.ndarray", "16-bit image frame, typically a numpy array")
    MASK = ("mask", "np.ndarray", "Binary mask, typically a numpy array")
    FRAME_MASK_PAIR = ("frame_mask_pair", "tuple", "Tuple of (frame, mask), both numpy arrays")
    TEXT = ("text", "str", "Plain text input")
    NUMBER = ("number", "int-float", "Single numeric value, e.g., 42 or 3.14")
    CMD_DICT = ("cmd_dict", "dict", "Command dictionary")
    CMD_LIST = ("cmd_list", "list", "List of commands")
    STATUS_DICT = ("status_dict", "dict", "Status dictionary with various keys")
    DATALIST = ("datalist", "[[list][list],name]", "List of X,Y data pairs, e.g., [[0,1,2],[10,20,30],'test']")
    POSITION = ("position", "int-float", "1D position, e.g., 100 or 100.5")
    POINT_LIST = ("point_list", "list", "List of points, e.g., [[x1, y1], [x2, y2]]")
    TRACKING = ("tracking", "dict", "Tracking data, e.g., {id: {'points': [(x,y)], 'dim': [(w,h)], 'color': (r,g,b)}}")
