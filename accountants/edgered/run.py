from datetime import date

from accountants.functions import (
    args_for_drive,
    cells,
    get_accountants_sheet_bookings,
    get_workbook,
    set_split_payments_worksheet
)
from default.database.database import Database
from default.database.functions import (
    get_database,
    search_properties
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
from default.workbook.functions import (
    create_worksheet,
    set_worksheet
)
from utils import sublog


from default.booking.functions import (
    determine_total_to_be_receipted,
    determine_owner_payment,
    logbooking,
)
from default.booking.booking import Booking
from default.settings import DEFAULT_ACCOUNT

DRIVE_FOLDER = 'EDGERED - Clube do Monaco'


@update
def update_edgered_workbooks(
    start: date = None, 
    end: date = None, 
    propertyName: str = None
) -> str:
    """
    Update the EDGERED accountancy workbooks for the specified date range.
    
    Creates monthly accountancy workbooks for EDGERED properties, downloads
    existing workbooks from Google Drive or creates new ones, and uploads
    the updated workbooks back to Drive.
    
    Args:
        start: Start date for the report period
        end: End date for the report period
        propertyName: Optional property name filter
    
    Returns:
        Success message string
    """
    if start is None and end is None: 
        start, end = updatedates.edgered_update_dates()
    
    database = get_database()
    datesByMonths = dates.breakDatesByMonths(start, end)
    
    for start, end in datesByMonths:
        yearVal, monthVal = start.year, updatedates.stringMonths()[start.month - 1]
        filename = f'End of Month EDGERED Accountancy Report - {monthVal}, {yearVal}.xlsx'
        driveFile = download_drive_file_to_local_storage(**args_for_drive(filename, DRIVE_FOLDER))
        sublog(f'EDITING: {filename}')        
        workbook = get_workbook(filename).create()
        
        for property in get_properties():
            if propertyName and propertyName not in (property.shortName, property.name): 
                continue
            sheetname = property.shortName

            if 'MON AA' in sheetname: 
                sheet = set_split_payments_worksheet(
                    name=sheetname, owners=('Somendra', 'Sahil'), fractions=(.2, .8))
                cellsToSet = cells(id=False, splitPayments=True)
            else: 
                sheet = set_worksheet(name=sheetname)
                cellsToSet = cells(id=False)
                
            bookings = get_bookings(database, start, end, sheetname)
            create_worksheet(workbook.insertSheet(sheet), bookings, cellsToSet)
            
        workbook.save()
        upload_local_file_to_drive(driveFile, **args_for_drive(filename, DRIVE_FOLDER))
    
    if updatedates.month() < 3: 
        archive_files_from_previous_years(**args_for_drive(filename, DRIVE_FOLDER))
    
    database.close()
    return 'Successfully updated EDGERED workbooks!'


def get_bookings(
    database: Database, 
    start: date, 
    end: date, 
    propertyName: str = None
) -> list[Booking]:
    """
    Get bookings for a property within a date range.
    
    Retrieves filtered booking records from the database for a specific property
    that have departure dates within the specified date range.
    
    Args:
        database: The database connection
        start: Start date for bookings to include
        end: End date for bookings to include
        propertyName: Name of the property to filter by
    
    Returns:
        List of booking records
    """
    search = get_accountants_sheet_bookings(database)
    
    # Set conditions for properties
    where = search.properties.where()
    where.shortName().isEqualTo(propertyName)

    where = search.departures.where()
    where.date().isGreaterThanOrEqualTo(start)
    where.date().isLessThanOrEqualTo(end)
    
    return search.fetchall()


def get_properties() -> list[Property]:
    """
    Get all Monaco properties from the database.
    
    Retrieves property records that have 'MONACO' in their name.
    
    Returns:
        List of Property objects for Monaco properties
    """
    search = search_properties()
    
    # Set conditions for properties
    where = search.propertyAccountants.where()
    where.company().isLike('EDGERED')
    
    return search.fetchall()


@update
def calculate_owners_totals_over_period(
    start: date = None, 
    end: date = None, 
) -> None:
    """
    Calculate and log owner totals for a property within a date range.
    
    This function retrieves bookings for a specific property and calculates
    the total amounts for each owner based on the bookings' details.
    
    Args:
        database: The database connection
        start: Start date for bookings to include
        end: End date for bookings to include
        propertyName: Name of the property to filter by
    """
    if start is None and end is None: 
        start, end = updatedates.calculate_mon_owners_totals_update_dates()
    
    owners = {}
    properties = get_properties()
    database = get_database()

    for property in properties:
        name = property.shortName
        bookings = get_bookings(database, start, end, name)

        if name in ('MON 2',):
            _calculate_totals(bookings, owners, 'Somendra', name)

        elif name in ('MON AA',):
            _calculate_totals(bookings, owners, 'Somendra', name, fraction=0.2)
            _calculate_totals(bookings, owners, 'Sahil', name, fraction=0.8)

        elif name in ('MON 8', 'MON AE', 'MON T'):
            _calculate_totals(bookings, owners, 'Sahil', name)

        elif name in ('MON 19', 'MON 4'):
            _calculate_totals(bookings, owners, 'Surbi', name)

    database.close()
    _send_owner_totals_over_period_email(
        start=start, 
        end=end, 
        totals=owners
    )
    return 'Successfully calculated owner totals over period!'


def _add_property_and_owner(
    owners: dict[str, dict], 
    ownerName: str,
    propertyName: str
) -> dict:
    """
    Ensure the owner and property exist in the owners dictionary.

    Args:
        owners: Dictionary to store totals for each owner
        ownerName: Name of the owner
        propertyName: Name of the property

    Returns:
        The dictionary for the specified owner and property
    """
    if ownerName not in owners:
        owners[ownerName] = {'total': _total_dict()}
    if propertyName not in owners[ownerName]:
        owners[ownerName][propertyName] = _total_dict()
    return owners[ownerName][propertyName]


def _total_dict() -> dict[str, float]:
    """
    Create a dictionary to hold total calculations.
    
    Returns:
        A dictionary with keys for different total calculations initialized to 0.0
    """
    return {
        'Receipted': 0.0,
        #'Paid to KLT': 0.0,
        #'Paid to Owner': 0.0,
    }


def _calculate_totals(
    bookings: list[Booking], 
    owners: dict[str, dict[str:float]],
    owner: str,
    propertyName: str,
    fraction: float = 1.0
) -> None:
    """
    Calculate totals for each owner based on the bookings.
    
    Args:
        bookings: List of booking records
        owners: Dictionary to store totals for each owner
    """
    _add_property_and_owner(owners, owner, propertyName)
    calcs = owners[owner]
    for booking in bookings:
        logbooking(booking)
        for calc in (calcs[propertyName], calcs['total']):
            calc['Receipted'] += determine_total_to_be_receipted(booking) * fraction
            #calc['Paid to KLT'] += booking.charges.totalRental * fraction
            #calc['Paid to Owner'] += determine_owner_payment(booking) * fraction


def _send_owner_totals_over_period_email(
    start: date = None, 
    end: date = None, 
    totals: dict[str:dict[str:float]] = None
) -> None:
    """
    Send an internal finance email with the EDGERED accountancy report.
    
    Args:
        start: Start date for the report period
        end: End date for the report period
        propertyName: Optional property name filter
    """
    from default.google.mail.functions import new_email, send_email
    user, message = new_email(
        subject=
            f'Periodic check for MON Owners Income - {updatedates.prettyDate(start, lenWeekday=0)} '
            f'to {updatedates.prettyDate(end, lenWeekday=0)}',
        to='kevin@algarvebeachapartments.com',
        name='Dad'
    )
    message.cc = DEFAULT_ACCOUNT.emailAddress
    body = message.body

    body.paragraph(
        f'Please see below the list of properties and their',
        f'owner income for the period {updatedates.prettify(start)} to {updatedates.prettify(end)}.'
    )

    for owner, totals in totals.items():
        body.section(f'{owner}:')
        for property, property_totals in totals.items():
            if property == 'total': 
                bold = True
            else: 
                bold = False
            body.paragraph(f'{property.upper()}:', bold=bold, indent=25)
            for title, value in property_totals.items():
                body.paragraph(f'- {title}: €{value:,.2f} EUR', indent=45, bold=bold)

    send_email(user, message)