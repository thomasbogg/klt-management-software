from datetime import date
from os import getcwd, path

from apis.google.account import GoogleAccount
from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.functions import (
    determine_arrival_details,
    determine_departure_details
)
from correspondence.guest.functions import (
    get_guest_email_bookings,
    new_guest_email
)
from default.booking.booking import Booking
from default.booking.functions import determine_price_of_extra
from default.database.database import Database


# Email creation functions
def new_guest_arrival_email(
    account: GoogleAccount = None,
    topic: str = None,
    booking: Booking = None
) -> tuple[GoogleMailMessages, GoogleMailMessage]:
    """
    Create a new email for guest arrival communication.
    
    Args:
        account: The Google account to use for sending the email
        topic: The topic of the email
        booking: The booking object containing guest information
        
    Returns:
        A tuple containing the email service and message objects
    """
    subject = f'{topic} for {booking.guest.lastName} to {booking.property.name}'
    return new_guest_email(account=account, subject=subject, booking=booking)


# Data formatting functions
def get_arrival_table_data(
    booking: Booking,
    addTravel: bool = True,
    addExtras: bool = True,
) -> list[tuple[str, str]]:
    """
    Generate a data table with booking details for email templates.
    
    Creates a list of key-value pairs containing property information, 
    guest count, arrival/departure dates, and optionally flight information.
    
    Args:
        booking: The booking object containing all relevant information
        addFlights: Whether to include flight information in the table
        addExtras: Whether to include extras requested in the table 
        
    Returns:
        A list of tuples containing table row labels and values
    """
    data = [
        ('Property:', booking.property.name),
        ('Total People:', booking.details.prettyGuests),
        ('Arriving:', booking.arrival.prettyDate),
        ('Departing:', booking.departure.prettyDate),
        ('Phone No:', booking.guest.phone),
    ]
    
    if addTravel: 
        flight = booking.arrival.flightNumber
        details = determine_arrival_details(booking)
        if flight: 
            data.append(('Inbound Flight:', details))
        else:
            data.append(('Arrival Plan:', details))
        
        flight = booking.departure.flightNumber
        details = determine_departure_details(booking)
        if flight: 
            data.append(('Outbound Flight:', details))
        else:
            data.append(('Departure Plan:', details))

    if addExtras:
        data += get_extras_and_charges(booking)
        
    
    return data


def linen_care_1(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph about proper care of linens regarding sunscreen and makeup.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'If using Sunscreen and/or Make-up, we kindly ask guests not to make',
        'direct contact with towels and linen before thoroughly washing the affected',
        'areas of the body. Whilst these products can be vitally important for skin',
        'protection, they have very deleterious and irreversible effects on fabrics.',
    )


def linen_care_2(body: GoogleMailMessage.Body) -> None:
    """
    Add paragraph about proper care of linens regarding sunscreen and makeup.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'Over the years, we have had to write off a catastrophically wasteful amount',
        'of our supply due to the unwashable stains left by lotions and paints. We',
        'sincerely appreciate our guests exercising extreme care when wearing these.'
    )


# Database query functions
def get_guest_arrival_email_bookings(
    database: Database,
    start: date = None,
    end: date = None,
    bookingId: int = None
) -> Database:
    """
    Get bookings for guest arrival emails within a date range.
    
    Creates a database search object with date range filters applied.
    
    Args:
        database: The database connection object
        start: The start date for filtering arrivals
        end: The end date for filtering arrivals
        bookingId: Optional specific booking ID to retrieve
        
    Returns:
        A configured database search object ready for further filtering
    """
    search = get_guest_email_bookings(database, bookingId)
    if not bookingId:
        where = search.arrivals.where()
        if start:
            where.date().isGreaterThanOrEqualTo(start)
        if end:
            where.date().isLessThanOrEqualTo(end)
    return search


def get_extras_and_charges(booking: Booking) -> list[tuple[str, str]]:
    """
    Determine extras and payment details for the booking.
    
    Args:
        booking: The booking object containing relevant information
        
    Returns:
        A list of tuples containing ('Extra:', extra and its cost)
    """
    extras = booking.extras.list
    if not extras:
        return []
    
    result = []
    count = 0
    ownerPays = booking.extras.ownerIsPaying
  
    for extra in extras:
        count += 1
        if ownerPays:
            extra += ' (owner paying)'
        else:
            charge = determine_price_of_extra(booking, extra)
            if charge:
                extra += f' @ €{charge}.00'
                if 'airport transfer' in extra.lower():
                    if 'transfers' in extra.lower():
                        extra += ' TOTAL'
                    extra += ' (to driver)'
            
        result.append((f'<u>Extras {count}</u>:', extra))
    return result


def code_of_conduct_explainer(body: GoogleMailMessage.Body) -> None:
    """
    Point to the tourist code of conduct attachment.
    
    Args:
        body: The email body object to modify
        
    Returns:
        None
    """
    body.paragraph(
        'Finally, we must point out that Albufeira has implemented stricter rules for',
        'tourist behaviour. Please open the attachment called "Albufeira Tourist Code',
        'of Conduct" and become familiar with the consequences of improper adherence.'
    )


def get_code_of_conduct_attachment() -> str:
    """
    Get the full path to the code of conduct PDF.
    
    Returns:
        str: Full path to the PDF attachment
    """
    abs = getcwd()
    filedir = 'correspondence/guest/arrival'
    filename = 'Albufeira_Tourist_Code_of_Conduct.pdf'
    attachmentPath = path.join(abs, filedir, filename)
    if not path.exists(attachmentPath):
        raise FileNotFoundError(f'Attachment not found: {attachmentPath}')
    return attachmentPath
