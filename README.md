# BACKUP SCRIPT

### Requires
pip install --upgrade google-api-python-client
sudo apt-get install libffi-dev
sudo apt-get install python-dev
sudo apt-get install python-openssl
pip install PyOpenSSL

helper.py from https://github.com/bachvtuan/Backup-To-Google-Drive

# You'll need Google app password: 

Read https://support.google.com/accounts/answer/185833

### Config Postgres For trust (only one user in the system)

1.You need to edit the pg_hba.conf file and edit the row as
        local   all             postgres                       trust
