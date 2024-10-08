import click
from mapper.core import generate_structure, reset_settings, get_version
from mapper.config import save_user_settings, load_user_settings, DEFAULT_SETTINGS

@click.group()
@click.option('-v', '--verbose', is_flag=True, default=False, help='Enable detailed output.')
@click.option('-q', '--quiet', is_flag=True, default=False, help='Suppress non-essential messages.')
@click.option('--save-settings', is_flag=True, default=False, help='Store current options for future invocations.')
@click.option('--load-settings', is_flag=True, default=False, help='Load previously saved settings.')
@click.pass_context
def main(ctx, verbose, quiet, save_settings, load_settings):
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['QUIET'] = quiet
    ctx.obj['SAVE_SETTINGS'] = save_settings
    ctx.obj['LOAD_SETTINGS'] = load_settings
    if load_settings:
        settings = load_user_settings()
        ctx.obj.update(settings)

@main.command()
def version():
    """Display Mapper's current version."""
    version = get_version()
    click.echo(f"Mapper version {version}")

@main.command(name='reset-settings')
@click.pass_context
def reset_settings_command(ctx):
    """Reset all stored settings to their default values."""
    reset_settings()
    click.echo("Settings have been reset to default values.")

@main.command()
@click.option('-o', '--output', default='map.md', help='Specify output file name.')
@click.option('-i', '--ignore', default='.mapignore', help='Specify custom ignore file.')
@click.option('-H', '--header', default='.mapheader', help='Specify custom header file.')
@click.option('-F', '--footer', default='.mapfooter', help='Specify custom footer file.')
@click.option('-a', '--indent-char', default='  ', help='Choose indentation character.')
@click.option('--arrow', default='->', help='Customize arrow symbol.')
@click.option('--ignore-hidden', type=bool, default=True, help='Toggle to ignore hidden files.')
@click.option('--max-size', type=int, default=1000000, help='Set maximum file size before truncation in bytes.')
@click.pass_context
def generate(ctx, output, ignore, header, footer, indent_char, arrow, ignore_hidden, max_size):
    """Creates the project structure output."""
    settings = {
        'output': output,
        'ignore': ignore,
        'header': header,
        'footer': footer,
        'indent_char': indent_char,
        'arrow': arrow,
        'ignore_hidden': ignore_hidden,
        'max_size': max_size,
        'verbose': ctx.obj.get('VERBOSE', False),
        'quiet': ctx.obj.get('QUIET', False)
    }
    if ctx.obj.get('SAVE_SETTINGS', False):
        save_user_settings(settings)
    generate_structure(settings)
    if not ctx.obj.get('QUIET', False):
        click.echo("Project structure generated")

if __name__ == '__main__':
    main()
