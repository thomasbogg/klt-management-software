from apis.google.account import GoogleAccount
from apis.google.contacts.person import GooglePerson
from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.functions import get_email_bookings
from default.booking.booking import Booking
from default.database.database import Database
from default.database.functions import set_valid_management_booking
from default.google.contacts.functions import create_contact, get_contacts
from default.google.mail.functions import new_email, send_email
from default.settings import (
    DEEPL_AUTH_KEY, 
    DEFAULT_ACCOUNT, 
    DEFAULT_LANGUAGE, 
)
from default.whatsapp.functions import send_whatsapp_message
from translator.deepl import Deepl
from web.whatsapp import BrowseWhatsApp


def new_guest_email(
    account: GoogleAccount = None,
    user: GoogleMailMessages = None, 
    subject: str = None, 
    booking: Booking = None
) -> tuple[GoogleMailMessages, GoogleMailMessage]:
    """
    Create a new email message for the guest.
    
    Args:
        account: The Google account to send from.
        user: The Google Mail user object if already authenticated.
        subject: The subject line for the email.
        booking: The booking object containing guest information.
        
    Returns:
        A tuple containing the user and the email message objects.
    """
    to = booking.guest.email
    name = booking.guest.firstName
    user, message = new_email(account=account, user=user, subject=subject, to=to, name=name)
    language = booking.guest.preferredLanguage
    if booking.guest.preferredLanguage != DEFAULT_LANGUAGE:
        message.translator = Deepl(authKey=DEEPL_AUTH_KEY, targetLang=language)
    return user, message


def send_guest_email(
    user: GoogleMailMessages = None, 
    message: GoogleMailMessage = None, 
    bookingId: int = None
) -> GoogleMailMessage | None:
    """
    Send an email to the guest and track its status.
    
    Args:
        user: The Google Mail user object.
        message: The prepared email message object.
        bookingId: The booking ID associated with the email for tracking purposes.
        
    Returns:
        The sent email message object or None if sending failed.
    """
    return send_email(user=user, message=message, checkSent=(bookingId is None))


def send_guest_whatsapp_message(
    whatsapp: BrowseWhatsApp = None, 
    booking: Booking = None, 
    content: list[str] = None
) -> bool:
    """
    Send a WhatsApp message to the guest.
    
    Formats the message with greeting and signature, then sends it via WhatsApp.
    
    Args:
        whatsapp: The WhatsApp browser interface for sending messages.
        booking: The booking object containing guest contact information.
        content: The content of the message as a list of text lines.
        
    Returns:
        True if the message was sent successfully, False otherwise.
    """
    content = (
        [f'Hello, {booking.guest.fullName}'] + 
        content + 
        ['Kind regards,', DEFAULT_ACCOUNT.name]
    )
    sent = send_whatsapp_message(
        whatsapp=whatsapp, 
        recipientContact=booking.guest.phone, 
        recipientName=booking.guest.fullName, 
        content=content,
        targetLang=booking.guest.preferredLanguage)
    return sent


def new_guest_contact(booking: Booking = None) -> bool:
    """
    Create a new Google contact for the guest if one doesn't already exist.
    
    Checks if a contact exists for the guest, and if not, creates one with
    booking and property details.
    
    Args:
        booking: The booking object containing guest information.
        
    Returns:
        True if the contact already existed or was created successfully.
    """
    contacts = get_contacts(booking.guest.fullName)
    if not contacts:
        contact: GooglePerson = create_contact(
            firstName=booking.guest.firstName, 
            lastName=booking.guest.lastName, 
            emailAddress=booking.guest.email, 
            phoneNumber=booking.guest.phone
        )
    else:
        contact = contacts
        if contact.firstName != booking.guest.firstName:
            contact.firstName = booking.guest.firstName
        if contact.lastName != booking.guest.lastName:
            contact.lastName = booking.guest.lastName
        
        contact.update()
        return True
    
    contact.userDefined = ('Property', booking.property.name)
    contact.userDefined = ('Arrival Date', booking.arrival.prettyDate)
    contact.create()

    return True


def get_guest_email_bookings(database: Database, bookingId: int = None) -> Database:
    """
    Retrieve guest email bookings with specified conditions.
    
    Configures a database search for guest-related emails with appropriate
    filters for valid booking status and email settings.
    
    Args:
        database: The database connection object.
        bookingId: Optional specific booking ID to filter by.
        
    Returns:
        A configured database search object ready to execute.
    """
    search = get_email_bookings(database, bookingId=bookingId)

    # Select details from the bookings table
    select = search.details.select()
    select.enquirySource()
    select.platformId()
    select.isOwner()
    
    # Select arrival date
    search.arrivals.select().date()

    # Select guest details
    select = search.guests.select()
    select.id()
    select.email()
    select.preferredLanguage()

    select = search.propertySpecs.select()
    select.bedrooms()

    # Apply conditions for valid bookings
    set_valid_management_booking(search)

    # Only include non-paused emails
    search.emails.where().paused().isFalse()

    return search