import traceback

from apis.google.drives.file import GoogleDriveFile
from cache.clear import clear_cache_and_conflicts
from correspondence.self.functions import (
    new_email_to_self,
    send_email_to_self
)
from dates import dates
from default.google.drive.functions import (
    get_klt_management_directory_on_drive,
    upload_local_file_to_drive
)
from default.settings import DATABASE_NAME, DATABASE_PATH
from interfaces.interface import Interface


LOAD_START = dates.now()


def update(func):
    """
    Decorator for update functions to handle logging and error handling.
    
    Wraps functions to provide standardized logging at start and end,
    runtime tracking, and error handling with email notifications.
    
    Args:
        func: The function to wrap.
        
    Returns:
        The wrapped function.
    """
    def wrapper(*args, **kwargs):
        interface = Interface()
        interface.divide()
        sections = interface.subsections()
        sections.log(f'NOW RUNNING: {func.__name__}')
        start = dates.now()
     
        try:
            run = func(*args, **kwargs)
            sections.log(run)    
        except Exception as e:
            user, message = new_email_to_self(subject=f'ERRORS IN {func.__name__}')
            message.body.paragraph(traceback.format_exc(chain=False))
            send_email_to_self(user, message)
            _log_exception(sections)
     
        end = dates.now()
        sections.log(f'UPDATE runtime: {end - start}')
        sections.log(f'TOTAL runtime: {end - LOAD_START}')
    return wrapper


def pull_database(func):
    """
    Decorator for functions that need database access.
    
    Pulls the latest database from cloud storage before executing the function,
    then uploads the potentially modified database back to the cloud after execution.
    
    Args:
        func: The function to wrap.
        
    Returns:
        The wrapped function.
    """
    def wrapper(*args, **kwargs):
        pullDatabase = kwargs.get('pullDatabase', True)
        if not pullDatabase:
            return func(*args, **kwargs)
        
        interface = Interface()
        interface.divide()
        sections = interface.subsections()
        sections.log('Clearing cache and pulling database from CLOUD...')
        
        clear_cache_and_conflicts()
        driveFile = _get_database_file_on_drive()
        driveFile.download()
        try: 
            func(*args, **kwargs)
        except Exception:
            _log_exception(sections)
        
        sections.smallDivide()  
        sections.log('Clearing cache and storing database on CLOUD...')
        upload_local_file_to_drive(driveFile)
        clear_cache_and_conflicts()
        interface.divide()

    return wrapper


def _get_database_file_on_drive() -> GoogleDriveFile:
    """
    Get the database file from Google Drive.
    
    Locates the database file in the management directory on Google Drive.
    
    Returns:
        The database file on Google Drive.
        
    Raises:
        FileNotFoundError: If the database file is not found.
    """
    driveDirectory = get_klt_management_directory_on_drive('Database')
    driveFile = driveDirectory.file(name=DATABASE_NAME)
    if not driveFile.exists:
        raise FileNotFoundError(
            f'Database file not found in Drive Directory {driveDirectory.id}.')
    driveFile.path = DATABASE_PATH
    return driveFile


def _log_exception(sections: Interface) -> None:
    """
    Log an exception to the console.
    
    Args:
        sections: The interface subsections object used for logging.
        
    Returns:
        None
    """
    sections.log('ERROR: Could not complete.')
    sections.divide()
    traceback.print_exc(chain=False)
    sections.divide()