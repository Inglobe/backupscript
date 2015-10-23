# Para script de backup
import os
import mimetypes
import helper
import json
import time
import logging
import subprocess
from datetime import datetime
from operator import itemgetter

# Para notificiar x email
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEImage import MIMEImage
from email.MIMEText import MIMEText

from config import LOGGER_FORMAT, LOG_FILENAME
from config import DRIVE_CONFIG_PATH
from config import MAX_FILES_DUMP_DIR


class IBackup(object):

    """
    Interfaz basica para backups de una base de datos especifica.
    """

    db_name = None
    dump_dir = None
    db_username = None
    db_password = None
    file_path = None

    def ejecutar(self):
        """
        Realiza dicho backup. Se fija que la cantidad de archivos en el
        directorio dumper no superer el numero de archivos maximo especificado
        en el archivo DRIVE_CONFIG_PATH.
        """

    def subir_archivo(self):
        """
        Sube el archivo adonde se desee subir. Chequea que el numero de archivos
        en nube ni en disco local no supere el especificado en archivo DRIVE_CONFIG_PATH.
        """

class Notificador(object):

    """
    Clase para enviar notificaciones por email. Se usa el mismo usuario para emisor
    y receptor.
    """
    server = None
    usuario = None

    def __init__(self, usuario, password):
        """
        Inicia el notificador para una cuenta especifica.
        """
        self.usuario = usuario
        self.server = smtplib.SMTP("smtp.gmail.com:587")
        self.server.starttls()
        self.server.login(self.usuario, password)

    def notificar(self, asunto, mensaje):
        """
        Envia el mensaje por email.
        """
        fromaddr = '%s@gmail.com' % self.usuario
        toaddrs = '%s@gmail.com' % self.usuario
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddrs
        msg['Subject'] = asunto
        msg.attach(MIMEText(mensaje))
        self.server.sendmail(fromaddr, toaddrs, msg.as_string())

    def cerrar(self):
        """
        Cierra el servicio.
        """
        self.server.quit()


class PostgressDriveBackup(IBackup):

    """
    Clase para realizar backups de base de datos Postgress y subir a Google
    drive.
    """

    def __init__(self, db_name, dump_dir, db_username):
        """
        Configura parametros para la instancia.
        """
        # Logger
        logging.basicConfig(
            filename=LOG_FILENAME, level=logging.INFO, format=LOGGER_FORMAT)
        self.logger = logging.getLogger('Postgres Drive Backup')
        # Base de datos
        self.db_name = db_name
        self.dump_dir = dump_dir
        try:
            os.stat(self.dump_dir)
        except:
            os.mkdir(self.dump_dir)
        self.db_username = db_username

    def ejecutar(self):
        """
        Este es el metodo que se utiliza para realizar dicho backup para
        una base de datos especifica.
        @param db_name: nombre de base de datos.
        """
        try:
            dumper = " -U %s -Z 9 -F c %s > %s "
            # Usamos una fecha en el nombre para identificar rapidamente cuando
            # se hizo
            date = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            temp_file_name = '%s--%s.sql' % (date, self.db_name)
            temp_file_path = os.path.join(self.dump_dir, temp_file_name)
            command = 'docker exec db-odoo80 pg_dump' + \
                dumper % (self.db_username, self.db_name, temp_file_path)
            subprocess.call(command, shell=True)
            subprocess.call('gzip -f ' + temp_file_path, shell=True)
            self.bkp_file = temp_file_name + '.gz'
            self.file_path = temp_file_path + '.gz'
            self.logger.info("Backup de base de datos %s creado en %s." %
                        (self.bkp_file, self.file_path))
        except Exception, e:
            self.logger.error('No se pudo crear el backup %s' % (self.db_name))
            raise Exception('No se pudo crear el backup %s' % (self.db_name))

        # Chequeamos cantidad de archivos en disco
        try:
            config_file = open(DRIVE_CONFIG_PATH, 'r')
            config = json.loads(config_file.read())
        except Exception, e:
            self.logger.error('Error al abrir el archivo drive_config.json.')
            raise Exception('Error al abrir el archivo drive_config.json.')

        files = os.listdir(self.dump_dir)
        if len(files) > MAX_FILES_DUMP_DIR:
            fileData = {}
            for fname in files:
                path = self.dump_dir + '/' + fname
                fileData[path] = os.stat(path).st_mtime
            sortedFiles = sorted(fileData.items(), key=itemgetter(1))
            os.remove(sortedFiles[0][0])

    def subir_archivo(self):
        """
        Sube el archivo adonde se desee subir siempre y cuando sea a una cuenta
        de Google Drive.
        """
        try:
            config_file = open(DRIVE_CONFIG_PATH, 'r')
            config = json.loads(config_file.read())
        except Exception, e:
            self.logger.error('Error al abrir el archivo drive_config.json.')
            raise Exception('Error al abrir el archivo drive_config.json.')
        try:
            drive_service = helper.createDriveService(config)
        except Exception, e:
            self.logger.error(
                'No se pudo conectar a la cuenta de Google Drive.')
            raise Exception('No se pudo conectar a la cuenta de Google Drive.')
        self.logger.info('Autentificacion a Google Driver exitosa')
        mimetype_upload_file = mimetypes.guess_type(self.file_path)
        upload_file_mimetype = mimetype_upload_file[0]
        self.logger.info(
            'Subiendo archivo backup %s a Google Drive...' % self.db_name)
        try:
            file_result = helper.insert_file(
                drive_service, config, self.file_path, self.bkp_file, upload_file_mimetype)
        except Exception, e:
            self.logger.info(
                'Ha ocurrido un error al subir el archivo a la cuenta de Google Drive')
            raise Exception('Ha ocurrido un error al subir el archivo a la cuenta de Google Drive')

        # Si excedemos cantidad de archivos a subir, borramos anteriores
        children_files = helper.files_in_folder( drive_service, config['backup_folder_id'] )
        if len( children_files ) > config['max_file_in_folder']:
            #Remove old backup file
            number_delete_file = len(children_files) - config['max_file_in_folder']
            count = 0
            index_delete_file = len(children_files) -1

            while count < number_delete_file:
                children_id = children_files[index_delete_file]['id']
                self.logger.info( "Removing old file with id " + children_id)
                helper.remove_file_from_folder( drive_service, config['backup_folder_id'], children_id )
                count +=1
                index_delete_file -=1


class MySqlDriveBackup(IBackup):

    """
    Clase para realizar backups de base de datos Postgress y subir a Google
    drive.
    """

    def __init__(self, db_name, dump_dir, db_username, db_password):
        """
        Configura parametros para la instancia.
        """
        # Logger
        logging.basicConfig(
            filename=LOG_FILENAME, level=logging.INFO, format=LOGGER_FORMAT)
        self.logger = logging.getLogger('Postgres Drive Backup')
        # Base de datos
        self.db_name = db_name
        self.dump_dir = dump_dir
        try:
            os.stat(self.dump_dir)
        except:
            os.mkdir(self.dump_dir)
        self.db_username = db_username
        self.db_password = db_password

    def ejecutar(self):
        """
        Este es el metodo que se utiliza para realizar dicho backup para
        una base de datos especifica.
        @param db_name: nombre de base de datos.
        """
        try:
            dumper = " -U %s -p %s %s "
            dumper = " --single-transaction -u %s -p%s %s "
            # Usamos una fecha en el nombre para identificar rapidamente cuando
            # se hizo
            date = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            temp_file_name = '%s--%s.sql' % (date, self.db_name)
            temp_file_path = os.path.join(self.dump_dir, temp_file_name)
            command = 'mysqldump' + \
                dumper % (self.db_username, self.db_password, self.db_name) + \
                '> ' + temp_file_path
            subprocess.call(command, shell=True)
            subprocess.call('gzip -f ' + temp_file_path, shell=True)
            self.bkp_file = temp_file_name + '.gz'
            self.file_path = temp_file_path + '.gz'
            self.logger.info("Backup de base de datos %s creado en %s." %
                        (self.bkp_file, self.file_path))
        except Exception, e:
            self.logger.error('No se pudo crear el backup %s' % (self.db_name))
            raise Exception('No se pudo crear el backup %s' % (self.db_name))

        # Chequeamos cantidad de archivos en disco
        try:
            config_file = open(DRIVE_CONFIG_PATH, 'r')
            config = json.loads(config_file.read())
        except Exception, e:
            self.logger.error('Error al abrir el archivo drive_config.json.')
            raise Exception('Error al abrir el archivo drive_config.json.')

        files = os.listdir(self.dump_dir)
        if len(files) > MAX_FILES_DUMP_DIR:
            fileData = {}
            for fname in files:
                path = self.dump_dir + '/' + fname
                fileData[path] = os.stat(path).st_mtime
            sortedFiles = sorted(fileData.items(), key=itemgetter(1))
            os.remove(sortedFiles[0][0])

    def subir_archivo(self):
        """
        Sube el archivo adonde se desee subir siempre y cuando sea a una cuenta
        de Google Drive.
        """
        try:
            config_file = open(DRIVE_CONFIG_PATH, 'r')
            config = json.loads(config_file.read())
        except Exception, e:
            self.logger.error('Error al abrir el archivo drive_config.json.')
            raise Exception('Error al abrir el archivo drive_config.json.')
        try:
            drive_service = helper.createDriveService(config)
        except Exception, e:
            self.logger.error(
                'No se pudo conectar a la cuenta de Google Drive.')
            raise Exception('No se pudo conectar a la cuenta de Google Drive.')
        self.logger.info('Autentificacion a Google Driver exitosa')
        mimetype_upload_file = mimetypes.guess_type(self.file_path)
        upload_file_mimetype = mimetype_upload_file[0]
        self.logger.info(
            'Subiendo archivo backup %s a Google Drive...' % self.db_name)
        try:
            file_result = helper.insert_file(
                drive_service, config, self.file_path, self.bkp_file, upload_file_mimetype)
        except Exception, e:
            self.logger.info(
                'Ha ocurrido un error al subir el archivo a la cuenta de Google Drive')
            raise Exception('Ha ocurrido un error al subir el archivo a la cuenta de Google Drive')

        # Si excedemos cantidad de archivos a subir, borramos anteriores
        children_files = helper.files_in_folder( drive_service, config['backup_folder_id'] )
        if len( children_files ) > config['max_file_in_folder']:
            #Remove old backup file
            number_delete_file = len(children_files) - config['max_file_in_folder']
            count = 0
            index_delete_file = len(children_files) -1

            while count < number_delete_file:
                children_id = children_files[index_delete_file]['id']
                self.logger.info( "Removing old file with id " + children_id)
                helper.remove_file_from_folder( drive_service, config['backup_folder_id'], children_id )
                count +=1
                index_delete_file -=1
