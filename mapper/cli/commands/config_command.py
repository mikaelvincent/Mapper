import click

from mapper.config.file_handling import parse_mapconfig, write_mapconfig

@click.command(name="config")
@click.option("--set", "pairs", multiple=True,
              help="Set a configuration value in the format key=value.")
def config_cmd(pairs):
    """
    Modify .mapconfig by passing --set key=value pairs.
    Creates .mapconfig if it does not exist.
    """
    config_path = ".mapconfig"
    current_config = parse_mapconfig(config_path)

    updated_count = 0
    for pair in pairs:
        if "=" not in pair:
            click.echo(f"Skipping invalid parameter: {pair}")
            continue
        key, value = pair.split("=", 1)
        key, value = key.strip(), value.strip()

        # Attempt to parse the value similarly to parse_mapconfig
        if key in ("max_files", "max_characters_per_file"):
            try:
                current_config[key] = int(value)
                updated_count += 1
            except ValueError:
                click.echo(f"Invalid integer for {key}: {value}. Skipped.")
        elif key in (
            "ignore_hidden",
            "trim_trailing_whitespaces",
            "trim_all_empty_lines",
            "minimal_output",
            "use_absolute_path_title",
        ):
            bool_val = value.lower() in ("true", "1", "yes")
            current_config[key] = bool_val
            updated_count += 1
        elif key == "encodings":
            enc_list = [v.strip() for v in value.replace(",", " ").split()]
            current_config[key] = [enc for enc in enc_list if enc]
            updated_count += 1
        else:
            # Accept any unrecognized key as a string
            current_config[key] = value
            updated_count += 1

    if updated_count > 0:
        write_mapconfig(current_config, config_path)
        click.echo(f"Updated {updated_count} value(s) in {config_path}")
    else:
        click.echo("No valid configuration changes found.")
