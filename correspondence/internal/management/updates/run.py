from correspondence.internal.functions import (
    get_booking_table_data,
    new_internal_email
)
from correspondence.internal.management.functions import (
    determine_manager_email, 
    determine_manager_name, 
    get_management_email_bookings,
    should_advise_transfers
)
from datetime import date
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import (
    get_database, 
    search_updates
)
from default.update.dates import updatedates
from default.update.wrapper import update


#######################################################
# MAIN FUNCTIONALITY
#######################################################

@update
def send_management_updates_emails(
        start: date = None, 
        end: date = None, 
        emailSent: bool = False) -> str:
    """
    Send emails to managers about updates to bookings and extras.
    
    Args:
        start: Starting date for update range
        end: Ending date for update range
        emailSent: Filter by whether email has already been sent
        
    Returns:
        Status message indicating success or no updates to send
    """
    if start is None and end is None: 
        start, end = updatedates.management_updates_emails_dates()
    
    database = get_database()
    updates = get_management_updates(start, end, emailSent)

    if not updates: 
        return 'No management updates to send.'
    
    updatesToSend = dict()
    done = list()
    
    for update in updates:
        booking = get_management_update_booking(database, update.bookingId)
        managerEmail = determine_manager_email(booking)
        managerName = determine_manager_name(booking)

        if (managerEmail, managerName) not in updatesToSend:
            updatesToSend[(managerEmail, managerName)] = updates_holder()
        
        managerToUpdate = updatesToSend[(managerEmail, managerName)]

        detailsUpdate = update.details
        if detailsUpdate:
            managerToUpdate['BOOKINGS'].append((booking, detailsUpdate))
         
            airportTransfers = get_airport_transfers(booking)
            if airportTransfers and booking.emails.airportTransfers:
            
                if update.isCancelledBooking:
                    send_airport_transfers_update_email(booking, airportTransfers, 'CANCELLED')

                elif should_advise_transfers(booking, update.details):
                    send_airport_transfers_update_email(booking, airportTransfers, 'UPDATED')
        
        else:
            if update.isCancelledTransfer:
                send_airport_transfers_update_email(booking, 'Airport Transfers', 'CANCELLED')

            elif should_advise_transfers(booking, update.extras):
                send_airport_transfers_update_email(booking, get_airport_transfers(booking), 'UPDATED')

            else:
                managerToUpdate['EXTRAS'].append((booking, update.extras))
                
        done.append(update)

    for (to, name) in updatesToSend.keys():
        send_management_updates_email(to, name, updatesToSend[(to, name)])
    
    for update in done: 
        update.emailSent = True
        update.update()

    database.close()
    return 'All updates emails sent successfully!'


#######################################################
# EMAIL FUNCTIONS
#######################################################

def updates_holder() -> dict[str, list]:
    """
    Create a dictionary to hold updates for each manager.
    
    Returns:
        Dictionary with empty lists for 'BOOKINGS' and 'EXTRAS'
    """
    return {
        'BOOKINGS': list(),
        'EXTRAS': list(),
    }


def send_management_updates_email(
        to: str, 
        name: str, 
        updates: dict[str, list]) -> None:
    """
    Create and send an update email to a property manager.
    
    Args:
        to: Email address of the manager
        name: Name of the manager
        updates: Dictionary containing booking and extras updates
        
    Returns:
        None
    """
    user, message = new_internal_email(to=to, name=name, subject='LATE UPDATE ON UPCOMING ARRIVALS')
    body = message.body

    if 'BOOKINGS' in updates and updates['BOOKINGS']:
        body.paragraph('There have been changes to upcoming BOOKINGS:')
        
        for booking, change in updates['BOOKINGS']:
            for line in change.split(':'):
                body.paragraph(line)
            
            body.table(get_booking_table_data(booking, **get_management_kwargs_for_booking_table_data(booking, change)))
            body.separation()

    if 'EXTRAS' in updates and updates['EXTRAS']:
        body.paragraph('There have been changes to upcoming EXTRAS:')
        
        for booking, change in updates['EXTRAS']:
            body.paragraph(f' - FOR {booking.guest.prettyName} in {booking.property.shortName} on {booking.arrival.prettyDate}: <b>{change}.</b>')

        body.separation()
    
    message.send()


def send_airport_transfers_update_email(
        booking: Booking, 
        transferType: str, 
        update: str) -> None:
    """
    Create and send an email about updates to airport transfers.
    
    Args:
        booking: The booking with airport transfer details
        transferType: Type of transfer (Airport Transfers, Inbound, Outbound)
        update: Type of update (UPDATED, CANCELLED)
        
    Returns:
        None
    """
    subject = f'{update} {transferType} Request for {booking.guest.lastName} to {booking.property.name}'
    user, message = new_internal_email(to='roadrunnertransfers@gmail.com', name='Wendy & Nick', subject=subject)
    body = message.body

    body.paragraph(f'The following {transferType} request has been {update}:')
   
    tableKwargs = get_transfers_kwargs_for_booking_table_data(transferType, update)
    body.table(get_booking_table_data(booking, **tableKwargs))
   
    body.paragraph('Thank you in advance. I await your confirmation.')
    
    message.send()


def get_management_kwargs_for_booking_table_data(
        booking: Booking, 
        change: str) -> dict[str, bool]:
    """
    Get keyword arguments for configuring booking table data for management emails.
    
    Args:
        booking: The booking containing property information
        change: Description of the change
        
    Returns:
        Dictionary of options for table display settings
    """
    boolean = 'UPDATED' in change
    return {
        'guestContactInfo': boolean and not booking.property.weClean,
        'cleanInfo': boolean and (not booking.property.weClean or booking.details.isOwner),
        'meetGreetInfo': boolean and not booking.property.weClean,
        'extrasInfo': boolean,
    }


def get_transfers_kwargs_for_booking_table_data(
        transferType: str, 
        update: str) -> dict[str, bool]:
    """
    Get keyword arguments for configuring booking table data for transfer emails.
    
    Args:
        transferType: Type of transfer (Airport Transfers, Inbound, Outbound)
        update: Type of update (UPDATED, CANCELLED)
        
    Returns:
        Dictionary of options for table display settings
    """
    transferType = transferType.lower()
    return {
        'arrivalInfo': 'transfers' in transferType or 'inbound' in transferType,
        'departureInfo': 'transfers' in transferType or 'outbound' in transferType,
        'guestContactInfo': 'cancelled' not in update.lower(),
    }


def get_airport_transfers(booking: Booking) -> str | None:
    """
    Determine the type of airport transfers booked.
    
    Args:
        booking: The booking containing extras information
        
    Returns:
        String describing the transfer type or None if no transfers
    """
    if booking.extras.airportTransfers:
        return 'Airport Transfers'
    
    elif booking.extras.airportTransferInboundOnly:
        return 'Inbound Airport Transfer'
    
    elif booking.extras.airportTransferOutboundOnly:
        return 'Outbound Airport Transfer'
    
    return None


#######################################################
# DATABASE FUNCTIONS
#######################################################

def get_management_updates(
        start: date = None, 
        end: date = None, 
        emailSent: bool = False) -> list:
    """
    Get management updates between dates with optional email sent filter.
    
    Args:
        database: Database connection
        start: Start date for updates
        end: End date for updates
        emailSent: Filter for updates that have had emails sent
        
    Returns:
        List of Update objects
    """
    # Initialize search with updates
    search = search_updates(start, end)
    
    # Select all update columns
    select = search.updates.select()
    select.all()
    
    # Set email sent condition if needed
    if emailSent is not None:
        search.updates.where().emailSent().isEqualTo(emailSent)
    
    # Return results
    return search.fetchall()


def get_management_update_booking(
        database: Database = None, 
        bookingId: int = None) -> Booking:
    """
    Get booking details for management update email.
    
    Args:
        database: Database connection
        bookingId: ID of the booking to fetch
        
    Returns:
        Booking object with all required fields
    """
    # Initialize search with booking ID
    search = get_management_email_bookings(database, bookingId=bookingId)
    
    # Select property columns
    select = search.properties.select()
    select.weClean()
    
    # Select property address columns
    select = search.propertyAddresses.select()
    select.street()
    select.directions()
    select.coordinates()
    select.map()
    
    # Select property manager columns
    select = search.propertyManagers.select()
    select.name()
    select.email()
    select.cleaning()
    select.cleaningEmail()
    select.maintenance()
    select.maintenancePhone()
    select.liaison()
    select.liaisonPhone()
    
    # Select guest columns
    select = search.guests.select()
    select.firstName()
    select.lastName()
    select.phone()
    select.email()
    
    # Select email columns
    select = search.emails.select()
    select.arrivalInformation()
    select.airportTransfers()
    
    # Return the booking
    return search.fetchone()