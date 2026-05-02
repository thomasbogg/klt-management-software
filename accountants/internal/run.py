from datetime import date

from accountants.functions import (
    args_for_drive,
    get_accountants_sheet_bookings,
    get_workbook
)
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_database,
    search_properties,
    set_property_name
)
from default.dates import dates
from default.google.drive.functions import (
    archive_files_from_previous_years,
    download_drive_file_to_local_storage,
    upload_local_file_to_drive
)
from default.property.property import Property
from default.update.dates import updatedates
from default.update.wrapper import update
from default.workbook.cells import (
    set_arrival_date_cell,
    set_booking_origin_cell,
    set_departure_date_cell,
    set_id_cell,
    set_issued_cell,
    set_lead_guest_cell,
    set_nationality_cell,
    set_nif_cell,
    set_passport_cell,
    set_platform_fee_cell,
    set_platform_fee_iva_cell,
    set_property_cell,
    set_running_total_cell,
    set_total_received_by_klt_cell,
    set_total_to_be_receipted_cell
)
from default.workbook.functions import (
    create_worksheet,
    set_worksheet,
    update_worksheet
)
from utils import sublog
from workbooks.workbook import Workbook
from workbooks.worksheet import Worksheet


DRIVE_DIR = 'Green Receipts Issuance for Owners'


@update
def update_internal_accountant_workbooks(start: date = None, end: date = None) -> str:
    """
    Update internal accountant workbooks with booking information for specified date range.
    
    Args:
        start: The start date for bookings to include. If None, uses default update dates.
        end: The end date for bookings to include. If None, uses default update dates.
        
    Returns:
        A string indicating successful completion.
    """
    if start is None and end is None: 
        start, end = updatedates.internal_accountant_update_dates()
   
    properties = get_properties()
    database = get_database()
    datesByYear = dates.breakDatesByYears(start, end)
   
    for start, end in datesByYear:
        filename = f'Green Receipts Issuance for Owners - {start.year}.xlsx'
        driveFile = download_drive_file_to_local_storage(**args_for_drive(filename, DRIVE_DIR))
        workbook = get_workbook(filename)
        workbook.load() if driveFile else workbook.create()
        sublog(f'EDITING: {filename}')
        
        for property in properties:
            propertyName = property.shortName
            bookings = get_bookings(database, start, end, propertyName)
            if not bookings:
                continue

            sublog(f'doing: {propertyName}...')
            sheet = set_worksheet(propertyName, start, end)
            if workbook.hasSheet(sheet): 
                update_worksheet(workbook.openSheet(sheet), bookings, cells(), startEndCol=5)
            else: 
                create_worksheet(workbook.insertSheet(sheet), bookings, cells())
        
        workbook.save()
        upload_local_file_to_drive(driveFile, **args_for_drive(filename, DRIVE_DIR))
   
    if dates.month() < 3: 
        archive_files_from_previous_years(**args_for_drive(filename, DRIVE_DIR))

    database.close()
    return 'Successfully updated Internal Accountant workbooks!'


def get_bookings(database: Database = None, start: date = None, 
                end: date = None, propertyName: str = None) -> list[Booking]:
    """
    Retrieve bookings for a specific property within a date range.
    
    Args:
        database: The database to query.
        start: The start date for bookings to include.
        end: The end date for bookings to include.
        propertyName: The name of the property to filter bookings for.
        
    Returns:
        A list of Booking objects matching the criteria.
    """
    search = get_accountants_sheet_bookings(database, start, end)
    
    where = search.details.where()
    where.enquirySource().isNotLike('Direct')
    where.isOwner().isFalse()

    set_property_name(search, propertyName)
    
    return search.fetchall()


def get_properties() -> list[Property]:
    """
    Retrieve properties where owners want accounting services.
    
    Returns:
        A list of Property objects where the property owner wants accounting.
    """
    search = search_properties()
    search.propertyOwners.where().wantsAccounting().isTrue()
    
    results = search.fetchall()
    search.close()
    return results
    

def cells() -> tuple:
    """
    Return a tuple of cell setter functions used for worksheet creation and updates.
    
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
        set_passport_cell,
        set_nif_cell,
        set_nationality_cell,
        set_platform_fee_cell,
        set_platform_fee_iva_cell,
        set_total_received_by_klt_cell,
        set_total_to_be_receipted_cell,
        set_running_total_cell,
        set_issued_cell,
    )