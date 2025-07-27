import importlib.util
import os
import json
from typing import Optional, Dict, List, Any, Type
import dearpygui.dearpygui as dpg
from loguru import logger

MODULES_REGISTRY: List[Any] = []  # List of all currently registered module instances


def register_module(module: Any) -> None:
    """Register a module instance in the global registry."""
    if module not in MODULES_REGISTRY:
        MODULES_REGISTRY.append(module)


def unregister_module(module: Any) -> None:
    """Unregister a module and clean up its references in other modules' connections."""
    if module in MODULES_REGISTRY:
        MODULES_REGISTRY.remove(module)

    for other in MODULES_REGISTRY:
        for output_key in other.connections:
            if module in other.connections[output_key]:
                print(module, "unregistering from", other, "output", output_key)
                other.connections[output_key].remove(module)


def get_registered_modules() -> List[Any]:
    """Return the list of registered module instances."""
    return MODULES_REGISTRY


def clear_registry() -> None:
    """Clear all registered modules."""
    MODULES_REGISTRY.clear()


def get_available_modules(base_path: str = "modules") -> Dict[str, Type[Any]]:
    """
    Discover available module files and return a dict mapping module paths to classes.
    Looks for .py files that define an `EXPORTED_CLASS`.
    """
    module_registry: Dict[str, Type[Any]] = {}

    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_path).replace("\\", "/")
                module_name = rel_path[:-3].replace("/", ".")

                spec = importlib.util.spec_from_file_location(module_name, full_path)
                mod = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(mod)  # type: ignore
                except Exception as e:
                    logger.error(f"Failed to load module {module_name}: {e}")
                    continue

                if hasattr(mod, "EXPORTED_CLASS"):
                    module_registry[module_name] = mod.EXPORTED_CLASS

    return module_registry


def export_workspace(instances: Optional[List[Any]] = None, filepath: str = "layout.json") -> None:
    """
    Export the layout and connections of all registered module instances to a JSON file.
    """
    if instances is None:
        instances = get_registered_modules()

    data = {
        "windows": [win.serialize() for win in instances],
        "connections": [
            {
                "from": win.UUID,
                "output": output_key,
                "to": tgt.UUID,
            }
            for win in instances
            for output_key, targets in getattr(win, "connections", {}).items()
            for tgt in targets
        ],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    logger.success(f"Workspace exported to {filepath}")


def load_workspace(filepath: str = "layout.json", module_registry: Optional[Dict[str, Type[Any]]] = None) -> List[Any]:
    """
    Load a workspace from a JSON file and recreate modules, merges, and connections.
    """
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    if module_registry is None:
        module_registry = get_available_modules()

    clear_registry()
    instances: Dict[str, Any] = {}
    merge_requests: List[tuple[str, str]] = []

    # Recreate each module window
    for wdata in data["windows"]:
        module_path = wdata["module"]
        cls = module_registry.get(module_path)
        if not cls:
            logger.warning(f"Unknown module: {module_path}")
            continue

        size = wdata.get("size", [-1, -1])
        visible = wdata.get("visible", True)

        params = dict(wdata.get("params", {}))
        merge_target_uuid = params.pop("merged_into", None)

        try:
            win = cls(
                uuid=wdata["uuid"],
                pos=tuple(wdata["pos"]),
                win_width=size[0],
                win_height=size[1],
                visible=visible,
                **params,
            )
        except Exception as e:
            logger.error(f"Failed to instantiate {cls} with UUID {wdata['uuid']}: {e}")
            continue

        register_module(win)
        instances[wdata["uuid"]] = win

        if merge_target_uuid:
            merge_requests.append((wdata["uuid"], merge_target_uuid))

        if dpg.does_item_exist(win.winID):
            dpg.set_item_pos(win.winID, win.pos)
            dpg.set_item_width(win.winID, win.win_width)
            dpg.set_item_height(win.winID, win.win_height)
            dpg.configure_item(win.winID, show=visible)

    # Reapply merges
    for src_uuid, tgt_uuid in merge_requests:
        src = instances.get(src_uuid)
        tgt = instances.get(tgt_uuid)
        if src and tgt:
            src.merge_into(tgt)

    # Recreate connections
    for conn in data["connections"]:
        src = instances.get(conn["from"])
        tgt_entry = conn.get("to")
        output_key = conn.get("output")

        # Legacy support: list of targets
        if isinstance(tgt_entry, list):
            for tgt_uuid in tgt_entry:
                tgt_obj = instances.get(tgt_uuid)
                if src and tgt_obj:
                    src.connect_to(tgt_obj, output=0)
            continue

        tgt = instances.get(tgt_entry)
        if src and tgt and output_key is not None:
            src.connect_to(tgt, output=output_key)

    logger.success(f"Workspace loaded from {filepath}")
    return list(instances.values())


def create_module_instance(cls: Type[Any]) -> Any:
    """
    Instantiate and register a module class.
    """
    instance = cls()
    register_module(instance)
    return instance
