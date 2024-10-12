import click
from mapper.core import get_version

@click.command(name='version')
def version_command():
    """Display Mapper's current version."""
    version = get_version()
    click.echo(f"Mapper version {version}")
