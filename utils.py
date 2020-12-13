# Flags
quiet_mode = False
no_log = False
no_cleanup = False
all_containers = False
no_confirm = False


def _print(text=None):
    if not quiet_mode:
        if not text is None:
            print(text)
        else:
            print()
