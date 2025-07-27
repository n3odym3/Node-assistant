from core import manual_layout

if __name__ == '__main__' :
    from core.module_registry import MODULES_REGISTRY 
    import sys,ctypes

    import multiprocessing
    multiprocessing.freeze_support()
    
    from config.config import config
    
    from loguru import logger
    if config["Debug"]["enabled"] is False:
        logger.disable()
    else :
        logger.configure(
            handlers=[
                {
                    "sink": sys.stdout,
                    "level": config['Debug']['log_level'],
                }
            ]
        )

    import dearpygui.dearpygui as dpg

    dpg.create_context()
    dpg.create_viewport(title=config['General']['app_name'], width=1920, height=1080, vsync=False)
    dpg.setup_dearpygui()

    dpg.configure_app(docking=False)

    from config.dpg_theme import theme
    dpg.bind_theme(theme)
    
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    ES_CONTINUOUS = 0x80000000
    ES_DISPLAY_REQUIRED = 0x00000002
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_DISPLAY_REQUIRED)

    from core.main_win import main_win,fusion_manager,node_editor
    dpg.set_primary_window(main_win.winID, True)

    from core.module_registry import export_workspace,load_workspace
    from core import manual_layout

    dpg.show_viewport()
    logger.info("Starting the app")

    # manual_layout.create_windows()

    # # export_workspace(None, 'layouts/manual_layout.json')
    layout = load_workspace('layouts/manual_layout.json')
    node_editor.rebuild_from_instances(MODULES_REGISTRY)


    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg_running = False
    dpg.destroy_context()

