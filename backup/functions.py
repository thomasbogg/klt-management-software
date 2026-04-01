from apis.google.drives.directory import GoogleDriveDirectory
from directories.directory import Directory
from directories.file import File


def backup_folders_and_files(
        contents: list[File | Directory], 
        driveDirectory: GoogleDriveDirectory, 
        toIgnore: list[str] = None, 
        repeated: int = 0, 
        maxRepeated: int = 15, 
        checks: int = 0, 
        maxChecks: int = 30) -> None:
    """
    Backup local folders and files to Google Drive.
    
    Recursively traverses the given contents and uploads them to the specified
    Google Drive directory, skipping items that match patterns in toIgnore.
    
    Args:
        contents: List of files and directories to back up.
        driveDirectory: The Google Drive directory to upload to.
        toIgnore: List of patterns to exclude from backup.
        repeated: Counter for repeated directories found (used in recursion).
        maxRepeated: Maximum number of repeated directories before stopping.
        checks: Counter for file existence checks (used in recursion).
        maxChecks: Maximum number of file checks before stopping.
        
    Returns:
        None
    """
    if toIgnore is None:
        toIgnore = []
        
    for item in contents:
        name = item.name
        if _item_should_be_ignored(toIgnore, name):
            continue

        if item.isDirectory:
            driveSubdirectory = driveDirectory.subdirectory(name=name)
            if not driveSubdirectory.exists:
                driveSubdirectory.create()
            else:
                repeated += 1
                if repeated > maxRepeated:
                    return None

            backup_folders_and_files(item.contents, driveSubdirectory, toIgnore)
        else:
            file = driveDirectory.file(name=name)
            if checks != maxChecks:
                if file.exists:
                    repeated += 1
                    if repeated > maxRepeated:
                        return None
                    continue
                checks += 1

            file.path = item.path
            file.mimeType = _guess_mimetype(item.extension)
            file.upload()


def _item_should_be_ignored(toIgnore: list[str], name: str) -> bool:
    """
    Check if the item should be ignored based on its name.
    
    Args:
        toIgnore: List of patterns to check against the name.
        name: The name of the file or directory to check.
        
    Returns:
        True if the item should be ignored, False otherwise.
    """
    for ignore in toIgnore:
        if ignore in name:
            return True
    return False


def _guess_mimetype(extension: str) -> str:
    """
    Guess the MIME type based on the file extension.
    
    Args:
        extension: The file extension including the dot (e.g., '.py').
        
    Returns:
        The MIME type string corresponding to the file extension.
    """
    if extension in ('.py', '.pyw'):
        return 'text/x-python'
    
    if extension in ('.pdf'):
        return 'application/pdf'
    
    if extension in ('.docx'):
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    
    if extension in ('.doc'):
        return 'application/msword'
    
    if extension in ('.txt'):
        return 'text/plain'
    
    if extension in ('.csv'):
        return 'text/csv'
    
    if extension in ('.xlsx'):
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    if extension in ('.xls'):
        return 'application/vnd.ms-excel'
    
    if extension in ('.pptx'):
        return 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    
    if extension in ('.ppt'):
        return 'application/vnd.ms-powerpoint'
    
    if extension in ('.log'):
        return 'text/plain'
    
    # Default mime type for unknown extensions
    return 'application/octet-stream'