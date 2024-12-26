import os
import click

@click.command(name="init")
def init_cmd():
    """
    Create Mapper-related files if they do not already exist.
    """
    files_to_create = [
        ".mapheader",
        ".mapfooter",
        ".mapignore",
        ".mapomit",
        ".mapinclude",
        ".mapconfig"
    ]

    for file_name in files_to_create:
        if not os.path.exists(file_name):
            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    if file_name == ".mapconfig":
                        f.write("# Mapper configuration file\n")
                    else:
                        f.write("")
                click.echo(f"Created {file_name}")
            except OSError as e:
                click.echo(f"Could not create {file_name}: {str(e)}")
        else:
            click.echo(f"Skipped {file_name}, already exists.")
