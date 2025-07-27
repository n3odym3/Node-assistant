import dearpygui.dearpygui as dpg
from core.module_registry import get_registered_modules
from typing import Dict, Optional, Any


class FusionManager:
    """
    UI window to manage the fusion (merging) of modules/windows in a DearPyGui interface.
    Allows visual drag-and-drop merging, displaying which modules are merged, and restoring them.
    """

    def __init__(self, label: str = "Fusion Manager") -> None:
        """
        Initialize the FusionManager window and its UI table.
        """
        self.label: str = label
        self.winID: str = f"fusion_manager_{label}"
        self.table_id: str = f"{self.winID}_table"
        self.tag_to_module: Dict[str, Any] = {}  # Mapping from button tag to module

        with dpg.window(label=self.label, width=600, height=400, tag=self.winID, pos=(25, 25), show=False):
            dpg.add_button(label="Refresh", callback=self.refresh, width=-1)

            with dpg.table(tag=self.table_id, header_row=True,
                            resizable=True, policy=dpg.mvTable_SizingStretchProp,
                            borders_innerH=True, borders_outerH=True):
                dpg.add_table_column(label="Window")
                dpg.add_table_column(label="Merged Into")
                dpg.add_table_column(label="Restore")

        self.refresh()

    def show(self) -> None:
        """
        Show and focus the FusionManager window.
        """
        dpg.show_item(self.winID)
        dpg.focus_item(self.winID)

    def refresh(self, sender: Optional[int] = None, app_data: Optional[Any] = None, user_data: Optional[Any] = None) -> None:
        """
        Clear and repopulate the table with the current list of registered modules,
        showing which ones are merged and offering restore buttons.
        Compatible with DearPyGui callback signature.
        """
        # Clear all existing rows in the table
        for child in dpg.get_item_children(self.table_id, 1):
            dpg.delete_item(child)

        self.tag_to_module.clear()

        for module in get_registered_modules():
            short_id: str = module.UUID[:8]
            btn_tag: str = f"btn_{short_id}"
            self.tag_to_module[btn_tag] = module

            with dpg.table_row(parent=self.table_id):
                btn_lbl: str = f"{module.label}##{short_id}"

                # Button used as both drag source and drop target
                dpg.add_button(label=btn_lbl,
                                tag=btn_tag,
                                drop_callback=self._on_drop,
                                payload_type="windows_fusion",
                                user_data=module,
                                callback=self._on_hover)

                dpg.add_drag_payload(parent=btn_tag,
                                    payload_type="windows_fusion",
                                    drag_data=module.UUID)

                tgt_label: str = module.merged_into.label if module.merged_into else ""
                dpg.add_text(tgt_label)

                if module.merged_into:
                    dpg.add_button(label="Restore", width=100,
                                    user_data=module,
                                    callback=lambda s, a, u: self._restore(u))
                else:
                    dpg.add_spacer(width=70)

    def _on_drop(self, sender: int, payload: Any, user_data: Any) -> None:
        """
        Handle drop event: merge source module (from payload) into the target module (sender).
        """
        target_module = self.tag_to_module.get(sender)
        source_uuid = payload

        if not target_module or not source_uuid:
            return

        source_module = next((m for m in get_registered_modules() if m.UUID == source_uuid), None)

        if not source_module or source_module == target_module:
            return

        source_module.merge_into(target_module)
        self.refresh()

    def _restore(self, module: Any) -> None:
        """
        Restore the contents of a previously merged module.
        """
        module.restore_contents()
        self.refresh()

    def _on_hover(self, sender: int, app_data: Any, user_data: Any) -> None:
        """
        If hovering a button, show and focus the corresponding module's window.
        """
        if dpg.is_item_hovered(sender):
            winID: str = user_data.winID
            if dpg.does_item_exist(winID):
                dpg.show_item(winID)
                dpg.focus_item(winID)
