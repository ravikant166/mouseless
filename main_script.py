import tkinter as tk
import keyboard
import pyautogui
import time
from screeninfo import get_monitors

# Import from your key configuration file
try:
    from key_config import (
        MAIN_GRID_COLS, MAIN_GRID_ROWS,
        SUB_GRID_COLS, SUB_GRID_ROWS,
        get_main_grid_key_map, get_sub_grid_key_map
    )
except ImportError:
    print("ERROR: Could not import from key_config.py. Make sure it exists and is in the same directory.")
    # Provide default values so the script doesn't crash immediately
    MAIN_GRID_COLS, MAIN_GRID_ROWS = 25, 36
    SUB_GRID_COLS, SUB_GRID_ROWS = 8, 3
    def get_main_grid_key_map(): print("WARNING: Using empty main_grid_key_map due to key_config.py import error."); return {}
    def get_sub_grid_key_map(): print("WARNING: Using empty sub_grid_key_map due to key_config.py import error."); return {}

# Import from your style configuration file
try:
    from style_config import (
        OVERLAY_ALPHA, OVERLAY_BACKGROUND_COLOR,
        GRID_COLOR, GRID_LINE_WIDTH, GRID_LINE_STYLE,
        SUB_GRID_HIGHLIGHT_COLOR, SUB_GRID_HIGHLIGHT_WIDTH,
        TEXT_COLOR, FONT_FAMILY, FONT_SIZE_BEHAVIOR, FONT_FIXED_SIZE, FONT_WEIGHT,
        DOUBLE_CLICK_INTERVAL, LEFT_ALT_KEY_NAME,
        validate_configs # Optional: for startup validation
    )
    # Optional: Validate style configurations on startup
    if 'validate_configs' in globals() and callable(validate_configs):
        if not validate_configs():
            print("INFO: Review style_config.py for warnings.")
except ImportError:
    print("ERROR: Could not import from style_config.py. Make sure it exists and is in the same directory.")
    print("INFO: Using default style values.")
    # Default style values if style_config.py is missing
    OVERLAY_ALPHA = 0.5
    OVERLAY_BACKGROUND_COLOR = "black"
    GRID_COLOR = "white"
    GRID_LINE_WIDTH = 1
    GRID_LINE_STYLE = "line" # Keep it simple for defaults
    SUB_GRID_HIGHLIGHT_COLOR = "lime"
    SUB_GRID_HIGHLIGHT_WIDTH = 3
    TEXT_COLOR = "white"
    FONT_FAMILY = "Arial"
    FONT_SIZE_BEHAVIOR = "dynamic"
    FONT_FIXED_SIZE = 10
    FONT_WEIGHT = "normal"
    DOUBLE_CLICK_INTERVAL = 0.35
    LEFT_ALT_KEY_NAME = 'alt'


# --- Load Key Maps ---
main_grid_key_map = get_main_grid_key_map()
sub_grid_key_map = get_sub_grid_key_map()

# --- Global State (remains mostly the same) ---
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

# --- Screen Dimensions ---
try:
    PRIMARY_MONITOR = get_monitors()[0]
    SCREEN_WIDTH, SCREEN_HEIGHT = PRIMARY_MONITOR.width, PRIMARY_MONITOR.height
except Exception:
    print("WARNING: screeninfo failed, falling back to pyautogui for screen size.")
    SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# --- Drawing Functions (Modified to use style_config) ---
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
            if GRID_LINE_STYLE == "dashes":
                # The 'dash' option for create_rectangle might only work on some systems/Tk versions.
                # It expects a tuple, e.g., (5, 3) means 5 pixels drawn, 3 pixels gap.
                rect_options["dash"] = (4, 4) # Example dash pattern
            # "dots" is harder with create_rectangle; could use create_line with dash=(1,3) for each side.
            # For simplicity, if GRID_LINE_STYLE is "dots" and not handled, it will draw a solid line.
            canvas.create_rectangle(x1, y1, x2, y2, **rect_options)

            key_label = cell_to_key_map.get((r_idx, c_idx), "")
            
            font_size_to_use = FONT_FIXED_SIZE
            if FONT_SIZE_BEHAVIOR == "dynamic":
                font_size_to_use = max(6, min(int(cell_height / 2.5), # Adjusted divisor for better fit
                                           int(cell_width / (len(key_label) + 0.5) * 1.2 if key_label else cell_width / 1.5))) # Adjusted
            
            font_tuple = (FONT_FAMILY, font_size_to_use, FONT_WEIGHT)
            canvas.create_text(x1 + cell_width / 2, y1 + cell_height / 2,
                               text=key_label, fill=TEXT_COLOR, font=font_tuple)

            if is_sub_grid and r_idx == SUB_GRID_ROWS // 2 and c_idx == SUB_GRID_COLS // 2:
                canvas.create_rectangle(x1, y1, x2, y2,
                                        outline=SUB_GRID_HIGHLIGHT_COLOR,
                                        width=SUB_GRID_HIGHLIGHT_WIDTH)

def draw_main_grid():
    global current_mode
    current_mode = "main"
    if canvas:
        draw_grid(MAIN_GRID_COLS, MAIN_GRID_ROWS, SCREEN_WIDTH, SCREEN_HEIGHT, is_sub_grid=False)

def draw_sub_grid(parent_cell_rect):
    global selected_main_cell_rect, current_mode
    current_mode = "sub"
    selected_main_cell_rect = parent_cell_rect
    x1, y1, x2, y2 = parent_cell_rect
    if canvas:
        draw_grid(SUB_GRID_COLS, SUB_GRID_ROWS, x2 - x1, y2 - y1, parent_rect_coords=(x1,y1,x2,y2), is_sub_grid=True)

# --- Mouse Action & UI Management (perform_mouse_click_action is unchanged by style) ---
def perform_mouse_click_action(target_x, target_y, is_right_click=False):
    global overlay_window, overlay_visible, current_mode, first_char_main, _suppressed_keys_in_overlay

    if overlay_window and overlay_window.winfo_exists() and overlay_window.state() == 'normal':
        overlay_window.withdraw()
        overlay_window.update_idletasks()
        time.sleep(0.05)

    button_to_click = 'right' if is_right_click else 'left'
    pyautogui.click(x=int(target_x), y=int(target_y), button=button_to_click)
    print(f"Clicked (Grid Action) {button_to_click} at ({int(target_x)}, {int(target_y)})")

    overlay_visible = False
    current_mode = "main"
    first_char_main = None
    _suppressed_keys_in_overlay.clear()

def clear_pending_double_click():
    global pending_double_click_info
    pending_double_click_info["is_pending"] = False
    pending_double_click_info["key_char"] = None

# --- UI Creation (Modified for style_config) ---
def create_overlay_window():
    global overlay_window, canvas
    if overlay_window and overlay_window.winfo_exists():
        overlay_window.destroy()
    overlay_window = tk.Tk()
    overlay_window.attributes('-alpha', OVERLAY_ALPHA) # From style_config
    overlay_window.attributes('-topmost', True)
    overlay_window.overrideredirect(True)
    overlay_window.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}+0+0")
    # Set window background (though canvas covers it)
    overlay_window.configure(bg=OVERLAY_BACKGROUND_COLOR) # From style_config

    canvas = tk.Canvas(overlay_window, width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
                       bg=OVERLAY_BACKGROUND_COLOR, # From style_config
                       highlightthickness=0)
    canvas.pack()
    overlay_window.withdraw()

def show_overlay_tk():
    global overlay_visible, current_mode, first_char_main, overlay_window
    if not overlay_window or not overlay_window.winfo_exists():
        create_overlay_window()
    overlay_visible = True
    current_mode = "main"
    first_char_main = None
    _suppressed_keys_in_overlay.clear()
    clear_pending_double_click()
    draw_main_grid() # This will use new style settings
    overlay_window.deiconify()
    overlay_window.lift()
    overlay_window.focus_force()

def hide_overlay_tk():
    global overlay_visible, overlay_window, current_mode, first_char_main
    overlay_visible = False
    current_mode = "main"
    first_char_main = None
    _suppressed_keys_in_overlay.clear()
    clear_pending_double_click()
    if overlay_window and overlay_window.winfo_exists():
        overlay_window.withdraw()

def actual_toggle_overlay():
    if overlay_visible:
        if overlay_window and overlay_window.winfo_exists():
            overlay_window.after(0, hide_overlay_tk)
    else:
        if not overlay_window or not overlay_window.winfo_exists():
            create_overlay_window()
        if overlay_window and overlay_window.winfo_exists():
            overlay_window.after(0, show_overlay_tk)

# --- Keyboard Event Handlers (global_key_event_handler & on_key_event_for_active_overlay_logic) ---
# These remain largely the same as the previous consolidated version,
# as style changes don't directly affect their core logic.
# The DOUBLE_CLICK_INTERVAL and LEFT_ALT_KEY_NAME are now sourced from style_config.

def global_key_event_handler(event):
    global g_left_alt_down_for_toggle, g_left_alt_press_timestamp, overlay_visible
    global pending_double_click_info, first_char_main, current_mode

    # print(f"Event: {event.name}, Type: {event.event_type}, Time: {event.time}") # DEBUG

    if event.name == LEFT_ALT_KEY_NAME: # From style_config
        if event.event_type == keyboard.KEY_DOWN:
            if not g_left_alt_down_for_toggle:
                g_left_alt_down_for_toggle = True
                g_left_alt_press_timestamp = event.time
        elif event.event_type == keyboard.KEY_UP:
            if g_left_alt_down_for_toggle:
                if 0.01 < (event.time - g_left_alt_press_timestamp) < 0.7: # Fixed toggle duration
                    actual_toggle_overlay()
            g_left_alt_down_for_toggle = False
        return

    elif g_left_alt_down_for_toggle and event.event_type == keyboard.KEY_DOWN and event.name != LEFT_ALT_KEY_NAME:
        g_left_alt_down_for_toggle = False

    if event.event_type == keyboard.KEY_DOWN and pending_double_click_info["is_pending"]:
        key_name_lower = event.name.lower()
        current_input_char_for_map = ' ' if key_name_lower == 'space' else \
                                     key_name_lower.upper() if len(key_name_lower) == 1 else None

        if current_input_char_for_map and \
           current_input_char_for_map == pending_double_click_info["key_char"] and \
           (event.time - pending_double_click_info["time"]) < DOUBLE_CLICK_INTERVAL: # From style_config
            time.sleep(0.05)
            pyautogui.click(
                x=pending_double_click_info["screen_x"],
                y=pending_double_click_info["screen_y"],
                button=pending_double_click_info["button"]
            )
            clear_pending_double_click()
            if event.name == LEFT_ALT_KEY_NAME: g_left_alt_down_for_toggle = False
            return
        else:
            clear_pending_double_click()

    if overlay_visible:
        on_key_event_for_active_overlay_logic(event)

def on_key_event_for_active_overlay_logic(event):
    global overlay_visible, current_mode, first_char_main, selected_main_cell_rect, overlay_window
    global _suppressed_keys_in_overlay, pending_double_click_info

    key_name_lower = event.name.lower()

    if event.event_type == keyboard.KEY_UP:
        _suppressed_keys_in_overlay.discard(key_name_lower)
        return

    if key_name_lower == 'esc':
        if overlay_window and overlay_window.winfo_exists():
            overlay_window.after(0, hide_overlay_tk)
        return

    is_modifier = key_name_lower in [
        LEFT_ALT_KEY_NAME.lower(), 'alt right', 'alt gr', 'ctrl',
        'right ctrl', 'left ctrl', 'control', 'shift',
        'left shift', 'right shift'
    ]
    if is_modifier:
        _suppressed_keys_in_overlay.add(key_name_lower)
        return

    if key_name_lower in _suppressed_keys_in_overlay: return
    _suppressed_keys_in_overlay.add(key_name_lower)

    input_char_for_map = None
    if key_name_lower == 'space':
        input_char_for_map = ' '
    elif len(key_name_lower) == 1 and (key_name_lower.isalnum() or key_name_lower in [';', ',', '.', '/']):
        input_char_for_map = key_name_lower.upper()

    if input_char_for_map is None: return

    if current_mode == "main":
        clear_pending_double_click()
        if first_char_main is None:
            first_char_main = input_char_for_map
        else:
            key_combo = first_char_main + input_char_for_map
            if key_combo in main_grid_key_map:
                r, c = main_grid_key_map[key_combo]
                cell_w, cell_h = SCREEN_WIDTH / MAIN_GRID_COLS, SCREEN_HEIGHT / MAIN_GRID_ROWS
                x1, y1 = c * cell_w, r * cell_h; x2, y2 = x1 + cell_w, y1 + cell_h
                first_char_main = None
                if overlay_window and overlay_window.winfo_exists():
                    overlay_window.after(0, lambda rect=(x1,y1,x2,y2): draw_sub_grid(rect))
            else:
                first_char_main = None
            _suppressed_keys_in_overlay.clear()

    elif current_mode == "sub":
        if not selected_main_cell_rect:
            _suppressed_keys_in_overlay.discard(key_name_lower)
            return

        main_x1, main_y1, main_x2, main_y2 = selected_main_cell_rect
        main_w, main_h = main_x2 - main_x1, main_y2 - main_y1
        sub_cell_w, sub_cell_h = main_w / SUB_GRID_COLS, main_h / SUB_GRID_ROWS
        target_r_sub, target_c_sub = -1, -1

        if input_char_for_map == ' ':
            target_r_sub, target_c_sub = SUB_GRID_ROWS // 2, SUB_GRID_COLS // 2
        elif input_char_for_map in sub_grid_key_map:
            target_r_sub, target_c_sub = sub_grid_key_map[input_char_for_map]

        if target_r_sub != -1:
            click_x = main_x1 + (target_c_sub * sub_cell_w) + (sub_cell_w / 2)
            click_y = main_y1 + (target_r_sub * sub_cell_h) + (sub_cell_h / 2)
            is_shift_mod = any(keyboard.is_pressed(k) for k in ['shift', 'left shift', 'right shift'])
            perform_mouse_click_action(click_x, click_y, is_right_click=is_shift_mod)
            pending_double_click_info.update({
                "is_pending": True, "key_char": input_char_for_map, "time": event.time,
                "screen_x": int(click_x), "screen_y": int(click_y),
                "button": 'right' if is_shift_mod else 'left'
            })
        else:
            current_mode = "main"; first_char_main = None; clear_pending_double_click()
            if overlay_window and overlay_window.winfo_exists():
                overlay_window.after(0, draw_main_grid)
            _suppressed_keys_in_overlay.clear()

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Script...")
    print(f"Screen Dimensions: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print(f"--- Style Settings (from style_config.py or defaults) ---")
    print(f"  Overlay Alpha: {OVERLAY_ALPHA}, Background: {OVERLAY_BACKGROUND_COLOR}")
    print(f"  Grid Color: {GRID_COLOR}, Line Width: {GRID_LINE_WIDTH}, Style: {GRID_LINE_STYLE}")
    print(f"  Text Color: {TEXT_COLOR}, Font: {FONT_FAMILY} ({FONT_WEIGHT})")
    print(f"  Font Size: {FONT_SIZE_BEHAVIOR}" + (f", Fixed Size: {FONT_FIXED_SIZE}" if FONT_SIZE_BEHAVIOR == "fixed" else ""))
    print(f"  Toggle Key: '{LEFT_ALT_KEY_NAME}', Double Click Interval: {DOUBLE_CLICK_INTERVAL}s")
    print(f"-----------------------------------------------------------")
    print(f"Main Grid: {MAIN_GRID_ROWS}x{MAIN_GRID_COLS}, Sub Grid: {SUB_GRID_ROWS}x{SUB_GRID_COLS}")
    print("--- Usage --- (refer to previous detailed instructions)")

    if not main_grid_key_map or not sub_grid_key_map:
        print("\nKEY_CONFIG WARNING: Key maps are empty or incomplete. Grid cells may not be labeled or selectable.")
    else:
        print("Key maps loaded successfully.")

    create_overlay_window()
    keyboard.hook(global_key_event_handler)
    print("\nKeyboard hooked. Script is active. Tap Alt to toggle overlay.")

    try:
        if overlay_window and overlay_window.winfo_exists():
            overlay_window.mainloop()
    except KeyboardInterrupt:
        print("\nScript terminated by user (Ctrl+C).")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Unhooking keyboard and exiting...")
        keyboard.unhook_all()
        if overlay_window and overlay_window.winfo_exists():
            overlay_window.quit()
        print("Script finished.")