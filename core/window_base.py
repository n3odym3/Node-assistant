import dearpygui.dearpygui as dpg
from core.module_registry import register_module, unregister_module, MODULES_REGISTRY
from loguru import logger

class WindowBase:
    """
    Base class for GUI modules in the system.
    Handles window creation, merging, serialization, and connectivity between modules.
    """

    def __init__(self,
                label="Window",
                pos=(10, 10),
                win_width=-1,
                win_height=-1,
                uuid=None,
                outputs=None,
                visible=True,
                 **kwargs):
        """
        Initialize a WindowBase instance.

        Args:
            label: Display label of the window.
            pos: Tuple for initial window position.
            win_width: Initial window width.
            win_height: Initial window height.
            uuid: Optional unique identifier.
            outputs: Dictionary of output types.
            visible: Whether the window is visible at creation.
            **kwargs: Additional persistent fields to apply.
        """
        self.label = label
        self.pos = pos
        self.win_width = win_width
        self.win_height = win_height
        self.visible = visible
        self.outputs = outputs or {}
        self.UUID = uuid or str(dpg.generate_uuid())
        self.winID = f"{label}_{self.UUID}"
        self.handler_tag = None
        self.accepted_input_types = []

        if not hasattr(self, "_persistent_fields"):
            self._persistent_fields = ["label"]

        for field in self._persistent_fields:
            if field in kwargs:
                setattr(self, field, kwargs[field])

        self.connections = {k: [] for k in self.outputs}
        self._original_children = []
        self.merged_into = None

        register_module(self)

    def _list_children(self):
        """Save the current list of children for potential restoration."""
        if dpg.does_item_exist(self.winID):
            return dpg.get_item_children(self.winID, 1) or []

    def inform_leaving(self, child_id):
        """Notify the target window that this window is leaving (used in recursive merges)."""
        for child in child_id:
            if child in self._original_children:
                self._original_children.remove(child)

        if self.merged_into is not None:
            self.merged_into.inform_leaving(child_id)

    def merge_into(self, target_window):
        """
        Move all widgets into another WindowBase instance.
        Restore first if already merged.
        """
        if not isinstance(target_window, WindowBase):
            raise TypeError("target_window must be a WindowBase")

        if self.merged_into is target_window:
            return

        if self.merged_into is not None:
            self.restore_contents()

        childrens = self._list_children()

        if set(childrens) & set(target_window._original_children):
            logger.warning(f"Cannot merge {self.label} into {target_window.label}: cyclic merge detected.")
            return

        self._original_children = childrens
        for child in self._original_children:
            dpg.move_item(child, parent=target_window.winID)

        dpg.hide_item(self.winID)
        self.merged_into = target_window

    def restore_contents(self):
        """Move back previously moved widgets to this window."""
        self.merged_into.inform_leaving(self._original_children)
        for child in self._original_children:
            if dpg.does_item_exist(child):
                dpg.move_item(child, parent=self.winID)

        self._original_children.clear()
        self.merged_into = None
        dpg.show_item(self.winID)

    def is_merged(self):
        """Check whether this window has been merged elsewhere."""
        return bool(self._original_children)

    def absorb(self, source_window):
        """Merge another window's content into this one."""
        if not isinstance(source_window, WindowBase):
            raise TypeError("source_window must be a WindowBase")
        source_window.merge_into(self)

    def eject(self, absorbed_window):
        """Restore a previously absorbed window."""
        if not isinstance(absorbed_window, WindowBase):
            raise TypeError("eject() expects a WindowBase instance.")
        absorbed_window.restore_contents()

    def get_merge_target_label(self):
        """Returns the label of the window this one is merged into, or None."""
        return self.merged_into.label if self.merged_into else None

    def connect_to(self, target, output=None):
        """
        Connect this module to another based on output type.

        Args:
            target: The target WindowBase instance.
            output: Output name (str) or index (int).

        Returns:
            True if the connection is valid and made, False otherwise.
        """
        if not hasattr(target, "accepted_input_types"):
            logger.error(f"Target {target} has no accepted_input_types")
            return False

        if isinstance(output, int):
            try:
                output_key = list(self.outputs.keys())[output]
            except IndexError:
                logger.error(f"Invalid output index: {output}")
                return False
        elif isinstance(output, str):
            if output not in self.outputs:
                logger.error(f"Output key '{output}' not found in outputs")
                return False
            output_key = output
        else:
            logger.error(f"Output must be a key (str) or index (int), got {type(output)}")
            return False

        output_type = self.outputs[output_key]
        input_types = getattr(target, "accepted_input_types", [])

        if input_types and output_type not in input_types:
            logger.warning(f"Incompatible types: {output_type} → {input_types}")
            return False

        if target not in self.connections[output_key]:
            self.connections[output_key].append(target)

        return True

    def _is_output_compatible_with(self, target):
        """Internal: Check if any output type is compatible with target's accepted input types."""
        output_types = getattr(self, "output_types", [])
        input_types = getattr(target, "accepted_input_types", [])
        return any(o in input_types for o in output_types)

    def disconnect_from(self, *windows):
        """Disconnect this module from the provided windows."""
        for win in windows:
            if win in self.outputs:
                self.outputs.remove(win)

    def serialize(self):
        """Serialize window state and configuration for saving/restoration."""
        if dpg.does_item_exist(self.winID):
            self.pos = dpg.get_item_pos(self.winID)
            self.win_width, self.win_height = dpg.get_item_rect_size(self.winID)
            self.visible = dpg.is_item_visible(self.winID)

        params = {field: getattr(self, field) for field in self._persistent_fields}

        if self.merged_into:
            params["merged_into"] = self.merged_into.UUID

        return {
            "module": self.__class__.__module__.replace("modules.", ""),
            "class_name": self.__class__.__name__,
            "uuid": self.UUID,
            "pos": self.pos,
            "size": [self.win_width, self.win_height],
            "visible": self.visible,
            "params": params,
        }

    def close(self):
        """Clean up and unregister the window from the registry."""
        if dpg.does_item_exist(self.winID):
            dpg.delete_item(self.winID)

        if dpg.does_item_exist(self.handler_tag):
            dpg.delete_item(self.handler_tag)

        unregister_module(self)
        self.connections.clear()

    def __del__(self):
        logger.info(f"WindowBase {self.label} ({self.UUID}) has been deleted.")

    def is_outputs_ready(self):
        """Check if all connected targets are ready to receive data."""
        for modules in self.connections.values():
            for module in modules:
                is_ready = getattr(module, "is_ready", lambda: True)
                if callable(is_ready) and not is_ready():
                    return False
        return True
