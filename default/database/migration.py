from bookings.fetch import FetchDatabaseBooking, FetchDatabaseBookings
from bookings.load import DatabaseBooking
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import get_database
from default.guest.guest import Guest
from default.update.wrapper import update


@update
def migrate_bookings() -> str:
    """
    Migrate booking data from an old database format to a new one.
    
    This function fetches all bookings from the old database, creates new
    booking objects in the new database format, and populates them with
    the migrated data.
    
    Returns:
        A message indicating successful migration
    """
    newDatabase = get_database()
    fetcher = FetchDatabaseBookings()
    fetcher.Stays().Selection().Set(all=True)
    fetcher.Extras().Selection().Set(all=True)
    fetcher.Flights().Selection().Set(all=True)
    fetcher.Guests().Selection().Set(all=True)
    fetcher.Forms().Selection().Set(all=True)
    fetcher.Emails().Selection().Set(all=True)
    fetcher.Properties().Selection().Set(['name'])
    fetcher.Owners().Selection().Set(['default_meet_greet', 'default_clean'])
    
    guestsDone = list()
    for loaded in fetcher.Get():
        booking = DatabaseBooking(loaded)
        if not booking.property.name():
            continue
            
        newBooking = Booking(newDatabase)
        bookingId = booking.stay.id()
        guestId = booking.stay.guest_id()
        
        if guestId not in guestsDone: 
            guest = Guest(newDatabase)
            migrate_guest(guest, guestId, booking.guest)
            guestsDone.append(guestId)
            
        migrate_booking_details(newBooking.details, booking.property.name(), booking.stay)
        migrate_booking_arrival(newBooking.arrival, booking)
        migrate_booking_departure(newBooking.departure, booking)
        
        if booking.stay.database_origin() == 'KKLJ':
            newBooking.charges.bookingId = bookingId
            newBooking.charges.insert()
        else:
            migrate_booking_charges(newBooking.charges, bookingId)
            
        migrate_booking_extras(newBooking.extras, bookingId, booking.extras)
        migrate_booking_emails(newBooking.emails, bookingId, booking.emails)
        migrate_booking_forms(newBooking.forms, bookingId, booking.forms)
        
    newDatabase.close()
    return 'Successfully migrated bookings to new database!'


def migrate_guest(guest: Guest, guestId: int, oldGuest) -> None:
    """
    Migrate guest data from old format to new Guest object.
    
    Args:
        guest: The new format Guest object to populate
        guestId: The ID of the guest
        oldGuest: The old format guest data source
    """
    guest.id = guestId
    guest.firstName = oldGuest.first_name()
    guest.lastName = oldGuest.last_name()
    guest.email = oldGuest.email()
    guest.phone = oldGuest.phone()
    guest.idCard = oldGuest.id_card()
    guest.nifNumber = oldGuest.nif_number()
    guest.nationality = oldGuest.nationality()
    guest.insert()


def migrate_booking_details(details, propertyName: str, oldStay) -> None:
    """
    Migrate booking details from old format to new Details object.
    
    Args:
        details: The new format booking details object to populate
        propertyName: The name of the property for this booking
        oldStay: The old format stay data source
    """
    details.id = oldStay.id()
    details.propertyId = propertyName
    details.platformId = oldStay.platform_id()
    details.guestId = oldStay.guest_id()
    
    if oldStay.owner_booking():
        details.isOwner = oldStay.owner_booking()
    else:
        details.isOwner = False
        
    if oldStay.database_origin() == 'KKLJ':
        details.enquirySource = 'KKLJ'
    else:
        details.enquirySource = oldStay.enquiry_source()
        details.PIMSId = oldStay.PIMS_id()
        
    details.enquiryDate = oldStay.enquiry_date()
    details.enquiryStatus = oldStay.enquiry_status()
    
    if oldStay.adults():
        details.adults = oldStay.adults()
    else:
        details.adults = 0
        
    if oldStay.children():
        details.children = oldStay.children()
    else:
        details.children = 0
        
    if oldStay.babies():
        details.babies = oldStay.babies()
    else:
        details.babies = 0    
        
    details.manualGuests = bool(oldStay.manual_guests())
    details.lastUpdated = oldStay.last_updated()
    details.insert()


def migrate_booking_arrival(arrival, booking) -> None:
    """
    Migrate arrival information from old format to new Arrival object.
    
    Args:
        arrival: The new format arrival object to populate
        booking: The old format booking data source
    """
    arrival.bookingId = booking.stay.id()
    arrival.date = booking.stay.arrival_date()
    arrival.flightNumber = booking.flights.inbound_number()
    arrival.isFaro = booking.flights.is_Faro_landing()
    arrival.details = booking.flights.arrival_details()
    arrival.selfCheckIn = booking.flights.self_check_in()
    
    if booking.flights.inbound_time():
        arrival.time = booking.flights.inbound_time()
    else:
        arrival.time = booking.stay.arrival_time()
        
    if booking.stay.owner_booking():
        if booking.stay.owner_meet_greet():
            arrival.meetGreet = booking.stay.owner_meet_greet()
        else:
            arrival.meetGreet = booking.property.owner.default_meet_greet()
    else:
        arrival.meetGreet = True
        
    arrival.manualDate = bool(booking.stay.manual_dates())
    arrival.insert()


def migrate_booking_departure(departure, booking) -> None:
    """
    Migrate departure information from old format to new Departure object.
    
    Args:
        departure: The new format departure object to populate
        booking: The old format booking data source
    """
    departure.bookingId = booking.stay.id()
    departure.date = booking.stay.departure_date()
    departure.flightNumber = booking.flights.outbound_number()
    departure.isFaro = booking.flights.is_Faro_take_off()
    departure.details = booking.flights.departure_details()
    
    if booking.flights.outbound_time():
        departure.time = booking.flights.outbound_time()
    else:
        departure.time = booking.stay.departure_time()
        
    if booking.stay.owner_booking():
        if booking.stay.owner_clean():
            departure.clean = booking.stay.owner_clean()
        else:
            departure.clean = booking.property.owner.default_clean()
    else:
        departure.clean = True
        
    departure.manualDate = bool(booking.stay.manual_dates())
    departure.insert()


def migrate_booking_charges(charges, id: int) -> None:
    """
    Migrate charges information from old format to new Charges object.
    
    Args:
        charges: The new format charges object to populate
        id: The booking ID to fetch charges for
    """
    fetcher = FetchDatabaseBooking(stay_id=id)
    fetcher.Charges().Selection().Set(all=True)
    oldCharges = DatabaseBooking(fetcher.Get()).charges
    
    charges.bookingId = id
    charges.bankTransfer = oldCharges.bank_transfer()
    charges.creditCard = oldCharges.credit_card()
    charges.currency = oldCharges.currency()
    charges.basicRental = oldCharges.basic_rental()
    charges.admin = oldCharges.admin()
    charges.security = oldCharges.security()
    charges.securityMethod = oldCharges.security_method()
    charges.platformFee = oldCharges.platform_fee()
    charges.extraNights = oldCharges.extra_nights()
    charges.manualCharges = bool(oldCharges.manual_charges())
    charges.insert()


def migrate_booking_extras(extras, id: int, oldExtras) -> None:
    """
    Migrate extras information from old format to new Extras object.
    
    Args:
        extras: The new format extras object to populate
        id: The booking ID
        oldExtras: The old format extras data source
    """
    extras.bookingId = id
    extras.cot = bool(oldExtras.cot())
    extras.highChair = bool(oldExtras.high_chair())
    extras.welcomePack = bool(oldExtras.welcome_pack())
    extras.welcomePackModifications = oldExtras.welcome_pack_modifications()
    extras.midStayClean = bool(oldExtras.mid_stay_clean())
    extras.lateCheckout = bool(oldExtras.late_checkout())
    extras.otherRequests = oldExtras.other_requests()
    
    if oldExtras.extra_nights():
        extras.extraNights = int(oldExtras.extra_nights())
    else:
        extras.extraNights = 0
        
    extras.airportTransfers = bool(oldExtras.airport_transfers())
    extras.airportTransferInboundOnly = bool(oldExtras.airport_transfer_inbound_only())
    extras.airportTransferOutboundOnly = bool(oldExtras.airport_transfer_outbound_only())
    extras.childSeats = oldExtras.child_seats()
    extras.excessBaggage = oldExtras.excess_baggage()
    extras.insert()


def migrate_booking_emails(emails, id: int, oldEmails) -> None:
    """
    Migrate emails information from old format to new Emails object.
    
    Args:
        emails: The new format emails object to populate
        id: The booking ID
        oldEmails: The old format emails data source
    """
    emails.bookingId = id
    emails.balancePayment = oldEmails.balance_payment()
    emails.arrivalQuestionnaire = oldEmails.four_weeks()
    emails.securityDepositRequest = oldEmails.security_deposit_request()
    emails.arrivalInformation = oldEmails.joining_instructions()
    emails.checkInInstructions = oldEmails.check_in_information()
    emails.airportTransfers = oldEmails.airport_transfers()
    emails.management = oldEmails.management()
    emails.guestRegistrationForm = oldEmails.guest_registration_form()
    emails.payOwner = oldEmails.pay_owner()
    emails.securityDepositReturn = oldEmails.return_security_deposit()
    emails.finalDaysReminder = oldEmails.final_days_reminder()
    emails.goodbye = oldEmails.goodbye()
    emails.guestRegistrationFormToOwner = oldEmails.guest_registration_form_to_owner()
    emails.paused = oldEmails.pause_emails()
    emails.insert()


def migrate_booking_forms(forms, id: int, oldForms) -> None:
    """
    Migrate forms information from old format to new Forms object.
    
    Args:
        forms: The new format forms object to populate
        id: The booking ID
        oldForms: The old format forms data source
    """
    forms.bookingId = id
    forms.guestRegistrationDone = oldForms.guest_registration_done()
    forms.arrivalQuestionnaire = oldForms.four_weeks()
    forms.PIMSuin = oldForms.PIMS_uin()
    forms.PIMSoid = oldForms.PIMS_oid()
    forms.insert()