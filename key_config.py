# key_config.py

# --- Grid Dimensions ---
MAIN_GRID_COLS = 25
MAIN_GRID_ROWS = 36
SUB_GRID_COLS = 8  # You'll still need to manually define these 24 keys below
SUB_GRID_ROWS = 3

def get_main_grid_key_map():
    """
    Generates 2-character key combinations for the main grid based on a specific pattern.
    The pattern cycles through predefined character sets for the first and second key character.
    """
    keys = {}
    total_cells_to_map = MAIN_GRID_ROWS * MAIN_GRID_COLS

    # Define the character sets for the first and second characters of the key combos
    # These will be cycled through for each row.
    # Format: Each inner list is a set of characters for one 'block' of rows for that key part.
    
    # For the first character of the 2-char key combo
    # Cycle: qwert -> asdfg -> zxcvb -> yuiop -> hjkl; -> nm,./ -> then repeat
    first_char_sources = [
        list("qwert"),  # Source for key1 when cycle is at 0
        list("asdfg"),  # Source for key1 when cycle is at 1
        list("zxcvb"),  # Source for key1 when cycle is at 2
        list("yuiop"),  # Source for key1 when cycle is at 3
        list("hjkl;"),  # Source for key1 when cycle is at 4
        list("nm,./"),  # Source for key1 when cycle is at 5
    ]

    # For the second character of the 2-char key combo
    # For row 0: qwert
    # For row 1: asdfg
    # For row 2: zxcvb
    # ... and so on, cycling through first_char_sources
    second_char_sources = first_char_sources # They use the same pool of sources

    keys_generated = 0
    for r in range(MAIN_GRID_ROWS):
        # Determine which source list to use for the first char based on the row
        # (r // len(second_char_sources)) determines how many full cycles of second_char_sources we've done for the first char
        # % len(first_char_sources) ensures we wrap around the first_char_sources if needed
        idx_first_char_source = (r // len(second_char_sources)) % len(first_char_sources)
        current_first_chars = first_char_sources[idx_first_char_source]

        # Determine which source list to use for the second char based on the row
        idx_second_char_source = r % len(second_char_sources)
        current_second_chars = second_char_sources[idx_second_char_source]
        
        # print(f"DEBUG Row {r}: First chars from '{''.join(current_first_chars)}', Second chars from '{''.join(current_second_chars)}'")


        for c in range(MAIN_GRID_COLS):
            if keys_generated >= total_cells_to_map:
                break

            # Generate the key combo by cycling through current_first_chars and current_second_chars
            # This creates len(current_first_chars) * len(current_second_chars) unique keys for this row's source combination
            # We need to map the column 'c' to these combinations.
            
            # Example: if current_first_chars = "qwert" (len 5) and current_second_chars = "qwert" (len 5)
            # This combination can produce 5 * 5 = 25 keys, perfect for one row if MAIN_GRID_COLS is 25.
            
            if not current_first_chars or not current_second_chars:
                print(f"ERROR: Empty char source for row {r}, col {c}. Skipping.")
                continue

            first_key_char_index = c // len(current_second_chars)
            second_key_char_index = c % len(current_second_chars)

            if first_key_char_index >= len(current_first_chars) :
                # This happens if MAIN_GRID_COLS > len(current_first_chars) * len(current_second_chars)
                # which means not enough unique key combos from the current char sets for all columns in this row.
                # For your specific request where each pair gives 25 keys, and COLS=25, this shouldn't be an issue.
                key_str = f"{r:02}{c:02}" # Fallback key to ensure something is there, will look like "0000", "0001"
                print(f"WARNING: Ran out of unique key combinations for row {r} at col {c}. Using fallback '{key_str}'.")
                print(f"         (First chars: '{''.join(current_first_chars)}', Second chars: '{''.join(current_second_chars)}')")
                print(f"         (first_key_char_index: {first_key_char_index}, second_key_char_index: {second_key_char_index})")

            else:
                key_char1 = current_first_chars[first_key_char_index]
                key_char2 = current_second_chars[second_key_char_index]
                key_str = key_char1 + key_char2
            
            if key_str in keys:
                # This means the pattern is generating duplicate keys.
                # This can happen if the cycling logic or source lists lead to repetition
                # before all cells are filled.
                original_r, original_c = keys[key_str]
                print(f"WARNING: Duplicate key '{key_str}' generated for ({r},{c}). It was already assigned to ({original_r},{original_c}). Using fallback.")
                key_str = f"D{r:02}{c:02}" # Fallback for duplicate

            keys[key_str] = (r, c)
            keys_generated += 1
        
        if keys_generated >= total_cells_to_map:
            break
            
    if keys_generated < total_cells_to_map:
        print(f"WARNING (key_config.py): Main grid key map generation is incomplete! Expected {total_cells_to_map} keys, generated {keys_generated}.")
    
    return keys


def get_sub_grid_key_map():
    """
    Define your 1-character key combinations for each cell in the sub-grid.
    The format is: "x": (row, col)
    where 'row' is 0 to SUB_GRID_ROWS-1, and 'col' is 0 to SUB_GRID_COLS-1.
    (8 * 3 = 24 key combinations for the sub-grid)
    """
    keys = {}

    # --- BEGIN MANUAL ASSIGNMENT FOR SUB GRID ---
    # Example for a 3x8 sub-grid - YOU MUST CUSTOMIZE OR COMPLETE THIS
    # Using a QWERTY-like layout for example
    keys["q"] = (0, 0); keys["w"] = (0, 1); keys["e"] = (0, 2); keys["r"] = (0, 3)
    keys["t"] = (0, 4); keys["y"] = (0, 5); keys["u"] = (0, 6); keys["i"] = (0, 7) # 8 keys for row 0

    keys["a"] = (1, 0); keys["s"] = (1, 1); keys["d"] = (1, 2); keys["f"] = (1, 3)
    keys["g"] = (1, 4); keys["h"] = (1, 5); keys["j"] = (1, 6); keys["k"] = (1, 7) # 8 keys for row 1

    keys["z"] = (2, 0); keys["x"] = (2, 1); keys["c"] = (2, 2); keys["v"] = (2, 3)
    keys["b"] = (2, 4); keys["n"] = (2, 5); keys["m"] = (2, 6); keys[","] = (2, 7) # 8 keys for row 2
    # --- END MANUAL ASSIGNMENT FOR SUB GRID ---

    if len(keys) < SUB_GRID_COLS * SUB_GRID_ROWS:
        print(f"WARNING (key_config.py): Sub-grid key map is incomplete! Expected {SUB_GRID_COLS * SUB_GRID_ROWS} keys, found {len(keys)}.")
    return keys

if __name__ == '__main__':
    print("--- Testing key_config.py ---")
    print(f"Main Grid Dimensions: {MAIN_GRID_ROWS} rows x {MAIN_GRID_COLS} cols")
    main_map = get_main_grid_key_map()
    print(f"Number of main grid keys generated: {len(main_map)}")
    
    # Print a sample of the generated main grid keys and their (row, col)
    print("\nSample of Main Grid Keys (key: (row, col)):")
    count = 0
    for r_test in range(MAIN_GRID_ROWS):
        if count >= 100 and r_test < MAIN_GRID_ROWS -1 : # Print first ~100 and last row
            if r_test == 10 : print("  ...") # Print ... once
            continue

        keys_in_row = []
        for c_test in range(MAIN_GRID_COLS):
            # Find key for this cell
            key_for_cell = None
            for k, v_rc in main_map.items():
                if v_rc == (r_test, c_test):
                    key_for_cell = k
                    break
            if key_for_cell:
                keys_in_row.append(f"{key_for_cell}:({r_test},{c_test})")
            else:
                keys_in_row.append(f"__MISSING__") # Should not happen if generation is complete

        print(f"Row {r_test:02d}: {'  '.join(keys_in_row[:5])} ... {'  '.join(keys_in_row[-5:]) if MAIN_GRID_COLS > 10 else '  '.join(keys_in_row)}" if MAIN_GRID_COLS > 5 else f"Row {r_test:02d}: {'  '.join(keys_in_row)}")
        count += MAIN_GRID_COLS


    print(f"\nSub Grid Dimensions: {SUB_GRID_ROWS} rows x {SUB_GRID_COLS} cols")
    sub_map = get_sub_grid_key_map()
    print(f"Number of sub grid keys defined: {len(sub_map)}")
    print("Sub map sample:", list(sub_map.items())[:8])