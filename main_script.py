import tkinter as tk
import keyboard
import pyautogui
import time
from screeninfo import get_monitors
import threading # For running pystray in a separate thread
import sys # For sys.exit()

# System Tray Icon
try:
    from PIL import Image # Pillow, for loading the icon image
    import pystray
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("WARNING: pystray or Pillow not installed. System tray icon feature will be disabled.")
    print("To enable, run: pip install pystray Pillow")

# --- CONFIG IMPORTS (key_config, style_config, feature_config) ---
# (Keep these sections as they were in the previous version)
# Import from your key configuration file
try:
    from key_config import (
        MAIN_GRID_COLS, MAIN_GRID_ROWS,
        SUB_GRID_COLS, SUB_GRID_ROWS,
        get_main_grid_key_map, get_sub_grid_key_map
    )
except ImportError:
    print("ERROR: Could not import from key_config.py.")
    MAIN_GRID_COLS, MAIN_GRID_ROWS = 25, 36
    SUB_GRID_COLS, SUB_GRID_ROWS = 8, 3
    def get_main_grid_key_map(): print("WARNING: Using empty main_grid_key_map."); return {}
    def get_sub_grid_key_map(): print("WARNING: Using empty sub_grid_key_map."); return {}

# Import from your style configuration file
try:
    from style_config import (
        OVERLAY_ALPHA, OVERLAY_BACKGROUND_COLOR,
        GRID_COLOR, GRID_LINE_WIDTH, GRID_LINE_STYLE,
        SUB_GRID_HIGHLIGHT_COLOR, SUB_GRID_HIGHLIGHT_WIDTH,
        TEXT_COLOR, FONT_FAMILY, FONT_SIZE_BEHAVIOR, FONT_FIXED_SIZE, FONT_WEIGHT,
        DOUBLE_CLICK_INTERVAL, LEFT_ALT_KEY_NAME,
        validate_configs
    )
    if 'validate_configs' in globals() and callable(validate_configs):
        if not validate_configs(): print("INFO: Review style_config.py for warnings.")
except ImportError:
    print("ERROR: Could not import from style_config.py. Using default styles.")
    OVERLAY_ALPHA, OVERLAY_BACKGROUND_COLOR = 0.5, "black"
    GRID_COLOR, GRID_LINE_WIDTH, GRID_LINE_STYLE = "white", 1, "line"
    SUB_GRID_HIGHLIGHT_COLOR, SUB_GRID_HIGHLIGHT_WIDTH = "lime", 3
    TEXT_COLOR, FONT_FAMILY, FONT_SIZE_BEHAVIOR = "white", "Arial", "dynamic"
    FONT_FIXED_SIZE, FONT_WEIGHT = 10, "normal"
    DOUBLE_CLICK_INTERVAL, LEFT_ALT_KEY_NAME = 0.35, 'alt'

# Import from your feature configuration file
try:
    from feature_config import (
        ENABLE_FREE_MODE, FREE_MODE_TOGGLE_KEY,
        MOUSE_MOVE_STEP, SCROLL_STEP,
        FREE_MODE_MOUSE_UP, FREE_MODE_MOUSE_DOWN, FREE_MODE_MOUSE_LEFT, FREE_MODE_MOUSE_RIGHT,
        FREE_MODE_SCROLL_UP, FREE_MODE_SCROLL_DOWN, FREE_MODE_SCROLL_LEFT, FREE_MODE_SCROLL_RIGHT
    )
except ImportError:
    print("INFO: Could not import from feature_config.py. Free Mode will be disabled.")
    ENABLE_FREE_MODE = False
    FREE_MODE_TOGGLE_KEY = ''
    MOUSE_MOVE_STEP, SCROLL_STEP = 20, 3
    FREE_MODE_MOUSE_UP, FREE_MODE_MOUSE_DOWN, FREE_MODE_MOUSE_LEFT, FREE_MODE_MOUSE_RIGHT = 'i','k','j','l'
    FREE_MODE_SCROLL_UP, FREE_MODE_SCROLL_DOWN, FREE_MODE_SCROLL_LEFT, FREE_MODE_SCROLL_RIGHT = 'm',',','b','n'


# --- Load Key Maps ---
main_grid_key_map = get_main_grid_key_map()
sub_grid_key_map = get_sub_grid_key_map()

# --- Global State ---
overlay_window = None
canvas = None
overlay_visible = False
current_mode = "main"
first_char_main = None
selected_main_cell_rect = None

g_left_alt_down_for_toggle = False
g_left_alt_press_timestamp = 0

pending_double_click_info = {
    "is_pending": False, "key_char": None, "time": 0,
    "screen_x": 0, "screen_y": 0, "button": "left"
}
_suppressed_keys_in_overlay = set()

free_mode_active = False
tray_icon_object = None # Will hold the pystray.Icon object
app_is_exiting = False # Flag to signal threads to stop

# --- Screen Dimensions ---
try:
    PRIMARY_MONITOR = get_monitors()[0]
    SCREEN_WIDTH, SCREEN_HEIGHT = PRIMARY_MONITOR.width, PRIMARY_MONITOR.height
except Exception:
    print("WARNING: screeninfo failed, falling back to pyautogui for screen size.")
    SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()


# --- SYSTEM TRAY FUNCTIONS ---
def on_quit_callback(icon, item):
    global app_is_exiting, tray_icon_object
    print("Quit command received from system tray.")
    app_is_exiting = True
    if tray_icon_object:
        tray_icon_object.stop() # Stop the pystray icon's event loop

    # Perform other cleanup (keyboard, tkinter)
    # This might be better handled in the main finally block,
    # but signaling is important here.
    keyboard.unhook_all() # Ensure hooks are removed
    if overlay_window and overlay_window.winfo_exists():
        # Schedule Tkinter quit from its own thread if possible,
        # but since tray might be in main thread, direct quit might be needed.
        overlay_window.quit() # This should break the mainloop

    # sys.exit(0) # This might be too abrupt if Tkinter hasn't quit yet.
                 # The main thread should handle exiting after mainloop breaks.

def setup_tray_icon():
    global tray_icon_object
    if not PYSTRAY_AVAILABLE:
        return

    icon_image = None
    try:
        # Make sure 'app_icon.png' (or .ico) is in the same directory
        # or provide the full path.
        icon_image = Image.open("app_icon.png")
    except FileNotFoundError:
        print("WARNING: app_icon.png not found. System tray icon may be missing or default.")
    except Exception as e:
        print(f"WARNING: Could not load app_icon.png: {e}")


    # Define menu items
    menu = (pystray.MenuItem('Quit', on_quit_callback),)

    # Create the icon
    tray_icon_object = pystray.Icon(
        "GridHelper",  # Name for the icon (shows on hover sometimes)
        icon=icon_image,      # The PIL.Image object
        title="Grid Helper",  # Tooltip text
        menu=menu
    )
    print("System tray icon thread starting...")
    tray_icon_object.run() # This is a blocking call, so it runs in its own thread
    print("System tray icon thread finished.") # Should only print on explicit stop


# --- DRAWING, MOUSE, UI FUNCTIONS (largely unchanged) ---
# (Copy the draw_grid, draw_main_grid, draw_sub_grid, perform_mouse_click_action,
#  clear_pending_double_click, create_overlay_window, show_overlay_tk,
#  hide_overlay_tk, actual_toggle_overlay, toggle_free_mode functions from
#  the previous version here. They don't need direct changes for the tray icon
#  itself, but show_overlay_tk and actual_toggle_overlay already handle
#  free_mode_active state which is good.)
def draw_grid(cols, rows, width, height, parent_rect_coords=None, is_sub_grid=False):
    global canvas
    if not canvas: return
    canvas.delete("all")
    base_x, base_y = (parent_rect_coords[0], parent_rect_coords[1]) if parent_rect_coords else (0, 0)
    cell_width, cell_height = width / cols, height / rows
    key_map_to_use = sub_grid_key_map if is_sub_grid else main_grid_key_map
    cell_to_key_map = {v: k for k, v in key_map_to_use.items()}
    for r_idx in range(rows):
        for c_idx in range(cols):
            x1, y1 = base_x + c_idx * cell_width, base_y + r_idx * cell_height
            x2, y2 = x1 + cell_width, y1 + cell_height
            rect_options = {"outline": GRID_COLOR, "width": GRID_LINE_WIDTH}
            if GRID_LINE_STYLE == "dashes": rect_options["dash"] = (4, 4)
            canvas.create_rectangle(x1, y1, x2, y2, **rect_options)
            key_label = cell_to_key_map.get((r_idx, c_idx), "")
            font_size_to_use = FONT_FIXED_SIZE
            if FONT_SIZE_BEHAVIOR == "dynamic":
                font_size_to_use = max(6, min(int(cell_height / 2.5),
                                           int(cell_width / (len(key_label) + 0.5) * 1.2 if key_label else cell_width / 1.5)))
            font_tuple = (FONT_FAMILY, font_size_to_use, FONT_WEIGHT)
            canvas.create_text(x1 + cell_width / 2, y1 + cell_height / 2, text=key_label, fill=TEXT_COLOR, font=font_tuple)
            if is_sub_grid and r_idx == SUB_GRID_ROWS // 2 and c_idx == SUB_GRID_COLS // 2:
                canvas.create_rectangle(x1, y1, x2, y2, outline=SUB_GRID_HIGHLIGHT_COLOR, width=SUB_GRID_HIGHLIGHT_WIDTH)

def draw_main_grid():
    global current_mode
    current_mode = "main"
    if canvas: draw_grid(MAIN_GRID_COLS, MAIN_GRID_ROWS, SCREEN_WIDTH, SCREEN_HEIGHT, is_sub_grid=False)

def draw_sub_grid(parent_cell_rect):
    global selected_main_cell_rect, current_mode
    current_mode = "sub"; selected_main_cell_rect = parent_cell_rect
    x1, y1, x2, y2 = parent_cell_rect
    if canvas: draw_grid(SUB_GRID_COLS, SUB_GRID_ROWS, x2 - x1, y2 - y1, parent_rect_coords=(x1,y1,x2,y2), is_sub_grid=True)

def perform_mouse_click_action(target_x, target_y, is_right_click=False):
    global overlay_window, overlay_visible, current_mode, first_char_main, _suppressed_keys_in_overlay
    if overlay_window and overlay_window.winfo_exists() and overlay_window.state() == 'normal':
        overlay_window.withdraw(); overlay_window.update_idletasks(); time.sleep(0.05)
    button_to_click = 'right' if is_right_click else 'left'
    pyautogui.click(x=int(target_x), y=int(target_y), button=button_to_click)
    print(f"Clicked (Grid Action) {button_to_click} at ({int(target_x)}, {int(target_y)})")
    overlay_visible = False; current_mode = "main"; first_char_main = None
    _suppressed_keys_in_overlay.clear()

def clear_pending_double_click():
    global pending_double_click_info
    pending_double_click_info["is_pending"] = False; pending_double_click_info["key_char"] = None

def create_overlay_window():
    global overlay_window, canvas
    if overlay_window and overlay_window.winfo_exists(): overlay_window.destroy()
    overlay_window = tk.Tk()
    overlay_window.attributes('-alpha', OVERLAY_ALPHA); overlay_window.attributes('-topmost', True)
    overlay_window.overrideredirect(True); overlay_window.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}+0+0")
    overlay_window.configure(bg=OVERLAY_BACKGROUND_COLOR)
    canvas = tk.Canvas(overlay_window, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, bg=OVERLAY_BACKGROUND_COLOR, highlightthickness=0)
    canvas.pack(); overlay_window.withdraw()

def show_overlay_tk():
    global overlay_visible, current_mode, first_char_main, overlay_window, free_mode_active
    if free_mode_active:
        free_mode_active = False
        print("Exited Free Mode (Overlay shown).")
    if not overlay_window or not overlay_window.winfo_exists(): create_overlay_window()
    overlay_visible = True; current_mode = "main"; first_char_main = None
    _suppressed_keys_in_overlay.clear(); clear_pending_double_click()
    draw_main_grid()
    overlay_window.deiconify(); overlay_window.lift(); overlay_window.focus_force()

def hide_overlay_tk():
    global overlay_visible, overlay_window, current_mode, first_char_main
    overlay_visible = False; current_mode = "main"; first_char_main = None
    _suppressed_keys_in_overlay.clear(); clear_pending_double_click()
    if overlay_window and overlay_window.winfo_exists(): overlay_window.withdraw()

def actual_toggle_overlay():
    global free_mode_active
    if overlay_visible:
        if overlay_window and overlay_window.winfo_exists(): overlay_window.after(0, hide_overlay_tk)
    else:
        if free_mode_active:
            free_mode_active = False
            print("Exited Free Mode (Overlay shown by Alt-toggle).")
        if not overlay_window or not overlay_window.winfo_exists(): create_overlay_window()
        if overlay_window and overlay_window.winfo_exists(): overlay_window.after(0, show_overlay_tk)

def toggle_free_mode():
    global free_mode_active, overlay_visible
    if not ENABLE_FREE_MODE: return
    free_mode_active = not free_mode_active
    if free_mode_active:
        if overlay_visible: hide_overlay_tk()
        print("Entered Free Mode. Use IJKL for mouse, M,BN for scroll. Press '`' to exit.")
    else:
        print("Exited Free Mode.")


# --- KEYBOARD EVENT HANDLERS ---
def global_key_event_handler(event):
    global g_left_alt_down_for_toggle, g_left_alt_press_timestamp, overlay_visible, free_mode_active
    global pending_double_click_info, app_is_exiting

    if app_is_exiting: # If app is trying to exit, don't process further key events
        return

    key_name_lower = event.name.lower()

    # Free Mode Toggle Key
    if ENABLE_FREE_MODE and key_name_lower == FREE_MODE_TOGGLE_KEY and event.event_type == keyboard.KEY_DOWN:
        toggle_free_mode()
        return

    # Overlay Alt-Toggle (if not in free mode)
    if not free_mode_active and key_name_lower == LEFT_ALT_KEY_NAME:
        if event.event_type == keyboard.KEY_DOWN:
            if not g_left_alt_down_for_toggle:
                g_left_alt_down_for_toggle = True; g_left_alt_press_timestamp = event.time
        elif event.event_type == keyboard.KEY_UP:
            if g_left_alt_down_for_toggle:
                if 0.01 < (event.time - g_left_alt_press_timestamp) < 0.7: actual_toggle_overlay()
            g_left_alt_down_for_toggle = False
        return
    elif not free_mode_active and g_left_alt_down_for_toggle and event.event_type == keyboard.KEY_DOWN and key_name_lower != LEFT_ALT_KEY_NAME:
        g_left_alt_down_for_toggle = False

    # Blind Double-Click (if not in free mode and overlay not visible)
    if not free_mode_active and not overlay_visible and event.event_type == keyboard.KEY_DOWN and pending_double_click_info["is_pending"]:
        current_input_char_for_map = ' ' if key_name_lower == 'space' else (key_name_lower.upper() if len(key_name_lower) == 1 else None)
        if current_input_char_for_map and current_input_char_for_map == pending_double_click_info["key_char"] and \
           (event.time - pending_double_click_info["time"]) < DOUBLE_CLICK_INTERVAL:
            time.sleep(0.05); pyautogui.click(x=pending_double_click_info["screen_x"], y=pending_double_click_info["screen_y"], button=pending_double_click_info["button"])
            clear_pending_double_click(); return
        else: clear_pending_double_click()

    # Free Mode Actions
    if ENABLE_FREE_MODE and free_mode_active and event.event_type == keyboard.KEY_DOWN:
        if key_name_lower == FREE_MODE_MOUSE_UP: pyautogui.move(0, -MOUSE_MOVE_STEP)
        elif key_name_lower == FREE_MODE_MOUSE_DOWN: pyautogui.move(0, MOUSE_MOVE_STEP)
        elif key_name_lower == FREE_MODE_MOUSE_LEFT: pyautogui.move(-MOUSE_MOVE_STEP, 0)
        elif key_name_lower == FREE_MODE_MOUSE_RIGHT: pyautogui.move(MOUSE_MOVE_STEP, 0)
        elif key_name_lower == FREE_MODE_SCROLL_UP: pyautogui.scroll(SCROLL_STEP)
        elif key_name_lower == FREE_MODE_SCROLL_DOWN: pyautogui.scroll(-SCROLL_STEP)
        elif key_name_lower == FREE_MODE_SCROLL_LEFT: pyautogui.hscroll(-SCROLL_STEP)
        elif key_name_lower == FREE_MODE_SCROLL_RIGHT: pyautogui.hscroll(SCROLL_STEP)
        return

    # Overlay Grid Logic
    if overlay_visible:
        on_key_event_for_active_overlay_logic(event)

# on_key_event_for_active_overlay_logic (unchanged from previous, paste it here)
def on_key_event_for_active_overlay_logic(event):
    global overlay_visible, current_mode, first_char_main, selected_main_cell_rect, overlay_window
    global _suppressed_keys_in_overlay, pending_double_click_info
    key_name_lower = event.name.lower()
    if event.event_type == keyboard.KEY_UP:
        _suppressed_keys_in_overlay.discard(key_name_lower); return
    if key_name_lower == 'esc':
        if overlay_window and overlay_window.winfo_exists(): overlay_window.after(0, hide_overlay_tk)
        return
    is_modifier = key_name_lower in [LEFT_ALT_KEY_NAME.lower(), 'alt right', 'alt gr', 'ctrl', 'right ctrl', 'left ctrl', 'control', 'shift', 'left shift', 'right shift']
    if is_modifier: _suppressed_keys_in_overlay.add(key_name_lower); return
    if key_name_lower in _suppressed_keys_in_overlay: return
    _suppressed_keys_in_overlay.add(key_name_lower)
    input_char_for_map = None
    if key_name_lower == 'space': input_char_for_map = ' '
    elif len(key_name_lower) == 1 and (key_name_lower.isalnum() or key_name_lower in [';', ',', '.', '/']): input_char_for_map = key_name_lower.upper()
    if input_char_for_map is None: return
    if current_mode == "main":
        clear_pending_double_click()
        if first_char_main is None: first_char_main = input_char_for_map
        else:
            key_combo = first_char_main + input_char_for_map
            if key_combo in main_grid_key_map:
                r, c = main_grid_key_map[key_combo]
                cell_w, cell_h = SCREEN_WIDTH / MAIN_GRID_COLS, SCREEN_HEIGHT / MAIN_GRID_ROWS
                x1, y1 = c * cell_w, r * cell_h; x2, y2 = x1 + cell_w, y1 + cell_h
                first_char_main = None
                if overlay_window and overlay_window.winfo_exists(): overlay_window.after(0, lambda rect=(x1,y1,x2,y2): draw_sub_grid(rect))
            else: first_char_main = None
            _suppressed_keys_in_overlay.clear()
    elif current_mode == "sub":
        if not selected_main_cell_rect: _suppressed_keys_in_overlay.discard(key_name_lower); return
        main_x1, main_y1, main_x2, main_y2 = selected_main_cell_rect
        main_w, main_h = main_x2 - main_x1, main_y2 - main_y1
        sub_cell_w, sub_cell_h = main_w / SUB_GRID_COLS, main_h / SUB_GRID_ROWS
        target_r_sub, target_c_sub = -1, -1
        if input_char_for_map == ' ': target_r_sub, target_c_sub = SUB_GRID_ROWS // 2, SUB_GRID_COLS // 2
        elif input_char_for_map in sub_grid_key_map: target_r_sub, target_c_sub = sub_grid_key_map[input_char_for_map]
        if target_r_sub != -1:
            click_x = main_x1 + (target_c_sub * sub_cell_w) + (sub_cell_w / 2)
            click_y = main_y1 + (target_r_sub * sub_cell_h) + (sub_cell_h / 2)
            is_shift_mod = any(keyboard.is_pressed(k) for k in ['shift', 'left shift', 'right shift'])
            perform_mouse_click_action(click_x, click_y, is_right_click=is_shift_mod)
            pending_double_click_info.update({"is_pending": True, "key_char": input_char_for_map, "time": event.time, "screen_x": int(click_x), "screen_y": int(click_y), "button": 'right' if is_shift_mod else 'left'})
        else:
            current_mode = "main"; first_char_main = None; clear_pending_double_click()
            if overlay_window and overlay_window.winfo_exists(): overlay_window.after(0, draw_main_grid)
            _suppressed_keys_in_overlay.clear()


# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Grid Helper...")
    # (Print startup messages as before)
    print(f"Screen Dimensions: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"--- Style Settings (from style_config.py or defaults) ---")
    print(f"  Overlay Alpha: {OVERLAY_ALPHA}, Background: {OVERLAY_BACKGROUND_COLOR}")
    print(f"  Grid Color: {GRID_COLOR}, Line Width: {GRID_LINE_WIDTH}, Style: {GRID_LINE_STYLE}")
    print(f"  Text Color: {TEXT_COLOR}, Font: {FONT_FAMILY} ({FONT_WEIGHT})")
    print(f"  Font Size: {FONT_SIZE_BEHAVIOR}" + (f", Fixed Size: {FONT_FIXED_SIZE}" if FONT_SIZE_BEHAVIOR == "fixed" else ""))
    print(f"  Overlay Toggle Key: '{LEFT_ALT_KEY_NAME}', Double Click Interval: {DOUBLE_CLICK_INTERVAL}s")
    if ENABLE_FREE_MODE:
        print(f"--- Free Mode Settings (from feature_config.py) ---")
        print(f"  Free Mode Toggle Key: '{FREE_MODE_TOGGLE_KEY}'")
        print(f"  Mouse Move: '{FREE_MODE_MOUSE_UP}/{FREE_MODE_MOUSE_DOWN}/{FREE_MODE_MOUSE_LEFT}/{FREE_MODE_MOUSE_RIGHT}', Step: {MOUSE_MOVE_STEP}px")
        print(f"  Scroll: '{FREE_MODE_SCROLL_UP}/{FREE_MODE_SCROLL_DOWN}/{FREE_MODE_SCROLL_LEFT}/{FREE_MODE_SCROLL_RIGHT}', Step: {SCROLL_STEP} units")
    else:
        print("--- Free Mode is DISABLED (via feature_config.py) ---")
    print(f"-----------------------------------------------------------")
    print(f"Main Grid: {MAIN_GRID_ROWS}x{MAIN_GRID_COLS}, Sub Grid: {SUB_GRID_ROWS}x{SUB_GRID_COLS}")


    if not main_grid_key_map or not sub_grid_key_map: print("\nKEY_CONFIG WARNING: Key maps empty.")
    else: print("Key maps loaded.")

    create_overlay_window() # Create Tkinter window (hidden initially)
    keyboard.hook(global_key_event_handler) # Hook global keyboard events
    print(f"\nKeyboard hooked. App active. Tray icon should appear if pystray is installed.")
    print(f"  Toggle Overlay: '{LEFT_ALT_KEY_NAME}'")
    if ENABLE_FREE_MODE: print(f"  Toggle Free Mode: '{FREE_MODE_TOGGLE_KEY}'")


    tray_thread = None
    if PYSTRAY_AVAILABLE:
        # Run the tray icon in a separate daemon thread
        # Daemon threads exit when the main program exits
        tray_thread = threading.Thread(target=setup_tray_icon, daemon=True)
        tray_thread.start()
    else:
        print("System tray icon disabled (pystray or Pillow not found).")

    try:
        # Start the Tkinter event loop (this is blocking for the main thread)
        if overlay_window and overlay_window.winfo_exists():
            overlay_window.mainloop() # This will run until overlay_window.quit() is called

        # If mainloop finishes (e.g., from tray quit), ensure app exits cleanly
        # This part might only be reached if Tkinter was not used or quit early
        if app_is_exiting and tray_thread and tray_thread.is_alive():
             print("Waiting for tray thread to finish...")
             tray_icon_object.stop() # Ensure it's stopped again
             tray_thread.join(timeout=2) # Wait for tray thread

    except KeyboardInterrupt:
        print("\nScript terminated by user (Ctrl+C).")
        app_is_exiting = True # Signal exit
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        app_is_exiting = True # Signal exit
    finally:
        print("Initiating shutdown sequence...")
        app_is_exiting = True # Ensure flag is set

        if tray_icon_object:
            print("Stopping system tray icon...")
            tray_icon_object.stop()
        if tray_thread and tray_thread.is_alive():
            print("Waiting for tray thread to join...")
            tray_thread.join(timeout=2) # Give it a couple of seconds

        print("Unhooking keyboard...")
        keyboard.unhook_all() # Crucial for cleanup

        # Tkinter cleanup: If overlay_window.quit() was called, mainloop ends.
        # If mainloop ended for other reasons or wasn't running, ensure destroy.
        if overlay_window and overlay_window.winfo_exists():
            print("Destroying Tkinter window...")
            overlay_window.destroy()

        print("Grid Helper finished.")
        sys.exit(0) # Force exit if anything is lingering