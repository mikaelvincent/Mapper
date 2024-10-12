import click
from mapper.core import reset_settings

@click.command(name='reset-settings')
@click.pass_context
def reset_settings_command(ctx):
    """Reset all stored settings to their default values."""
    reset_settings()
    click.echo("Settings have been reset to default values.")
