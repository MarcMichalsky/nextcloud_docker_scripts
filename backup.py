#!/usr/bin/env python3

import datetime
import os
import sys
import yaml
from colorama import Fore, Style
import Models.Backup
from Models.Container import Container
from Models.NextcloudBackupException import NextcloudBackupException


def backup(container_names=None):
    global backup_successfull
    with open(r"./settings.yaml") as file:
        # Load settings
        settings_list = yaml.full_load(file)
        log_file = settings_list['paths']['log_file']
        containers = Container.deserialize_containers(settings_list)

    if type(container_names) is list:
        containers_tmp = []
        for container_name in container_names:
            if container_name is str and container_name in containers:
                containers_tmp.append(containers[container_name])
            else:
                print(F"{Fore.RED}Cannot find configuration for {container_name} in settings.yaml{Style.RESET_ALL}")
        containers = containers_tmp

    # Loop through Nextcloud container instances
    container: Container
    for container in containers:
        # Create backup folder if it does not yet exist
        if container.create_backup_dir():
            try:
                print(F"{Fore.GREEN}Backup folder created under: {container.backup_folder}{Style.RESET_ALL}")
            except OSError as e:
                sys.exit(F"{Fore.RED}Could not create backup folder: {e.strerror}{Style.RESET_ALL}")

        print(F"Starting backup for {container.name}:")
        try:
            backup_successfull = True
            for key, status in container.create_backup():
                if status is True:
                    print(F"{Fore.GREEN}{key}: success{Style.RESET_ALL}")
                else:
                    print(F"{Fore.RED}{key}: failed{Style.RESET_ALL}")
                    backup_successfull = False
        except NextcloudBackupException as e:
            print(F"{Fore.RED}Backup for {container.name} failed!/n{e.message}{Style.RESET_ALL}")
        print("---------------------------------")
        if backup_successfull is True:
            print(F"{Fore.GREEN}Backup for {container.name} was successful{Style.RESET_ALL}")
        else:
            print(F"{Fore.RED}Backup for {container.name} failed{Style.RESET_ALL}")



if __name__ == '__main__':
    backup(sys.argv)

