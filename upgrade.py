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
import backup
from simple_term_menu import TerminalMenu


def upgrade():

    # Set flags
    utils.set_flags(sys.argv)

    # Load settings
    settings = Path(__file__).parent / "settings.yaml"
    with open(settings) as file:
        # Load settings
        settings_list = yaml.full_load(file)
        log = Log(settings_list['log']['log_dir'])
        containers = Container.instantiate_containers(settings_list)

    # If any container names were passed as parameters, do only upgrade them
    containers_wanted = {name: container for name, container in containers.items() if name in sys.argv}
    if containers_wanted:
        containers = containers_wanted

    # If no container was chosen ask for it
    elif not utils.all_containers:
        containers_to_choose_from = [container.name for container in containers.values()]
        terminal_menu = TerminalMenu(containers_to_choose_from, title="Which Nextcloud instance do you want to "
                                                                      "upgrade?")
        choice_index = terminal_menu.show()
        containers = {containers_to_choose_from[choice_index]: containers.get(containers_to_choose_from[choice_index])}

    # Loop through Nextcloud container instances
    container: Container
    for container in containers.values():
        go_on = True
        # Make a backup
        if not utils.no_backup:
            utils.keep_maintenance_mode = True
            go_on = backup.backup()
        if go_on:
            # Make the upgrade
            utils.keep_maintenance_mode = True if "--maintenance" in sys.argv else False
            _print("----------------------------------------------")
            _print(F"Start upgrade for {container.name} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            result = container.upgrade()
            if result == 1:
                _print(F"{Fore.GREEN}{container.name} upgraded successfully{Style.RESET_ALL}")
                upgrade_status = True
            elif result == 2:
                _print(F"{Fore.GREEN}No upgrades available for {container.name}.{Style.RESET_ALL}")
                upgrade_status = True
            else:
                _print(F"{Fore.RED}Upgrade for {container.name} failed{Style.RESET_ALL}")
                for func, traceback in container.exceptions.items():
                    _print()
                    _print(F"{Fore.YELLOW}Exception occurred in method: Container.{func}(){Style.RESET_ALL}")
                    _print(traceback)
                    _print()
            # Log upgrade
            if not utils.no_log and settings_list['log']['logging']:
                if upgrade_status:
                    log.log(F"Upgrade ; {container.name} ; SUCCESS")
                else:
                    log.log(F"Upgrade ; {container.name} ; FAIL")
                    if len(log.exceptions) > 0:
                        for func, traceback in log.exceptions.items():
                            _print()
                            _print(F"{Fore.YELLOW}Exception occurred in method: Log.{func}(){Style.RESET_ALL}")
                            _print(traceback)
                            _print()


if __name__ == '__main__':
    upgrade()
