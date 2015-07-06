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

### Google Drive Configuration

You should share the folder where youre uploading the files to your deb user:
You go to API & Auth tab and click on Credentials. From here, click on button with label Create new Client ID and select service account and click on Create Client ID button , after created service account, you download the private key to somewhere such as I put at path "configs/74214843aee8aba9f11b7825e0a22ef1f06533b7-privatekey.p12" and copy service account id such as "xxxxx-5kfab22qfu82uub2887gi0c9e6eincmu@developer.gserviceaccount.com"
You come back to your google drive drive.google.com and create share folder( you create an empty folder and right click on the folder and share to user xxxxx-5kfab22qfu82uub2887gi0c9e6eincmu@developer.gserviceaccount.com ) and copy the folder id ( You can look at the url after visit folder and the id is there ) and in my case the backup folder url is https://drive.google.com/#folders/0B0XTTQmH9aXreFdxS0txVU5Xb1U so that the id is 0B0XTTQmH9aXreFdxS0txVU5Xb1U
Create config file( such as config_file.json ) and input into this file with json format such as

{
    "service_account":"xxxxx-5kfab22qfu82uub2887gi0c9e6eincmu@developer.gserviceaccount.com",
    "private_key12_path":"configs/74214843aee8aba9f11b7825e0a22ef1f06533b7-privatekey.p12",
    "backup_folder_id":"0B0XTTQmH9aXreFdxS0txVU5Xb1U",
    "description" : "Description for backup file",
    "max_file_in_folder": 5
}


### Config Postgres For trust (only one user in the system)

1.You need to edit the pg_hba.conf file and edit the row as

# "local" is for Unix domain socket connections only
local   all             all                                     trust

### MySQL

We may need to add a user to a database to avoid user root. To do this:

       $  mysql -h localhost  -u root -p
       mysql> grant CREATE,INSERT,DELETE,UPDATE,SELECT on testingdb.* to ignacio@localhost;
       mysql> set password for ignacio@localhost = password('mysecretpassword');
       mysql> flush privileges;
       mysql> exit;

