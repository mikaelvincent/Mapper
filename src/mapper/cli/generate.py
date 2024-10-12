import click
from mapper.core import generate_structure
from mapper.config import save_user_settings

@click.command()
@click.option('-o', '--output', default='.map', help='Specify output file name.')
@click.option('-i', '--ignore', default='.mapignore', help='Specify custom ignore file.')
@click.option('-H', '--header', default='.mapheader', help='Specify custom header file.')
@click.option('-F', '--footer', default='.mapfooter', help='Specify custom footer file.')
@click.option('-a', '--indent-char', default='  ', help='Choose indentation character.')
@click.option('--arrow', default='->', help='Customize arrow symbol.')
@click.option('--ignore-hidden', type=bool, default=True, help='Toggle to ignore hidden files.')
@click.option('--max-size', type=int, default=1000000, help='Set maximum file size before truncation in bytes.')
@click.pass_context
def generate_command(ctx, output, ignore, header, footer, indent_char, arrow, ignore_hidden, max_size):
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
