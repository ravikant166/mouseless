# feature_config.py

# --- Free Mode Settings ---
ENABLE_FREE_MODE = True  # Set to False to disable this feature entirely

# Key to toggle Free Mode ON/OFF when the overlay is *NOT* active.
# This key should be distinct from the overlay toggle key.
# Example: '`' (backtick/tilde key) or a function key like 'f12'.
# IMPORTANT: This key is listened for globally, even when the overlay is hidden.
FREE_MODE_TOGGLE_KEY = '`' # Backtick key

# Behavior when Free Mode is active:
# - Overlay is hidden.
# - I, K, J, L control mouse cursor movement.
# - M, ",", B, N control mouse scrolling.
# - Pressing FREE_MODE_TOGGLE_KEY again exits Free Mode.
# - Pressing LEFT_ALT_KEY_NAME (from style_config) to show the overlay will also exit Free Mode.

MOUSE_MOVE_STEP = 20  # Pixels to move the mouse per key press in Free Mode
SCROLL_STEP = 100       # Units to scroll per key press (OS/app dependent)

# --- Keys for Free Mode Actions (ensure these are lowercase) ---
FREE_MODE_MOUSE_UP = 'i'
FREE_MODE_MOUSE_DOWN = 'k'
FREE_MODE_MOUSE_LEFT = 'j'
FREE_MODE_MOUSE_RIGHT = 'l'

FREE_MODE_SCROLL_UP = 'm'
FREE_MODE_SCROLL_DOWN = ',' # Comma key
FREE_MODE_SCROLL_LEFT = 'b'
FREE_MODE_SCROLL_RIGHT = 'n'


if __name__ == "__main__":
    print("--- Feature Configurations (feature_config.py) ---")
    print(f"Enable Free Mode: {ENABLE_FREE_MODE}")
    print(f"Free Mode Toggle Key: '{FREE_MODE_TOGGLE_KEY}'")
    print(f"Mouse Move Step: {MOUSE_MOVE_STEP} pixels")
    print(f"Scroll Step: {SCROLL_STEP} units")
    print("Free Mode Action Keys:")
    print(f"  Mouse Up: '{FREE_MODE_MOUSE_UP}', Down: '{FREE_MODE_MOUSE_DOWN}', Left: '{FREE_MODE_MOUSE_LEFT}', Right: '{FREE_MODE_MOUSE_RIGHT}'")
    print(f"  Scroll Up: '{FREE_MODE_SCROLL_UP}', Down: '{FREE_MODE_SCROLL_DOWN}', Left: '{FREE_MODE_SCROLL_LEFT}', Right: '{FREE_MODE_SCROLL_RIGHT}'")