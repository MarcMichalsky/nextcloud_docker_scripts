# Flags
quiet_mode = False
no_log = False
no_cleanup = False
all_containers = False
no_confirm = False
no_backup = False

# intern Flags
keep_maintenance_mode = False


def set_flags(flags=list):
    global quiet_mode
    global no_log
    global no_cleanup
    global all_containers
    global no_confirm
    global no_backup

    quiet_mode = "--quiet" in flags
    no_log = "--nolog" in flags
    all_containers = "--all" in flags
    no_cleanup = "--nocleanup" in flags
    no_confirm = "--yes" in flags
    no_backup = "--nobackup" in flags


def _print(text=None):
    global quiet_mode
    if not quiet_mode:
        if not text is None:
            print(text)
        else:
            print()
