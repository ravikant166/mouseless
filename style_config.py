# style_config.py

# --- Overlay Appearance ---
OVERLAY_ALPHA = 0.4  # Transparency (0.0 = fully transparent, 1.0 = fully opaque)
OVERLAY_BACKGROUND_COLOR = "black" # The color of the overlay window/canvas background

# --- Grid Appearance ---
GRID_COLOR = "white"
GRID_LINE_WIDTH = 1 # Thickness of grid lines in pixels
GRID_LINE_STYLE = "line" # "line", "dashes", "dots" (Note: "dots" might not be directly supported by tkinter create_line options, "dashes" is)
                        # For "dots", we might need custom drawing or very short dashes.
                        # Tkinter create_rectangle `outline` doesn't directly support dash styles.
                        # We can use `dash` option for `create_line` if we draw lines instead of rects,
                        # or for `create_rectangle` outline if on newer Tk versions/platforms.
                        # Let's assume `create_rectangle` with a solid line for now, or handle `dash` if available.
SUB_GRID_HIGHLIGHT_COLOR = "lime"
SUB_GRID_HIGHLIGHT_WIDTH = 3

# --- Text Appearance ---
TEXT_COLOR = "white"
# FONT_FAMILY = "Arial"
FONT_FAMILY = "Consolas" # Monospaced font, might look better for grid labels
# FONT_SIZE_BEHAVIOR = "dynamic" # "dynamic" or "fixed"
FONT_SIZE_BEHAVIOR = "dynamic" # "dynamic" will try to fit text in cell, "fixed" will use FONT_FIXED_SIZE
FONT_FIXED_SIZE = 10 # Used if FONT_SIZE_BEHAVIOR is "fixed"
# FONT_WEIGHT = "normal" # "normal" or "bold"
FONT_WEIGHT = "normal"

# --- Double Click ---
DOUBLE_CLICK_INTERVAL = 0.35 # Seconds

# --- Hotkey ---
# Moved from main script for better organization
LEFT_ALT_KEY_NAME = 'alt' # Or 'left alt', 'right alt' - check your system with print(event.name)

# --- Validation (Optional but good practice) ---
def validate_configs():
    """
    Simple validation for some config values.
    Returns True if valid, prints warnings and returns False otherwise.
    """
    valid = True
    if not (0.0 <= OVERLAY_ALPHA <= 1.0):
        print("STYLE_CONFIG WARNING: OVERLAY_ALPHA should be between 0.0 and 1.0.")
        valid = False
    if GRID_LINE_STYLE not in ["line", "dashes"]: # "dots" is harder with create_rectangle
        print(f"STYLE_CONFIG WARNING: GRID_LINE_STYLE '{GRID_LINE_STYLE}' may not be fully supported. Using 'line'.")
        # You might choose to default GRID_LINE_STYLE = "line" here if invalid
    if FONT_SIZE_BEHAVIOR not in ["dynamic", "fixed"]:
        print("STYLE_CONFIG WARNING: FONT_SIZE_BEHAVIOR should be 'dynamic' or 'fixed'.")
        valid = False
    if not (0.1 <= DOUBLE_CLICK_INTERVAL <= 1.0):
        print("STYLE_CONFIG WARNING: DOUBLE_CLICK_INTERVAL seems unusual. Recommended 0.2-0.5s.")
        # This is more of a soft warning
    return valid

if __name__ == "__main__":
    if validate_configs():
        print("style_config.py: All configurations seem valid.")
    else:
        print("style_config.py: Some configuration warnings were noted above.")

    print("\n--- Current Style Configurations ---")
    print(f"Overlay Alpha: {OVERLAY_ALPHA}")
    print(f"Overlay Background: {OVERLAY_BACKGROUND_COLOR}")
    print(f"Grid Color: {GRID_COLOR}")
    print(f"Grid Line Width: {GRID_LINE_WIDTH}")
    print(f"Grid Line Style: {GRID_LINE_STYLE}")
    print(f"Sub-grid Highlight Color: {SUB_GRID_HIGHLIGHT_COLOR}")
    print(f"Sub-grid Highlight Width: {SUB_GRID_HIGHLIGHT_WIDTH}")
    print(f"Text Color: {TEXT_COLOR}")
    print(f"Font Family: {FONT_FAMILY}")
    print(f"Font Size Behavior: {FONT_SIZE_BEHAVIOR}")
    print(f"Font Fixed Size: {FONT_FIXED_SIZE}")
    print(f"Font Weight: {FONT_WEIGHT}")
    print(f"Double Click Interval: {DOUBLE_CLICK_INTERVAL}")
    print(f"Left Alt Key Name: {LEFT_ALT_KEY_NAME}")