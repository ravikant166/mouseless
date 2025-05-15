import tkinter as tk
import keyboard
import pyautogui
# import string # No longer needed here
# import math   # No longer needed here (unless used elsewhere, but not for key gen)
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
    print("ERROR: Could not import from key_config.py. Make sure it exists in the same directory.")
    # Provide default values so the script doesn't crash immediately if config is missing
    MAIN_GRID_COLS = 25 
    MAIN_GRID_ROWS = 36
    SUB_GRID_COLS = 8
    SUB_GRID_ROWS = 3
    def get_main_grid_key_map(): print("WARNING: Using empty main_grid_key_map due to import error."); return {}
    def get_sub_grid_key_map(): print("WARNING: Using empty sub_grid_key_map due to import error."); return {}


# --- Configuration (from key_config.py or defaults) ---
LEFT_ALT_KEY_NAME = 'alt'

OVERLAY_ALPHA = 0.7
GRID_COLOR = "white"
TEXT_COLOR = "white"
SUB_GRID_HIGHLIGHT_COLOR = "lime"
DOUBLE_CLICK_INTERVAL = 0.35

# --- Load Key Maps ---
main_grid_key_map = get_main_grid_key_map()
sub_grid_key_map = get_sub_grid_key_map()

# --- Global State ---
overlay_window = None; canvas = None
overlay_visible = False
current_mode = "main"
first_char_main = None
selected_main_cell_rect = None

g_left_alt_down_for_toggle = False
g_left_alt_press_timestamp = 0

pending_double_click_info = {"is_pending":False, "key_char":None, "time":0, "screen_x":0, "screen_y":0, "button":"left"}
_suppressed_keys_in_overlay = set()

# --- Screen Dimensions ---
try:
    PRIMARY_MONITOR = get_monitors()[0]
    SCREEN_WIDTH, SCREEN_HEIGHT = PRIMARY_MONITOR.width, PRIMARY_MONITOR.height
except Exception: SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# --- Drawing Functions ---
def draw_grid(cols, rows, width, height, parent_rect_coords=None, is_sub_grid=False):
    global canvas # Uses global main_grid_key_map and sub_grid_key_map
    if not canvas: return
    canvas.delete("all")
    base_x, base_y = (parent_rect_coords[0], parent_rect_coords[1]) if parent_rect_coords else (0, 0)
    cell_width, cell_height = width / cols, height / rows
    
    key_map_to_use = sub_grid_key_map if is_sub_grid else main_grid_key_map
    # Invert the map for drawing: (row, col) -> "key_string"
    cell_to_key_map = {v: k for k, v in key_map_to_use.items()} 

    for r_idx in range(rows):
        for c_idx in range(cols):
            x1,y1 = base_x+c_idx*cell_width, base_y+r_idx*cell_height; x2,y2 = x1+cell_width,y1+cell_height
            canvas.create_rectangle(x1,y1,x2,y2,outline=GRID_COLOR,width=1)
            
            key_label = cell_to_key_map.get((r_idx,c_idx),"") # Get key string for this (row,col)
            
            font_size = max(6, min(int(cell_height/3), int(cell_width/(len(key_label)+1)*1.5 if key_label else cell_width/2)))
            canvas.create_text(x1+cell_width/2,y1+cell_height/2,text=key_label,fill=TEXT_COLOR,font=("Arial",font_size))
            
            if is_sub_grid and r_idx==SUB_GRID_ROWS//2 and c_idx==SUB_GRID_COLS//2:
                canvas.create_rectangle(x1,y1,x2,y2,outline=SUB_GRID_HIGHLIGHT_COLOR,width=3)

def draw_main_grid():
    global current_mode
    current_mode = "main"
    if canvas: draw_grid(MAIN_GRID_COLS, MAIN_GRID_ROWS, SCREEN_WIDTH, SCREEN_HEIGHT, is_sub_grid=False)

def draw_sub_grid(parent_cell_rect):
    global selected_main_cell_rect, current_mode
    current_mode = "sub"; selected_main_cell_rect=parent_cell_rect; x1,y1,x2,y2=parent_cell_rect
    if canvas: draw_grid(SUB_GRID_COLS, SUB_GRID_ROWS, x2-x1,y2-y1,parent_rect_coords=(x1,y1,x2,y2),is_sub_grid=True)

# --- Mouse Action & UI Management ---
def perform_mouse_click_action(target_x, target_y, is_right_click=False): 
    global overlay_window, overlay_visible, current_mode, first_char_main, _suppressed_keys_in_overlay

    if overlay_window and overlay_window.state() == 'normal':
        overlay_window.withdraw(); overlay_window.update_idletasks(); time.sleep(0.05) 
    
    button_to_click = 'right' if is_right_click else 'left'
    pyautogui.click(x=int(target_x), y=int(target_y), button=button_to_click)
    print(f"Clicked (Grid Action) {button_to_click} at ({int(target_x)}, {int(target_y)})")

    overlay_visible = False 
    current_mode = "main"; first_char_main = None
    _suppressed_keys_in_overlay.clear()

def clear_pending_double_click():
    global pending_double_click_info
    if pending_double_click_info["is_pending"]: pass
    pending_double_click_info["is_pending"] = False; pending_double_click_info["key_char"] = None

def create_overlay_window():
    global overlay_window, canvas
    if overlay_window: overlay_window.destroy()
    overlay_window=tk.Tk(); overlay_window.attributes('-alpha',OVERLAY_ALPHA); overlay_window.attributes('-topmost',True)
    overlay_window.overrideredirect(True); overlay_window.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}+0+0")
    overlay_window.configure(bg='black')
    canvas=tk.Canvas(overlay_window,width=SCREEN_WIDTH,height=SCREEN_HEIGHT,bg='black',highlightthickness=0)
    canvas.pack(); overlay_window.withdraw()

def show_overlay_tk():
    global overlay_visible, current_mode, first_char_main, overlay_window
    if not overlay_window: create_overlay_window()
    overlay_visible = True; current_mode = "main"; first_char_main = None
    _suppressed_keys_in_overlay.clear(); clear_pending_double_click()
    draw_main_grid()
    overlay_window.deiconify(); overlay_window.lift(); overlay_window.focus_force()

def hide_overlay_tk(): 
    global overlay_visible, overlay_window, current_mode, first_char_main
    overlay_visible = False; current_mode = "main"; first_char_main = None
    _suppressed_keys_in_overlay.clear(); clear_pending_double_click()
    if overlay_window: overlay_window.withdraw()

def actual_toggle_overlay():
    if overlay_visible:
        if overlay_window: overlay_window.after(0, hide_overlay_tk)
    else:
        if overlay_window: overlay_window.after(0, show_overlay_tk)

# --- Unified Keyboard Event Handler ---
def global_key_event_handler(event):
    global g_left_alt_down_for_toggle, g_left_alt_press_timestamp, overlay_visible
    global pending_double_click_info

    if event.name == LEFT_ALT_KEY_NAME: 
        if event.event_type == keyboard.KEY_DOWN:
            if not g_left_alt_down_for_toggle : 
                g_left_alt_down_for_toggle = True; g_left_alt_press_timestamp = event.time
        elif event.event_type == keyboard.KEY_UP:
            if g_left_alt_down_for_toggle: 
                if 0.01 < (event.time - g_left_alt_press_timestamp) < 0.7: actual_toggle_overlay()
            g_left_alt_down_for_toggle = False 
        return 
    elif g_left_alt_down_for_toggle and event.event_type == keyboard.KEY_DOWN and event.name != LEFT_ALT_KEY_NAME :
        g_left_alt_down_for_toggle = False

    if event.event_type == keyboard.KEY_DOWN and pending_double_click_info["is_pending"]:
        key_name = event.name; current_key_char = ' ' if key_name=='space' else key_name if len(key_name)==1 else None
        if current_key_char and current_key_char == pending_double_click_info["key_char"] and \
           (event.time - pending_double_click_info["time"]) < DOUBLE_CLICK_INTERVAL:
            # print(f"DEBUG: Completing BLIND double click for '{current_key_char}' at ({pending_double_click_info['screen_x']}, {pending_double_click_info['screen_y']})")
            time.sleep(0.05) 
            pyautogui.click(x=pending_double_click_info["screen_x"], y=pending_double_click_info["screen_y"], button=pending_double_click_info["button"])
            clear_pending_double_click()
            if event.name == LEFT_ALT_KEY_NAME: g_left_alt_down_for_toggle = False
            return
        else: clear_pending_double_click()

    if overlay_visible:
        on_key_event_for_active_overlay_logic(event)

# --- Logic for when Overlay is Active ---
def on_key_event_for_active_overlay_logic(event):
    global overlay_visible, current_mode, first_char_main, selected_main_cell_rect, overlay_window
    global _suppressed_keys_in_overlay, pending_double_click_info

    if event.event_type == keyboard.KEY_UP:
        _suppressed_keys_in_overlay.discard(event.name); return 

    key_name = event.name.lower()
    if key_name == 'esc':
        if overlay_window: overlay_window.after(0, hide_overlay_tk); return

    is_modifier_key = key_name in [LEFT_ALT_KEY_NAME.lower(), 'alt right', 'alt gr',
                                   'ctrl','right ctrl','left ctrl','control',
                                   'shift', 'left shift', 'right shift'] 
    if is_modifier_key:
        _suppressed_keys_in_overlay.add(key_name); return 

    if key_name in _suppressed_keys_in_overlay and current_mode == "main" and first_char_main: return
    _suppressed_keys_in_overlay.add(key_name)

    key_pressed_char = ' ' if key_name == 'space' else key_name if len(key_name) == 1 else None
    if key_pressed_char is None: _suppressed_keys_in_overlay.discard(key_name); return

    if current_mode == "main":
        clear_pending_double_click() 
        if first_char_main is None: first_char_main = key_pressed_char
        else:
            key_combo = first_char_main + key_pressed_char
            if key_combo in main_grid_key_map: # main_grid_key_map is loaded from key_config
                r,c = main_grid_key_map[key_combo]; cell_w,cell_h=SCREEN_WIDTH/MAIN_GRID_COLS,SCREEN_HEIGHT/MAIN_GRID_ROWS
                x1,y1=c*cell_w,r*cell_h; x2,y2=x1+cell_w,y1+cell_h
                first_char_main=None; clear_pending_double_click()
                if overlay_window: overlay_window.after(0, lambda: draw_sub_grid((x1,y1,x2,y2)))
            else: first_char_main = None
            _suppressed_keys_in_overlay.clear()
    
    elif current_mode == "sub":
        if not selected_main_cell_rect: _suppressed_keys_in_overlay.discard(key_name); return
        main_x1,main_y1,main_x2,main_y2 = selected_main_cell_rect
        main_w,main_h=main_x2-main_x1,main_y2-main_y1; sub_w,sub_h=main_w/SUB_GRID_COLS,main_h/SUB_GRID_ROWS
        target_r_sub,target_c_sub = (-1,-1)
        if key_pressed_char==' ': target_r_sub,target_c_sub=SUB_GRID_ROWS//2,SUB_GRID_COLS//2
        elif key_pressed_char in sub_grid_key_map: # sub_grid_key_map is loaded from key_config
            target_r_sub,target_c_sub=sub_grid_key_map[key_pressed_char]

        if target_r_sub != -1:
            click_x=main_x1+(target_c_sub*sub_w)+(sub_w/2); click_y=main_y1+(target_r_sub*sub_h)+(sub_h/2)
            is_shift_mod = keyboard.is_pressed('shift') or keyboard.is_pressed('left shift') or keyboard.is_pressed('right shift')
            
            perform_mouse_click_action(click_x, click_y, is_right_click=is_shift_mod) 
            
            pending_double_click_info["is_pending"] = True
            pending_double_click_info["key_char"] = key_pressed_char
            pending_double_click_info["time"] = event.time
            pending_double_click_info["screen_x"] = int(click_x)
            pending_double_click_info["screen_y"] = int(click_y)
            pending_double_click_info["button"] = 'right' if is_shift_mod else 'left'
        else: 
            current_mode="main"; first_char_main=None; clear_pending_double_click()
            if overlay_window: overlay_window.after(0, draw_main_grid)
            _suppressed_keys_in_overlay.clear()

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Script...")
    print(f"LEFT_ALT_KEY_NAME is set to: '{LEFT_ALT_KEY_NAME}'")
    print(f"Main Grid: {MAIN_GRID_ROWS}x{MAIN_GRID_COLS}, Sub Grid: {SUB_GRID_ROWS}x{SUB_GRID_COLS} (from key_config.py or defaults)")
    print(f"Double click interval for sub-grid keys: {DOUBLE_CLICK_INTERVAL}s")
    print("Tap Left Alt to toggle. Esc to hide. Press sub-grid key twice quickly for double click.")

    if not main_grid_key_map or not sub_grid_key_map:
        print("\nWARNING: Key maps are empty or incomplete. Grid cells may not be labeled or selectable.")
        print("Please ensure key_config.py is present and correctly filled out.")
        print("The script will run, but functionality will be limited.\n")


    create_overlay_window()
    keyboard.hook(global_key_event_handler)

    try:
        if overlay_window: overlay_window.mainloop()
    except KeyboardInterrupt: print("\nScript terminated by user (Ctrl+C).")
    except Exception as e: print(f"\nAn unexpected error: {e}"); import traceback; traceback.print_exc()
    finally:
        print("Unhooking and exiting..."); keyboard.unhook_all()
        if overlay_window: overlay_window.quit()