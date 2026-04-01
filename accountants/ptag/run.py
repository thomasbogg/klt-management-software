from accountants.functions import (
    DRIVE_FOLDER as ACC_DRIVE_FOLDER,
    args_for_drive,
    cells,
    get_workbook
)
import datetime
from default.accountancy.functions import get_accountancy_sheet_bookings
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.google.drive.functions import (
    download_drive_file_to_local_storage,
    get_klt_management_directory_on_drive,
    upload_local_file_to_drive
)
from default.google.mail.functions import (
    get_sent,
    new_email,
    send_email
)
from default.update.dates import updatedates
from default.update.wrapper import update
from default.workbook.functions import (
    create_worksheet,
    determine_years_order,
    set_worksheet,
    update_worksheet
)
from utils import sublog
from workbooks.worksheet import Worksheet


# Constants
DRIVE_FOLDER = 'PTAG - Parque da Corcovada 39-2B'
FILENAME = 'Parque da Corcovada 39-2B, PTAG Accountants Report.xlsx'


@update
def update_ptag_workbooks(start: datetime.date | None = None, end: datetime.date | None = None) -> str:
    """
    Update PTAG workbooks for Parque da Corcovada 39-2B.
    
    Args:
        start: Start date for the update. If None, uses default dates.
        end: End date for the update. If None, uses default dates.
        
    Returns:
        Success message string
    """
    if start is None and end is None: 
        start, end = updatedates.ptag_update_dates()
    
    driveFile = download_drive_file_to_local_storage(**args_for_drive(FILENAME, DRIVE_FOLDER))
    database = get_database()
    workbook = get_workbook(FILENAME)
    workbook.load() if driveFile else workbook.create()
    
    sublog(f'EDITING: {FILENAME}')
    datesByYears = updatedates.breakDatesByYears(start=start, end=end)
    
    for start, end in datesByYears:
        name: str = str(start.year)
        bookings: list[Booking] = get_bookings(database, start, end)
        sheet: Worksheet = set_worksheet(name, start, end, checkHide=True)
        cellsToSet: tuple[callable] = cells(management=False)
    
        for booking in bookings:
            date: datetime.date = booking.arrival.date
            if updatedates.calculate(days=-4) <= date <= updatedates.calculate(days=-2):
                send_email_to_accountant(booking)
        
        if workbook.hasSheet(sheet): 
            update_worksheet(workbook.getSheet(sheet), bookings, cellsToSet, startEndCol=4)
        else:
            create_worksheet(workbook.insertSheet(sheet), bookings, cellsToSet)
        
    workbook.orderSheets(determine_years_order(workbook.sheetnames)).save()
    upload_local_file_to_drive(driveFile, **args_for_drive(FILENAME, DRIVE_FOLDER))
    database.close()
    return 'Successfully updated PTAG workbooks!'


def get_bookings(database: Database, start: datetime.date, end: datetime.date) -> list[Booking]:
    """
    Retrieve bookings for PTAG accounting from database.
    
    Args:
        database: Database connection to use
        start: Start date for booking search
        end: End date for booking search
        
    Returns:
        List of bookings matching the criteria
    """
    search: Database = get_accountancy_sheet_bookings(database, start, end)

    select = search.propertyAccountants.select()
    select.name()
    select.email()

    select = search.charges.select()
    select.admin()

    select = search.propertyOwners.select()
    select.cleansAreInvoiced()

    where = search.details.where()
    where.enquirySource().isNotEqualTo('Direct')
    
    where = search.properties.where()
    where.shortName().isEqualTo('39-2B')
    
    return search.fetchall()


def send_email_to_accountant(booking: Booking) -> None:
    """
    Send notification email to accountant about payment made.
    
    Args:
        booking: The booking for which payment notification is to be sent
    """
    subject = 'Payment made to Swati Tandon and Matt Cook for Parque da Corcovada 39-2B'
    to = booking.property.accountant.email

    if get_sent(to=to, subject=subject, start=updatedates.calculate(days=-3), end=updatedates.calculate(days=1)):
        return None
    
    user, message = new_email(to=to, subject=subject, name=booking.property.accountant.name)
    message.cc = 'kevin@algarvebeachapartments.com'
    body = message.body

    body.paragraph('A payment has been made into the account of Swati Tandon and Matt Cook.')
    body.paragraph('The full details of the payment can be found in the Google Drive folder.')
    body.paragraph(f'Guest Name: <b>{booking.guest.name}</b>')
    body.paragraph(f'Arrival Date: <b>{booking.arrival.prettyDate}</b>')
    body.link(
        drive_directory_link(),
        'Google Drive folder for PTAG',
        bold=True
    )
    body.paragraph('I trust this has been helpful. As always, I remain available for questions.')

    send_email(user, message)


def drive_directory_link() -> str:
    """
    Get the link to the Google Drive folder for PTAG.
    
    Returns:
        The URL link to the Google Drive folder
    """
    drivePath: str = f'{ACC_DRIVE_FOLDER}/{DRIVE_FOLDER}'
    return get_klt_management_directory_on_drive(drivePath=drivePath).link