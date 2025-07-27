import dearpygui.dearpygui as dpg

with dpg.theme() as theme:
    with dpg.font_registry():
        fontsize = 20
        default_font = dpg.add_font("ressources/consola.ttf", fontsize)
    dpg.bind_font(default_font)
    # dpg.set_global_font_scale(0.5)

    with dpg.theme_component(dpg.mvAll):
        #Window
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (30,30,40,255))
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 15, 15)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 5)
        dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)
        dpg.add_theme_color(dpg.mvThemeCol_Border, (50,50,50,50))
        dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0,0,0,0))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (0,60,170,255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (20,110,170,255))
        dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 5)
        dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 6, 5)
        dpg.add_theme_style(dpg.mvStyleVar_IndentSpacing, 20)
        dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 10)
        dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 5)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
        dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 20)
        dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 5)
        dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 5)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (30,60,80,255))
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (40,40,50, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Border, (110,110,128, 128))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (85,85,85,255))
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (30,60,80,255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (35,50,80,255))
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (0,0,0,0))

        #Graph
        dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 2, category=dpg.mvThemeCat_Plots)
        dpg.add_theme_color(dpg.mvPlotCol_Crosshairs, (255, 0, 50, 175), category=dpg.mvThemeCat_Plots)
        dpg.add_theme_style(dpg.mvPlotStyleVar_FillAlpha, 0.50)
        dpg.add_theme_color(dpg.mvPlotCol_Fill, (100, 150, 220, 50), category=dpg.mvThemeCat_Plots)

def edit_button_style(id, color) :
    with dpg.theme() as button_theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0,255,0,255))
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding,30)
    dpg.bind_item_theme(id,button_theme)

def set_button_color(button_tag, color):
    """
    Sets the color of a button in the Dear PyGui interface.

    Parameters:
        button_tag (int): The unique identifier for the button whose color is to be set.
        color (tuple): A tuple representing the color in RGBA format (e.g., (255, 0, 0, 255) for red).
    """
    with dpg.theme() as theme_id:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, color, category=dpg.mvThemeCat_Core)
            dpg.bind_item_theme(button_tag, theme_id)
