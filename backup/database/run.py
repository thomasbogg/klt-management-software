import datetime

from apis.google.drives.directory import GoogleDriveDirectory
from apis.google.drives.file import GoogleDriveFile
from default.database.functions import last_database_update
from default.dates import dates
from default.directory.functions import get_KLT_directory
from default.google.drive.functions import get_todays_backup_directory_on_drive
from default.settings import DATABASE_NAME, DATABASE_PATH
from default.update.wrapper import update
from directories.directory import Directory
from directories.file import File
from utils import log, sublog


@update
def back_up_database() -> str:
    """
    Back up the database to Google Drive.
    
    Retrieves the local database file, resolves any conflicts between multiple files,
    and uploads the most recent version to Google Drive with a timestamp.
    
    Returns:
        A message indicating the success of the backup operation.
    """
    localFiles: list[File] = get_database_named_files()
    if len(localFiles) > 1:         
        localFile, conflicts = resolve_conflicting_database_files(localFiles)
       
        for conflictingFile in conflicts:
            if 'journal' not in conflictingFile.name.lower():
                conflictingFile.delete() 
      
        localFile.name = DATABASE_NAME
        localFile.rename()
    else:
        localFile = localFiles[0]

    timeStr: str = dates.prettyHour() + '.00'
    uploadName: str = f'{DATABASE_NAME} - {timeStr}'
    driveDirectory: GoogleDriveDirectory = get_database_backup_directory_on_drive()
    driveFile: GoogleDriveFile = driveDirectory.file(name=uploadName)
    if not driveFile.exists:
        driveFile.path = DATABASE_PATH
        driveFile.mimeType = 'application/vnd.sqlite3'
        driveFile.upload()

    return 'Successfully backed up database!'


@update
def retrieve_database_backup(time: datetime.time) -> str:
    """
    Retrieve a database backup from Google Drive.
    
    Args:
        time: The time of the backup to retrieve.
        
    Returns:
        A message indicating the success or failure of the retrieval operation.
    """
    driveDirectory: GoogleDriveDirectory = get_database_backup_directory_on_drive()
    timeStr: str = dates.prettyHour(time) + '.00'
    driveFile: GoogleDriveFile = driveDirectory.file(name=f'Database - {timeStr}')
    if not driveFile.exists:
        return f'Database backup not found for given time {timeStr}!'
   
    driveFile.path = DATABASE_PATH
    driveFile.download()
    return 'Successfully downloaded database backup!'


def get_database_named_files() -> list[File]:
    """
    Get the database files from the local directory.
    
    Searches the local directory for files with 'klt' in their name
    and a '.db' extension.
    
    Returns:
        A list of File objects representing database files.
    """
    localDirectoryPath = '/'.join(DATABASE_PATH.split('/')[:-1])
    localDirectory: Directory = get_KLT_directory(localPath=localDirectoryPath)
    databaseOnly = lambda x: 'klt' in x.name.lower() and x.extension == '.db'
    return list(filter(databaseOnly, localDirectory.files))
    

def get_database_backup_directory_on_drive() -> GoogleDriveDirectory:
    """
    Get the database backup directory on Google Drive.
    
    Creates the directory if it doesn't exist.
    
    Returns:
        A GoogleDriveDirectory object for the database backup directory.
    """
    driveDirectory: GoogleDriveDirectory = get_todays_backup_directory_on_drive()
    driveSubdirectory: GoogleDriveDirectory = driveDirectory.subdirectory(name='Database')
    if not driveSubdirectory.exists:
        driveSubdirectory.create()
    return driveSubdirectory
                

def resolve_conflicting_database_files(
        localFiles: list[File], 
        lastUpdatedDatabase: File = None, 
        latestDatabaseUpdate: str = None
) -> tuple[File, list[File]]:
    """
    Resolve conflicting database files by finding the most recently updated file.
    
    Args:
        localFiles: The list of local database files.
        lastUpdatedDatabase: The last updated database file (default is None).
        latestDatabaseUpdate: The latest database update date (default is None).
        
    Returns:
        A tuple containing the most recently updated database file and a list of 
        conflicting files.
    """
    log(f'Found conflicting database local files: {len(localFiles)}')
    
    for localFile in localFiles:
        try:
            lastUpdate: str = last_database_update(localFile.path)
            sublog(f'localFile = {localFile.name}, last updated: {lastUpdate}')
        except Exception as e:
            sublog(f'Error retrieving date time for {localFile.name}: {e}. Will not delete local file.')
            continue

        if not latestDatabaseUpdate or lastUpdate > latestDatabaseUpdate:
            lastUpdatedDatabase = localFile
            latestDatabaseUpdate = lastUpdate

    log(f'Found last updated local file: {lastUpdatedDatabase.name} @ {latestDatabaseUpdate}')
    localFiles.remove(lastUpdatedDatabase)
    return lastUpdatedDatabase, localFiles