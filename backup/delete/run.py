import os
from datetime import date

from apis.google.drives.directory import GoogleDriveDirectory
from default.dates import dates
from default.google.drive.functions import get_klt_management_directory_on_drive
from default.update.dates import updatedates
from default.update.wrapper import update


@update
def delete_old_backups(start: date = None) -> str:
    """
    Delete old backup folders from Google Drive.
    
    Deletes backup folders for days that are not on the 8th or 24th of the month,
    keeping only important snapshots and freeing up storage space.
    
    Args:
        start: The start date from which to begin deletion. If None, uses default deletion dates.
        
    Returns:
        A message indicating successful deletion.
    """
    if start is None: 
        start = updatedates.delete_backups_dates()
    
    daysInMonth = dates.daysInMonth(start.year, start.month)
    
    for i in range(daysInMonth):
        nextDateToDelete = dates.calculate(date=start, days=i)
        
        # Keep backups from 8th and 24th of each month
        if nextDateToDelete.day not in (8, 24):
            folderName = dates.prettyDate(nextDateToDelete)
            drivePath = os.path.join('Backups', folderName)
            
            folder: GoogleDriveDirectory = get_klt_management_directory_on_drive(drivePath, giveError=False)
            if not folder: 
                continue
            
            folder.delete()
    
    return 'All folders deleted successfully!'