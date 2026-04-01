from datetime import date

from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.functions import determine_inbound_transfer
from correspondence.guest.arrival.functions import (
    get_arrival_table_data,
    get_guest_arrival_email_bookings,
    new_guest_arrival_email
)
from correspondence.guest.functions import send_guest_email
from default.google.mail.functions import send_email
from correspondence.internal.functions import new_internal_email
from default.booking.booking import Booking
from default.booking.functions import determine_self_check_in
from default.database.database import Database


# Database query functions
def get_arrival_instructions_bookings(
    database: Database, 
    start: date = None, 
    end: date = None, 
    bookingId: int = None
) -> Database:
    """
    Create database search for bookings needing arrival instructions.
    
    Sets up a comprehensive database search that retrieves all the details
    needed for sending arrival instruction emails to guests.
    
    Args:
        database: The database connection object.
        start: Optional start date for filtering arrivals.
        end: Optional end date for filtering arrivals.
        bookingId: Optional specific booking ID to filter by.
        
    Returns:
        The configured database search object ready to execute.
    """
    search = get_guest_arrival_email_bookings(database, start, end, bookingId)
    
    # Select details from the bookings table
    select = search.details.select()
    select.adults()
    select.children()
    select.babies()

    # Select guest details
    select = search.guests.select()
    select.phone()

    # Select manager details
    select = search.propertyManagers.select()
    select.liaison()
    select.liaisonPhone()
    select.liaisonEmail()
    select.maintenance()
    select.maintenancePhone()
    select.cleaning()
    select.cleaningEmail()
    
    # Select property details
    select = search.properties.select()
    select.weClean()

    select = search.propertyOwners.select()
    select.name()
    select.email()
    
    # Select arrival questionnaire from forms and emails
    select = search.forms.select()
    select.arrivalQuestionnaire()
    
    select = search.emails.select()
    select.arrivalQuestionnaire()
    select.securityDepositRequest()

    select = search.charges.select()
    select.extraNights()
    select.currency()
    
    # Select all extras, arrivals, departures, and addresses
    search.extras.select().all()
    search.arrivals.select().all()
    search.departures.select().all()
    search.propertyAddresses.select().all()
    
    return search


def get_changeover_bookings(
    database: Database, 
    date: date = None, 
    guestId: int = None
) -> list[Booking]:
    """
    Retrieve bookings for a specific date and guest for changeover.
    
    Args:
        database: The database connection object.
        date: The specific departure date to filter by.
        guestId: The specific guest ID to filter by.
        
    Returns:
        List of Booking objects matching the criteria.
    """
    search = get_arrival_instructions_bookings(database)
    where = search.departures.where()
    where.date().isEqualTo(date)
    where = search.details.where()
    where.guestId().isEqualTo(guestId)
    return search.fetchall()


def determine_owner_booking_with_transfers(booking: Booking) -> bool:
    """
    Determine if an owner booking should not receive an email but has transfers.
    
    Args:
        booking: The booking object to check.
        
    Returns:
        True if the booking is an owner booking with transfers, False otherwise.
    """
    if booking.details.isOwner:
        if booking.extras.airportTransfers:
            return True
        if booking.extras.airportTransferInboundOnly:
            return True
    return False


# Email composition and sending functions
def send_new_arrival_instructions_email(
    account: GoogleMailMessages = None, 
    topic: str = None,
    booking: Booking = None, 
    bookingId: int = None, 
    twoWeeks: bool = True
) -> None:
    """
    Compose and send arrival instructions email to guest.
    
    Creates an email with comprehensive arrival instructions tailored to the
    booking details, including transport options, check-in procedures, and
    property access information.
    
    Args:
        account: Optional specific email account to use.
        topic: Email subject.
        booking: The booking object containing guest and property information.
        bookingId: Optional booking ID for tracking purposes.
        twoWeeks: Whether the email is sent two weeks before arrival (affects wording).
        
    Returns:
        None
    """
    user, message = new_guest_arrival_email(account=account, topic=topic, booking=booking)
    body = message.body

    if not booking.guest.email:
        if determine_inbound_transfer(booking):
            message.to = booking.property.owner.email
            subject = message.subject
            message.subject = f'SEND TO GUEST: {subject}'
        else:
            raise Exception(
                'FATAL: trying to send email to guest with no email address')

    _opening(body, booking, twoWeeks)
    _please_read(body)
    _we_have(body)
    _table(body, booking)
    check_discrepancies(body, twoWeeks)

    if not determine_inbound_transfer(booking):
        _own_transport(body)    
        _address(body, booking)
        _directions(body, booking)
    else:
        _airport_transfer_0(body, booking)
        _airport_transfer_1(body)
        _airport_transfer_2(body)
        _airport_transfer_3(body)
        _address(body, booking)

    if booking.arrival.meetGreet:
        if determine_self_check_in(booking):
            if not twoWeeks and booking.property.isQuintaDaBarracuda:
                send_check_in_teams_email(booking)
            if booking.arrival.isLate:
                _late_arrival_1(body)
            _late_arrival_2(body, booking)
            _late_arrival_3(body, booking)
            _late_arrival_4(body)
        else:
            _on_arrival(body, twoWeeks)
            if not determine_inbound_transfer(booking):
                _contact_team(body, booking, twoWeeks)
    
            _talk_with_team(body, twoWeeks)

        if _determine_if_property_has_luggage_storage(booking) and twoWeeks:
            _last_day_access(body)
        
        if not determine_self_check_in(booking):
            _extras_payments(body)
   
    _during_stay(body, booking)

    if booking.property.isParqueDaCorcovada:
        _pool_area_invigilator(body)
   
    cornerShop = booking.property.address.nearestCornerShop
    if cornerShop:
        body.paragraph(cornerShop)
   
    supermarket = booking.property.address.nearestSupermarket
    if supermarket:
        body.paragraph(supermarket)
   
    _useful_tips(body)
    _book_trips(body)
    closing(body)
    _fabulous_holiday(body)

    send_guest_email(user, message, bookingId)
    return None
    
    
# Email content functions - opening and introduction
def _opening(body: GoogleMailMessage.Body, booking: Booking, twoWeeks: bool = True) -> None:
    """
    Add opening paragraph to the email based on timing.
    
    Args:
        body: The email body object to modify.
        booking: The booking containing arrival information.
        twoWeeks: Whether email is sent two weeks before arrival.
        
    Returns:
        None
    """
    if twoWeeks:
        body.paragraph(
            'I guess that you must be looking forward to your holiday now!'
        )
    else:
        body.paragraph(
            'This is the Algarve Beach Apartments Team. We will be checking you into',
            f'the apartment on {booking.arrival.prettyDate}'
        )


def _please_read(body: GoogleMailMessage.Body) -> None:
    """
    Add instruction to read the email carefully.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Please read this email carefully; it contains a lot of important and useful',
        'information.',
        bold=True
    )


def _we_have(body: GoogleMailMessage.Body) -> None:
    """
    Add introduction for the booking details section.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph('We have your holiday for:')


def _table(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add booking details table to the email.
    
    Args:
        body: The email body object to modify.
        booking: The booking containing details for the table.
        
    Returns:
        None
    """
    body.table(get_arrival_table_data(booking))


def check_discrepancies(body: GoogleMailMessage.Body, twoWeeks: bool = True) -> None:
    """
    Add instructions for checking and reporting discrepancies in booking details.
    
    Args:
        body: The email body object to modify.
        twoWeeks: Whether email is sent two weeks before arrival.
        
    Returns:
        None
    """
    if twoWeeks:    
        body.paragraph(
            '*Contact me as soon as possible about any missing details or visible',
            'discrepancies.*'
        )
    else:
        body.paragraph(
            'If you find any discrepancies in these details, contact me as soon as',
            'possible.'
        )


# Location and directions information
def _address(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add property address and location information to the email.
    
    Args:
        body: The email body object to modify.
        booking: The booking containing property address information.
        
    Returns:
        None
    """
    body.paragraph(
        f'The address of the apartment is {booking.property.address.street}.',
        f'The GPS coordinates for precise location are',
        f'<b>{booking.property.address.coordinates}</b>.',
        f'And here is a link to Google Maps: {booking.property.address.map}'
    )


def _directions(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add driving directions to the property.
    
    Args:
        body: The email body object to modify.
        booking: The booking containing property address information.
        
    Returns:
        None
    """
    if booking.property.address.directions:
        body.paragraph(booking.property.address.directions)


# Transportation information
def _own_transport(body: GoogleMailMessage.Body) -> None:    
    """
    Add section header for guests using their own transportation.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'I understand that you will be using your own transport to reach the',
        'accommodation:',
        underlined=True
    )


def _airport_transfer_0(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add section header for airport transfer information.
    
    Args:
        body: The email body object to modify.
        booking: The booking containing transfer information.
        
    Returns:
        None
    """
    if booking.extras.airportTransfers:
        body.paragraph(
            'Airport transfers have been arranged for you:',
            underlined=True
        )
    else:
        body.paragraph(
            'An airport transfer has been arranged for you:',
            underlined=True
        )


def _airport_transfer_1(body: GoogleMailMessage.Body) -> None:    
    """
    Add information about meeting the transfer driver at the airport.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'After you leave Baggage Reclaim, pass through Customs, and enter the',
        'Arrivals Hall, on your left-hand side you will see a row of travel company',
        'stands and representatives. Your driver will be waiting next to \'Café',
        'Central\' with your name displayed on a board. In the unlikely event you',
        'don\'t see your driver, you may contact Nick <b>(+351) 933 059 171</b>.'
    )


def _airport_transfer_2(body: GoogleMailMessage.Body) -> None:    
    """
    Add information about flight delays and transfer driver expectations.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        '<u>The transfer driver will be aware of your flight details and know of any',
        'unexpected changes to the scheduled landing time. You do not need to worry',
        'about this, the driver will still be there to meet you.</u>'
    )


def _airport_transfer_3(body: GoogleMailMessage.Body) -> None:    
    """
    Add information about payment for airport transfers.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Once you arrive at the accommodation, you should pay the driver in cash for',
        'the cost of the transfer. If you are getting a return transfer, the driver',
        'will ask that the cost of that be paid at this time also. Unfortunately,',
        'the driver will not be able to accept card payments. This is also the time',
        'to discuss the return transfer arrangements, if applicable. Standard procedure',
        'is to collect you 2 hours and 45 minutes before your scheduled take-off time.',
    )


# Check-in and key information
def _on_arrival(body: GoogleMailMessage.Body, twoWeeks: bool = True) -> None:
    """
    Add information about the check-in process with property management.
    
    Args:
        body: The email body object to modify.
        twoWeeks: Whether email is sent two weeks before arrival.
        
    Returns:
        None
    """
    if twoWeeks:
        body.paragraph(
            'On arrival day someone from the <u>Property Management Team</u> will be',
            'at the complex to show you around, take you to the apartment, hand over',
            'keys and provide all of the information needed to get your holiday off',
            'to the best possible start.'
        )
    else:
        body.paragraph(
            'As you arrive, we will be at the complex to show you around, take you',
            'to the apartment, hand over keys and provide all of the information',
            'needed to get your holiday off to the best possible start. Please be',
            'aware that whilst we do all that we can to avoid making you wait at',
            'this juncture, on the busiest days it may take us a few minutes longer',
            'to reach you.'
        )


def _contact_team(body: GoogleMailMessage.Body, booking: Booking, twoWeeks: bool) -> None:
    """
    Add instructions for contacting the management team on arrival.
    
    Args:
        body: The email body object to modify.
        booking: The booking containing manager contact information.
        twoWeeks: Whether email is sent two weeks before arrival.
        
    Returns:
        None
    """
    subjectPronoun = 'They' if twoWeeks else 'We'
    objectPronoun = 'them' if twoWeeks else 'us'
    body.paragraph(
        f'You will need to ring {objectPronoun} on {booking.property.manager.liaisonPhone}',
        f'(WhatsApp or regular network call) to let {objectPronoun} know that you are on',
        f'your way. {subjectPronoun} are not based at the property, so notice is needed',
        'to coordinate your arrival. Please call this number once you leave Faro airport',
        'or, if coming from another location, 40 minutes prior to your ETA.',
        bold=True
    )


def _talk_with_team(body: GoogleMailMessage.Body, twoWeeks: bool) -> None:
    """
    Add information about check-in/check-out times.
    
    Args:
        body: The email body object to modify.
        twoWeeks: Whether email is sent two weeks before arrival.
        
    Returns:
        None
    """
    objectPronoun = 'them' if twoWeeks else 'us'
    body.paragraph(
        f'Please confirm with {objectPronoun} the time that the apartment must be',
        'vacated on departure day. <u>Standard check-in is 14:00 and check-out 10:00</u> -',
        'though we will be able to check you in as soon as you arrive in Albufeira',
        'and let you check out later on departure day if given enough notice.'
    )


def _late_arrival_1(body: GoogleMailMessage.Body) -> None:
    """
    Add introduction to self check-in instructions for late arrivals.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'As you are arriving late on the day of your check-in, and to avoid making',
        'you pay a €20.00 surcharge, <b>I am giving you instructions to access the',
        'apartment via the Key Box method</b>.'
    )


def _late_arrival_2(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add general building entry instructions for late arrivals.
    
    Args:
        body: The email body object to modify.
        booking: The booking containing property information.
        
    Returns:
        None
    """
    if booking.property.isQuintaDaBarracuda:
        body.paragraph(
            'As you arrive at the main gate into the condominium, please look to',
            'your right where you will see the postboxes for the apartments. Look',
            'for the one labeled B31. There will be two key boxes inside.'
        )
    else:
        body.paragraph(
            '<u>The code to enter the building is 9999</u>. As you enter the main door,',
            'turn right and go through the hallway. You will quickly see some stairs.'
        )


def _late_arrival_3(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add property-specific key box instructions based on apartment.
    
    Args:
        body: The email body object to modify.
        booking: The booking containing property information.
        
    Returns:
        None
    """
    if booking.property.isQuintaDaBarracuda:
       
        if '1' in booking.arrival.selfCheckIn:
            _body = 'The keys will be in the Key Box labeled 1. ' \
                    'The code to open it is 5377.'
        else:
            _body = 'The keys will be in the Key Box labeled 2. ' \
                    'The code to open it is 5388.'
        body.paragraph(
            _body,
            'Once you have the keys, either use the blue fob to open the pedestrian',
            'gate or press the A button on the electronic controller to open the vehicle',
            'gate. Go in and proceed until you reach the building, approx. 50 metres.',
            'There are two entrances into the building and the main lobby is through',
            'the glass doors further to the left.'
        )
        
        propName = booking.property.shortName
        side, floor, door = propName
        body.paragraph(
            'Head through the glass doors into the main lobby, turn', 
            f'{"left" if side in ("A", "B") else "right"} towards the elevators which',
            'you will see after walking about 20 metres. Press the button for floor', 
            f'{floor} and go up. Come out of the elevator and turn', 
            f'{"right" if side in ("A", "D") else "left"}. Walk along the',
            f'corridor until you reach the door to your apartment, {propName}.',
        )
        return
   
    if booking.property.shortName == 'MON 2':
        body.paragraph(
            'Go down the stairs. At the bottom, bear right into a corridor and follow',
            'it until the end. Your apartment is number 2. It will be on your right.',
            'There is a Master Lock key holder by the door. <u>The code is 4332</u>.',
            'The key will be inside.'
        )   
    elif booking.property.shortName == 'MON 4':        
        body.paragraph(        
            'Go down the stairs. At the bottom, bear left making a U-shaped turn and',
            'follow until the end. Your apartment is number 4. It will be on your',
            'right. There is a Master Lock key holder by the door. <u>The code is',
            '0404</u>. The key will be inside.'
        )
    elif booking.property.shortName == 'MON 8':        
        body.paragraph(        
            'Go past them by bearing right. You will see a couple of vending machines.',
            'Just beyond them you will see some apartment doors. Your apartment is',
            'number 8. It will be on your left-hand side. There is a Master Lock key',
            'holder by the door. <u>The code is 5443</u>. The key will be inside.'
        )    
    elif booking.property.shortName == 'MON T':        
        body.paragraph(        
            'Go up the stairs and turn left. You will see a fountain and some more',
            'stairs. Head towards the fountain and, as you face it, you will see',
            'apartment T in the corner just to the left. There is a Master Lock key',
            'holder by the door. <u>The code is 1414</u>. The key will be inside.'
        )
    elif booking.property.shortName in ('MON AA', 'MON AB'):
        propName = booking.property.shortName.split()[1]  # Extract 'AA' or 'AB'
        body.paragraph(        
            'Go up the stairs and turn left. You will see a fountain and some more',
            f'stairs. Go up those stairs as well and then look for apartment {propName}.',
            'It will be on your left. There is a Master Lock key holder by the door.',
            f'<u>The code is {"7665" if propName == "AA" else None}</u>. The key',
            'will be inside.'
        )    
    elif booking.property.shortName == 'MON AE':        
        body.paragraph(        
            'Go up the stairs and turn left. You will see a fountain and some more',
            'stairs. Go up those stairs as well and then look for your apartment AE.',
            'It will be on your right. There is a Master Lock key holder by the door.',
            '<u>The code is 6554</u>. The key will be inside. When unlocking the door,',
            'you may find it is a little rigid, so try pulling the handle towards you.'
        )
    elif booking.property.shortName == 'MON 19':        
        body.paragraph(        
            'Go up the stairs and turn left. You will see a fountain and some more',
            'stairs. Go up those stairs as well and then look for apartment 19.',
            'It will be on your right. There is a Master Lock key holder by the door.',
            '<u>The code is 1919</u>. The key will be inside. When unlocking the door,',
            'you may find it is a little rigid, so try pulling the handle towards you.'
        )
    
    body.paragraph(
        'Once you have unlocked the door, please remember to put the key back in the',
        'Master Lock key holder. You will have another 2 sets of keys waiting for you',
        'on the dining table.'    
    )


def _late_arrival_4(body: GoogleMailMessage.Body) -> None:
    """
    Add information about follow-up meeting after self check-in.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(        
        'Someone from the <u>Property Management Team</u> will be there to meet you',
        'at the apartment at <b>10:00 the following day</b>. They will be able to',
        'give you a more complete overview of the accommodation and answer any',
        'questions that may have arisen since your arrival. This will also be the',
        'time to pay (in cash only) the cost of any optional extras you have',
        'requested, i.e., Welcome Pack, Cot and/or High Chair.'
    )
        

# Additional facility information
def _last_day_access(body: GoogleMailMessage.Body) -> None:
    """
    Add information about access to facilities on the last day.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'There is space to store cases if needed. And special access to the general',
        'facilities, including the pool and communal showers, can be provided on the',
        'final day in cases where a later check-out is not possible.'    
    )


def _extras_payments(body: GoogleMailMessage.Body) -> None:
    """
    Add information about late check-in fees and payment for extras.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Note that there is a €20.00 fee for check-ins after 20:00 (flights landing',
        '18:00 and later). This should be paid during the check-in stage, as well as',
        'the cost of any optional extras you have requested.'    
    )


# Stay information and closing
def _during_stay(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add information about who to contact during the stay.
    
    Args:
        body: The email body object to modify.
        booking: The booking containing manager contact information.
        
    Returns:
        None
    """
    body.paragraph(
        f'During your stay, {booking.property.manager.maintenance}',
        f'({booking.property.manager.maintenancePhone}) is your first point of',
        'contact should you experience any problems or have unresolved questions',
        'about the accommodation.',   
        bold=True
    )


# Stay information and closing
def _pool_area_invigilator(body: GoogleMailMessage.Body) -> None:
    """
    Add note about the pool area invigilator at Corcovada 39.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'Please note that there is a pool area invigilator who may ask you to',
        'identify yourselves at some point during the stay. Please oblige them',
        'as they are there for everyone\'s safety and to ensure all present have',
        'the right to use the facilities. Simply let him know which apartment you',
        'are staying in: 2B.'
    )


def _useful_tips(body: GoogleMailMessage.Body) -> None:    
    """
    Add information about the information booklet in the apartment.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'When you settle into the apartment, please take the chance to read the',
        'important <i>Information Booklet and Useful Tips</i> for even more details',
        'about the apartment and the surrounding area. You will find it on the',
        'dining room table.'    
    )


def _book_trips(body: GoogleMailMessage.Body) -> None:
    """
    Add information about booking trips and excursions.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'If you are interested in booking day trips or short excursions, such as city, boat,',
        'or wine tours, golf outings, dining experiences, tailored evenings, outdoor activities',
        'like hikes, horse-riding, or something even more adventurous, please contact our',
        'excellent partner ShhAlgarve who will be able to assist you from start to finish:',
        'joanna@shhalgarve.com'
    )


def closing(body: GoogleMailMessage.Body) -> None:
    """
    Add final paragraph before sign-off.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph(
        'That is all I have to share for now. Do get back to me if you have any',
        'questions.'
    )


def _fabulous_holiday(body: GoogleMailMessage.Body) -> None:
    """
    Add final sign-off wish.
    
    Args:
        body: The email body object to modify.
        
    Returns:
        None
    """
    body.paragraph('Have a fabulous holiday!')


def send_check_in_teams_email(booking: Booking) -> None:
    """
    Send a Teams message to the property management team for check-in.
    
    Args:
        booking: The booking object containing property and guest information.
        
    Returns:
        None
    """
    subject = f'Self-Check-in for {booking.guest.name} to ' \
              f'{booking.property.shortName} on {booking.arrival.prettyDate}'
    user, message = new_internal_email(
                                    to=booking.property.manager.liaisonEmail, 
                                    name=booking.property.manager.liaison,
                                    subject=subject)
    body = message.body

    body.paragraph(
        f'{booking.guest.name} going into {booking.property.shortName} on',
        f'{booking.arrival.prettyDate} will be using {booking.arrival.selfCheckIn}.',
        bold=True
    )
    body.paragraph(
        'Please ensure that the keys are in the Key Box. The booking is showing on',
        'the calendar for a next day meet and greet at 10:00.'
    )
    
    send_email(user, message)


def _determine_if_property_has_luggage_storage(booking: Booking) -> bool:
    if booking.property.isQuintaDaBarracuda:
        return True
    if booking.property.isClubeDoMonaco:
        return True
    return False