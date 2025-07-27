import dearpygui.dearpygui as dpg
from core.module_registry import get_available_modules, create_module_instance
from collections import defaultdict
from loguru import logger
from typing import Any, Dict, Tuple, List, Optional


class NodeEditor:
    """
    NodeEditor manages a visual node-based interface using DearPyGui.
    It supports dynamic module instantiation, node linking, validation of type compatibility,
    and interactive graph reconstruction from saved instances.
    """

    def __init__(self, label: str = "Node editor") -> None:
        """
        Initialize the NodeEditor and build the base GUI with popup and editor area.
        """
        self.UUID: str = str(dpg.generate_uuid())
        self.winID: str = f"{label}_{self.UUID}"
        self.node_map: Dict[int, Any] = {}  # Maps node_id to module instance
        self.link_map: Dict[int, Tuple[int, int]] = {}  # Maps link_id to (output_attr_id, input_attr_id)
        self.mouse_pos: List[float] = [0.0, 0.0]
        self.popup_tag: str = "node_popup_menu"
        self.editor_tag: str = "node_editor"
        self.anchor_node_tag: str = "anchor_node"

        with dpg.window(label=label, width=800, height=600, pos=(25, 25), tag=self.winID, show=False):

            # Create the main node editor canvas
            with dpg.node_editor(callback=self.link_callback,
                                delink_callback=self.delink_callback,
                                tag=self.editor_tag,
                                minimap=True,
                                minimap_location=dpg.mvNodeMiniMap_Location_BottomRight):

                # Add an anchor node used for panning correction
                with dpg.node(label="", draggable=False, tag=self.anchor_node_tag):
                    with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                        dpg.add_text("")

            # Right and left click handlers
            with dpg.handler_registry():
                dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Right, callback=self.right_click_callback)
                dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left, callback=self.left_click_callback)

            # Popup menu for creating new modules
            with dpg.window(tag=self.popup_tag, show=False, no_title_bar=True, no_resize=True, no_move=True):
                grouped_modules = defaultdict(list)
                for name, cls in get_available_modules().items():
                    folder, module = name.split(".", 1)
                    grouped_modules[folder].append((module, cls))

                for folder, entries in grouped_modules.items():
                    with dpg.menu(label=folder):
                        for module_name, cls in entries:
                            dpg.add_menu_item(label=module_name, callback=self.add_node, user_data=cls)

        logger.info("Node editor initialized")

    def show(self) -> None:
        """Show the node editor window."""
        dpg.show_item(self.winID)
        dpg.focus_item(self.editor_tag)

    def hide(self) -> None:
        """Hide the node editor window."""
        dpg.hide_item(self.winID)

    def get_mouse_pos(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Calculate mouse position relative to the editor area,
        correcting for internal panning using the anchor node.

        Returns:
            Tuple containing relative and absolute mouse position.
        """
        abs_pos = dpg.get_mouse_pos(local=False)
        ref_screen_pos = dpg.get_item_rect_min(self.anchor_node_tag)
        ref_editor_pos = dpg.get_item_pos(self.anchor_node_tag)
        pan_offset = (ref_editor_pos[0] - ref_screen_pos[0], ref_editor_pos[1] - ref_screen_pos[1])
        rel_pos = (abs_pos[0] + pan_offset[0], abs_pos[1] + pan_offset[1])
        return rel_pos, abs_pos

    def right_click_callback(self, sender: int, app_data: Any) -> None:
        """
        Open popup menu at the mouse location if the editor is hovered.
        """
        if dpg.is_item_hovered(self.editor_tag):
            self.mouse_pos, absolute_mouse_pos = self.get_mouse_pos()
            dpg.focus_item(self.popup_tag)
            dpg.configure_item(self.popup_tag, pos=absolute_mouse_pos, show=True)

    def left_click_callback(self, sender: int, app_data: Any) -> None:
        """
        Hide the popup menu if the click occurs outside of it.
        """
        if dpg.is_item_visible(self.popup_tag):
            if dpg.is_item_hovered(self.popup_tag):
                return
            for child in dpg.get_item_children(self.popup_tag, 1):
                if dpg.is_item_hovered(child):
                    return
            dpg.configure_item(self.popup_tag, show=False)

    def delete_node(self, sender: int, app_data: Any, node_id: int) -> None:
        """
        Delete a node and all its links from the editor.
        """
        if node_id in self.node_map:
            dpg.delete_item(node_id)
            self.node_map[node_id].close()
            del self.node_map[node_id]

            to_remove = [lid for lid, (src, tgt) in self.link_map.items()
                        if src == node_id or tgt == node_id]

            for lid in to_remove:
                from_attr, to_attr = self.link_map[lid]
                src = self.node_map.get(dpg.get_item_parent(from_attr))
                tgt = self.node_map.get(dpg.get_item_parent(to_attr))
                if src and tgt and tgt in src.outputs:
                    src.outputs.remove(tgt)
                dpg.delete_item(lid)
                del self.link_map[lid]

    def add_node(self, sender: int, app_data: Any, module_class: Any) -> None:
        """
        Add a new node to the editor based on the selected module class.
        """
        label = module_class.__name__

        with dpg.node(label=label, parent=self.editor_tag, pos=self.mouse_pos) as node_id:
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("In")

            instance = create_module_instance(module_class)
            self.node_map[node_id] = instance

            for output in instance.outputs.keys():
                with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, tag=f"{node_id}_{output}"):
                    dpg.add_text(output)

                if hasattr(instance, "descriptions") and output in instance.descriptions:
                    with dpg.tooltip(parent=f"{node_id}_{output}"):
                        dpg.add_text(instance.descriptions[output])

        with dpg.popup(node_id, mousebutton=dpg.mvMouseButton_Right):
            dpg.add_button(label="Delete Node", callback=self.delete_node, user_data=node_id)

        dpg.configure_item(self.popup_tag, show=False)

    def _get_output_IDs(self, node_id: int) -> List[int]:
        """
        Return all output attribute IDs from a given node.
        """
        children = dpg.get_item_children(node_id, 1)
        return [attr_id for attr_id in children
                if dpg.get_item_type(attr_id) == "mvAppItemType::mvNodeAttribute"
                and dpg.get_item_configuration(attr_id).get("attribute_type") == dpg.mvNode_Attr_Output]

    def link_callback(self, sender: int, app_data: Tuple[int, int]) -> None:
        """
        Callback triggered when a link is created between two node attributes.
        Validates type compatibility before adding.
        """
        link_id = dpg.generate_uuid()
        from_attr, to_attr = app_data
        from_node = dpg.get_item_parent(from_attr)
        to_node = dpg.get_item_parent(to_attr)

        src = self.node_map.get(from_node)
        tgt = self.node_map.get(to_node)

        output_ids = self._get_output_IDs(from_node)
        try:
            output_index = output_ids.index(from_attr)
            src_key = list(src.outputs.keys())[output_index]
        except (ValueError, IndexError):
            logger.warning("Failed to resolve output key from attribute.")
            return

        src_type = src.outputs.get(src_key)
        tgt_types = getattr(tgt, "accepted_input_types", [])

        if tgt_types and src_type not in tgt_types:
            logger.warning(f"Incompatible types: {src_type} → {tgt_types}")
            return

        if tgt not in src.connections[src_key]:
            src.connections[src_key].append(tgt)
            dpg.add_node_link(from_attr, to_attr, parent=self.editor_tag, tag=link_id)
            self.link_map[link_id] = (from_attr, to_attr)

    def delink_callback(self, sender: int, app_data: int) -> None:
        """
        Callback triggered when a link is removed manually.
        Updates connection tracking and internal mappings.
        """
        link_id = app_data
        if link_id not in self.link_map:
            dpg.delete_item(link_id)
            return

        from_attr, to_attr = self.link_map.pop(link_id)
        from_node = dpg.get_item_parent(from_attr)
        to_node = dpg.get_item_parent(to_attr)

        src = self.node_map.get(from_node)
        tgt = self.node_map.get(to_node)

        if src and tgt:
            output_ids = self._get_output_IDs(from_node)
            try:
                output_index = output_ids.index(from_attr)
                src_key = list(src.outputs.keys())[output_index]
                if tgt in src.connections[src_key]:
                    src.connections[src_key].remove(tgt)
            except (ValueError, IndexError, KeyError):
                logger.warning("Unable to disconnect nodes cleanly.")

        dpg.delete_item(link_id)

    def _get_first_input_attr(self, node_id: int) -> Optional[int]:
        """
        Get the first input attribute ID of a node, if any.
        """
        for attr in dpg.get_item_children(node_id, 1):
            config = dpg.get_item_configuration(attr)
            if config.get("attribute_type") == dpg.mvNode_Attr_Input:
                return attr
        return None

    def connect_nodes_by_output_name(self, source_node_id: int, target_node_id: int, output_name: str) -> None:
        """
        Programmatically connect two nodes using an output name as key.
        Validates compatibility and adds visual link.
        """
        src = self.node_map.get(source_node_id)
        tgt = self.node_map.get(target_node_id)
        if not src or not tgt:
            logger.warning("Invalid source or target node instance.")
            return

        src_type = src.outputs.get(output_name)
        tgt_types = getattr(tgt, "accepted_input_types", [])
        if tgt_types and src_type not in tgt_types:
            logger.warning(f"Incompatible types: {src_type} → {tgt_types}")
            return

        from_attr = None
        for attr_id in self._get_output_IDs(source_node_id):
            for child_id in dpg.get_item_children(attr_id, 1):
                if dpg.get_item_type(child_id) == "mvAppItemType::mvText" and dpg.get_value(child_id) == output_name:
                    from_attr = attr_id
                    break
            if from_attr:
                break

        if from_attr is None:
            logger.warning(f"Output '{output_name}' not found on node {source_node_id}")
            return

        input_attr = self._get_first_input_attr(target_node_id)
        if input_attr is None:
            logger.warning(f"No input attribute found on node {target_node_id}")
            return

        if tgt in src.connections[output_name]:
            logger.info(f"Connection already exists: {src} → {tgt}")
            return

        src.connections[output_name].append(tgt)
        link_id = dpg.generate_uuid()
        dpg.add_node_link(from_attr, input_attr, parent=self.editor_tag, tag=link_id)
        self.link_map[link_id] = (from_attr, input_attr)

    def rebuild_from_instances(self, instances: List[Any]) -> None:
        """
        Reconstruct node graph from a list of module instances.
        This method is typically used after deserialization.
        """
        uuid_to_nodeid: Dict[str, int] = {}

        for win in instances:
            uuid = getattr(win, "UUID", None)
            if uuid is None:
                continue

            pos = getattr(win, "pos", (100, 100))
            label = getattr(win, "label", win.__class__.__name__)

            with dpg.node(label=label, parent=self.editor_tag, pos=pos) as node_id:
                with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                    dpg.add_text("In")

                self.node_map[node_id] = win
                uuid_to_nodeid[uuid] = node_id

                for output_name in win.outputs.keys():
                    with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                        dpg.add_text(output_name)

                with dpg.popup(node_id, mousebutton=dpg.mvMouseButton_Right):
                    dpg.add_button(label="Delete Node", callback=self.delete_node, user_data=node_id)

        for src_win in instances:
            src_uuid = src_win.UUID
            src_node_id = uuid_to_nodeid.get(src_uuid)
            if src_node_id is None:
                continue

            for output_name, targets in src_win.connections.items():
                from_attr = None
                for attr_id in self._get_output_IDs(src_node_id):
                    for child_id in dpg.get_item_children(attr_id, 1):
                        if dpg.get_item_type(child_id) == "mvAppItemType::mvText" and dpg.get_value(child_id) == output_name:
                            from_attr = attr_id
                            break
                    if from_attr:
                        break

                if from_attr is None:
                    logger.warning(f"Output '{output_name}' not found on node {src_uuid}")
                    continue

                for tgt_win in targets:
                    tgt_node_id = uuid_to_nodeid.get(tgt_win.UUID)
                    if tgt_node_id is None:
                        continue

                    to_attr = self._get_first_input_attr(tgt_node_id)
                    if to_attr is None:
                        logger.warning(f"No input attribute found on node {tgt_win.UUID}")
                        continue

                    link_id = dpg.generate_uuid()
                    dpg.add_node_link(from_attr, to_attr, parent=self.editor_tag, tag=link_id)
                    self.link_map[link_id] = (from_attr, to_attr)
