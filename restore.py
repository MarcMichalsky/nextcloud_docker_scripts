#!/usr/bin/env python3
import datetime
import os
import sys
from pathlib import Path
import yaml
from colorama import Fore, Style
import utils
from utils import _print
from models import Container
from models import Log

from simple_term_menu import TerminalMenu


# terminal_menu = TerminalMenu(["entry 1", "entry 2", "entry 3"])
# choice_index = terminal_menu.show()
# https://stackoverflow.com/posts/61265356/revisions

def restore():
    restore_status = True

    # Fetch arguments
    utils.all_containers = "--all" in sys.argv
    utils.quiet_mode = "--quiet" in sys.argv
    utils.no_log = "--nolog" in sys.argv

    # Load settings
    settings = Path(__file__).parent / "settings.yaml"
    with open(settings) as file:
        # Load settings
        settings_list = yaml.full_load(file)
        log = Log(settings_list['log']['log_dir'])
        containers = Container.instantiate_containers(settings_list)

    # If any container names where passed as parameters, do only restore them
    containers_wanted = {name: container for name, container in containers.items() if name in sys.argv}
    if containers_wanted:
        containers = containers_wanted
    # If no container was chosen ask for it
    elif not utils.all_containers:
        containers_to_choose_from = [container.name for container in containers.values()]
        terminal_menu = TerminalMenu(containers_to_choose_from, title="For which Nextcloud instance do you want "
                                                                      "to restore a backup?")
        choice_index = terminal_menu.show()
        containers = {containers_to_choose_from[choice_index]: containers.get(containers_to_choose_from[choice_index])}

    container: Container
    for container in containers.values():

        # Start backup restore
        _print("----------------------------------------------")
        _print(F"Restore backup for {container.name}")

        backup_dir = os.scandir(container.backup_dir)
        backup_files = {file.name: file for file in backup_dir if
                        file.is_file() and file.name.startswith(container.name) and file.name.endswith(".tar.gz")}
        if len(backup_files) < 1:
            _print(F"{Fore.YELLOW}No backups found for {container.name}{Style.RESET_ALL}")
            break
        backup_files_to_choose_from = [file.name for file in backup_files.values()]
        backup_files_to_choose_from.sort(reverse=True)
        _print()
        terminal_menu = TerminalMenu(backup_files_to_choose_from, title="Which backup do you want to restore?")
        choice_index = terminal_menu.show()
        backup_file = backup_files.get(backup_files_to_choose_from[choice_index])
        print(backup_file.path)

        confirm = input(F"Are you sure that you want to restore {backup_files_to_choose_from[choice_index]}? "
                        F"(Type: yes)\n").lower() == "yes"
        if confirm:
            result = container.restore_backup(backup_file.path)
        else:
            break


if __name__ == '__main__':
    restore()
