import datetime
import os
import stat
import tarfile
from Models.NextcloudBackupException import NextcloudBackupException


class Container:

    def __init__(self, name, password, backup_folder, compose_file_path) -> None:
        self.__datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        self.name = name
        self.__password = password
        self.backup_folder = backup_folder
        self.compose_file_path = compose_file_path
        self.__dump_file = self.name + '_' + self.__datetime + '.sql'
        self.__dump_file_path = os.path.join(self.backup_folder, self.__dump_file)
        self.__tar_file = self.name + '_' + self.__datetime + 'tar.gz'
        self.__tar_file_path = os.path.join(self.backup_folder, self.__tar_file)

    def __str__(self) -> str:
        return F"name: {self.name}\npassword: {self.__password}\ncompose_file_path: {self.compose_file_path}"

    # Create backup folder if it does not yet exist
    def create_backup_dir(self):
        if not os.path.isfile(self.backup_folder):
            try:
                os.makedirs(self.backup_folder)
            except OSError as e:
                raise OSError(e)
            return True
        else:
            return False

    # Dump database
    def __dump_db(self) -> bool:
        try:
            os.system(F"docker exec {self.name} mysqldump --password={self.__password} --all-databases > "
                      F"{self.__dump_file}")
            return os.path.isfile(self.__dump_file)
        except Exception as e:
            raise Exception(e)

    # Tar config and settings folder within container and copy it into backup folder
    def __export_config(self) -> bool:
        try:
            os.system(F"docker exec {self.name} tar -czf config_settings.tar config settings")
            os.system(F"docker cp {self.name}:/var/www/html/config_settings.tar {self.__tar_file_path}")
            os.system(F"docker exec {self.name} rm config_settings.tar")
            return os.path.isfile(self.__tar_file_path)
        except Exception as e:
            raise NextcloudBackupException(e)

    # Tar database with config and settings
    def __tar_db(self) -> bool:
        try:
            with tarfile.open(self.__tar_file_path, 'w:gz') as tarball:
                tarball.add(self.__dump_file_path, arcname=self.__dump_file)
            return tarball.gettarinfo(self.__dump_file).isfile()
        except Exception as e:
            raise NextcloudBackupException(e)

    # Set secure file permissions
    def __set_file_permissions(self) -> bool:
        try:
            os.chmod(self.__tar_file_path, stat.S_IREAD)
            return oct(os.stat(self.__tar_file_path).st_mode)[-3:] == 600
        except Exception as e:
            raise NextcloudBackupException(e)

    # Create backup
    def create_backup(self) -> dict:
        try:
            return {"database dump": self.__dump_db(),
                    "export config": self.__export_config(),
                    "include db in backup": self.__tar_db(),
                    "set secure backup file permissions": self.__set_file_permissions()}
        except NextcloudBackupException as e:
            raise NextcloudBackupException(e)

    @staticmethod
    def deserialize_containers(data: dict) -> list:
        containers = []
        for name, values in data['nextcloud_containers'].items():
            containers.append(Container(
                name,
                values['mysql_password'],
                values['backup_folder'],
                values['compose_file_path'])
            )
        return containers
