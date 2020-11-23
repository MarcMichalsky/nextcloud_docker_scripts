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


def backup():
    backup_status = True

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

    # If any container names where passed as parameters, do only backup them
    containers_wanted = {name: container for name, container in containers.items() if name in sys.argv}
    if containers_wanted:
        containers = containers_wanted

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
        if not utils.no_log:
            if settings_list['log']['logging']:
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
        if not utils.no_cleanup:
            deleted_files = 0
            backup_dir = os.scandir(container.backup_dir)
            backup_files = [file for file in backup_dir if
                            file.is_file() and file.name.startswith(container.name) and file.name.endswith(".tar.gz")]

            while len(backup_files) > container.number_of_backups:
                del_file = min(backup_files, key=os.path.getctime)
                backup_files.remove(del_file)
                os.remove(del_file)
                deleted_files += 1

            if deleted_files == 1:
                _print(F"{Fore.YELLOW}Deleted 1 old backup file.{Style.RESET_ALL}")
            elif deleted_files >= 1:
                _print(F"{Fore.YELLOW}Deleted {deleted_files} old backup files.{Style.RESET_ALL}")

    return backup_status


if __name__ == '__main__':
    backup()
