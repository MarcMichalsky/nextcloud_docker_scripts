#!/usr/bin/env python3
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


def restore():

    # Set flags
    utils.set_flags(sys.argv)

    # Load config
    config = Path(__file__).parent / "config.yaml"
    with open(config) as file:
        # Load config
        config_list = yaml.full_load(file)
        log = Log(config_list['log']['log_dir'])
        containers = Container.instantiate_containers(config_list)

    # If any container names were passed as parameters, do only restore them
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

        # Start restore
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

        # Choose backup to restore from
        terminal_menu = TerminalMenu(backup_files_to_choose_from, title="Which backup do you want to restore?")
        choice_index = terminal_menu.show()
        backup_file = backup_files.get(backup_files_to_choose_from[choice_index])
        print(backup_file.path)

        # Confirm restore
        if not utils.no_confirm:
            confirm = input(F"Are you sure that you want to restore {backup_files_to_choose_from[choice_index]}? "
                            F"(Type: yes)\n").lower() == "yes"
        else:
            confirm = False

        # Do the restore
        if confirm or utils.no_confirm:
            result = container.restore_backup(backup_file.path)
        else:
            break

        # Print result and log
        if result:
            _print(F"{Fore.GREEN}Backup {container.restore_tar_file} for {container.name} successfully restored.{Style.RESET_ALL}")
            if not utils.no_log and config_list['log']['logging']:
                log.log(F"Restore backup ; {container.name} ; {container.restore_tar_file_path} ; SUCCESS")
        else:
            _print(F"{Fore.RED}Could not restore {container.restore_tar_file} for {container.name}.{Style.RESET_ALL}")
            for func, traceback in container.exceptions.items():
                _print()
                _print(F"{Fore.YELLOW}Exception occurred in method: Container.{func}(){Style.RESET_ALL}")
                _print(traceback)
                _print()
            if not utils.no_log and config_list['log']['logging']:
                log.log(F"Restore backup ; {container.name} ; {container.restore_tar_file_path} ; FAIL")


if __name__ == '__main__':
    restore()
