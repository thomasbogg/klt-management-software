from accountants.edgered.run import calculate_owners_totals_over_period, update_edgered_workbooks
from accountants.generic.run import update_generic_accounts_reports_workbooks
from accountants.harmonious_jungle.run import update_harmonious_jungle_workbooks
from accountants.ptag.run import update_ptag_workbooks

from arrivals.run import update_arrivals_calendar

from backup.database.run import back_up_database
from backup.delete.run import delete_old_backups
from backup.programming.run import back_up_programming_files

from commissions.run import update_commissions_breakdown_workbooks

from correspondence.guest.arrival.balance_payment.reminder.run import send_balance_payment_emails
from correspondence.guest.arrival.four_weeks.run import send_guest_four_weeks_emails
from correspondence.guest.arrival.instructions.two_days.run import send_two_days_instructions_emails
from correspondence.guest.arrival.instructions.two_weeks.run import send_two_weeks_instructions_emails
from correspondence.guest.arrival.registration.run import send_guest_registration_emails
from correspondence.guest.arrival.security_deposit.run import send_security_deposit_request_emails
from correspondence.guest.departure.final_days.run import send_final_day_reminder_emails
from correspondence.guest.departure.goodbye.run import send_goodbye_emails
from correspondence.internal.accountancy.payments_to_owners.run import send_payments_to_owners_email
from correspondence.internal.accountancy.security_deposits.run import send_security_deposit_returns_email
from correspondence.internal.management.arrivals.run import send_management_arrivals_emails
from correspondence.internal.management.cleans.run import send_management_cleans_emails
from correspondence.internal.management.realco.run import send_realco_email
from correspondence.internal.management.transfers.run import send_airport_transfers_request_emails
from correspondence.internal.management.updates.run import send_management_updates_emails
from correspondence.owner.details_prompting.run import send_arrival_details_prompting_emails
from correspondence.owner.four_weeks.run import send_owner_four_weeks_emails

from default.settings import TEST
from default.update.dates import updatedates
from default.update.wrapper import pull_database

from forms.arrival.guest.run import (
    delete_old_guest_arrival_forms,
    update_from_guest_arrival_forms,
) 
from forms.arrival.owner.run import (
    delete_old_owner_arrival_forms,
    update_from_owner_arrival_forms
)
from forms.registration.run import update_from_guest_registrations
from forms.registration.complete import complete_empty_guest_details

from interfaces.interface import Interface

from payments.run import update_payments_to_owner_workbooks

from PIMS.download import download_latest_from_PIMS
from PIMS.upload import update_PIMS_platform_bookings

from platforms.airbnb.download import update_from_airbnb
from platforms.airbnb.review import review_airbnb_guests
from platforms.bookingCom.contacts import update_bookingCom_guest_contacts
from platforms.bookingCom.download import update_from_bookingCom
from platforms.functions import notify_platform_bookings_without_PIMS_ID
from platforms.vrbo.download import update_from_vrbo

from reports.owner.run import update_bookings_reports_workbooks
from reports.internal.run import update_end_of_month_internal_report

from sheets.ABA.run import update_ABA_properties_sheets
from sheets.KKLJ.run import update_KKLJ_properties_sheets


def main() -> None:
    """
    Main entry point for the KLT management and database system updater.
    
    Determines whether to run a full or last-minute update based on the current 
    time and user input.
    """
    interface = Interface(title='GENERAL UPDATER FOR KLT MGMT. AND DB. SYSTEM')
    sections = interface.subsections()
    sections.log(f'Current time is {updatedates.now()}')

    if TEST:
        sections.log(
            'IN TESTING MODE. No updates will be performed. Change setting in ' \
            'default.settings to run upupdatedates.')
        return

    if updatedates.isUpdateHour(): 
        sections.log(
            'Will do FULL update. Press ENTER to continue or 1 for smaller update')
    else: 
        sections.log(
            'Will do SMALLER update. Press ENTER to continue or 1 for full update.')
    
    option = sections.integer()
    if option:
        if updatedates.isUpdateHour(): 
            last_minute_update(sections)
        else:
            full_update()
            update_backups()
    else:
        if updatedates.isUpdateHour():
            full_update()
            update_backups()
        else: 
            last_minute_update(sections)


@pull_database
def full_update() -> None:
    """
    Perform a full update of all systems.
    
    Backs up the database, updates from all sources, and performs all scheduled tasks.
    """
    back_up_database()
    update_from_platforms()
    update_from_forms()
    daily_update_from_pims()
    update_properties_sheets()
    update_accountancy_system()
    update_arrivals_system()
    update_guest_arrivals_system()
    update_guest_departures_system()
    update_and_review_platform_guests()
    back_up_database()
    

def update_backups() -> None:
    """
    Update system backups based on scheduled intervals.
    
    Programming files are backed up every 8 days.
    Old backups are deleted at the end of each month.
    """
    if updatedates.day() % 8 == 0: 
        back_up_programming_files()
    
    if updatedates.isLastOfMonth(): 
        delete_old_backups()


def update_from_platforms() -> None:
    """
    Update booking data from all external platforms.
    """
    update_from_bookingCom()
    update_bookingCom_guest_contacts()
    update_from_vrbo()
    update_from_airbnb()


def update_from_forms() -> None:
    """
    Update data from various forms and delete old forms on a schedule.
    """
    update_from_guest_arrival_forms()
    update_from_owner_arrival_forms()
    update_from_guest_registrations()
    
    if updatedates.day() % 14 == 0:
        delete_old_guest_arrival_forms()
        delete_old_owner_arrival_forms()


def daily_update_from_pims() -> None:
    """
    Download the latest data from PIMS.
    """
    download_latest_from_PIMS()


def update_properties_sheets() -> None:
    """
    Update property sheets for ABA and KKLJ properties.
    """
    update_ABA_properties_sheets()
    update_KKLJ_properties_sheets()


def update_accountancy_system() -> None:
    """
    Update various accountancy workbooks and send related emails.
    Certain updates are only performed on specific days of the month.
    """
    update_payments_to_owner_workbooks()
    send_payments_to_owners_email()
    send_security_deposit_returns_email()
    update_ptag_workbooks()

    if updatedates.isLastOfMonth():
        update_commissions_breakdown_workbooks()
        update_edgered_workbooks()
        update_harmonious_jungle_workbooks()
        update_end_of_month_internal_report()
        if updatedates.month() in (3, 6, 9, 12):
            calculate_owners_totals_over_period()


    if updatedates.day() in (1, 2):
        update_generic_accounts_reports_workbooks(
            'PNM - Consultadoria, Lda',
            'GRACIETE GRACE - Contabilidade e Consultoria, Lda',
            direct=False)

    if updatedates.day() in (1, 16):
        complete_empty_guest_details()
        update_bookings_reports_workbooks()


def update_arrivals_system() -> None:
    """
    Update arrival calendar and send various management emails related to arrivals.
    Send realco email on the first day of the month.
    """
    update_arrivals_calendar()
    send_management_updates_emails()
    send_management_arrivals_emails()
    send_management_cleans_emails()
    send_airport_transfers_request_emails()
    if updatedates.date() in (25, 26):
        send_realco_email()


def update_guest_arrivals_system() -> None:
    """
    Send various emails to guests and owners related to upcoming arrivals.
    """
    send_two_days_instructions_emails()
    send_guest_registration_emails()
    send_two_weeks_instructions_emails()
    send_security_deposit_request_emails()
    update_bookingCom_guest_contacts()
    send_guest_four_weeks_emails()
    send_owner_four_weeks_emails()
    send_arrival_details_prompting_emails()
    send_balance_payment_emails()


def update_guest_departures_system() -> None:
    """
    Send emails to guests related to their departures.
    """
    send_goodbye_emails()
    send_final_day_reminder_emails()


def update_and_review_platform_guests() -> None:
    """
    Update platform bookings from PIMS.
    Review Airbnb guests based on the latest data.
    """
    update_PIMS_platform_bookings()
    review_airbnb_guests()
    if updatedates.day() == 1:
        notify_platform_bookings_without_PIMS_ID(
                                            start=updatedates.date(), 
                                            end=updatedates.calculate(365))



@pull_database
def last_minute_update(sections: Interface) -> None:
    """
    Perform a more limited update for last-minute changes.
    
    Args:
        sections: Interface object for user interaction
    """
    back_up_database()
    start = updatedates.calculate(days=-1)
    end = updatedates.calculate(days=8)
    
    subsections = sections.subsections()
    subsections.section('Last-minute update started. Which part are we updating?')
    option = subsections.option((
                            'Properties we book?', 
                            'Properties we property manage, only?'))

    if option == 1:
        update_from_bookingCom()
        update_bookingCom_guest_contacts(start=start, end=end)
        update_from_airbnb()
        update_from_vrbo()
        download_latest_from_PIMS(start=start, end=end, updatedSince=1)
    elif option == 2: 
        update_KKLJ_properties_sheets()

    update_arrivals_calendar(start=start, end=end)
    send_management_updates_emails(start=start, end=end)
    send_management_cleans_emails(start=start, end=end)
    send_management_arrivals_emails(start=start, end=end)
    send_airport_transfers_request_emails(start=start, end=end)
    
    if option == 1:
        update_bookingCom_guest_contacts(start=start, end=end)
        send_guest_four_weeks_emails(start=updatedates.calculate(days=1), end=end)

    send_owner_four_weeks_emails(start=updatedates.calculate(days=1), end=end)
    back_up_database()


if __name__ == '__main__':
    main()