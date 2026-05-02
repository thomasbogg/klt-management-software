from datetime import date

from accountants.functions import (
    args_for_drive,
    cells,
    create_permissions,
    get_accountants_sheet_bookings,
    get_workbook,
    send_new_email_to_accountant
)
from default.accountancy.functions import get_property_accountant
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.google.drive.functions import (
    archive_files_from_previous_years,
    download_drive_file_to_local_storage,
    upload_local_file_to_drive
)
from default.update.dates import updatedates
from default.update.wrapper import update
from default.workbook.functions import (
    create_worksheet,
    set_worksheet
)
from utils import sublog


DRIVE_FOLDER = 'HARMONIOUS JUNGLE - D21'


@update
def update_harmonious_jungle_workbooks(
    start: date = None, 
    end: date = None
) -> str:
    """
    Update the Harmonious Jungle accountancy workbooks for the specified date range.
    
    Creates monthly accountancy workbooks for Harmonious Jungle property D21,
    downloads existing workbooks from Google Drive or creates new ones, and uploads
    the updated workbooks back to Drive.
    
    Args:
        start: Start date for the report period
        end: End date for the report period
    
    Returns:
        Success message string
    """
    if start is None and end is None: 
        start, end = updatedates.harmonious_jungle_update_dates()

    database = get_database()
    datesByMonths = updatedates.breakDatesByMonths(start, end)
    
    for start, end in datesByMonths:
        year = start.year        
        month = updatedates.prettyMonth(start.month)
        filename = f'End of Month Harmonious Jungle Accountancy Report - {month}, {year}.xlsx'
        driveFile = download_drive_file_to_local_storage(**args_for_drive(filename, DRIVE_FOLDER))
        sublog(f'EDITING: {filename}')
        
        workbook = get_workbook(filename).create()
        bookings = get_bookings(database, start, end)
        sheet = set_worksheet('D21')
        create_worksheet(workbook.insertSheet(sheet), bookings, cells(id=False))
        workbook.save()
        
        driveFile = upload_local_file_to_drive(driveFile, **args_for_drive(filename, DRIVE_FOLDER))
        accountant = get_property_accountant(propertyName='D21')
        create_permissions(driveFile, accountant.email)
        send_new_email_to_accountant(
            accountantEmail=accountant.email,
            accountantName=accountant.name,
            propertyName='D21',
            driveFile=driveFile,
            date= start,
        )

    if updatedates.month() < 3:
        archive_files_from_previous_years(**args_for_drive(filename, DRIVE_FOLDER))
    
    database.close()
    return 'Successfully updated HARMONIOUS JUNGLE workbooks!'


def get_bookings(
    database: Database, 
    start: date, 
    end: date
) -> list[Booking]:
    """
    Get bookings for the D21 property within a date range.
    
    Retrieves filtered booking records from the database for the D21 property
    that are within the specified date range.
    
    Args:
        database: The database connection
        start: Start date for bookings to include
        end: End date for bookings to include
    
    Returns:
        List of booking records
    """
    search = get_accountants_sheet_bookings(database, start, end)
    
    where = search.properties.where()
    where.shortName().isEqualTo('D21')
    
    return search.fetchall()