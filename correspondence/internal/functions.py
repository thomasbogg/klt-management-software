from apis.google.account import GoogleAccount
from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.functions import determine_on_site_extras
from datetime import date
from default.booking.booking import Booking
from default.google.mail.functions import new_email
from default.update.dates import updatedates


#######################################################
# EMAIL CREATION FUNCTIONS
#######################################################

def new_internal_email(
        account: GoogleAccount = None,
        user: GoogleMailMessages = None,
        to: str = None, 
        name: str = None, 
        subject: str = None
) -> tuple[GoogleMailMessages, GoogleMailMessage]:

    """
    Creates a new internal email message.
    
    Args:
        account: The Google account to use for sending the email
        user: The Google Mail user object
        to: The recipient's email address
        name: The recipient's name
        subject: The subject of the email
        
    Returns:
        A Google Mail message object
    """
    return new_email(account=account, user=user, subject=subject, to=to, name=name)


def get_subject(
        topic: str = None, 
        start: date = None, 
        end: date = None, 
        daily: bool = True) -> str:
    """
    Returns a formatted subject line based on the provided parameters.
    
    Args:
        topic: The topic of the email
        start: The start date for the email
        end: The end date for the email
        daily: Whether the email is a daily update
        
    Returns:
        A formatted subject line string
    """
    if topic is None:
        topic = ""
    if daily:
        dateValue = updatedates.tomorrow()
        return f'DAILY {topic} EMAIL for {updatedates.prettyDate(dateValue)}'
    if start and end:
        return (f'GENERAL {topic} UPDATE EMAIL for {updatedates.prettyDate(start)} '
                f'to {updatedates.prettyDate(end)}')
    return topic


#######################################################
# BOOKING INFORMATION FUNCTIONS
#######################################################

def get_booking_table_data(
        booking: Booking, 
        arrivalInfo: bool = True,
        departureInfo: bool = True,
        guestContactInfo: bool = False, 
        cleanInfo: bool = False, 
        meetGreetInfo: bool = False, 
        extrasInfo: bool = False, 
        airportTransferInfo: bool = False) -> list[tuple[str, str]]:
    """
    Returns a list of tuples containing booking information for the email body.
    Each tuple contains a label and its corresponding value.
    
    Args:
        booking: The booking object containing the information
        arrivalInfo: Include arrival information
        departureInfo: Include departure information
        guestContactInfo: Include guest contact information
        cleanInfo: Include clean information
        meetGreetInfo: Include meet and greet information
        extrasInfo: Include extras information
        airportTransferInfo: Include airport transfer information
        
    Returns:
        A list of tuples containing the booking information
    """ 
   
    data: list[tuple[str, str]] = [
        ('Lead Guest:', f'<b>{booking.guest.prettyName}</b>'),
        ('Property:', f'<b>{booking.property.name}</b>'),
        ('Total People:', f'<b>{booking.details.prettyGuests}</b>')
    ]

    if arrivalInfo:
        data.append(('Arriving:', f'<b>{booking.arrival.prettyDate}</b>'))
        data.append(('Arrival Details:', 
                    f'<b>{booking.arrival.prettyDetails}</b>'))
    
    if departureInfo:
        data.append(('Departing:', f'<b>{booking.departure.prettyDate}</b>'))
        data.append(('Departure Details: ', 
                    f'<b>{booking.departure.prettyDetails}</b>'))

    if guestContactInfo:
        data.append(('Lead Guest Email:', f'<b>{booking.guest.email}</b>'))
        data.append(('Lead Guest Phone:', f'<b>{booking.guest.phone}</b>'))
   
    if meetGreetInfo:
        data.append(('Wants Meet & Greet:', 
                    f'<b>{determine_meet_greet(booking)}</b>'))
   
    if cleanInfo:
        data.append(('Wants Clean:', f'<b>{determine_clean(booking)}</b>'))
   
    if airportTransferInfo:
        childSeats = booking.extras.childSeats       
        children, babies = booking.details.children, booking.details.babies
        if childSeats and (children or babies):
            ages = '; '.join([
                f'{age} years' if 'month' not in age 
                else f'{age} months' 
                for age in childSeats.split(',')
            ])
            data.append(('Child Age(s):', f'<b>{ages}</b>'))
       
        excessBaggage = booking.extras.excessBaggage
        if excessBaggage and excessBaggage != '0': 
            data.append(('Excess Baggage:', f'<b>{excessBaggage}</b>'))

    if extrasInfo:
        extras = determine_on_site_extras(booking.extras.arrival)
        extras += determine_on_site_extras(booking.extras.departure)
        if not extras: 
            return data
     
        data.append(('EXTRAS:', f'<b>{extras[0]}</b>'))
        for extra in extras[1:]:
            data.append(('', f'<b>{extra}</b>'))
    
    return data


def determine_clean(booking: Booking) -> str:
    """
    Determines if a clean is required based on the booking details.
    
    Args:
        booking: The booking object containing the information
        
    Returns:
        'YES' if a clean is required, 'NO' otherwise
    """
    return 'YES' if booking.departure.clean else 'NO'


def determine_meet_greet(booking: Booking) -> str:
    """
    Determines if a meet and greet is required based on the booking details.
    
    Args:
        booking: The booking object containing the information
        
    Returns:
        'YES' if a meet and greet is required, 'NO' otherwise
    """
    return 'YES' if booking.arrival.meetGreet else 'NO'