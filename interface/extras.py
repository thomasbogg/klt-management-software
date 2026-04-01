from correspondence.guest.arrival.instructions.two_weeks.run import send_two_weeks_instructions_emails
from correspondence.guest.departure.outbound_transfer.run import send_outbound_transfer_confirmation_email
from correspondence.internal.management.transfers.run import send_airport_transfers_request_emails
from correspondence.internal.management.updates.run import send_airport_transfers_update_email, send_management_updates_emails
import database
from default.booking.booking import Booking
from default.dates import dates
from default.updates.functions import (
    airport_transfers_changes,
    arrival_date_has_changed,
    child_seats_changes,
    cot_changes,
    departure_date_has_changed,
    excess_baggage_changes,
    high_chair_changes,
    late_checkout_changes,
    mid_stay_clean_changes,
    other_request_changes,
    welcome_pack_changes,
    welcome_pack_modifications_changes,
)
from interface.functions import get_text, get_bool, open_PIMS, should_update_PIMS
from interfaces.interface import Interface


def update_extras(subsection: Interface, databaseBooking: Booking, updatedBooking: Booking) -> None:
    """
    Update extras for a booking.
    
    Presents a menu of available extras (airport transfers, accommodation features,
    and services) and processes the user's selection. Updates both the database
    and updated booking objects accordingly.
    
    Parameters:
        subsection: Interface object for user interaction
        databaseBooking: Original booking data from the database
        updatedBooking: Copy of booking to track changes
    
    Returns:
        None if user exits, otherwise recursively continues updating
    """
    extras = [
        'Airport Transfers',
        'Airport Transfer (Inbound Only)',
        'Airport Transfer (Outbound Only)',
        'Cot',
        'High Chair',
        'Mid-Stay Clean',
        'Welcome Pack',
        'Late Check-out',
        'Add modification to Welcome Pack',
        'Set Child Seats (for airport transfer)',
        'Other requests',
        'Set Excess Baggage (for airport transfer)',
        'Extra Nights',
        'Owner is Paying',
    ]
    
    subsection.section('Updating extras for selected booking. Which are we changing?')
    extra = subsection.option(extras)

    if extra is None:
        return None
    
    # Handle boolean extras (options 1-8)
    if extra < 9:
        boolean = subsection.bool(f'Are we adding (1) or cancelling (0) the ({extras[extra - 1]})?')

        if boolean is None:
            return update_extras(subsection, databaseBooking, updatedBooking)
        
        # Airport transfers 
        if extra < 4:
            updatedBooking.extras.airportTransfers = False
            updatedBooking.extras.airportTransferInboundOnly = False
            updatedBooking.extras.airportTransferOutboundOnly = False

            if extra == 1:
                updatedBooking.extras.airportTransfers = boolean
                changes = airport_transfers_changes(databaseBooking, updatedBooking, toDatabase=False)
                cancelled = boolean == False and changes
            
                databaseBooking.extras.airportTransfers = boolean
                databaseBooking.extras.update()

                if databaseBooking.emails.airportTransfers:
                    if cancelled:
                        send_airport_transfers_update_email(databaseBooking, 'Airport Transfers', 'CANCELLED')
                    elif changes:
                        send_airport_transfers_request_emails(bookingId=databaseBooking.id)

                if databaseBooking.emails.arrivalInformation and boolean and changes:
                    send_two_weeks_instructions_emails(bookingId=databaseBooking.id)

            elif extra == 2:
                updatedBooking.extras.airportTransferInboundOnly = boolean
                changes = airport_transfers_changes(databaseBooking, updatedBooking, toDatabase=False)
                cancelled = boolean == False and changes
                
                databaseBooking.extras.airportTransferInboundOnly = boolean
                databaseBooking.extras.update()

                if databaseBooking.emails.airportTransfers and cancelled:
                    if cancelled:
                        send_airport_transfers_update_email(databaseBooking, 'Inbound', 'CANCELLED')
                    elif changes:
                        send_airport_transfers_request_emails(bookingId=databaseBooking.id)

                if databaseBooking.emails.arrivalInformation and boolean and changes:
                    send_two_weeks_instructions_emails(bookingId=databaseBooking.id)

            elif extra == 3:
                updatedBooking.extras.airportTransferOutboundOnly = boolean
                changes = airport_transfers_changes(databaseBooking, updatedBooking, toDatabase=False)
                cancelled = boolean == False and changes
            
                databaseBooking.extras.airportTransferOutboundOnly = boolean
                databaseBooking.extras.update()

                if boolean and changes:
                    send_outbound_transfer_confirmation_email(databaseBooking.id)
                    send_airport_transfers_request_emails(bookingId=databaseBooking.id)
                elif databaseBooking.emails.airportTransfers and cancelled:
                    send_airport_transfers_update_email(databaseBooking, 'Outbound', 'CANCELLED')

        # Accommodation extras
        elif extra == 4:
            updatedBooking.extras.cot = boolean
            if databaseBooking.emails.management:
                cot_changes(databaseBooking, updatedBooking)
            databaseBooking.extras.cot = boolean

        elif extra == 5:
            updatedBooking.extras.highChair = boolean
            if databaseBooking.emails.management:
                high_chair_changes(databaseBooking, updatedBooking)
            databaseBooking.extras.highChair = boolean
            
        elif extra == 6:
            updatedBooking.extras.midStayClean = boolean
            if databaseBooking.emails.management:
                mid_stay_clean_changes(databaseBooking, updatedBooking)
            databaseBooking.extras.midStayClean = boolean

        elif extra == 7:
            updatedBooking.extras.welcomePack = boolean
            if databaseBooking.emails.management:
                welcome_pack_changes(databaseBooking, updatedBooking)
            databaseBooking.extras.welcomePack = boolean

        elif extra == 8:
            updatedBooking.extras.lateCheckout = boolean
            if databaseBooking.emails.management:
                late_checkout_changes(databaseBooking, updatedBooking)
            databaseBooking.extras.lateCheckout = boolean

        databaseBooking.extras.update()
        set_extras_in_PIMS(databaseBooking, option=extra, boolean=boolean, extras=extras)
        return update_extras(subsection, databaseBooking, updatedBooking)

    # Handle text-based extras (options 9-12)
    if extra == 9:
        value = get_text(subsection, 'Modification of Welcome Pack', databaseBooking.extras.welcomePackModifications) 
        updatedBooking.extras.welcomePackModifications = value
        if databaseBooking.emails.management:
            welcome_pack_modifications_changes(databaseBooking, updatedBooking)
        
        databaseBooking.extras.welcomePack = True
        databaseBooking.extras.welcomePackModifications = value
        set_extras_in_PIMS(databaseBooking, option=extra, value=value, extras=extras)

    elif extra == 10:
        value = get_text(subsection, 'Child Seats', databaseBooking.extras.childSeats) 
        updatedBooking.extras.childSeats = value
        if databaseBooking.emails.management:
            child_seats_changes(databaseBooking, updatedBooking)
        databaseBooking.extras.childSeats = value

    elif extra == 11:
        value = get_text(subsection, 'Other Requests', databaseBooking.extras.otherRequests) 
        updatedBooking.extras.otherRequests = value
        if databaseBooking.emails.management:
            other_request_changes(databaseBooking, updatedBooking)
        
        databaseBooking.extras.otherRequests = value
        set_extras_in_PIMS(databaseBooking, option=extra, value=value, extras=extras)

    elif extra == 12:
        value = get_text(subsection, 'Excess Baggage', databaseBooking.extras.excessBaggage) 
        updatedBooking.extras.excessBaggage = value
        if databaseBooking.emails.airportTransfers:
            excess_baggage_changes(databaseBooking, updatedBooking)
        databaseBooking.extras.excessBaggage = value

    # Handle extra nights (option 13)
    elif extra == 13:
        add_extra_nights(subsection, databaseBooking, updatedBooking)

    elif extra == 14:
        value = get_bool(subsection, 'Owner is Paying', databaseBooking.extras.ownerIsPaying)
        databaseBooking.extras.ownerIsPaying = value

    databaseBooking.update()
    return update_extras(subsection, databaseBooking, updatedBooking)


def add_extra_nights(subsection: Interface, databaseBooking: Booking, updatedBooking: Booking) -> None:
    """
    Add extra nights to beginning and/or end of a stay.
    
    Allows adding nights before arrival and/or after departure,
    updating dates accordingly and calculating additional charges.
    
    Parameters:
        subsection: Interface object for user interaction
        databaseBooking: Original booking data from the database
        updatedBooking: Copy of booking to track changes
    
    Returns:
        None
    """
    subsection.log('Adding extra nights to booking. How many to beginning and end of stay?')
    numArrival = subsection.integer('Number of days to add before arrival')
    numDeparture = subsection.integer('Number of days to add after departure')
    
    if numArrival is None and numDeparture is None:
        return None

    if numArrival:    
        newArrivalDate = dates.calculate(date=databaseBooking.arrival.date, days=-numArrival)
        updatedBooking.arrival.date = newArrivalDate
        if databaseBooking.emails.management:
            arrival_date_has_changed(databaseBooking, updatedBooking)
        databaseBooking.arrival.date = newArrivalDate
        databaseBooking.arrival.manualDate = True
    else:
        numArrival = 0
    
    if numDeparture:    
        newDepartureDate = dates.calculate(date=databaseBooking.departure.date, days=numDeparture)    
        updatedBooking.departure.date = newDepartureDate
        if databaseBooking.emails.management:
            departure_date_has_changed(databaseBooking, updatedBooking)
    
        databaseBooking.departure.date = newDepartureDate
        databaseBooking.departure.manualDate = True
    else: 
        numDeparture = 0

    totalExtraNights = numArrival + numDeparture
    databaseBooking.extras.extraNights = totalExtraNights

    # Add extra charge for the additional night(s)
    subsection.log('And how much are these extra nights priced at?')
    total = subsection.float('Type here total without commas')
    databaseBooking.charges.extraNights = total

    return None


def set_extras_in_PIMS(
    databaseBooking: Booking, 
    boolean: bool | None = None, 
    option: int | None = None, 
    value: str | None = None, 
    extras: list[str] | None = None
) -> None:
    """
    Update extras in the PIMS system.
    
    Takes booking extras information and updates the corresponding fields in PIMS.
    Only updates PIMS if the should_update_PIMS function returns True.
    
    Parameters:
        databaseBooking: Original booking data from the database
        boolean: Flag indicating whether to add or remove an extra
        option: Index of the selected extra
        value: Text value for text-based extras
        extras: List of available extras
    
    Returns:
        None
    """
    if not should_update_PIMS(databaseBooking): 
        return None

    arrivalExtras = databaseBooking.extras.arrival
    departureExtras = databaseBooking.extras.departure
    allExtras = arrivalExtras + departureExtras

    if boolean is not None:
        extra = extras[option - 1]
        
        if boolean == True: 
            allExtras.append(extra)
        else:
            if extra in ('Cot', 'High Chair') and 'Cot & High Chair' in allExtras:
                allExtras.remove('Cot & High Chair')
        
                if extras == 'Cot': 
                    allExtras.append('High Chair')
                else: 
                    allExtras.append('Cot')
            else: 
                allExtras.remove(extra)

    allExtras = ' // '.join(allExtras)
    if value is not None: 
        allExtras += f' // {value}'

    browser = open_PIMS(databaseBooking)
    browser.extras = allExtras
    browser.update()
    browser.quit()
    
    return None