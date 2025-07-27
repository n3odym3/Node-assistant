import numpy as np
import cv2
from typing import Any, Dict, Optional
from core.processing_base import ProcessingBase

class Binarize_Frame(ProcessingBase):
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

    def _process_data(self, frame: Any, p: Dict[str, Any]) -> Any:
        return self._binarize_frame(frame, p)

    def _binarize_frame(self, frame: np.ndarray, p: Dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
        blur = int(p.get('blur', 3))
        block_size = int(p.get('block_size', 25))
        bin_thresh = int(p.get('bin_thresh', 15))
        erosion = int(p.get('erosion', 0))

        if isinstance(frame, np.ndarray) and len(frame.shape) == 3 and frame.shape[2] == 3:
            mask = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            mask = frame.copy()

        mask = cv2.GaussianBlur(mask, (blur, blur), 0)
        mask = cv2.adaptiveThreshold(
            mask, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            block_size, bin_thresh
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, None, iterations=erosion)

        return frame, mask