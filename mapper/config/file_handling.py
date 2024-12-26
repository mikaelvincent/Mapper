import os

def parse_mapconfig(config_path=".mapconfig"):
    """
    Parse the .mapconfig file if it exists. Return a dictionary
    of configuration settings. Lines starting with '#' are treated
    as comments and ignored. Configuration is assumed to be in
    'key=value' format.
    """
    config_data = {}
    if not os.path.isfile(config_path):
        return config_data

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Attempt basic type parsing
                if key in ("max_files", "max_characters_per_file"):
                    try:
                        config_data[key] = int(value)
                    except ValueError:
                        # Invalid integer; ignore or handle as needed
                        pass
                elif key in (
                    "ignore_hidden",
                    "trim_trailing_whitespaces",
                    "trim_all_empty_lines",
                    "minimal_output",
                    "use_absolute_path_title",
                ):
                    # Convert string to boolean
                    config_data[key] = value.lower() in ("true", "1", "yes")
                elif key == "encodings":
                    # Split on commas or spaces
                    enc_list = [v.strip() for v in value.replace(",", " ").split()]
                    config_data[key] = [enc for enc in enc_list if enc]
                else:
                    # Unrecognized or additional fields can be stored directly
                    config_data[key] = value
    except OSError:
        # If there's an issue reading the file, treat as empty config
        pass

    return config_data

def write_mapconfig(config_data, config_path=".mapconfig"):
    """
    Write the provided configuration dictionary to .mapconfig,
    attempting to preserve valid formatting.
    """
    lines = ["# Mapper configuration file"]
    for key, value in config_data.items():
        if isinstance(value, bool):
            val_str = "true" if value else "false"
        elif isinstance(value, int):
            val_str = str(value)
        elif isinstance(value, list):
            val_str = ",".join(value)
        else:
            val_str = str(value)
        lines.append(f"{key}={val_str}")

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except OSError as e:
        # Keep the existing comment if relevant
        pass
