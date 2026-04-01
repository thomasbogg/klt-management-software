import datetime

from default.booking.booking import Booking
from default.database.functions import search_bookings
from default.dates import dates
from default.google.drive.functions import (
    download_drive_file_to_local_storage,
    upload_local_file_to_drive
)
from default.google.mail.functions import new_email, send_email
from default.settings import LOCAL_STORAGE_DIR
from default.update.dates import updatedates
from default.update.wrapper import update
from reports.internal.accounts.run import accounts_report_creator
from reports.internal.bookings.run import bookings_vs_enquiries_report_creator
from reports.internal.commissions.run import commissions_report_creator
from reports.internal.extras.run import extras_report_creator
from reports.internal.management.run import management_report_creator
from reports.internal.properties.run import properties_report_creator
from reports.internal.revenue.run import revenue_report_creator
from reports.internal.stays.run import stays_vs_nights_reports_creator
from utils import log, sublog
from workbooks.workbook import Workbook


DATE = f'{dates.prettyMonth()} {dates.year()}'
DRIVE_FOLDER = 'Monthly Business Reports'
LOCAL_DIR = f'{LOCAL_STORAGE_DIR}/monthly-reports'


@update
def update_end_of_month_internal_report(
    start: datetime.date = None, 
    end: datetime.date = None,
    sendEmail: bool = True) -> str:
    """ 
    Create monthly reports for the business.

    :param start: Start date for the report period.
    :param end: End date for the report period.
    
    :return: Success message indicating the reports were created.
    """
    if not start or not end:
        start, end = updatedates().internal_reports_update_dates()
    
    workbook, driveFile = _create_workbook()
    bookings = _get_bookings(start, end)

    onlyValidBookings = [
        booking for booking in bookings if booking.details.managementStatusIsOkay]
    onlyValidABABookings = [
        booking for booking in onlyValidBookings if booking.property.weBook]
    onlyValidABAGuestBookings = [
        booking for booking in onlyValidABABookings if not booking.details.isOwner]
    onlyGuestBookings = [
        booking for booking in bookings if not booking.details.isOwner]
    onlyValidYearBookings = [
        booking for booking in onlyValidBookings if booking.arrival.year == dates.year()]

    stays_vs_nights_reports_creator(workbook, onlyValidABABookings, onlyGuest=False)
    stays_vs_nights_reports_creator(workbook, onlyValidABAGuestBookings, onlyGuest=True)
    bookings_vs_enquiries_report_creator(workbook, onlyGuestBookings)
    revenue_report_creator(workbook, onlyValidABAGuestBookings)
    accounts_report_creator(workbook, onlyValidABAGuestBookings)
    commissions_report_creator(workbook, onlyValidABAGuestBookings)
    management_report_creator(workbook, onlyValidBookings)
    extras_report_creator(workbook, onlyValidBookings)
    properties_report_creator(workbook, onlyValidYearBookings)

    workbook.save()
 
    upload_local_file_to_drive(
                            driveFile=driveFile,
                            filename=workbook.name, 
                            drivePath=DRIVE_FOLDER, 
                            localDirectory=LOCAL_DIR)
    if sendEmail:
        _send_monthly_report_email(workbook)
    
    return 'Successfully created and sent monthly reports for business!'


def _create_workbook() -> Workbook:
    """
    Create a new workbook for monthly reports.

    :return: Workbook object for the monthly reports.
    """
    log(f'Creating monthly reports workbook for {DATE}...')
    filename = f'Monthly Business Report - {DATE}.xlsx'
    driveFile = download_drive_file_to_local_storage(
                                                filename=filename,
                                                drivePath=DRIVE_FOLDER,
                                                localDirectory=LOCAL_DIR)
    workbook = Workbook(filename, LOCAL_DIR)
    workbook.create()
    return workbook, driveFile


def _get_bookings(start: datetime.date, end: datetime.date) -> list[Booking]:
    """
    Get bookings for the specified date range.

    :param start: Start date for the bookings.
    :param end: End date for the bookings.

    :return: List of Booking objects within the specified date range.
    """
    search = search_bookings(start=start, end=end)
    search.guests.select().id()
    search.details.select().all()
    search.arrivals.select().all()
    search.departures.select().all()
    search.extras.select().all()
    search.charges.select().all()
    search.properties.select().all()
    search.propertyAddresses.select().all()
    search.propertyOwners.select().all()
    return search.fetchall()


def _send_monthly_report_email(workbook: Workbook) -> None:
    """
    Send the monthly report via email.
    
    :param workbook: Workbook containing the monthly reports.
    """
    sublog('Report created, sending by email...')
  
    user, message = new_email(subject=f"Monthly Business Report - {DATE}")
    message.to = 'kevin@algarvebeachapartments.com, thomas@algarvebeachapartments.com'
    message.greeting.name = 'Most Excellent Team'
    message.attachments = workbook.file
    body = message.body

    body.paragraph(
        f"Please find attached the monthly business report for {DATE}.",
        "This report includes various insights and statistics about our",
        "bookings, revenue, and more."
    )
    body.paragraph(
        "If you have questions or notice potential issues, please contact me."
    )

    send_email(user, message, checkSent=True)