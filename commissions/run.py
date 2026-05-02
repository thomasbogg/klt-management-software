from datetime import date

from default.accountancy.functions import ACC_STORAGE_DIR, get_accountancy_sheet_bookings
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database, set_property_location
from default.dates import dates
from default.google.drive.functions import (
    archive_files_from_previous_years,
    download_drive_file_to_local_storage,
    upload_local_file_to_drive
)
from default.property.functions import determine_location
from default.update.dates import updatedates
from default.update.wrapper import update
from default.workbook.cells import (
    set_arrival_date_cell,
    set_basic_holiday_charge_cell,
    set_booking_origin_cell,
    set_commission_after_iva_cell,
    set_departure_date_cell,
    set_id_cell,
    set_internal_commission_cell,
    set_klt_commission_cell,
    set_lead_guest_cell,
    set_marias_commission_cell,
    set_property_cell,
    set_running_total_cell
)
from default.workbook.functions import (
    create_worksheet, 
    get_workbook, 
    set_worksheet
)
from utils import sublog
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet


@update
def update_commissions_breakdown_workbooks(start: date = None, end: date = None) -> str:
    """
    Update commissions breakdown workbooks with booking information for specified date range.
    
    Creates monthly reports showing commission breakdowns for different property locations.
    
    Args:
        start: The start date for bookings to include. If None, uses default update dates.
        end: The end date for bookings to include. If None, uses default update dates.
        
    Returns:
        A string indicating successful completion.
    """
    if start is None and end is None: 
        start, end = updatedates.commissions_update_dates()
  
    database: Database = get_database()
    datesByMonths = dates.breakDatesByMonths(start, end)

    for start, end in datesByMonths:
        month = updatedates.prettyMonth(start)
        year = start.year
        filename = f'Monthly Commissions Report - {month}, {year}.xlsx'
        driveFile = download_drive_file_to_local_storage(**_args_for_drive(filename))
        sublog(f'EDITING: {filename}')
        workbook: Workbook = get_workbook(filename, ACC_STORAGE_DIR).create()
       
        for location in ('Quinta da Barracuda', 'Clube do Monaco', 'Parque da Corcovada'):
            sheet: Worksheet = workbook.insertSheet(set_worksheet(location))
            bookings: list[Booking] = _get_bookings(database, start, end, **determine_location(location))
            create_worksheet(sheet, bookings, _cells())
       
        workbook.save()
        upload_local_file_to_drive(driveFile, **_args_for_drive(filename))
   
    if updatedates.month() < 3:
        archive_files_from_previous_years(**_args_for_drive_archive())
    
    database.close()
    return 'Successfully updated Commissions Breakdown workbooks!'


def _args_for_drive(filename: str) -> dict[str, str]:
    """
    Generate arguments for Google Drive operations.
    
    Args:
        filename: The name of the file to operate on.
        
    Returns:
        A dictionary with the necessary arguments for Drive operations.
    """
    return {
        'drivePath': 'Accountancy Sheets/Commissions Breakdown',
        'filename': filename,
        'localDirectory': ACC_STORAGE_DIR,
        'backupFolderOnDrive': 'Accountancy Sheets'
    }


def _args_for_drive_archive() -> dict[str, str]:
    """
    Generate arguments for archiving old Drive files.
    
    Returns:
        A dictionary with the necessary arguments for archiving operations.
    """
    return {
        'localDirectory': ACC_STORAGE_DIR,
        'drivePath': 'Accountancy Sheets/Commissions Breakdown',
        'localPath': 'accountancy-sheets'
    }


def _get_bookings(database: Database, start: date = None, end: date = None, **locations) -> list[Booking]:
    """
    Retrieve bookings for a specific location within a date range.
    
    Args:
        database: The database to query.
        start: The start date for bookings to include.
        end: The end date for bookings to include.
        locations: Location filtering criteria passed to set_property_location.
        
    Returns:
        A list of Booking objects matching the criteria.
    """
    search = get_accountancy_sheet_bookings(database, start, end)
    select = search.propertyOwners.select()
    select.rentalCommissionsAreInvoiced()
    set_property_location(search, **locations)    
    return search.fetchall()


def _cells() -> tuple:
    """
    Return a tuple of cell setter functions used for worksheet creation.
    
    Returns:
        A tuple of functions for setting cell values in worksheets.
    """
    return (
        set_id_cell,
        set_lead_guest_cell,
        set_booking_origin_cell,
        set_property_cell,
        set_arrival_date_cell,
        set_departure_date_cell,
        set_basic_holiday_charge_cell,
        set_internal_commission_cell,
        set_commission_after_iva_cell,
        set_klt_commission_cell,
        set_marias_commission_cell,
        set_running_total_cell,
    )