# key_config.py

# --- Grid Dimensions ---
# These define the size of your grids.
MAIN_GRID_COLS = 25
MAIN_GRID_ROWS = 36
SUB_GRID_COLS = 8
SUB_GRID_ROWS = 3 # For a 3x8 sub-grid as in previous examples

def get_main_grid_key_map():
    """
    Programmatically generates 2-character key combinations for the main grid
    based on the specified pattern:
    - The first character of the key combo comes from a set that cycles every 6 rows.
    - The second character of the key combo comes from a set that cycles for each row within that 6-row block.
    - Each combination of a first character (from its set) and a second character (from its set)
      forms a key for a column.
    """
    keys = {}
    
    # Define the character sets for the first character of the key combo
    # These correspond to the "first" set in your row descriptions
    # Each set should ideally have 5 characters if MAIN_GRID_COLS / 5 is an integer.
    # Since MAIN_GRID_COLS is 25, and we pair 5 chars with 5 chars, this works.
    first_char_sets = [
        "QWERT",  # For rows 0-5
        "ASDFG",  # For rows 6-11
        "ZXCVB",  # For rows 12-17
        "YUIOP",  # For rows 18-23
        "HJKL;",  # For rows 24-29
        "NM,./"   # For rows 30-35
    ]

    # Define the character sets for the second character of the key combo
    # These correspond to the "second" set in your row descriptions
    second_char_sets = [
        "QWERT",  # Used with first_char_sets[0] for row 0, first_char_sets[1] for row 6, etc.
        "ASDFG",  # Used with first_char_sets[0] for row 1, first_char_sets[1] for row 7, etc.
        "ZXCVB",  # Used with first_char_sets[0] for row 2, ...
        "YUIOP",  # Used with first_char_sets[0] for row 3, ...
        "HJKL;",  # Used with first_char_sets[0] for row 4, ...
        "NM,./"   # Used with first_char_sets[0] for row 5, ...
    ]

    keys_generated_count = 0

    for r_idx in range(MAIN_GRID_ROWS):
        # Determine which set of first characters to use based on the row index
        # Each first_char_set is used for len(second_char_sets) consecutive rows (e.g., 6 rows)
        first_set_index = r_idx // len(second_char_sets)
        if first_set_index >= len(first_char_sets):
            print(f"WARNING (key_config.py): Not enough 'first_char_sets' defined to cover row {r_idx}. Stopping main grid key generation for this row and subsequent ones.")
            break 
        chars1_for_row = first_char_sets[first_set_index]

        # Determine which set of second characters to use based on the row index
        # This cycles through second_char_sets for each block of rows defined by first_char_sets
        second_set_index = r_idx % len(second_char_sets)
        # No need to check second_set_index bounds if len(second_char_sets) is > 0, modulo will handle it.
        chars2_for_row = second_char_sets[second_set_index]
        
        col_idx = 0
        # Create combinations from chars1_for_row and chars2_for_row
        # Example: chars1_for_row = "QWERT", chars2_for_row = "QWERT"
        # Generates: QQ, QW, QE, QR, QT (5 keys)
        #            WQ, WW, WE, WR, WT (5 keys)
        #            ...
        #            TQ, TW, TE, TR, TT (5 keys)
        # Total: 5 * 5 = 25 keys, matching MAIN_GRID_COLS
        for char1 in chars1_for_row:
            for char2 in chars2_for_row:
                if col_idx < MAIN_GRID_COLS:
                    key_combo = char1 + char2
                    # Check for duplicate key assignments (should not happen with this logic if char sets are distinct enough)
                    if key_combo in keys and keys[key_combo] != (r_idx, col_idx):
                        print(f"ERROR (key_config.py): Duplicate key '{key_combo}' encountered! Current: ({r_idx},{col_idx}), Previous: {keys[key_combo]}")
                    keys[key_combo] = (r_idx, col_idx)
                    keys_generated_count += 1
                    col_idx += 1
                else:
                    break # Filled all columns for this row
            if col_idx >= MAIN_GRID_COLS:
                break # Filled all columns for this row
        
        if col_idx < MAIN_GRID_COLS:
            print(f"WARNING (key_config.py): Row {r_idx} was not completely filled. Needed {MAIN_GRID_COLS} keys, generated {col_idx} from sets '{chars1_for_row}' and '{chars2_for_row}'. Check character set lengths.")

    expected_total_keys = MAIN_GRID_COLS * MAIN_GRID_ROWS
    if keys_generated_count < expected_total_keys:
        print(f"WARNING (key_config.py): Main grid key map generation is INCOMPLETE! Expected {expected_total_keys} keys, generated {keys_generated_count}.")
    elif keys_generated_count > expected_total_keys:
         print(f"WARNING (key_config.py): Main grid key map generation produced TOO MANY keys! Expected {expected_total_keys}, generated {keys_generated_count}. This implies duplicate key strings mapping to different cells, which is an error.")
    
    return keys


def get_sub_grid_key_map():
    """
    Define your 1-character key combinations for each cell in the sub-grid.
    The format is: "x": (row, col)
    where 'row' is 0 to SUB_GRID_ROWS-1, and 'col' is 0 to SUB_GRID_COLS-1.
    YOU NEED TO MANUALLY DEFINE THESE.
    """
    keys = {}
    
    # Example for a 3x8 sub-grid - YOU MUST CUSTOMIZE THIS if your SUB_GRID_COLS/ROWS change
    # or if you want different keys.
    # Ensure you have SUB_GRID_COLS * SUB_GRID_ROWS unique keys. (8 * 3 = 24 keys)

    # Row 0
    keys["Q"] = (0, 0); keys["W"] = (0, 1); keys["E"] = (0, 2); keys["R"] = (0, 3)
    keys["U"] = (0, 4); keys["I"] = (0, 5); keys["O"] = (0, 6); keys["P"] = (0, 7)

    keys["A"] = (1, 0); keys["S"] = (1, 1); keys["D"] = (1, 2); keys["F"] = (1, 3)
    keys["J"] = (1, 4); keys["K"] = (1, 5); keys["L"] = (1, 6); keys[";"] = (1, 7)

    keys["Z"] = (2, 0); keys["X"] = (2, 1); keys["C"] = (2, 2); keys["V"] = (2, 3)
    keys["N"] = (2, 4); keys["M"] = (2, 5); keys[","] = (2, 6); keys["."] = (2, 7) # Example using a symbol

    expected_sub_keys = SUB_GRID_COLS * SUB_GRID_ROWS
    if len(keys) < expected_sub_keys:
        print(f"WARNING (key_config.py): Sub-grid key map is incomplete! Expected {expected_sub_keys} keys, found {len(keys)}.")
    elif len(keys) > expected_sub_keys:
        # This can happen if you have duplicate keys assigned to different cells by mistake
        print(f"WARNING (key_config.py): Sub-grid key map has more entries ({len(keys)}) than expected cells ({expected_sub_keys}). Check for duplicate key strings assigned to different cells.")

    return keys

if __name__ == '__main__':
    print("--- Testing key_config.py ---")
    
    print(f"\n--- Main Grid Key Mappings ({MAIN_GRID_ROWS} rows x {MAIN_GRID_COLS} cols) ---")
    main_map = get_main_grid_key_map()
    print(f"Total number of main grid keys generated: {len(main_map)}")
    
    print("\nSample Main Grid Keys (Key: (Row, Col)) to verify pattern:")
    # Row 0: QWERT + QWERT
    if ("QQ" in main_map): print(f"  keys[\"QQ\"] = {main_map['QQ']}") # Expected (0,0)
    if ("QW" in main_map): print(f"  keys[\"QW\"] = {main_map['QW']}") # Expected (0,1)
    if ("QT" in main_map): print(f"  keys[\"QT\"] = {main_map['QT']}") # Expected (0,4)
    if ("WQ" in main_map): print(f"  keys[\"WQ\"] = {main_map['WQ']}") # Expected (0,5)
    if ("TT" in main_map): print(f"  keys[\"TT\"] = {main_map['TT']}") # Expected (0,24)

    # Row 1: QWERT + ASDFG
    if ("QA" in main_map): print(f"  keys[\"QA\"] = {main_map['QA']}") # Expected (1,0)
    if ("QG" in main_map): print(f"  keys[\"QG\"] = {main_map['QG']}") # Expected (1,4)
    if ("TG" in main_map): print(f"  keys[\"TG\"] = {main_map['TG']}") # Expected (1,24)

    # Row 6: ASDFG + QWERT
    if ("AQ" in main_map): print(f"  keys[\"AQ\"] = {main_map['AQ']}") # Expected (6,0)
    if ("SQ" in main_map): print(f"  keys[\"SQ\"] = {main_map['SQ']}") # Expected (6,5)
    if ("GT" in main_map): print(f"  keys[\"GT\"] = {main_map['GT']}") # Expected (6,24)

    # Row 35 (last row): NM,./ + NM,./
    if ("NN" in main_map and main_map["NN"] == (35,0)): print(f"  keys[\"NN\"] = {main_map['NN']}")
    if ("//" in main_map and main_map["//"] == (35,24)): print(f"  keys[\"//\"] = {main_map['//']}")


    # Uncomment to print all generated main grid keys (can be very long for 900 keys)
    # print("\n--- All Generated Main Grid Key Mappings (Sorted) ---")
    # sorted_main_map_items = sorted(main_map.items(), key=lambda item: (item[1][0], item[1][1]))
    # for key, (row, col) in sorted_main_map_items:
    #     print(f"keys[\"{key}\"] = ({row}, {col})")
    
    print(f"\n--- Sub Grid Key Mappings ({SUB_GRID_ROWS} rows x {SUB_GRID_COLS} cols) ---")
    sub_map = get_sub_grid_key_map()
    print(f"Number of sub grid keys defined: {len(sub_map)}")
    # Uncomment to print all defined sub grid keys
    # print("\n--- All Defined Sub Grid Key Mappings ---")
    # for key, (row, col) in sub_map.items():
    #     print(f"keys[\"{key}\"] = ({row}, {col})")