# -*- coding: utf-8 -*-
# Basicos de OS
import sys
import logging
import json

from classes import Notificador
from classes import PostgressDriveBackup
from classes import MySqlDriveBackup
from config import LOGGER_FORMAT, LOG_FILENAME
from config import MAIL_ERROR_SUBJECT
from config import MAIL_SUCCESS_SUBJECT


if __name__ == '__main__':
    logging.basicConfig(
        filename=LOG_FILENAME, level=logging.INFO, format=LOGGER_FORMAT)
    logger = logging.getLogger('BackupScript')
    config = sys.argv[1]
    config_file = open(config, 'r')
    config_data = json.loads(config_file.read())
    db_tipo = config_data['db_tipo']
    db_name = config_data['db_nombre']
    db_username = config_data['db_usuario']
    db_password = config_data['db_password']
    dump_dir = config_data['path_backup_file']
    google_user = config_data['google_user']
    google_app_passw = config_data['google_app_passw']
    notificador = Notificador(google_user, google_app_passw)
    if db_tipo == 'postgres':
        backup = PostgressDriveBackup(db_name, dump_dir, db_username)
    else db_tipo == 'mysql':
        backup = MySqlDriveBackup(db_name, dump_dir, db_username, db_password)

    # Se genera el archivo primero
    try:
        backup.ejecutar()
    except Exception, e:
        message = "No se pudo generar archivo de backup.\nBase de datos: %s\nError: %s" % (
            db_name, e.message)
        logger.error(message)
        notificador.notificar(MAIL_ERROR_SUBJECT, message)
        notificador.cerrar()
        sys.exit()

    # Despues se sube a la nube
    try:
        backup.subir_archivo()
    except Exception, e:
        message = "Fallo al subir backup a la nube.\nBase de datos: %s\nArchivo: %s\nError: %s" % (
            db_name, backup.file_path, e.message)
        logger.error(message)
        notificador.notificar(MAIL_ERROR_SUBJECT, message)
        notificador.cerrar()
        sys.exit()
    success_msg = "Exito al realizar backup.\nBase de datos: %s\nArchivo: %s" % (
            db_name, backup.file_path)
    logger.info(success_msg)
    notificador.notificar(MAIL_SUCCESS_SUBJECT, success_msg)
    notificador.cerrar()
    logger.info('Backup realizado exitosamente.')
