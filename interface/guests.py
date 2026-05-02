from default.booking.booking import Booking
from default.guest.guest import Guest
from default.updates.functions import (
    clean_has_changed,
    guest_numbers_have_changed,
    meet_greet_has_changed,
)
from forms.arrival.functions import reset_arrival_form
from forms.arrival.guest.functions import set_guest_arrival_form
from interface.functions import (
    get_bool,
    get_int,
    get_text,
    open_PIMS,
    should_update_PIMS,
)
from interfaces.interface import Interface
from translator.deepl import Deepl

def update_guests(subsection: Interface, databaseBooking: Booking, updatedBooking: Booking) -> None:
    """
    Update guest details for a booking.
    
    Presents a menu of guest detail options that can be modified and processes
    the user's selection. Updates both the database and updated booking objects
    accordingly.
    
    Parameters:
        subsection: Interface object for user interaction
        databaseBooking: Original booking data from the database
        updatedBooking: Copy of booking to track changes
    
    Returns:
        None if user exits, otherwise recursively continues updating
    """
    subsection.section('Updating owner/guest details for selected booking')
    
    details = [
        'Lead Guest Contact Details',
        'Lead Guest Registration Details',
        'Group Composition',
        'Reset Guest',
        'Owner Details',
    ]
    
    detail = subsection.option(details)

    if detail is None:
        return None

    elif detail == 1:
        update_lead_guest_basic_details(subsection, databaseBooking)
    elif detail == 2:
        update_lead_guest_registration_details(subsection, databaseBooking)
    elif detail == 3:
        update_group(subsection, databaseBooking, updatedBooking)
    elif detail == 4:
        reset_guest(subsection, databaseBooking)
    elif detail == 5:
        update_owner(subsection, databaseBooking, updatedBooking)

    databaseBooking.update()
    return update_guests(subsection, databaseBooking, updatedBooking)


def update_lead_guest_basic_details(subsection: Interface, booking: Booking) -> None:
    """
    Update lead guest details for a booking.
    
    Collects updated information for the lead guest including name, contact
    details, and identification. Updates both the database and PIMS if applicable.
    
    Parameters:
        subsection: Interface object for user interaction
        booking: Booking object to update
    
    Returns:
        None
    """
    firstName = booking.guest.firstName
    firstNameAnswer = get_text(subsection, 'First Name', firstName)
    
    lastName = booking.guest.lastName
    lastNameAnswer = get_text(subsection, 'Last Name', lastName)
    
    email = booking.guest.email
    emailAnswer = get_text(subsection, 'Email', email)
    
    phone = booking.guest.phone
    phoneAnswer = get_text(subsection, 'Phone', phone)

    originalLanguage = booking.guest.preferredLanguage
    while True:
        languageAnswer = get_text(subsection, 'Preferred Language', originalLanguage)
        if languageAnswer in (None, originalLanguage):
            break
        try:
            Deepl.langExists(languageAnswer)
            subsection.log('Checking language answer...')
            break
        except ValueError:
            subsection.log('ERROR: THE GIVEN LANGUAGE DOES NOT EXIST...')
            Deepl.print(subsection)

    booking.guest.firstName = firstNameAnswer
    booking.guest.lastName = lastNameAnswer
    booking.guest.email = emailAnswer
    booking.guest.phone = phoneAnswer
    booking.guest.preferredLanguage = languageAnswer
    booking.update()

    if originalLanguage != languageAnswer:
        if not booking.arrival.hasDetails:
            if booking.forms.arrivalQuestionnaire:
                subsection.log('Resetting arrival form for booking with new language...')
                reset_arrival_form(booking, set_guest_arrival_form)

    if not should_update_PIMS(booking):
        return None
        
    browser = open_PIMS(booking)
        
    browser.firstName = firstNameAnswer
    browser.lastName = lastNameAnswer
    browser.email = emailAnswer
    browser.phone = phoneAnswer
    
    browser.update()
    browser.quit()

    return None

def update_lead_guest_registration_details(subsection: Interface, booking: Booking) -> None:
    """
    Update lead guest registration details for a booking.
    
    Collects updated information for the lead guest's registration including
    identification number and nationality. Updates both the database and PIMS if applicable.

    Parameters:
        subsection: Interface object for user interaction
        booking: Booking object to update

    Returns:
        None
    """
    nif = booking.guest.nifNumber
    nifAnswer = get_text(subsection, 'NIF', nif)

    nationality = booking.guest.nationality
    nationalityAnswer = get_text(subsection, 'Nationality', nationality)

    idCard = booking.guest.idCard
    idCardAnswer = get_text(subsection, 'ID Card', idCard)

    booking.guest.nifNumber = nifAnswer
    booking.guest.nationality = nationalityAnswer
    booking.guest.idCard = idCardAnswer
    booking.guest.update()

    if not nifAnswer or not booking.details.enquirySource == 'Direct':
        return None

    browser = open_PIMS(booking)

    browser.nifNumber = nifAnswer
    browser.nationality = nationalityAnswer

    browser.update()
    browser.quit()

    return None

def update_group(subsection: Interface, databaseBooking: Booking, updatedBooking: Booking) -> None:
    """
    Update group composition for a booking.
    
    Collects updated information about the number of adults, children,
    and babies for the booking group. Updates both the database and updated 
    booking objects accordingly, and PIMS if applicable.
    
    Parameters:
        subsection: Interface object for user interaction
        databaseBooking: Original booking data from the database
        updatedBooking: Copy of booking to track changes
    
    Returns:
        None
    """
    adults = databaseBooking.details.adults
    adultsAnswer = get_int(subsection, 'Adult', adults)
    
    children = databaseBooking.details.children
    childrenAnswer = get_int(subsection, 'Children', children)
    
    babies = databaseBooking.details.babies
    babiesAnswer = get_int(subsection, 'Babies', babies)

    updatedBooking.details.adults = adultsAnswer
    updatedBooking.details.children = childrenAnswer
    updatedBooking.details.babies = babiesAnswer
    updatedBooking.details.manualGuests = True

    if databaseBooking.emails.management:
        guest_numbers_have_changed(databaseBooking, updatedBooking)
    
    databaseBooking.details.adults = adultsAnswer
    databaseBooking.details.children = childrenAnswer
    databaseBooking.details.babies = babiesAnswer
    databaseBooking.details.manualGuests = True
    databaseBooking.update()

    if not should_update_PIMS(databaseBooking):
        return None
    
    browser = open_PIMS(databaseBooking)    
    
    browser.adults = adultsAnswer
    browser.children = childrenAnswer
    browser.babies = babiesAnswer
    
    browser.update()
    browser.quit()

    return None


def reset_guest(subsection: Interface, databaseBooking: Booking) -> None:
    """
    Reset guest information to create a new guest record.
    
    Collects new guest information and creates a new guest record in the
    database, then associates it with the booking.
    
    Parameters:
        subsection: Interface object for user interaction
        databaseBooking: Booking object to associate with new guest
    
    Returns:
        None
    """
    databaseBooking.guest = Guest(databaseBooking._database)
    firstNameAnswer = get_text(subsection, 'First Name', None)
    databaseBooking.guest.firstName = firstNameAnswer

    lastNameAnswer = get_text(subsection, 'Last Name', None)
    databaseBooking.guest.lastName = lastNameAnswer

    emailAnswer = get_text(subsection, 'Email', None)
    databaseBooking.guest.email = emailAnswer
    
    phoneAnswer = get_text(subsection, 'Phone', None)
    databaseBooking.guest.phone = phoneAnswer

    guestId = databaseBooking.guest.insert()
    databaseBooking.details.guestId = guestId
    databaseBooking.update()

    return None


def update_owner(subsection: Interface, databaseBooking: Booking, updatedBooking: Booking) -> None:
    """
    Update owner status and related preferences for a booking.
    
    Changes owner status and associated preferences like clean and meet & greet
    options. Updates both the database and updated booking objects accordingly.
    
    Parameters:
        subsection: Interface object for user interaction
        databaseBooking: Original booking data from the database
        updatedBooking: Copy of booking to track changes
    
    Returns:
        None
    """
    isOwnerAnswer = get_bool(subsection, 'Is this an owner booking?', databaseBooking.details.isOwner)

    if not isOwnerAnswer:
        databaseBooking.details.isOwner = False
        return None
    
    clean = databaseBooking.departure.clean
    cleanAnswer = get_bool(subsection, 'Owner Clean', clean)
    
    meetGreet = databaseBooking.arrival.meetGreet
    meetGreetAnswer = get_bool(subsection, 'Owner Meet & Greet', meetGreet)

    updatedBooking.details.isOwner = isOwnerAnswer
    updatedBooking.departure.clean = cleanAnswer
    updatedBooking.arrival.meetGreet = meetGreetAnswer
    
    if databaseBooking.emails.management:
        if not clean_has_changed(databaseBooking, updatedBooking):
            meet_greet_has_changed(databaseBooking, updatedBooking)

    databaseBooking.details.isOwner = isOwnerAnswer
    databaseBooking.departure.clean = cleanAnswer
    databaseBooking.arrival.meetGreet = meetGreetAnswer

    return None