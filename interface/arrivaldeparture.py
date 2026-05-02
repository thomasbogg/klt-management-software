from arrivals.run import update_arrivals_calendar
from default.booking.booking import Booking
from default.booking.functions import determine_key_box_for_self_check_in
from default.dates import dates
from default.updates.functions import (
    arrival_date_has_changed,
    arrival_flight_has_changed,
    arrival_time_has_changed,
    clean_has_changed,
    departure_date_has_changed,
    departure_flight_has_changed,
    departure_time_has_changed,
    meet_greet_has_changed,
)
from interface.functions import (
    get_bool,
    get_date,
    get_text,
    get_time,
    open_PIMS,
    should_update_PIMS,
)
from interfaces.interface import Interface


def update_arrival_departure(
    subsection: Interface,
    databaseBooking: Booking,
    updatedBooking: Booking
) -> None:
    """
    Update arrival and departure details for a booking.
    
    Presents a menu of arrival/departure details that can be modified and
    processes the user's selection, updating both the database and updated
    booking objects accordingly.
    
    Parameters:
        subsection: Interface object for user interaction
        databaseBooking: Original booking data from the database
        updatedBooking: Copy of booking to track changes
    
    Returns:
        None if user exits, otherwise recursively continues updating
    """
    details = [
        'Arrival Date',
        'Departure Date',
        'Inbound Flight',
        'Outbound Flight',
        'Arrival Details',
        'Departure Details',
        'Self Check-in',
        'Meet Greet Option',
        'Cleaning Option',
    ]
    
    subsection.section('Updating arrival/departure details for selected booking.')
    
    detail = subsection.option(details)

    if detail is None:
        return None

    detailName = details[detail - 1]

    if detail == 1:
        newDate = get_date(subsection, detailName, databaseBooking.arrival.date)
        
        if newDate is not None:
            updatedBooking.arrival.date = newDate
            updatedBooking.arrival.manualDate = True
            
            if databaseBooking.emails.management:
                arrival_date_has_changed(databaseBooking, updatedBooking)
            
            databaseBooking.arrival.date = newDate
            databaseBooking.arrival.manualDate = True

    elif detail == 2:
        newDate = get_date(subsection, detailName, databaseBooking.departure.date)
        
        if newDate is not None:
            updatedBooking.departure.date = newDate
            updatedBooking.departure.manualDate = True
    
            if databaseBooking.emails.management:
                departure_date_has_changed(databaseBooking, updatedBooking)
            
            databaseBooking.departure.date = newDate
            databaseBooking.departure.manualDate = True
    
    elif 2 < detail < 5:
        if detail == 3:
            hasFlight = databaseBooking.arrival.flightNumber
            
            if hasFlight:
                currentNumber = databaseBooking.arrival.flightNumber
                currentTime = databaseBooking.arrival.time
                currentFaro = databaseBooking.arrival.isFaro
            else:
                currentNumber, currentTime, currentFaro = None, None, None
        
        else:
            hasFlight = databaseBooking.departure.flightNumber
            
            if hasFlight:
                currentNumber = databaseBooking.departure.flightNumber
                currentTime = databaseBooking.departure.time
                currentFaro = databaseBooking.departure.isFaro
            else:
                currentNumber, currentTime, currentFaro = None, None, None
        
        number = get_text(subsection, f'{detailName} Number', currentNumber)
        time = get_time(subsection, f'{detailName} Time', currentTime)
        isFaro = get_bool(subsection, f'{detailName} Is Faro', currentFaro)
        
        if detail == 3:
            updatedBooking.arrival.flightNumber = number
            updatedBooking.arrival.time = time
            updatedBooking.arrival.isFaro = isFaro
            
            if databaseBooking.emails.management:
                arrival_flight_has_changed(databaseBooking, updatedBooking)
            
            databaseBooking.arrival.flightNumber = number
            databaseBooking.arrival.time = time
            databaseBooking.arrival.isFaro = isFaro
    
            if should_update_PIMS(databaseBooking):
                browser = open_PIMS(databaseBooking)
                browser.inboundFlight = f'{number} {databaseBooking.arrival.prettyTime}'
                browser.update()
                browser.quit()
        
        else:
            updatedBooking.departure.flightNumber = number
            updatedBooking.departure.time = time
            updatedBooking.departure.isFaro = isFaro
            
            if databaseBooking.emails.management:
                departure_flight_has_changed(databaseBooking, updatedBooking)
            
            databaseBooking.departure.flightNumber = number
            databaseBooking.departure.time = time
            databaseBooking.departure.isFaro = isFaro
    
            if should_update_PIMS(databaseBooking):
                browser = open_PIMS(databaseBooking)
                browser.outboundFlight = (
                    f'{number} {databaseBooking.departure.prettyTime}'
                )
                browser.update()
                browser.quit()

    elif detail < 7:
        if detail == 5:
            currentInfo = databaseBooking.arrival.details
            currentTime = databaseBooking.arrival.time
        else:
            currentInfo = databaseBooking.departure.details
            currentTime = databaseBooking.departure.time
        
        info = get_text(subsection, f'{detailName} Info', currentInfo)
        time = get_time(subsection, f'{detailName} Time', currentTime)
        
        if detail == 5:
            updatedBooking.arrival.time = time
            updatedBooking.arrival.details = info
            
            if databaseBooking.emails.management:
                arrival_time_has_changed(databaseBooking, updatedBooking)
            
            databaseBooking.arrival.time = time
            databaseBooking.arrival.details = info

            if should_update_PIMS(databaseBooking):
                browser = open_PIMS(databaseBooking)
                browser.inboundFlight = f'{info}'
                browser.arrivalHour = f'{time.hour}'
                minute = f'{time.minute}'
                if minute == '0':
                    minute = '00'
                browser.arrivalMinute = f'{minute}'
                browser.update()
                browser.quit()
        
        else:
            updatedBooking.departure.time = time
            updatedBooking.departure.details = info
            
            if databaseBooking.emails.management:
                departure_time_has_changed(databaseBooking, updatedBooking)
            
            databaseBooking.departure.time = time
            databaseBooking.departure.details = info
    
            if should_update_PIMS(databaseBooking):
                browser = open_PIMS(databaseBooking)
                browser.outboundFlight = f'{info}'
                browser.departureHour = f'{time.hour}'
                minute = f'{time.minute}'
                if minute == '0':
                    minute = '00'
                browser.departureMinute = f'{minute}'
                browser.update()
                browser.quit()

    elif detail == 7:
        boolean = get_bool(subsection, detailName, databaseBooking.arrival.selfCheckIn)
        
        if boolean and databaseBooking.property.isQuintaDaBarracuda:
            determine_key_box_for_self_check_in(databaseBooking)
        else:
            databaseBooking.arrival.selfCheckIn = boolean

        databaseBooking.emails.arrivalInformation = False

    elif detail == 8:
        boolean = get_bool(subsection, detailName, databaseBooking.arrival.meetGreet)
        
        updatedBooking.arrival.meetGreet = boolean
        databaseBooking.arrival.meetGreet = boolean

        if databaseBooking.emails.management:
            meet_greet_has_changed(databaseBooking, updatedBooking)

    elif detail == 9:
        boolean = get_bool(subsection, detailName, databaseBooking.departure.clean)
        
        updatedBooking.departure.clean = boolean
        databaseBooking.departure.clean = boolean

        if databaseBooking.emails.management:
            clean_has_changed(databaseBooking, updatedBooking)

    databaseBooking.update()

    arrivalDate = databaseBooking.arrival.date
    today, tomorrow = dates.date(), dates.tomorrow()
    if arrivalDate in (today, tomorrow):
        update_arrivals_calendar(start=today, end=tomorrow)

    return update_arrival_departure(subsection, databaseBooking, updatedBooking)
