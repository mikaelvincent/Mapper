import click

from mapper import __version__

@click.command(name="version")
def version_cmd():
    """
    Display placeholder version information.
    """
    click.echo(f"Mapper version: {__version__}")
