from typing import Any, Dict, Optional
from core.processing_base import ProcessingBase
import time  

class Processor_Template(ProcessingBase):
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

    def _process_data(self ) -> Any:
        time.sleep(10)
        return True