# Para script de backup
import os
from datetime import datetime
import mimetypes
import helper
import json
import time
import logging
import subprocess

# Para notificiar x email
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEImage import MIMEImage
from email.MIMEText import MIMEText

from config import LOGGER_FORMAT, LOG_FILENAME
from config import DRIVE_CONFIG_PATH


class IBackup(object):

    """
    Interfaz basica para backups de una base de datos especifica.
    """

    db_name = None
    dump_dir = None
    db_username = None
    file_path = None

    def ejecutar(self):
        """
        Este es el metodo que se utiliza para realizar dicho backup.
        """

    def subir_archivo(self):
        """
        Sube el archivo adonde se desee subir.
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
        self.db_username = db_username

    def ejecutar(self):
        """
        Este es el metodo que se utiliza para realizar dicho backup para
        una base de datos especifica.
        @param db_name: nombre de base de datos.
        """
        try:
            dumper = " -U %s -Z 9 -f %s -F c %s  "
            # Usamos una fecha en el nombre para identificar rapidamente cuando
            # se hizo
            date = datetime.now().strftime('%Y-%m-%d-%H%M')
            temp_file_name = '%s--%s.sql' % (date, self.db_name)
            temp_file_path = os.path.join(self.dump_dir, temp_file_name)
            command = 'pg_dump' + \
                dumper % (self.db_username, temp_file_path, self.db_name)
            subprocess.call(command, shell=True)
            subprocess.call('gzip -f ' + temp_file_path, shell=True)
            self.bkp_file = temp_file_name + '.gz'
            self.file_path = temp_file_path + '.gz'
            self.logger.info("Backup de base de datos %s creado en %s." %
                        (self.bkp_file, self.file_path))
        except Exception, e:
            self.logger.error('No se pudo crear el backup %s' % (self.db_name))
            raise Exception('No se pudo crear el backup %s' % (self.db_name))

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
            import pdb;pdb.set_trace()
            self.logger.info(
                'Ha ocurrido un error al subir el archivo a la cuenta de Google Drive')
            raise Exception('Ha ocurrido un error al subir el archivo a la cuenta de Google Drive')