# Deployment

## First deployment on a new server (such as seduce1)

Install dependencies on the server:

```shell
apt install -y git python3 python3-pip redis-server
pip3 install supervisord
```

and launch supervisord

```
supervisord
```

You have now to install influxdb. You may follow instructions on their website [instructions](https://docs.influxdata.com/influxdb/v1.8/introduction/install/).
For sake of simplicity, here are the instructions for ubuntu:
```shell
# Add the package repository of influxdb
wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
source /etc/lsb-release
echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list

# Install influxdb
sudo apt-get update && sudo apt-get install influxdb
sudo service influxdb start
```

You have to disable redis and influx as service, as they will be managed by influxdb:

```shell
systemctl disable redis-server
systemctl disable influxdb
```

Now, clone the github repository:

```shell
git clone git@github.com:SeduceProject/seduceboard.git
```

and copy the template of the seduce configuration from the project folder to `/etc/seduce.conf`:
```shell
cp conf/seduce/seduce.conf.example /etc/seduce.conf
```

and copy the template of the supervisord configuration from the project folder to `/etc/supervisord.conf`:
```shell
cp conf/seduce/supervisord.conf.example /etc/supervisord.conf
```

Now we need to make supervisord aware of the services composing the SeDuCe dashboard:

```shell
supervisorctl reread # Supervisord will read '/etc/supervisord.conf' and be aware of any changes made to this file
supervisorctl update all # Update the configuration file of all services
supervisorctl restart all # Ensure all services are running
```

You can check that all services are running via this command:

```shell
supervisorctl status all
```

which should results in:

```shell
root@seduce1:~# supervisorctl status all
api                              RUNNING   pid 235022, uptime 119 days, 15:29:10
celery_beat                      RUNNING   pid 13338, uptime 119 days, 7:54:07
celery_worker                    RUNNING   pid 33534, uptime 116 days, 21:46:49
frontend                         RUNNING   pid 72984, uptime 114 days, 0:38:09
influxdb                         RUNNING   pid 235030, uptime 119 days, 15:29:10
modbus_crawler_entech            RUNNING   pid 178870, uptime 109 days, 16:39:44
modbus_crawler_inrow             RUNNING   pid 180327, uptime 109 days, 16:39:37
pdu_crawler_z1_10                RUNNING   pid 235027, uptime 119 days, 15:29:10
pdu_crawler_z1_11                RUNNING   pid 235026, uptime 119 days, 15:29:10
pdu_crawler_z1_20                RUNNING   pid 235036, uptime 119 days, 15:29:10
pdu_crawler_z1_21                RUNNING   pid 235037, uptime 119 days, 15:29:10
pdu_crawler_z1_40                RUNNING   pid 235032, uptime 119 days, 15:29:10
pdu_crawler_z1_41                RUNNING   pid 235033, uptime 119 days, 15:29:10
pdu_crawler_z1_50                RUNNING   pid 235024, uptime 119 days, 15:29:10
pdu_crawler_z1_51                RUNNING   pid 235023, uptime 119 days, 15:29:10
poe_crawler                      RUNNING   pid 235028, uptime 119 days, 15:29:10
redis                            RUNNING   pid 157200, uptime 119 days, 9:24:33
sensors_crawler                  RUNNING   pid 235031, uptime 119 days, 15:29:10
temperature_registerer           RUNNING   pid 235019, uptime 119 days, 15:29:10
```

# Deployment of an update

Move to the folder of the SeDuCe project that you cloned in Section `First deployment on a new server (such as seduce1)`. 

First, identify which services are concerned by the update. For each service `[service]`, stop the service with the following command:
```shell
supervisorctl stop [service]
```

Then ensure that the last backup of SeDuCe data is recent with the following command:
```shell
borg list /backup/
```

If this is not the case, create a new backup as explained in the `Backup` Section.

!!! warning
    The step of checking if a recent backup exists is very important. If you make an error you will have to either correct it manually or either restore a previous version. In both cases, it means losing several hours of work/data.

Now, update the source of the SeDuCe dashboard. Go in the clone folder, and run the following command:
```shell
git pull
``` 

Once the update of the code is made, for each service `[service]` that have been stopped, restart the service with the following command:
```shell
supervisorctl restart [service]
```

Now checks that everything is OK:
```shell
supervisorctl status all
```

And browse in the dashboard to ensure everything is OK.

## Backup

### How it works?

On the server `seduce1`, we have configured the [borg](https://borgbackup.readthedocs.io/en/stable/) backup system to
backup periodically serveral files and folder of the SeDuCe dashboard.

You can check that borg is running and performing regular backups (roughly every 30 minutes) thanks to this line in `/etc/crontab`:
```shell
*/30 *   * * *   root    /bin/bash -c "/etc/cron.hourly/borg-backup"
```

The referenced `/etc/cron.hourly/borg-backup` script contains the following instructions:
```shell
#!/bin/bash

/root/.pyenv/versions/3.7.3/bin/borg create --stats -v --compression zlib,9 /backup::{hostname}_{now:%d.%m.%Y_%T} /root/influx /root/seduceboard/test.db /var/lib/mysql
backup_exit=$?

/root/.pyenv/versions/3.7.3/bin/borg prune -v --list --keep-within=10d --keep-weekly=4 --keep-monthly=-1 /backup/

exit ${backup_exit}
```

This script does the following:

 - create a backup of the following paths
     - `/root/influx`
     - `/root/seduceboard/test.db`
     - `/var/lib/mysql`

you can check the backup with the following command:

```shell
borg list /backup/
```

borg have been configured to do its backups in the `/backup/` folder of `seduce1` server.

### Create a new manual backup

The simplest way is to launch the script that runs periodically:
```shell
bash /etc/cron.hourly/borg-backup
```

### Restore a backup

First create a folder in which the backup will be mounted:

```shell
mkdir /root/borg_backup_mount
```

Identify which backup you want to restore:
```shell
borg list /backup/
```

In this example, I will restore `seduce1_01.07.2020_11:30:01`. To ask borg to restore this backup in the previously created folder:

```shell
cd /root/borg_backup_mount
borg extract --progress /backup::seduce1_01.07.2020_11:30:01
```

In our case, `/root/borg_backup_mount` will contain the following folders

```shell
.
|-- root
|   |-- influx
|   `-- seduceboard
|       `-- test.db
`-- var
    `-- lib
        `-- mysql
            |
           [...]
```

We can notice the following:

- `/root/borg_backup_mount/root/influx` is the backup of the `/root/influx` folder which contains a subfolder `.influx` which contains the real influxdb data. To restore influx, you may stop the influx service, move the `/root/influx` in an other path (such as `/root/influx_save`)' and restore `/root/borg_backup_moun/root/influx` to `root/influx`.
- `/root/borg_backup_mount/seduceboard/test.db` is the backup of the relational databse used by the dashboard.
- `/root/borg_backup_mount/var/lib/mysql` is a legacy database used for [piseduce](pi.seduce.fr/). It may be useful to keep this folder backed-up if later the relational database of the SeDuCe dashboar uses mariadb.

After restoring the data, you may restart the stopped services, and delete the folder `/root/borg_backup_mount`