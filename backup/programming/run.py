from apis.google.drives.directory import GoogleDriveDirectory
from backup.functions import backup_folders_and_files
from default.directory.functions import get_KLT_directory
from default.google.drive.functions import get_todays_backup_directory_on_drive
from default.update.wrapper import update
from directories.directory import Directory


@update
def back_up_programming_files() -> str:
    """
    Back up programming files to Google Drive.
    
    This function retrieves the local code directory and creates a backup
    on Google Drive, excluding files and directories specified in the ignore list.
    
    Returns:
        A message indicating successful backup completion.
    """
    localDirectory: Directory = get_KLT_directory()
    driveDirectory: GoogleDriveDirectory = get_backup_directory()
    backup_folders_and_files(localDirectory.contents, driveDirectory, ignored())
    return 'Successfully backed up programming files!'


def get_backup_directory() -> GoogleDriveDirectory:
    """
    Get the backup directory for programming files on Google Drive.
    
    Retrieves today's backup directory and creates a subdirectory for programming
    files if it doesn't already exist.
    
    Returns:
        A GoogleDriveDirectory object pointing to the programming files backup location.
    """
    todaysDirectory: GoogleDriveDirectory = get_todays_backup_directory_on_drive()
    programming: GoogleDriveDirectory = todaysDirectory.subdirectory(name='Programming Files')
    if not programming.exists:
        programming.create()
    return programming


def ignored() -> tuple[str, ...]:
    """
    Get a list of file and folder patterns to ignore during backup.
    
    Returns:
        A tuple of strings representing file/directory patterns to exclude from backup.
    """
    return (
        '~',
        'cache',
        'update-log',
        '__pycache__',
        'cleaning-schedules',
        'downloaded_files',
        '__init__.py',
        '.log',
        '.venv',
        '.vscode',
        '.pdf',
        '.docx',
        '.doc',
        '.txt',
        '.csv',
        '.bak',
        '.zip',
        '.tmp',
        '.log.old',
        '.json',
        '.tar',
        '.gz',
        '.rar',
        '.exe',
        '.bat',
    )