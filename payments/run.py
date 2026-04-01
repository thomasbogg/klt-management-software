from datetime import date
from apis.google.drives.file import GoogleDriveFile
from default.accountancy.functions import get_accountancy_sheet_bookings
from default.database.database import Database
from default.database.functions import (
    get_database,
    set_property_location
)
from default.dates import dates
from default.google.drive.functions import (
    archive_files_from_previous_years,
    download_drive_file_to_local_storage, 
    upload_local_file_to_drive
)
from default.property.functions import determine_location
from default.update.dates import updatedates as updateDates
from default.update.wrapper import update
from default.workbook.cells import (
    set_admin_charge_cell,
    set_arrival_date_cell,
    set_booking_origin_cell,
    set_departure_date_cell,
    set_id_cell,
    set_internal_commission_cell,
    set_invoiced_cell,
    set_lead_guest_cell,
    set_nationality_cell,
    set_nif_cell,
    set_paid_cell,
    set_passport_cell,
    set_platform_fee_cell,
    set_platform_fee_plus_iva_cell,
    set_property_cell,
    set_rental_to_owner_cell,
    set_total_received_by_klt_cell
)
from default.workbook.functions import (
    create_worksheet, 
    determine_months_order, 
    get_workbook, 
    set_worksheet, 
    update_worksheet
)
from utils import logdivider, sublog
from workbooks.workbook import Workbook


# Directory constants
LOCAL_DIR = 'payments-to-owners'
DRIVE_DIR = 'Payments to Owners'


@update
def update_payments_to_owner_workbooks(start: date = None, end: date = None) -> str:
    """
    Update workbooks containing payment information to property owners.
    
    Downloads, updates, and uploads payment workbooks for the specified date range.
    If no dates are provided, uses default update dates from updatedates. Also handles
    archiving files from previous years in January.
    
    Parameters:
        start: Start date for the update, defaults to None
        end: End date for the update, defaults to None
    
    Returns:
        Success message string
    """
    if start is None and end is None: 
        start, end = updateDates.payments_to_owner_update_dates()
   
    database = get_database()
    datesByYear = dates.breakDatesByYears(start, end)
   
    for yearStart, yearEnd in datesByYear:
        update_by_the_year(database, yearStart, yearEnd, get_filenames(yearStart.year))
   
    if dates.month() == 1 and 15 < dates.day() < 19: 
        archive_files_from_previous_years(**args_for_drive())
    
    return 'Successfully updated Payments to Owners workbooks!'
        

def update_by_the_year(database: Database, start: date, end: date, filenames: list[str]) -> None:
    """
    Update payment workbooks for a specific year.
    
    Downloads, updates, and uploads workbooks for each location, creating or updating
    worksheets for each month with booking payment information.
    
    Parameters:
        database: Database connection
        start: Start date for the year
        end: End date for the year
        filenames: List of Excel filenames to process
    
    Returns:
        None
    """
    if not filenames:
        return None

    logdivider()
    
    filename = filenames.pop(0)
    driveFile = download_drive_file_to_local_storage(**args_for_drive(filename))
    workbook = get_workbook(filename, LOCAL_DIR)
    workbook.load() if driveFile else workbook.create()

    sublog(f'EDITING: {filename}')
    
    datesByMonths = dates.breakDatesByMonths(start=start, end=end)
    for monthStart, monthEnd in datesByMonths:
        bookings = get_bookings(database, monthStart, monthEnd, **determine_location(filename))
        prettyMonth = dates.prettyMonth(monthStart)
        sheet = set_worksheet(prettyMonth, monthStart, monthEnd, checkExchange=True, internal=True)
    
        if workbook.hasSheet(sheet): 
            update_worksheet(workbook.openSheet(sheet), bookings, cells(), startEndCol=5)
        else: 
            create_worksheet(workbook.insertSheet(sheet), bookings, cells())

    workbook.orderSheets(determine_months_order(workbook.sheetnames))
    workbook.save()
    
    upload_local_file_to_drive(driveFile, **args_for_drive(filename))
    return update_by_the_year(database, start, end, filenames)


def get_filenames(year: int) -> list[str]:
    """
    Generate filenames for payment workbooks for a given year.
    
    Parameters:
        year: The year to generate filenames for
    
    Returns:
        List of filenames for each location
    """
    return [
        f'Payments to Owners {year} - Quinta da Barracuda.xlsx',
        f'Payments to Owners {year} - Clube do Monaco.xlsx',
        f'Payments to Owners {year} - Parque da Corcovada.xlsx',
    ]


def args_for_drive(filename: str = None) -> dict[str, str]:
    """
    Generate arguments for Google Drive operations.
    
    Parameters:
        filename: Optional filename to include in the arguments
    
    Returns:
        Dictionary of drive operation arguments
    """
    return {
        'drivePath': DRIVE_DIR,
        'filename': filename,
        'localDirectory': LOCAL_DIR,
        'backupFolderOnDrive': DRIVE_DIR
    }


def get_bookings(database: Database, start: date = None, end: date = None, **properties) -> list:
    """
    Get bookings for accountancy sheets within a date range.
    
    Parameters:
        database: Database connection
        start: Start date for bookings
        end: End date for bookings
        properties: Additional property filters
    
    Returns:
        List of booking objects
    """
    search = get_accountancy_sheet_bookings(database, start, end)
    select = search.charges.select()
    select.admin()
    set_property_location(search, **properties)    
    return search.fetchall()


def cells() -> tuple:
    """
    Get a tuple of cell setter functions for workbook operations.
    
    Returns:
        Tuple of cell setter functions
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
        set_platform_fee_plus_iva_cell,
        set_total_received_by_klt_cell,
        set_admin_charge_cell,
        set_internal_commission_cell,
        set_rental_to_owner_cell,
        set_paid_cell,
        set_invoiced_cell,
    )