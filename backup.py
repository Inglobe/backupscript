# -*- coding: utf-8 -*-
"""
  @reference links
  http://stackoverflow.com/questions/12211859/i-cant-see-the-files-and-folders-created-via-code-in-my-google-drive/12218662#12218662
  http://stackoverflow.com/questions/13736394/which-google-apis-can-be-accessed-with-service-account-authorization
  https://developers.google.com/drive/web/service-accounts
  https://appengine.google.com/permissions?&app_id=s~sixth-trainer-527
  https://developers.google.com/drive/web/service-accounts
  https://developers.google.com/drive/v2/reference/permissions/insert#try-it
  https://developers.google.com/quickstart/
  https://developers.google.com/drive/v2/reference/files/insert
  https://developers.google.com/drive/v2/reference/children/list
  https://developers.google.com/drive/web/search-parameters
"""
# Basicos de OS
import sys
import os
import time
import subprocess
import logging
import logging.handlers
from datetime import datetime

# Para script de backup
import json
import ntpath
import mimetypes
import helper

# Para notificiar x email
import smtplib
from email.mime.text import MIMEText



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

    def notificar(self, mensaje):
        """
        Envia el mensaje por email.
        """
        fromaddr = '%s@gmail.com' % self.usuario
        toaddrs = '%s@gmail.com' % self.usuario
        self.server.sendmail(fromaddr, toaddrs, mensaje)

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
        FORMAT = "%(asctime)-15s %(name)s: %(message)s"
        LOG_FILENAME = './logging_example.out'
        logging.basicConfig(
            filename=LOG_FILENAME, level=logging.INFO, format=FORMAT)
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
            bkp_file = '%s--%s.sql' % (date, self.db_name)
            self.file_path = os.path.join(self.dump_dir, bkp_file)
            command = 'pg_dump' + \
                dumper % (self.db_username, self.file_path, self.db_name)
            subprocess.call(command, shell=True)
            subprocess.call('gzip -f ' + self.file_path, shell=True)
            self.logger.info("Backup de base de datos %s creado en %s." %
                        (self.db_name, self.file_path))
        except Exception, e:
            self.logger.error('No se pudo crear el backup %s' % (self.db_name))
            raise Exception('No se pudo crear el backup %s' % (self.db_name))

    def subir_archivo(self):
        """
        Sube el archivo adonde se desee subir siempre y cuando sea a una cuenta
        de Google Drive.
        """
        try:
            config_file = open('drive_config.json', 'r')
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
                drive_service, config, self.dump_dir, self.file_path, upload_file_mimetype)
        except Exception, e:
            self.logger.info(
                'Ha ocurrido un error al subir el archivo a la cuenta de Google Drive')
            raise Exception('Ha ocurrido un error al subir el archivo a la cuenta de Google Drive')


if __name__ == '__main__':
    config = sys.argv[1]
    # try:
    config_file = open(config, 'r')
    config_data = json.loads(config_file.read())
    # except Exception, e:
        # self.logger.error('Error al abrir el archivo %s.' % config) #no existe este logger
        # TODO: Mandar email por error
    db_tipo = config_data['db_tipo']
    db_name = config_data['db_nombre']
    db_username = config_data['db_usuario']
    db_password = config_data['db_password']
    dump_dir = config_data['path_backup_file']
    notificador = Notificador('', '')
    if db_tipo == 'postgress':
        backup = PostgressDriveBackup(db_name, dump_dir, db_username)
    # TODO: falta para MySql
    try:
        backup.ejecutar()
        backup.subir_archivo()
    except Exception, e:
        notificador.notificar(e.message)
        print 'Fallo el backup'
        print e.message
        notificador.cerrar()
        sys.exit()
    notificador.cerrar()
    print 'Backup realizado exitosamente.'
    # TODO: Mandar email notificando el exito


# Hasta ahora cosas que se instalaron en mi caso:
# pip install --upgrade google-api-python-client
# pip install PyOpenSSL - pidio lo sgte:
    # sudo apt-get install libffi-dev
    # sudo apt-get install python-dev
    # sudo apt-get install python-openssl


# Para google se necesita password de app: https://support.google.com/accounts/answer/185833