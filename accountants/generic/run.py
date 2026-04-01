import datetime

from accountants.functions import (
    args_for_drive,
    cells,
    create_permissions,
    get_accountants_sheet_bookings,
    get_workbook,
    send_new_email_to_accountant
)
from apis.google.drives.file import GoogleDriveFile
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_database,
    search_properties,
    set_enquiry_sources,
    set_property_name,
)
from default.google.drive.functions import (
    download_drive_file_to_local_storage,
    upload_local_file_to_drive
)
from default.property.property import Property
from default.update.dates import updatedates
from default.update.wrapper import update
from default.workbook.functions import (
    create_worksheet,
    determine_years_order,
    set_worksheet,
    update_worksheet
)
from workbooks.workbook import Workbook


DRIVE_FOLDER = 'GenAcc - Gerenciamento e Contabilidade'


# Main functions
@update
def update_generic_accounts_reports_workbooks(
    *accountants : tuple[str],
    start: datetime.date = None,
    end: datetime.date = None,
    **enquirySources
) -> str:
    """File
    Update generic accountancy report workbooks for the specified date range.
    
    Creates or updates accountancy workbooks for properties managed by the specified
    accountants, and emails the reports to the accountant.
    
    Args:
        accountants: Name of the accountancy company
        start: Start date for the report period
        end: End date for the report period
        **enquirySources: Additional filtering by enquiry sources
    
    Returns:
        Success message string
    """
    if not start and not end:
        start, end = updatedates.gen_acc_update_dates()

    database = get_database()
    for accountant in accountants:
        properties: list[Property] = get_properties(accountant)
        workbooks = get_workbooks(properties)
        datesByYears = updatedates.breakDatesByYears(start, end)
        
        processedWorkbooks = []
        for startDate, endDate in datesByYears:
            processedWorkbooks = update_workbooks(
                database, 
                workbooks, 
                startDate, 
                endDate, 
                **enquirySources
            )
        
        upload_and_send_workbooks(
            processedWorkbooks, 
            start
        )
        
    database.close()
    return 'Successfully updated Generic Accountancy workbooks!'


# Workbook handling functions
def get_workbooks(properties: list[Property]) -> dict[str, tuple[Workbook, GoogleDriveFile | None]]:
    """
    Create or load workbooks for each property.
    
    Downloads existing workbooks from Google Drive or creates new ones.
    
    Args:
        properties: List of properties to create/load workbooks for
    
    Returns:
        Dictionary mapping property names to (workbook, driveFile) tuples
    """
    result = {}
    for property in properties:
        filename = f'Accountancy Bookings Report for {property.owner.name.upper()} at {property.name}.xlsx'
        workbook = get_workbook(filename)
        driveFile = download_drive_file_to_local_storage(**args_for_drive(filename, DRIVE_FOLDER))
        
        if driveFile:
            workbook.load()
        else:
            workbook.create()
            
        result[property] = (workbook, driveFile)
    
    return result


def update_workbooks(
    database: Database,
    workbooks: dict[Property, tuple[Workbook, GoogleDriveFile | None]],
    start: datetime.date,
    end: datetime.date,
    **enquirySources
) -> list[tuple[str, Workbook, GoogleDriveFile]]:
    """
    Update workbooks with booking data for the specified period.
    
    Creates or updates worksheets for each property with booking data.
    
    Args:
        database: The database connection
        workbooks: Dictionary mapping property names to (workbook, driveFile) tuples
        start: Start date for bookings to include
        end: End date for bookings to include
        **enquirySources: Additional filtering by enquiry sources
    
    Returns:
        List of processed (propertyName, workbook, driveFile) tuples
    """
    result = []

    for property, (workbook, driveFile) in workbooks.items():
        bookings = get_bookings(database, property.name, start, end, **enquirySources)
        
        if not bookings:
            continue
        
        worksheet = set_worksheet(name=f'{start.year}', start=start, end=end)
        cellsToSet = cells(management=False)
        
        if workbook.hasSheet(worksheet):
            update_worksheet(workbook.getSheet(worksheet), bookings, cellsToSet, startEndCol=4)
        else: 
            create_worksheet(workbook.insertSheet(worksheet), bookings, cellsToSet)
        
        workbook.orderSheets(determine_years_order(workbook.sheetnames)).save()
        result.append((property, workbook, driveFile))
    
    return result


def upload_and_send_workbooks(
    workbooks: list[tuple[Property, Workbook, GoogleDriveFile | None]], 
    date: datetime.date
) -> None:
    """
    Upload workbooks to Google Drive and email the accountant.
    
    Uploads each workbook to Google Drive, sets permissions for the recipient,
    and sends an email notification with a link to the file.
    
    Args:
        workbooks: List of (propertyName, workbook, driveFile) tuples to process
        date: Date for email subject line
    """
    for property, workbook, driveFile in workbooks:
        driveFileExisted = driveFile is not None
        
        driveFile = upload_local_file_to_drive(
            driveFile, 
            **args_for_drive(workbook.name, DRIVE_FOLDER)
        )
        
        if not driveFileExisted:
            create_permissions(driveFile)#, property.accountant.email)

        send_new_email_to_accountant(
            property.accountant.email, 
            property.accountant.name, 
            property.name, 
            driveFile, 
            date
        )


# Data retrieval functions
def get_properties(accountant: str = None) -> list[Property]:
    """
    Get properties managed by the specified accountants.
    
    Retrieves property records from the database that are associated with
    the specified accountancy company.
    
    Args:
        accountants: Name of the accountancy company
    
    Returns:
        List of Property objects
    """
    search = search_properties()

    # Select accountant id
    select = search.propertyAccountants.select()
    select.name()
    select.email()
    
    # Select owner names
    select = search.propertyOwners.select()
    select.name()
    
    where = search.propertyAccountants.where()
    where.company().isEqualTo(accountant)
    
    return search.fetchall()


def get_bookings(
    database: Database, 
    propertyName: str, 
    start: datetime.date, 
    end: datetime.date, 
    **enquirySources
) -> list[Booking]:
    """
    Fetch accountancy sheet bookings for a specific property within a date range.
    
    Retrieves bookings with accountancy-relevant data from the database,
    filtered by property name, date range, and optional enquiry sources.
    
    Args:
        database: The database connection
        propertyName: Name of the property to get bookings for
        start: Start date for bookings to include
        end: End date for bookings to include
        **enquirySources: Additional filtering by enquiry sources
    
    Returns:
        List of Booking objects
    """
    search = get_accountants_sheet_bookings(database, start, end)
    set_property_name(search, propertyName)
    set_enquiry_sources(search, **enquirySources)    
    return search.fetchall()