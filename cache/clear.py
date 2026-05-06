from default.directory.functions import (
    get_KLT_directory,
    get_local_storage_directory,
)
from libraries.directory.directory import Directory
from default.settings import LOCAL

def clear_cache_and_conflicts() -> None:
    """
    Clear cache files and resolve conflicts across the KLT directory.
    
    Removes selenium leftovers, pycache conflicted files, and cached update files.
    
    Returns:
        None
    """
    if not LOCAL:
        return None
    directory: Directory = get_KLT_directory()
    _delete_selenium_base_leftovers(directory)
    _delete_all_pycache_conflicted_files(directory)
    _delete_all_conflicted_credentials_token_files()
    _delete_all_cached_updated_files()


def _delete_selenium_base_leftovers(directory: Directory) -> None:
    """
    Delete downloaded_files folder used by Selenium.
    
    Args:
        directory: The root KLT directory.
        
    Returns:
        None
    """
    directory = get_KLT_directory('downloaded_files')
    if directory.exists:
        directory.delete()
    return None


def _delete_all_pycache_conflicted_files(directory: Directory) -> None:
    """
    Recursively delete conflicted files in all __pycache__ folders.
    
    Args:
        directory: The directory to search within.
        
    Returns:
        None
    """
    for subdirectory in directory.subdirectories:
        if subdirectory.name == '__pycache__': 
            for file in subdirectory.files:
                if 'conflict' in file.name:
                    file.delete()
        else:    
            _delete_all_pycache_conflicted_files(subdirectory)
    return None


def _delete_all_conflicted_credentials_token_files() -> None:
    """
    Recursively delete conflicted files in the Google credentials directory.
    
    Args:
        directory: The directory to search within.
        
    Returns:
        None
    """
    for file in get_KLT_directory('.secrets/google-credentials').files:
        if 'conflict' in file.name:
            file.delete()
    return None
        

def _delete_all_cached_updated_files() -> None:
    """
    Delete all files in the cache subdirectories.
    
    Args:
        directory: The root KLT directory.
        
    Returns:
        None
    """
    subdirectoryNames: tuple = (
        'accountancy-sheets',
        'bookings-reports',
        'html',
        'payments-to-owners',
        'properties-sheets',
        'guest-management',
        'reports'
    )
    subdirectories: list[Directory] = get_local_storage_directory().subdirectories
    for subdirectory in subdirectories:
        if subdirectory.name in subdirectoryNames:
            for file in subdirectory.files:
                file.delete()
    return None