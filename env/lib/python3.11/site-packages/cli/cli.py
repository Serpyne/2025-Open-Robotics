#from .version import __version__
from os.path import abspath, dirname, join
import sys, os, stat, json, getpass
import commands
import click
import mmap

from importlib.metadata import version, PackageNotFoundError
__version__ = None

try:
    __version__ = version("luma")
except PackageNotFoundError:
    # package is not installed
    pass
"""
    This is the top level of the CLI command tree. The CLI group is created and the
    subcommands are imported from the commands dir and added to the group. This allows
    these commands to be run with 'luma <command>'.
"""

@click.group(help='This CLI will allow you to interact with the Lumavate platform from your terminal. For setup instructions, look in github. \
Each command below has subcommands. Pass the --help flag to those commands for more information on how to use them.')
@click.version_option(version=__version__, prog_name="Lumavate CLI")
def cli():
    pass

cli.add_command(commands.env)
cli.add_command(commands.profile)
cli.add_command(commands.organization)
cli.add_command(commands.widget)
cli.add_command(commands.widget_version)
cli.add_command(commands.app_builder)
cli.add_command(commands.app_builder_version)
cli.add_command(commands.asset)
cli.add_command(commands.asset_version)
cli.add_command(commands.component_set)
cli.add_command(commands.component_set_version)
cli.add_command(commands.microservice)
cli.add_command(commands.microservice_version)
cli.add_command(commands.api)
cli.add_command(commands.experience)
cli.add_command(commands.experience_collection)

def init_config_file():
    luma_dir = os.path.expanduser('~/.luma')
    cli_path = os.path.join(luma_dir, 'luma_cli_config.json')

    if not os.path.exists(luma_dir):
        os.mkdir(luma_dir, mode=0o700)

    if os.path.exists(cli_path):
        print("Luma config exists already, skipping", flush=True)
    else:
        with open(cli_path, 'w+') as config:
            json.dump({ "envs": {}, "profiles": {} }, config)

    os.chmod(cli_path, 0o777)
    os.chmod(luma_dir, 0o777)

def init_auto_complete():
    zshrc = os.path.expanduser('~/.zshrc')
    bashrc = os.path.expanduser('~/.bash_profile')

    if os.path.exists(zshrc) and os.stat(zshrc).st_size != 0:
        tab_comp = False
        with open(zshrc, 'rb', 0) as zsh_config, mmap.mmap(zsh_config.fileno(), 0, access=mmap.ACCESS_READ) as s:
            if s.find(b'_LUMA_COMPLETE=source_zsh luma') != -1:
                tab_comp = True
                print("Completion already activated for ZSH")

        if tab_comp is False:
            with open(zshrc, 'a') as zsh:
                zsh.write('eval "$(_LUMA_COMPLETE=source_zsh luma)"')

    if os.path.exists(bashrc) and os.stat(bashrc).st_size != 0:
        tab_comp = False
        with open(bashrc, 'rb', 0) as bash_config, mmap.mmap(bash_config.fileno(), 0, access=mmap.ACCESS_READ) as s:
            if s.find(b'_LUMA_COMPLETE=source luma') != -1:
                tab_comp = True
                print("Completion already activated for Bash")

        if tab_comp is False:
            with open(bashrc, 'a+') as bash:
                bash.write('eval "$(_LUMA_COMPLETE=source luma)"')
    else:
        with open(bashrc, 'a+') as bash:
            bash.write('eval "$(_LUMA_COMPLETE=source luma)"')


if __name__ == '__main__':
    init_config_file()
    init_auto_complete()
    cli()
