#!/usr/bin/env python3

import datetime
import sys
from pathlib import Path
import yaml
from colorama import Fore, Style
import utils
from utils import _print
from models import Container
from models import Log
from simple_term_menu import TerminalMenu


def backup():
    backup_status = True

    # Set flags
    utils.set_flags(sys.argv)

    # Load configuration
    config = Path(__file__).parent / "config.yml"
    with open(config) as file:
        # Load config
        config_list = yaml.full_load(file)
        log = Log(config_list['log']['log_dir'])
        containers = Container.instantiate_containers(config_list)

    # If any container names were passed as parameters, do only back up them
    containers_wanted = {name: container for name, container in containers.items() if name in sys.argv}
    if containers_wanted:
        containers = containers_wanted

    # If no container was chosen ask for it
    elif not utils.all_containers:
        containers_to_choose_from = [container.name for container in containers.values()]
        terminal_menu = TerminalMenu(containers_to_choose_from, title="Which Nextcloud instance do you want to back up?")
        choice_index = terminal_menu.show()
        containers = {containers_to_choose_from[choice_index]: containers.get(containers_to_choose_from[choice_index])}

    # Loop through Nextcloud container instances
    container: Container
    for container in containers.values():

        # Start backup
        _print("----------------------------------------------")
        _print(F"Start backup for {container.name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        result = container.create_backup()
        if result:
            _print(F"{Fore.GREEN}Backup for {container.name} successfully created under "
                   F"{container.tar_gz_file_path} [{result} MB]{Style.RESET_ALL}")
        else:
            _print(F"{Fore.RED}Backup for {container.name} failed{Style.RESET_ALL}")
            for func, traceback in container.exceptions.items():
                _print()
                _print(F"{Fore.YELLOW}Exception occurred in method: Container.{func}(){Style.RESET_ALL}")
                _print(traceback)
                _print()
                backup_status = False

        # Log backup
        if not utils.no_log and config_list['log']['logging']:
            if backup_status:
                log.log(F"Created a backup ; {container.name} ; {container.tar_gz_file_path} ; {result} MB")
            else:
                log.log(F"Backup for {container.name} failed")
                if len(log.exceptions) > 0:
                    for func, traceback in log.exceptions.items():
                        _print()
                        _print(F"{Fore.YELLOW}Exception occurred in method: Log.{func}(){Style.RESET_ALL}")
                        _print(traceback)
                        _print()

        # Clean up backup folder
        container.cleanup()

    return backup_status

if __name__ == '__main__':
    backup()
