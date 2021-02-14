# Nextcloud Docker Scripts

I'd like to share my collection of scripts to back up, upgrade and restore Nextcloud Docker installations. They come 
handy especially if you are managing multiple Nextcloud installations on your server.

I am using the [Docker Homelab](https://github.com/cbirkenbeul/docker-homelab) for my Nextcloud instances.

**NOTE:**
**This scripts will only work if you...**
- have installed your Nextcloud within a Docker container
- are using a container for the Nextcloud app and a separate container for the MySQL database  
- are using a docker-compose file to bring up both containers

**This scripts will only backup or restore the database and the config files of your Nextcloud installation!**

## Usage

### Install requirements
```bash
pip3 install -r requirements.txt
```

### Configuration
1. Copy the `example_configuration.yml`.
```bash
cp example_configuration.yml configuration.yml
```

2. Adjust the `configuration.yml` with an editor of your choice.

### Back up a Nextcloud installation

The `backup.py` script will create a **backup of the database and the configuration** of your Nextcloud installations. 
You can adjust the backup directory and the maximum number of backups in the `configuration.yml`.

```bash
python3 backup.py
```
or without user prompt
```bash
python3 backup.py cloud1 cloud2
```

### Restore a Nextcloud installation
The `restor.py` script will **restore the database and the configuration** of your Nextcloud installations.

```bash
python3 restore.py
```
or without user prompt
```bash
python3 restore.py cloud1 cloud2
```

### Upgrade a Nextcloud installation
The `upgrade.py` script will first back up and then try to upgrade your Nextcloud installations.

```bash
python3 upgrade.py
```
or without user prompt
```bash
python3 upgrade.py cloud1 cloud2
```

### Flags
| Flag | function                                                        |
|------|-----------------------------------------------------------------|
|--yes|won't ask for confirmation                                        |
|--all|will treat all Nextcloud installations defined in the `config.yml`|
|--quiet|the script will produce no output on terminal                   |
|--nolog|no logs will be written                                         |
|--nocleanup|there will be no cleanup of the backup directory afterwards |
|--nobackup|no backup will be made before upgrade                        |


## Known issues
- Sometimes the maintenance mode is not getting disabled properly after upgrades. 
  A simple `docker exec --user www-data <app-cotainer> php occ maintenance:mode --off` does the trick.
