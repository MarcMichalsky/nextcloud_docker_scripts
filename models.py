import datetime
import os
import stat
import subprocess
from subprocess import check_output
import tarfile
import traceback
import shutil
from colorama import Fore, Style
from pathlib import Path
from utils import _print


class Container:

    def __init__(self, name, password, app_container, db_container, backup_dir, docker_compose_file_path,
                 number_of_backups) -> None:
        self.__datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.name = name
        self.__password = password
        self.app_container = app_container
        self.db_container = db_container
        self.backup_dir = backup_dir
        self.tmp_dir = os.path.join(backup_dir, 'tmp')
        self.docker_compose_file_path = docker_compose_file_path
        self.number_of_backups = number_of_backups
        self.__dump_file = self.name + '_' + self.__datetime + '.sql'
        self.__dump_file_path = os.path.join(self.tmp_dir, self.__dump_file)
        self.__tar_file = self.name + '_' + self.__datetime + '.tar'
        self.__tar_file_path = os.path.join(self.tmp_dir, self.__tar_file)
        self.tar_gz_file = self.__tar_file + '.gz'
        self.tar_gz_file_path = os.path.join(self.backup_dir, self.tar_gz_file)
        self.exceptions = {}
        self.SUCCESS = F"{Fore.GREEN}success{Style.RESET_ALL}"
        self.FAILED = F"{Fore.RED}failed{Style.RESET_ALL}"
        self.restore_dump_file = ""
        self.restore_dump_file_path = ""
        self.restore_tar_file_path = ""
        self.restore_tar_file = ""

    # Create backup dir if it does not yet exist
    def __create_backup_dir(self):
        if not os.path.isdir(self.backup_dir):
            try:
                os.makedirs(self.backup_dir)
                _print(F"{Fore.GREEN}Backup folder created under: {self.backup_dir}{Style.RESET_ALL}")
                return True
            except:
                _print(F"{Fore.RED}Could not backup tmp folder under {self.backup_dir}{Style.RESET_ALL}")
                self.exceptions.update({'create_backup_dir': traceback.format_exc()})
                return False
        else:
            return True

    # Create tmp dir
    def __create_tmp_dir(self) -> bool:
        if not os.path.isdir(self.tmp_dir):
            try:
                os.mkdir(self.tmp_dir)
                return os.path.isdir(self.tmp_dir)
            except:
                _print(F"{Fore.RED}Could not create tmp folder{Style.RESET_ALL}")
                self.exceptions.update({'create_tmp_dir': traceback.format_exc()})
                return False
        else:
            if self.__delete_tmp_dir():
                return self.__create_tmp_dir()

    # Delete tmp dir
    def __delete_tmp_dir(self) -> bool:
        try:
            shutil.rmtree(self.tmp_dir)
            return not os.path.isdir(self.tmp_dir)
        except:
            _print(F"{Fore.RED}Could not delete old tmp folder{Style.RESET_ALL}")
            self.exceptions.update({'delete_tmp_dir': traceback.format_exc()})
            return False

    # Dump database
    def __dump_db(self) -> bool:
        try:
            os.system(
                F"docker exec {self.db_container} mysqldump --password={self.__password} --all-databases > {self.__dump_file_path}")
            status = os.path.isfile(self.__dump_file_path)
            _print(F"Dump Nextcloud database: {self.SUCCESS if status else self.FAILED}")
            return status
        except:
            _print(F"Dump Nextcloud database: {self.FAILED}")
            self.exceptions.update({'__dump_db': traceback.format_exc()})
            return False

    # Import database
    def __import_db(self) -> bool:
        try:
            import_db = subprocess.Popen(['cat', self.restore_dump_file_path], stdout=subprocess.PIPE)
            result = check_output(
                ["docker", "exec", self.db_container, "mysql", "--user=root", "--password=" + self.__password, ],
                stdin=import_db.stdout)
            status = 'ERROR' not in result.decode("utf-8")
            _print(F"Import Nextcloud database: {self.SUCCESS if status else self.FAILED}")
            return status
        except subprocess.CalledProcessError as e:
            _print(F"Import Nextcloud database: {self.FAILED}")
            self.exceptions.update({'__import_db': traceback.format_exc()})
            return False

    # Tar config folder within container and copy it into backup folder
    def __export_config(self) -> bool:
        try:
            os.system(F"docker exec {self.app_container} tar -cf config.tar config/")
            os.system(F"docker cp {self.app_container}:/var/www/html/config.tar {self.__tar_file_path}")
            os.system(F"docker exec {self.app_container} rm config.tar")
            if os.path.isfile(self.__tar_file_path):
                with tarfile.open(self.__tar_file_path, 'r') as tarball:
                    tarball.extractall(self.tmp_dir)
                status = os.path.isdir(os.path.join(self.tmp_dir, "config"))
                _print(F"Export Nextcloud configuration: {self.SUCCESS if status else self.FAILED}")
                return status
            else:
                _print(F"Export Nextcloud configuration: {self.FAILED}")
        except:
            _print(F"Export Nextcloud configuration: {self.FAILED}")
            self.exceptions.update({'__export_config': traceback.format_exc()})
            return False

    # Tar config folder within container and copy it into backup folder
    def __import_config(self) -> bool:
        try:
            if os.path.isdir(os.path.join(self.tmp_dir, "config")):
                with tarfile.open(self.restore_tar_file_path, 'w') as tarball:
                    tarball.add(os.path.join(self.tmp_dir, "config"), arcname="/config")
            os.system(F"docker cp {self.restore_tar_file_path} {self.app_container}:/var/www/html/config.tar")
            os.system(F"docker exec {self.app_container} rm -r config")
            os.system(F"docker exec {self.app_container} tar -xf config.tar")
            os.system(F"docker exec {self.app_container} rm config.tar")
            status = True  # TODO: implement a test if export into docker container was successful
            _print(F"Import Nextcloud configuration: {self.SUCCESS if status else self.FAILED}")
            return status
        except:
            _print(F"Import Nextcloud configuration: {self.FAILED}")
            self.exceptions.update({'__import_config': traceback.format_exc()})
            return False

    # Tar database with config and settings
    def __tar_backup(self) -> bool:
        try:
            with tarfile.open(self.tar_gz_file_path, 'w:gz') as tarball:
                tarball.add(self.__dump_file_path, arcname=self.__dump_file)
                tarball.add(os.path.join(self.tmp_dir, "config"), arcname="/config")
            status = True  # TODO: Implement a test to confirm that files where added to tar file
            _print(F"Zip backup: {self.SUCCESS if status else self.FAILED}")
            return status
        except:
            _print(F"Zip backup: {self.FAILED}")
            self.exceptions.update({'__tar_backup': traceback.format_exc()})
            return False

    # Untar backup
    def __untar_backup(self) -> bool:
        try:
            with tarfile.open(self.backup_file_path, 'r:gz') as tarball:
                tarball.extractall(self.tmp_dir)
            status = os.path.isdir(os.path.join(self.tmp_dir, "config"))
            _print(F"Unzip backup: {self.SUCCESS if status else self.FAILED}")
            return status
        except:
            _print(F"Unzip backup: {self.FAILED}")
            self.exceptions.update({'__untar_backup': traceback.format_exc()})
            return False

    # Set secure file permissions
    def __set_file_permissions(self) -> bool:
        try:
            os.chmod(self.tar_gz_file_path, stat.S_IREAD)
            status = oct(os.stat(self.tar_gz_file_path).st_mode)[-3:] == '400'
            _print(F"Set secure file permissions: {self.SUCCESS if True else self.FAILED}")
            return status
        except:
            _print(F"Set secure file permissions: {self.FAILED}")
            self.exceptions.update({'__set_file_permissions': traceback.format_exc()})
            return False

    # Enable Nextcloud maintenance mode
    def __enable_maintenance_mode(self):
        try:
            enable_maintenance_mode = check_output(
                ["docker", "exec", "--user", "www-data", self.app_container, "php", "occ", "maintenance:mode", "--on"])
            chunks = enable_maintenance_mode.decode("utf-8").split('\n')
            if 'Maintenance mode enabled' in chunks or 'Maintenance mode already enabled' in chunks:
                _print(F"Enable Nextcloud maintenance mode: {self.SUCCESS}")
                return True
            else:
                _print(F"Enable Nextcloud maintenance mode: {self.FAILED}")
                return False
        except:
            self.exceptions.update({'__enable_maintenance_mode': traceback.format_exc()})
            _print(F"Enable Nextcloud maintenance mode: {self.FAILED}")
            return False

    # Disable Nextcloud maintenance mode
    def __disable_maintenance_mode(self):
        try:
            disable_maintenance_mode = check_output(
                ["docker", "exec", "--user", "www-data", self.app_container, "php", "occ", "maintenance:mode", "--off"])
            chunks = disable_maintenance_mode.decode("utf-8").split('\n')
            if 'Maintenance mode disabled' in chunks:
                _print(F"Disable Nextcloud maintenance mode: {self.SUCCESS}")
                return True
            else:
                _print(F"Disable Nextcloud maintenance mode: {self.FAILED}")
                return False
        except:
            self.exceptions.update({'__disable_maintenance_mode': traceback.format_exc()})
            _print(F"Disable Nextcloud maintenance mode: {self.FAILED}")
            return False

    # Pull new docker images
    def __pull_images(self):
        update_required = False
        try:
            if os.path.isfile(self.docker_compose_file_path):
                path = Path(self.docker_compose_file_path)
                directory = path.parent
            elif os.path.isdir(self.docker_compose_file_path):
                directory = self.docker_compose_file_path
            else:
                raise Exception("Docker Compose path invalid")
            os.chdir(directory)
            result = check_output(["docker-compose", "pull"])
            result = result.decode("utf-8").split("\n")
            for line in result:
                if line.startswith("Status:"):
                    _print(line)
                    if 'Image is up to date' not in line:
                        update_required = True
            return update_required
        except:
            self.exceptions.update({'__pull_images': traceback.format_exc()})
            _print(F"Pull new docker images: {self.FAILED}")
            return False

    # Restart docker containers
    def __restart_containers(self):
        try:
            if os.path.isfile(self.docker_compose_file_path):
                path = Path(self.docker_compose_file_path)
                directory = path.parent
            elif os.path.isdir(self.docker_compose_file_path):
                directory = self.docker_compose_file_path
            else:
                raise Exception("Docker Compose path invalid")
            os.chdir(directory)
            result = check_output(["docker-compose", "up", "-d"])
            _print(F"Restart docker containers: {self.SUCCESS}")
            return True  # TODO: Implement test
        except:
            self.exceptions.update({'__restart_containers': traceback.format_exc()})
            _print(F"Restart docker containers: {self.FAILED}")
            return False

    # Create backup and return file size in MB or False if it failed
    def create_backup(self):

        backup_functions = [
            self.__enable_maintenance_mode,
            self.__dump_db,
            self.__export_config,
            self.__disable_maintenance_mode,
            self.__tar_backup,
            self.__set_file_permissions,
            self.__delete_tmp_dir
        ]

        if self.__create_backup_dir() and self.__create_tmp_dir():
            try:
                for fn in backup_functions:
                    if not fn():
                        _print(F"{Fore.RED}Backup aborted.{Style.RESET_ALL}")
                        return False
                return round(Path(self.tar_gz_file_path).stat().st_size / 1000000, 2)
            except:
                self.exceptions.update({'backup': traceback.format_exc()})
                return False
        else:
            _print(F"{Fore.RED}Could not create temporary folder or backup folder. Backup aborted.{Style.RESET_ALL}")
            return False

    def restore_backup(self, backup_file_path):

        self.backup_file_path = backup_file_path
        self.restore_dump_file = os.path.basename(backup_file_path[:-6] + "sql")
        self.restore_dump_file_path = os.path.join(self.tmp_dir, self.restore_dump_file)
        self.restore_tar_file = os.path.basename(backup_file_path[:-3])
        self.restore_tar_file_path = os.path.join(self.tmp_dir, self.restore_tar_file)

        restore_functions = [
            self.__untar_backup,
            self.__enable_maintenance_mode,
            self.__import_db,
            self.__import_config,
            self.__disable_maintenance_mode,
            self.__delete_tmp_dir
        ]

        if self.__create_tmp_dir():
            try:
                for fn in restore_functions:
                    if not fn():
                        return False
                return True
            except:
                self.exceptions.update({'restore': traceback.format_exc()})
                return False
        else:
            _print(F"{Fore.RED}Could not create temporary folder. Restore aborted.{Style.RESET_ALL}")
            return False

    def upgrade(self):

        upgrade_functions = [
            self.__enable_maintenance_mode,
            self.__restart_containers,
            self.__disable_maintenance_mode,
        ]

        if self.__pull_images():
            for fn in upgrade_functions:
                if not fn():
                    return 0
        else:
            return 2
        return 1

    @staticmethod
    def instantiate_containers(data: dict) -> dict:
        containers = {}
        for name, values in data['nextcloud_containers'].items():
            containers.update({name: Container(
                name,
                values['mysql_root_password'],
                values['app_container'],
                values['db_container'],
                values['backup_dir'],
                values['docker_compose_file_path'],
                values['number_of_backups'])
            })
        return containers


class Log:

    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.__log_file = 'nextcloud_docker_scripts.log'
        self.__log_file_path = os.path.join(self.log_dir, self.__log_file)
        self.exceptions = {}

    # Create log entry
    def log(self, message):
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = dt + "  ;  " + message + "\n"
        if self.__check_log_dir():
            try:
                with open(self.__log_file_path, "a+") as log_file:
                    log_file.writelines(entry)
                return True
            except:
                _print(F"{Fore.RED}Could not write to log file: {self.__log_file}{Style.RESET_ALL}")
                self.exceptions.update({'log': traceback.format_exc()})
                return False

    # Try to create log directory if it does not yet exists
    def __check_log_dir(self) -> bool:
        if not os.path.isdir(self.log_dir):
            try:
                os.makedirs(self.log_dir)
                return True
            except:
                _print(F"{Fore.RED}Could not create log directory under: {self.log_dir}{Style.RESET_ALL}")
                self.exceptions.update({'get_log_file': traceback.format_exc()})
                return False
        else:
            return True


if __name__ == '__main__':
    pass
