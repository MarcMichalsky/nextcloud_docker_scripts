
class NextcloudBackupException(Exception):
    def __init__(self, message):
        self.message = message


    def __write_to_log(self):
        pass
