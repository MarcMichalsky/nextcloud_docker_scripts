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


def upgrade():
    upgrade_status = True

    # Fetch arguments
    utils.all_containers = "--all" in sys.argv
    utils.quiet_mode = "--quiet" in sys.argv
    utils.no_log = "--nolog" in sys.argv
    utils.no_cleanup = "--nocleanup" in sys.argv

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

        # Loop through Nextcloud container instances
        container: Container
        for container in containers.values():

            # Start backup
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
                    upgrade_status = False

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

        return upgrade_status


if __name__ == '__main__':
    upgrade()