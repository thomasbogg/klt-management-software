import re
import datetime
from time import sleep

from apis.google.calendars.calendar import GoogleCalendar
from apis.google.calendars.utils import (
    get_google_calendar_events,
    get_google_calendars
)
from default.booking.booking import Booking
from default.booking.functions import (
    determine_meet_greet,
    determine_price_of_extra,
    determine_security_deposit_request,
    determine_self_check_in,
    determine_tourist_tax,
    logbooking
)
from default.database.database import Database
from default.database.functions import (
    get_booking,
    get_database,
    search_bookings,
    set_valid_management_booking
)
from default.dates import dates
from default.guest.functions import guest_has_stayed_before
from default.settings import DEFAULT_ACCOUNT, TEST
from default.update.dates import updatedates
from default.update.wrapper import update
from utils import log, logdivider, logerror


# Main update function
@update
def update_arrivals_calendar(start: datetime.date = None, end: datetime.date = None) -> str:
    """
    Update Google Calendar with arrival and departure events for specified dates.
    
    Args:
        start: The start date for calendar update. If None, uses default update dates.
        end: The end date for calendar update. If None, uses default update dates.
        
    Returns:
        A string indicating successful completion or None if error occurred.
    """
    if start is None and end is None: 
        start, end = updatedates.calendar_update_dates()

    calendar = get_google_calendars(name='INS AND OUTS', account=DEFAULT_ACCOUNT, TEST=TEST)
    if not calendar:
        logerror('Google Calendar connection failed. Cannot update calendar.')
        return None
    
    database: Database = get_database()
    
    logdivider()
    log('1) UPDATING EXISTING EVENTS...')
    events = get_google_calendar_events(calendar, startDate=start, endDate=end)
    existingBookingIds: dict[str, list[int]] = {'arrivals': [], 'departures': []}
    update_existing_events(database, calendar, events, existingBookingIds)
    
    logdivider()
    log('2) INSERTING NEW EVENTS...')
    bookings = get_new_arrivals(database, start, end, existingBookingIds['arrivals'])
    if not bookings: 
        database.close()
        return 'Got NO new bookings to insert in calendar.'
    
    insert_new_events(bookings, calendar, existingBookingIds)
    
    database.close()
    return f'Successfully updated all calendar entries for dates {start} and {end}'


# Event update functions
def update_existing_events(
        database: Database, 
        calendar: GoogleCalendar, 
        events: list[GoogleCalendar.Event], 
        existingBookingIds: dict[str, list[int]]
) -> dict[str, list[int]]:
    """
    Update existing calendar events based on current booking information.
    
    Args:
        database: The database connection.
        calendar: The Google Calendar to update.
        events: List of calendar events to process.
        existingBookingIds: Dictionary tracking processed booking IDs.
        
    Returns:
        Updated dictionary of processed booking IDs.
    """
    if not events: 
        return existingBookingIds

    event: GoogleCalendar.Event = events.pop(0)
    parsed: re.Match | None = parse_event_ids(event)
    if not parsed: 
        return update_existing_events(database, calendar, events, existingBookingIds)
    
    bookingId: int = int(parsed.group(1))
    booking: Booking = get_calendar_booking(database, bookingId)
    if not booking.managementStatusIsOkay:
        logbooking(booking, f'BOOKING no longer valid. DELETING it.')
        event.delete()
        return update_existing_events(database, calendar, events, existingBookingIds)

    if is_arrival_event(parsed):
        if bookingId in existingBookingIds['arrivals']:
            log(f'{event.summary} is duplicate. DELETING it.')
            event.delete()
            return update_existing_events(database, calendar, events, existingBookingIds)
     
        existingBookingIds['arrivals'].append(bookingId)
        set_arrival_event(calendar, event, booking)
    
    elif is_departure_event(parsed):
        if bookingId in existingBookingIds['departures']:
            log(f'{event.summary} is duplicate. DELETING it.')
            event.delete()
            return update_existing_events(database, calendar, events, existingBookingIds)
     
        existingBookingIds['departures'].append(bookingId)
        set_departure_event(calendar, event, booking)
    
    event.update()
    sleep(.2)
    return update_existing_events(database, calendar, events, existingBookingIds)


def insert_new_events(
        bookings: list[Booking], 
        calendar: GoogleCalendar, 
        existingBookingIds: dict[str, list[int]]
) -> None:
    """
    Insert new calendar events for arrivals and departures.
    
    Args:
        bookings: List of bookings to create events for.
        calendar: The Google Calendar to update.
        existingBookingIds: Dictionary tracking processed booking IDs.
    """
    if not bookings:
        return None
   
    booking: Booking = bookings.pop(0)
    set_arrival_event(calendar, calendar.event(), booking, update=False).insert()
    set_departure_event(calendar, calendar.event(), booking, update=False).insert()
    logbooking(booking, 'New arrival/departure events inserted for booking:')
    return insert_new_events(bookings, calendar, existingBookingIds)


# Event setting functions
def set_arrival_event(
        calendar: GoogleCalendar, 
        event: GoogleCalendar.Event, 
        booking: Booking, 
        update: bool = True
) -> GoogleCalendar.Event:
    """
    Configure an event for a guest arrival.
    
    Args:
        calendar: The Google Calendar to update.
        event: The event to configure.
        booking: The booking data to use.
        update: Whether this is an update to an existing event.
        
    Returns:
        The configured event.
    """
    event.summary = get_summary_for_arrival(booking)
    event.description = get_event_description(event, booking, arrival=True, update=update)
    event.location = booking.property.address.street
    eventDate = booking.arrival.date
   
    if determine_self_check_in(booking):
        eventDate = dates.calculate(date=eventDate, days=1)
        eventTime = dates.time(10, 0)
        if booking.property.isQuintaDaBarracuda:
            _set_key_box_reminder_event(calendar, booking)
    elif booking.arrival.timeIsValid:
        eventTime = booking.arrival.eta
    else:
        eventTime = dates.time(14, 0)
  
    if update:
        check_changes_of_dates_times(calendar, event, eventDate, eventTime, arrival=True)
    else:
        set_event_start_and_end(calendar, event, eventDate, eventTime)
   
    event.colorId = get_arrival_colour_id(event, booking)
    event.start.timezone = 'Europe/Lisbon'
    event.end.timezone = 'Europe/Lisbon'
    return event


def set_departure_event(
        calendar: GoogleCalendar, 
        event: GoogleCalendar.Event, 
        booking: Booking, 
        update: bool = True
) -> GoogleCalendar.Event:
    """
    Configure an event for a guest departure.
    
    Args:
        calendar: The Google Calendar to update.
        event: The event to configure.
        booking: The booking data to use.
        update: Whether this is an update to an existing event.
        
    Returns:
        The configured event.
    """
    event.summary = get_summary_for_departure(booking)
    event.description = get_event_description(event, booking, arrival=False, update=update)
    event.location = booking.property.address.street
    eventDate = booking.departure.date
    eventTime = dates.time(4, 0)
 
    if update: 
        check_changes_of_dates_times(calendar, event, eventDate, eventTime, arrival=False)
    else: 
        set_event_start_and_end(calendar, event, eventDate, eventTime)
 
    event.colorId = '11'
    event.start.timezone = 'Europe/Lisbon'
    event.end.timezone = 'Europe/Lisbon'
    return event


def set_event_start_and_end(
        calendar: GoogleCalendar, 
        event: GoogleCalendar.Event, 
        eventDate: datetime.date, 
        eventTime: datetime.time
) -> GoogleCalendar.Event:
    """
    Set the start and end time for a calendar event.
    
    Args:
        calendar: The Google Calendar to update.
        event: The event to configure times for.
        eventDate: The date for the event.
        eventTime: The preferred time for the event.
        
    Returns:
        The configured event.
    """
    event.start.date = eventDate
    bestEventStartTime = get_best_event_time(calendar, eventDate, eventTime) 
    if goes_into_next_day(bestEventStartTime):  
        bestEventStartTime = dates.time(23, 29)

    event.start.time = bestEventStartTime    
    bestEventEndTime = dates.calculate(time=bestEventStartTime, minutes=30)
    event.end.date = eventDate
    event.end.time = bestEventEndTime
    return event


def check_changes_of_dates_times(
        calendar: GoogleCalendar, 
        event: GoogleCalendar.Event, 
        eventDate: datetime.date,
        eventTime: datetime.time, 
        arrival: bool = True
) -> GoogleCalendar.Event | None:
    """
    Check if event date/time needs updating and update if necessary.
    
    Args:
        calendar: The Google Calendar to update.
        event: The event to check.
        eventDate: The date to compare against.
        eventTime: The time to compare against.
        arrival: Whether this is an arrival event.
        
    Returns:
        The updated event or None if no update was needed.
    """
    if eventDate == event.start.date:
        if arrival: 
            if dates.subtractTimes(event.start.time, eventTime) <= 90: 
                return None
        else:
            if dates.subtractTimes(event.start.time, eventTime) <= 180: 
                return None
    
    log(f'EVENT date/time has changed for: {event.summary}')
    return set_event_start_and_end(calendar, event, eventDate, eventTime)


# Event description and summary functions
def get_event_description(
        event: GoogleCalendar.Event, 
        booking: Booking, 
        arrival: bool = True, 
        update: bool = True
) -> str:
    """
    Generate the event description from booking information.
    
    Args:
        event: The event being created/updated.
        booking: The booking data to use.
        arrival: Whether this is an arrival event.
        update: Whether this is an update to an existing event.
        
    Returns:
        The formatted event description string.
    """
    if update: 
        custom = parse_event_custom_description(event.description) 
    else: 
        custom = get_custom_description()    
  
    selfGenerated = get_self_generated_description(booking, arrival)
    return custom + selfGenerated


def get_summary_for_arrival(booking: Booking) -> str:
    """
    Generate the event summary text for an arrival event.
    
    Args:
        booking: The booking data to use.
        
    Returns:
        The formatted event summary string.
    """
    if not booking: 
        return ''
    string: str = booking.property.shortName
   
    if determine_self_check_in(booking):
        eventDate = booking.arrival.date
        details = f'SELF CHECK-IN on {eventDate.day}/{eventDate.month}'
        if booking.arrival.meetGreet:
            details += ': next day meet & greet @ 10.00'
        else:
            details += ': no meet & greet GREET required'
    else:
        details = booking.arrival.prettyDetails
        if 'unk' in details.lower():
            details = 'NO INFO' 

    string += f' - ({details})'
    string += f' - {booking.guest.prettyName}'
    string += f' - {booking.details.prettyGuests}'
    
    if 'Airport Transfer' in booking.extras.arrival:
        string += ' - Airport Transfer'
    else:
        otherDetails: str = booking.arrival.otherPrettyDetails
       
        if otherDetails:
            string += f' - {otherDetails}'
    
    return string


def get_summary_for_departure(booking: Booking) -> str:
    """
    Generate the event summary text for a departure event.
    
    Args:
        booking: The booking data to use.
        
    Returns:
        The formatted event summary string.
    """
    string: str = booking.property.shortName
    details: str = booking.departure.prettyDetails
    
    if 'unk' in details.lower():
        details = 'NO INFO'

    string += f' ({details})'
    string += f' - {booking.guest.prettyName}'
    
    if 'Airport Transfer' in booking.extras.departure:
        string += ' - Airport Transfer'

    return string


def get_custom_description() -> str:
    """
    Generate the standard placeholder for custom event description notes.
    
    Returns:
        The formatted placeholder string.
    """
    string: str = '(type above this line to add custom notes)\n'
    string += '_______________'
    return string


def get_self_generated_description(booking: Booking, arrival: bool = True) -> str:
    """
    Generate the automated part of the event description from booking data.
    
    Args:
        booking: The booking data to use.
        arrival: Whether this is an arrival event.
        
    Returns:
        The formatted description string.
    """
    if not booking: 
        return ''
    string: str = '\n'
    phone: str = booking.guest.phone
    email: str = booking.guest.email
   
    if phone:
        string += f'\n{phone}'
 
    if email:
        string += f'\n{email}'
  
    string += '\n'
 
    if arrival:
        string = get_elements_for_arrival_description(booking, string)
        string += f'\n[{booking.id}][1]'
    else:
        string = get_elements_for_departure_description(booking, string)
        string += f'\n[{booking.id}][0]'

    return string
    
    
def get_elements_for_arrival_description(booking: Booking, string: str) -> str:
    """
    Add arrival-specific elements to the event description.
    
    Args:
        booking: The booking data to use.
        string: The description string being built.
        
    Returns:
        The updated description string.
    """
    if not determine_meet_greet(booking):
        return string
    
    if not determine_self_check_in(booking):
        if booking.arrival.meetGreetIsLate:
            string += '\n- Late Check-in Fee @ €20.00'
    
    elif booking.property.isQuintaDaBarracuda:
        keyBoxNumber = booking.arrival.selfCheckIn
        string += f'\n- Using {keyBoxNumber} for Self Check-in'

    for extra in booking.extras.arrival:
        if 'Airport Transfer' not in extra:
            string += f'\n- {extra}'

            if booking.extras.ownerIsPaying:
                string += ' (owner is paying)'
            else:
                price = determine_price_of_extra(booking, extra)
                if price:
                    string += f' @ €{"{:.2f}".format(price)}'
        
    if determine_security_deposit_request(booking):
        string += f'\n- Security Deposit @ €200.00'
    
    if guest_has_stayed_before(booking):
        string += f'\n- This is a Returning Guest'
    
    if determine_tourist_tax(booking):
        string += f'\n- Mention Tourist Tax to Guest'

    if determine_guest_registration_form_notification(booking):
        string += '\n- Mention Guests Registration Form to Guest'
    
    string += '\n'
    return string


def get_elements_for_departure_description(booking: Booking, string: str) -> str:
    """
    Add departure-specific elements to the event description.
    
    Args:
        booking: The booking data to use.
        string: The description string being built.
        
    Returns:
        The updated description string.
    """
    if booking.extras.lateCheckout:
        string += '\n- Late Check-out'
    string += '\n'
    return string


# Event utility functions
def is_arrival_event(parsed: re.Match) -> bool:
    """
    Determine if an event is an arrival or departure based on its ID.
    
    Args:
        parsed: Parsed regex match containing event type code.
        
    Returns:
        True if arrival event, False otherwise.
    """
    if parsed is None: 
        return False
    return parsed.group(2) == '1'


def is_departure_event(parsed: re.Match) -> bool:
    """
    Determine if an event is a self check-in key box reminder based on its ID.

    Args:
        parsed: Parsed regex match containing event type code.
        
    Returns:
        True if arrival event, False otherwise.
    """
    if parsed is None: 
        return False
    return parsed.group(2) == '0'


def get_arrival_colour_id(event: GoogleCalendar.Event, booking: Booking) -> str:
    """
    Determine the color ID for an arrival event based on meet and greet status.
    
    Args:
        event: The event being created/updated.
        booking: The booking data to use.
        
    Returns:
        The Google Calendar color ID to use.
    """
    currentId = None if not event.has('colorId') else event.colorId
    meetGreet = determine_meet_greet(booking)
    
    if not currentId or currentId == '1': 
        return '10' if meetGreet else '9'
    if meetGreet and currentId == '9': 
        return '10'
    if not meetGreet and currentId == '10': 
        return '9'
   
    return currentId


def parse_event_ids(event: GoogleCalendar.Event) -> re.Match | None:
    """
    Extract booking ID and event type from event description.
    
    Args:
        event: The event to parse.
        
    Returns:
        Regex match containing booking ID and event type, or None if not found.
    """
    if not event.has('description'): 
        return None
    return re.search(r'\[([0-9]+)\]\[([012])\]', event.description)


def parse_event_custom_description(description: str) -> str:
    """
    Extract custom part of description that was manually added.
    
    Args:
        description: The full event description.
        
    Returns:
        The custom portion of the description.
    """
    if description is None: 
        return ''
    return re.search(r'^([\d\W\w\s]+___+)', description).group(1)


def goes_into_next_day(eventTime: datetime.time) -> bool:
    """
    Check if event time is at very end or beginning of day.
    
    Args:
        eventTime: The time to check.
        
    Returns:
        True if time is near day boundary, False otherwise.
    """
    if eventTime is None: 
        return False
    if eventTime >= dates.time(23, 29):
        return True
    if eventTime <= dates.time(2):
        return True
    return False
        

def get_best_event_time(
        calendar: GoogleCalendar, 
        eventDate: datetime.date, 
        eventTime: datetime.time
) -> datetime.time:
    """
    Find a suitable event time that doesn't conflict with existing events.
    
    Args:
        calendar: The Google Calendar to check against.
        eventDate: The date for the event.
        eventTime: The preferred time for the event.
        
    Returns:
        A time slot that minimizes conflicts.
    """
    endTime = dates.calculate(time=eventTime, minutes=30)
    events: list[GoogleCalendar.Event] = get_google_calendar_events(
        calendar, 
        startDate=eventDate, 
        startTime=eventTime, 
        endDate=eventDate,
        endTime=endTime
    )
    if len(events) < 3: 
        return eventTime
    return get_best_event_time(calendar, eventDate, endTime)


# Data retrieval functions
def get_calendar_booking(database: Database, bookingId: int) -> Booking | None:
    """
    Retrieve booking data by ID with fields needed for calendar events.
    
    Args:
        database: The database connection.
        bookingId: The booking ID to retrieve.
        
    Returns:
        The booking object or None if not found.
    """
    if not bookingId: 
        return None
    search = get_booking(database, bookingId)
    search = set_selection(search)
    search.details.select().enquiryStatus()
    return search.fetchone()


def get_new_arrivals(
        database: Database, 
        start: datetime.date, 
        end: datetime.date, 
        existingBookingIds: list[int]
) -> list[Booking]:
    """
    Find all valid bookings in date range that don't have calendar events yet.
    
    Args:
        database: The database connection.
        start: The start date to search for.
        end: The end date to search for.
        existingBookingIds: List of booking IDs that already have events.
        
    Returns:
        List of bookings that need calendar events created.
    """
    search: Database = search_bookings(database, start, end)
    search = set_selection(search)

    set_valid_management_booking(search)
    
    if existingBookingIds:
        where = search.details.where()
        where.id().isNotIn(existingBookingIds)
    
    return search.fetchall()


def set_selection(search: Database) -> Database:
    """
    Configure the database query to select all fields needed for calendar events.
    
    Args:
        search: The database search query object.
        
    Returns:
        The configured database search query.
    """
    select = search.details.select()
    select.isOwner()
    select.adults()
    select.children()
    select.babies()
    select.enquirySource()
    select.enquiryStatus()
   
    search.arrivals.select().all()
    search.departures.select().all()
    search.extras.select().all()
   
    select = search.properties.select()
    select.name()
    select.shortName()
    select.weClean()
    select.alNumber()
    select.weBook()
   
    select = search.guests.select()
    select.firstName()
    select.lastName()
    select.phone()
    select.email()
   
    select = search.charges.select()
    select.security()
    select.securityMethod()
    select.extraNights()
    select.currency()

    select = search.forms.select()
    select.guestRegistrationDone()
   
    search.propertyAddresses.select().street()
    search.propertySpecs.select().bedrooms()
    search.propertyOwners.select().name()
    return search


def determine_guest_registration_form_notification(booking: Booking) -> bool:
    """
    Check if the guest registration form notification should be sent.
    
    Args:
        booking: The booking data to check.
        
    Returns:
        True if notification should be sent, False otherwise.
    """
    if not booking:
        return False
    if not booking.property.weBook:
        return False
    if booking.forms.guestRegistrationDone:
        return False
    return True


def _set_key_box_reminder_event(calendar: GoogleCalendar, booking: Booking) -> None:
    """
    Set a reminder event for the key box if the property is Quinta Da Barracuda.
    
    Args:
        calendar: The Google Calendar object to insert the event into.
        booking: The booking data containing property information.
        
    Returns:
        None
    """
    def __summary() -> str:
        return (
            f'{booking.property.shortName} - SET '
            f'{booking.arrival.selfCheckIn.upper()} for '
            f'{booking.guest.prettyName}'
        )
    
    def __description() -> str:
        return (
            f'\nReminder to set {booking.arrival.selfCheckIn.upper()} '
            f'for self check-in of {booking.guest.prettyName} on '
            f'{booking.arrival.prettyDate}.'
            f'\n\n{booking.guest.phone}'
            f'\n{booking.arrival.prettyDetails}'
            f'\n\n[{booking.details.id}][2]'
        )
   
    if not calendar:
        logerror('Google Calendar connection failed. Cannot set key box reminder.')
        return
    
    event = calendar.event()

    event.summary = __summary()
    event.description = __description()
    event.location = booking.property.address.street
    event.start.date = booking.arrival.date
    event.end.date = booking.arrival.date
    event.start.timezone = 'Europe/Lisbon'
    event.end.timezone = 'Europe/Lisbon'
    
    existingEvents = get_google_calendar_events(
                                            calendar=calendar, 
                                            startDate=booking.arrival.date, 
                                            startTime=dates.time(8, 30),
                                            endDate=booking.arrival.date,
                                            endTime=dates.time(11, 59))
    for existingEvent in existingEvents:
        if existingEvent.summary.lower() == event.summary.lower():
            event.id = existingEvent.id
            event.start.time = existingEvent.start.time
            event.end.time = existingEvent.end.time
            event.colorId = existingEvent.colorId
            event.update()
            return

    event.start.time = dates.time(10, 0)
    event.end.time = dates.time(10, 30)
    event.colorId = '10'
    event.insert()