import datetime
from os import name
import re
from PIMS.browser import BrowsePIMS
from dates import dates
from default.booking.functions import logbooking
from default.database.functions import get_database, search_valid_bookings
from default.property.property import Property
from utils import log, sublog, superlog
from default.google.mail.functions import new_email, send_email, get_inbox, get_sent
from default.settings import DEFAULT_ACCOUNT, LOCAL_STORAGE_DIR


def date(days=0, year=None, month=None, day=None):
    if year: 
        return dates.date(year, month, day)
    return dates.calculate(days=days)


from default.update.wrapper import pull_database
@pull_database
def main(pullDatabase=False):
    pass



    ### DO SOMETHINGS ###
    
    #do_something_in_database()
    #add_column_to_database_table()
    #do_something()
    #from default.whatsapp.functions import send_whatsapp_test_message
    #send_whatsapp_test_message('login attempt successful')
    #change_prices_in_database()
    #test_html_parsing()



    ##### BACKUPS & CACHE #####

    #from backup.programming.run import back_up_programming_files
    #back_up_programming_files()

    #from cache.clear import clear_cache_and_conflicts
    #clear_cache_and_conflicts()

    #from backup.delete.run import delete_old_backups
    #delete_old_backups()



    ##### PLATFORMS #####
    
    #from platforms.airbnb.download import update_from_airbnb
    #update_from_airbnb()#start=date(year=2026, month=5, day=17), end=date(year=2026, month=5, day=18))
#
    #from platforms.vrbo.download import update_from_vrbo
    #update_from_vrbo()#start=date(year=2026, month=7, day=16), end=date(year=2026, month=7, day=16))

    #from platforms.bookingCom.download import update_from_bookingCom
    #update_from_bookingCom()#start=date(year=2026, month=5, day=15), end=date(year=2026, month=5, day=15), properties=['Clube do Monaco'])
    
    #from platforms.bookingCom.contacts import update_bookingCom_guest_contacts
    #update_bookingCom_guest_contacts()

    #from platforms.airbnb.review import review_airbnb_guests
    #review_airbnb_guests()

    #from platforms.functions import notify_platform_bookings_without_PIMS_ID
    #notify_platform_bookings_without_PIMS_ID()



    ##### FORMS #####
    
    #from forms.arrival.guest.run import update_from_guest_arrival_forms
    #update_from_guest_arrival_forms()

    #from forms.arrival.owner.run import update_from_owner_arrival_forms
    #update_from_owner_arrival_forms()

    from forms.registration.run import update_from_guest_registrations
    update_from_guest_registrations()
    
    #from forms.arrival.guest.run import delete_old_guest_arrival_forms
    #delete_old_guest_arrival_forms()
    
    #from forms.arrival.owner.run import delete_old_owner_arrival_forms
    #delete_old_owner_arrival_forms()

    #from forms.registration.complete import complete_empty_guest_details
    #complete_empty_guest_details()



    ##### PIMS #####

    #from PIMS.download import download_latest_from_PIMS
    #download_latest_from_PIMS(visible=True)#start=date(year=2026, month=1, day=1), end=date(year=2026, month=6, day=30), visible=True, updatedSince=360)

    #from PIMS.upload import update_PIMS_platform_bookings
    #update_PIMS_platform_bookings(visible=True)
    
    #from PIMS.clean import delete_cancelled_platform_bookings_in_PIMS
    #delete_cancelled_platform_bookings_in_PIMS(start=date(year=2022, month=5, day=1), end=date(year=2024, month=12, day=31), visible=True)



    ##### SHEETS #####
    
    #from sheets.ABA.run import update_ABA_properties_sheets
    #update_ABA_properties_sheets(propertyNames=['MON 2'])

    #from sheets.KKLJ.run import update_KKLJ_properties_sheets
    #update_KKLJ_properties_sheets(propertyName='B22')



    ##### ACCOUNTANCY #####

    #from payments.run import update_payments_to_owner_workbooks
    #update_payments_to_owner_workbooks()

    #from accountants.generic.run import update_generic_accounts_reports_workbooks
    #update_generic_accounts_reports_workbooks(
    #    'PNM - Consultadoria, Lda',
    #    start=date(year=2025, month=10, day=1),
    #    end=date(year=2025, month=10, day=31),
    #    #'GRACIETE GRACE - Contabilidade e Consultoria, Lda', 
    #    direct=False
    #)

    #from accountants.ptag.run import update_ptag_workbooks
    #update_ptag_workbooks()
    
    #from accountants.harmonious_jungle.run import update_harmonious_jungle_workbooks
    #update_harmonious_jungle_workbooks(start=date(year=2025, month=11, day=1), end=date(year=2025, month=11, day=30))

    #from accountants.edgered.run import update_edgered_workbooks
    #update_edgered_workbooks(start=date(year=2025, month=1, day=1), end=date(year=2025, month=1, day=31))
    
    #from accountants.internal.run import update_internal_accountant_workbooks
    #update_internal_accountant_workbooks()
    
    #from commissions.run import update_commissions_breakdown_workbooks
    #update_commissions_breakdown_workbooks(start=date(year=2025, month=1, day=1), end=date(year=2025, month=1, day=31))
    
    #from correspondence.internal.management.realco.run import send_realco_email
    #send_realco_email()
    
    #from correspondence.internal.accountancy.security_deposits.run import send_security_deposit_returns_email
    #send_security_deposit_returns_email()
    
    #from correspondence.internal.accountancy.payments_to_owners.run import send_payments_to_owners_email
    #send_payments_to_owners_email()
    
    #from reports.internal.run import update_end_of_month_internal_report
    #update_end_of_month_internal_report(sendEmail=False)
    
    #from reports.owner.run import update_bookings_reports_workbooks
    #update_bookings_reports_workbooks()

    #from accountants.edgered.run import calculate_owners_totals_over_period
    #calculate_owners_totals_over_period(start=date(year=2025, month=7, day=1), end=date(year=2025, month=9, day=30))

    #from prices.run import update_prices_for_year
    #update_prices_for_year()

    #from prices.run import email_owners_with_new_prices
    #email_owners_with_new_prices(year=2026)

    #from prices.run import update_a_price
    #update_a_price(
    #    name='QdB6', 
    #    year=2026, 
    #    january=1290,
    #    february=1290,
    #    march=1290,
    #    april=1370,
    #    may=1725,
    #    june=2250,
    #    july=2800,
    #    august=2800,
    #    september=1900,
    #    october=1370,
    #    november=1290,
    #    december=1290,
    #    festive=1290,
    #    earlyWinterMonthlyRate=3000,
    #    lateWinterMonthlyRate=3400,
    #)
    #from prices.run import set_price_tables
    #set_price_tables(year=2025)



    ##### MANAGEMENT #####
    
    #from arrivals.run import update_arrivals_calendar
    #update_arrivals_calendar()

    #from correspondence.internal.management.cleans.run import send_management_cleans_emails
    #send_management_cleans_emails()

    #from correspondence.internal.management.updates.run import send_management_updates_emails
    #send_management_updates_emails(start=date(days=-3), end=date(days=0))

    #from correspondence.internal.management.arrivals.run import send_management_arrivals_emails
    #send_management_arrivals_emails(start=date(1), end=date(183))

    #from correspondence.internal.management.transfers.run import send_airport_transfers_request_emails
    #send_airport_transfers_request_emails()



    ## GUEST/OWNER EMAILS

    #from correspondence.guest.arrival.instructions.two_days.run import send_two_days_instructions_emails
    #send_two_days_instructions_emails()

    #from correspondence.owner.details_prompting.run import send_arrival_details_prompting_emails
    #send_arrival_details_prompting_emails()
    
    #from correspondence.guest.arrival.registration.run import send_guest_registration_emails
    #send_guest_registration_emails(emailSent=True)
    
    #from correspondence.guest.arrival.instructions.two_weeks.run import send_two_weeks_instructions_emails
    #send_two_weeks_instructions_emails()#start=date(1), end=date(12))
    
    #from correspondence.guest.arrival.security_deposit.run import send_security_deposit_request_emails
    #send_security_deposit_request_emails()#bookingId=3987)

    #from correspondence.guest.arrival.four_weeks.run import send_guest_four_weeks_emails
    #send_guest_four_weeks_emails()
    
    #from correspondence.owner.four_weeks.run import send_owner_four_weeks_emails
    #send_owner_four_weeks_emails()
    
    #from correspondence.guest.arrival.balance_payment.reminder.run import send_balance_payment_emails
    #send_balance_payment_emails()
    
    #from correspondence.guest.departure.goodbye.run import send_goodbye_emails
    #send_goodbye_emails()

    #from correspondence.guest.departure.final_days.run import send_final_day_reminder_emails
    #send_final_day_reminder_emails()

    #from correspondence.guest.departure.outbound_transfer.run import send_outbound_transfer_confirmation_email
    #send_outbound_transfer_confirmation_email()




def test_html_parsing():
    from web.html import HTML
    parser = HTML(open(LOCAL_STORAGE_DIR + '/html/test.html'))
    for property in parser.findAll('ul', {'aria-label': 'Check all details'}):
        titleEl = property.find('button')
        title = re.search(r'\(([A-Z \-0-9]+)\)', titleEl.text).group(1)
        print(title)
        print(property.text)
        occupancy = re.search(r'Booked occupancy ([\d\s,()\w"]+) Max occupancy', property.text).group(1)
        print(occupancy)


def do_something_in_database() -> None:
    from default.database.functions import get_database, search_guests, set_minimum_logging_criteria
    from default.database.functions import get_booking, search_bookings, search_valid_bookings, get_guest
    from interface.source import update_at_source
    from default.settings import PLATFORMS
    from default.database.functions import search_guests

    database = get_database()

    database.cursor.execute('SELECT id, guestId, PIMSId, platformId, enquirySource FROM bookings')
    ids = database.cursor.fetchall()
    PIMSIds = list()
    for id, guestId, PIMSId, platformId, enquirySource in ids:
        guestSearch = get_guest(id=guestId)
        guest = guestSearch.fetchone()
        if not guest:
            superlog(f'Guest with ID {guestId} not found for booking with ID {id}, PIMSId {PIMSId}, platformId {platformId}, enquirySource {enquirySource}')
            if PIMSId:
                PIMSIds.append(PIMSId)
        guestSearch.close()

    if PIMSIds:
        from PIMS.download import download_latest_from_PIMS
        download_latest_from_PIMS(PIMSId=PIMSIds, visible=True)


def change_prices_in_database() -> None:
    from default.database.functions import get_property

    search = get_property(name='C31')

    select = search.propertyPrices.select()
    select.all()

    where = search.propertyPrices.where()
    where.year().isEqualTo(dates.year(1))

    property = search.fetchone()

    from prices.run import new_price_tier
    prices = [property.prices.month(i) + 70 for i in range(1, 14)]
    prices += [property.prices.earlyWinterMonthlyRate]
    prices += [property.prices.lateWinterMonthlyRate]
    
    print(prices)

    new_price_tier(name='C31', prices=prices, propertyNames=['C31'])


def add_column_to_database_table():
    from databases.column import Column
    from databases.table import Table
    from default.database.functions import get_database
    database = get_database()
    table = Table(database=database, name='properties')
    table.add(object=Column(name='vrboId', tablename=table.name, dataType='text'))
    database.close()


def do_something():
    from default.database.functions import set_minimum_logging_criteria
    
    search = search_valid_bookings(
                                start=dates.date(2025, 1, 1), 
                                end=dates.date(2025, 9, 10),
                                propertyName='D02')
    
    set_minimum_logging_criteria(search)

    select = search.charges.select()
    select.basicRental()
    select.currency()

    select = search.propertyOwners.select()
    select.rentalCommissionsAreInvoiced()
    select.wantsAccounting()

    where = search.details.where()
    where.enquirySource().isEqualTo('Direct')

    bookings = search.fetchall()
    search.close()

    from default.booking.functions import determine_commission, determine_commission_after_IVA
    totalCommission = 0.0
    totalAfterIVA = 0.0
    totalDifference = 0.0
    for booking in bookings:
        logbooking(booking)
        commission = determine_commission(booking)
        afterIVA = determine_commission_after_IVA(booking)
        difference = commission - afterIVA
        sublog(f'Commission: €{commission:,.2f} EUR')
        sublog(f'Commission after IVA: €{afterIVA:,.2f} EUR')
        sublog(f'Difference: €{difference:,.2f} EUR')
        totalCommission += commission
        totalAfterIVA += afterIVA
        totalDifference += difference
    log(f'Total Commission: €{totalCommission:,.2f} EUR')
    log(f'Total Commission after IVA: €{totalAfterIVA:,.2f} EUR')
    log(f'Total Difference: €{totalDifference:,.2f} EUR')




def _do_something():
    from accountants.edgered.run import get_properties, get_bookings 
    from default.booking.functions import determine_owner_payment, determine_owner_balance

    properties = get_properties()
    database = get_database()
    result = dict()
    for property in properties:
        if property.shortName in ('MON AA', 'MON T', 'MON 8', 'MON AE'):
            if property.shortName not in result:
                result[property.shortName] = dict()
                bookings = get_bookings(database=database, start=dates.firstOfYear(-1), end=dates.lastOfYear(), propertyName=property.shortName)
                for booking in bookings:
                    year = booking.arrival.year
                    if year < 2024:
                        continue
                    if year not in result[property.shortName]:
                        result[property.shortName][year] = _total_dict()
                    result[property.shortName][year]['Total Paid to Owner after Commission'] += determine_owner_payment(booking)
                    result[property.shortName][year]['Total Paid to Owner after Commission + Cleaning + Meet & Greet Fees'] += determine_owner_balance(booking)


    from correspondence.self.functions import new_email_to_self, send_email_to_self
    user, message = new_email_to_self(
        subject=f'Owner revenue for Sahil Khosla 2024 and 2025',
    )
    body = message.body

    body.paragraph(
        f'As promised, please see below the list of properties and their',
        f'owner income for the period.'
    )

    total2024 = _total_dict()
    total2025 = _total_dict()

    for propName, years in result.items():
        body.section(f'{propName}:')
        for year, totals in years.items():
            body.paragraph(f'Year {year}:')
            if year == 2024:
                yearTot = total2024
            elif year == 2025:
                yearTot = total2025
            for title, value in totals.items():
                if propName == 'MON AA':
                    value = value * .8
                body.paragraph(f'- {title}: €{value:,.2f} EUR', indent=25)
                yearTot[title] += value

    for years, total in (('2024', total2024), ('2025', total2025)):
        body.section(f'Total for {years}:')
        for title, value in total.items():
            body.paragraph(f'- {title}: €{value:,.2f} EUR', indent=25)

    send_email_to_self(user, message)


def _total_dict():
    return {
        'Total Paid to Owner after Commission': 0.0,
        'Total Paid to Owner after Commission + Cleaning + Meet & Greet Fees': 0.0,
    }
    


if __name__ == '__main__':
    from backup.database.run import back_up_database
    back_up_database()
    from interfaces.interface import Interface
    interface = Interface(title='This is the test environment for klt programming management')
    sections = interface.subsections()
    sections.section('Would you like to download and use the cloud Database?')
    pullDatabase = sections.bool()
    main(pullDatabase=pullDatabase)