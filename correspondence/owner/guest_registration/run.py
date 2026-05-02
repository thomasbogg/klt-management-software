from apis.google.mail.message import GoogleMailMessage
from correspondence.owner.functions import new_owner_email
from default.booking.booking import Booking
from default.google.mail.functions import send_email


#######################################################
# MAIN FUNCTIONALITY
#######################################################

def send_new_guest_registration_to_owner_email(booking: Booking) -> None:
    """
    Send guest registration information to the property owner.
    
    Args:
        booking: The booking containing guest and property information
        
    Returns:
        None
    """
    user, message = new_owner_email(subject=f'SEF Report for party of {booking.guest.name}', booking=booking)
    body = message.body
    
    if booking.guest.nifNumber: 
        introduction_no_form(body, booking)
        fiscal_number(body, booking)
    else:
        introduction_form(body, booking)
        click_below(body)
        link(body, booking)        

    send_email(user, message)


#######################################################
# EMAIL CONTENT FUNCTIONS
#######################################################

def introduction_form(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add introduction paragraph for guests who completed the SEF form.
    
    Args:
        body: The email body to append text to
        booking: The booking containing guest and property information
        
    Returns:
        None
    """
    body.paragraph(
        f'The guest, <b>{booking.guest.name}</b>, staying <u>{booking.arrival.prettyDate}</u>',
        f'to <u>{booking.departure.prettyDate}</u> in {booking.property.shortName} has',
        'filled out the <u>Serviço de Estrangeiros e Fronteiras</u> registration form.'
    )    


def introduction_no_form(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add introduction paragraph for guests with Portuguese fiscal numbers.
    
    Args:
        body: The email body to append text to
        booking: The booking containing guest and property information
        
    Returns:
        None
    """
    body.paragraph(
        f'The guest, <b>{booking.guest.name}</b>, staying <u>{booking.arrival.prettyDate}</u>',
        f'to <u>{booking.departure.prettyDate}</u> in {booking.property.shortName} has',
        'a Portuguese fiscal number so does not need to complete the usual form.'
    )


def fiscal_number(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add the guest's fiscal number to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking containing guest information
        
    Returns:
        None
    """
    body.paragraph(
        f'The guest\'s Número de Identificação Fiscal is: {booking.guest.nifNumber}',
    )


def click_below(body: GoogleMailMessage.Body) -> None:
    """
    Add instructions to click the link below.
    
    Args:
        body: The email body to append text to
        
    Returns:
        None
    """
    body.paragraph(
        'You can access the form and the relevant information by clicking the link below.',
    )


def link(body: GoogleMailMessage.Body, booking: Booking) -> None:
    """
    Add the SEF form link to the email body.
    
    Args:
        body: The email body to append text to
        booking: The booking containing form information
        
    Returns:
        None
    """
    body.link(
        booking.forms.guestRegistration,
        f'Guest Registration form for {booking.guest.name}',
    )