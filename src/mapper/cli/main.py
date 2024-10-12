import click
from mapper.core import generate_structure, reset_settings, get_version
from mapper.config import save_user_settings, load_user_settings, DEFAULT_SETTINGS
from .version import version_command
from .reset_settings import reset_settings_command
from .generate import generate_command

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

main.add_command(version_command)
main.add_command(reset_settings_command)
main.add_command(generate_command)

if __name__ == '__main__':
    main()
