import dearpygui.dearpygui as dpg
from core.module_registry import export_workspace, MODULES_REGISTRY
from core.fusion_manager import FusionManager
from core.node_editor import NodeEditor


class Main_win:
    """
    Main application window with a menu bar for managing modules, tools, and workspace saving.
    """

    def __init__(self) -> None:
        self.winID: str = "main_win"

        with dpg.window(tag=self.winID):
            # Create top menu bar
            with dpg.menu_bar():
                # File menu
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Save Workspace", callback=self.save_workspace)

                # Modules menu
                with dpg.menu(label="Modules"):
                    dpg.add_menu_item(label="Node Editor", callback=lambda: node_editor.show())
                    dpg.add_menu_item(label="Fusion Manager", callback=lambda: fusion_manager.show())

                # Tools menu
                with dpg.menu(label="Tools"):
                    dpg.add_menu_item(label="Show Debug", callback=lambda: dpg.show_tool(dpg.mvTool_Debug))
                    dpg.add_menu_item(label="Show Font Manager", callback=lambda: dpg.show_tool(dpg.mvTool_Font))
                    dpg.add_menu_item(label="Show Item Registry", callback=lambda: dpg.show_tool(dpg.mvTool_ItemRegistry))
                    dpg.add_menu_item(label="Show Metrics", callback=lambda: dpg.show_tool(dpg.mvTool_Metrics))
                    dpg.add_menu_item(label="Toggle Fullscreen", callback=lambda: dpg.toggle_viewport_fullscreen())
                    dpg.add_menu_item(label="Show About", callback=lambda: dpg.show_tool(dpg.mvTool_About))

            # Apply custom theme to the main window
            with dpg.theme() as mainwin_theme:
                with dpg.theme_component(dpg.mvAll):
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (20, 20, 25, 255))

            dpg.bind_item_theme(self.winID, mainwin_theme)

    def save_workspace(self) -> None:
        """
        Save the current module workspace layout to a JSON file.
        """
        export_workspace(MODULES_REGISTRY, "layouts/manual_layout.json")


# Instantiate global components
fusion_manager: FusionManager = FusionManager()
node_editor: NodeEditor = NodeEditor()
main_win: Main_win = Main_win()
