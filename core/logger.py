import logging
import logging.handlers
import os
import sys

def _get_log_path() -> str:
    """Obtiene la ruta del log compatible con PyInstaller frozen."""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        # Si estamos en core/, subimos un nivel para que esté en la raíz del proyecto
        base_path = os.path.dirname(base_path)
    return os.path.join(base_path, "log_parque.txt")

def setup_logger() -> logging.Logger:
    """Configura el logger singleton con rotación de archivos."""
    logger = logging.getLogger("scienceworld")
    logger.setLevel(logging.DEBUG)

    # Evitar duplicidad si ya tiene handlers
    if not logger.handlers:
        log_file = _get_log_path()
        
        # RotatingFileHandler: 5MB, 3 backups, UTF-8
        fh = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=5_242_880, 
            backupCount=3, 
            encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(module)-20s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

# Instancia singleton para importar en todo el proyecto
log = setup_logger()