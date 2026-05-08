
from correspondence.guest.arrival.four_weeks.run import send_airbnb_arrival_form_messages, get_four_weeks_bookings
from default.database.functions import get_database
from default.google.mail.functions import get_user, get_inbox
from default.settings import DEFAULT_ACCOUNT
from default.update.wrapper import update
from forms.arrival.guest.run import send_whatsapp_prompts_for_guest_arrival_forms, get_guest_arrival_form_bookings
from forms.registration.run import send_whatsapp_prompts_for_guest_registration_forms, get_guest_registration_form_bookings
from libraries.web.html import HTML
from platforms.airbnb.review import review_airbnb_guests
from platforms.vrbo.download import update_from_vrbo


@update
def send_guest_messages_from_local_update() -> str:
    """
    Send messages to guests based on the updates table in the database.
    
    This function retrieves updates from the database that have messages to be 
        sent and have not yet been marked as sent.
    
    Depending on the type of message, it sends the appropriate messages to 
        guests, such as Airbnb arrival form messages or WhatsApp prompts for guest 
        registration and arrival forms.
    
    Args:
        start: The start date for retrieving updates. If not provided, 
            it defaults to a calculated date range.
        end: The end date for retrieving updates. If not provided, 
            it defaults to a calculated date range.
        
    Returns:
        A string summarizing the number of messages sent for each type.
    """
    user = get_user(DEFAULT_ACCOUNT)
    sender = DEFAULT_ACCOUNT.emailAddress
    subject = 'LOCAL UPDATE RUN REQUIRED'
    messages = get_inbox(user=user, sender=sender, subject=subject)

    if not messages:
        return 'No messages found in inbox for additional local updating.'
    
    database = get_database()
   
    reviewAirbnbGuests = False
    updateVrboArrivals = False
    sendAirbnb4Weeks = []
    sendWhatsAppGuestReg = []
    sendWhatsApp4Weeks = []
    for message in messages:
     
        for para in HTML(message.body.body).findAll('p'):
            p: str = para.text.strip()
            if not p.startswith('-- '):
                continue
            if 'a review for' in p.lower():
                reviewAirbnbGuests = True
                continue
            if 'vrbo arrival' in p.lower():
                updateVrboArrivals = True
                continue
            bookingId = int(p.split(':')[0].strip('-- '))
            if 'Airbnb:Arrival Form' in p:
                sendAirbnb4Weeks += get_four_weeks_bookings(database, bookingId=bookingId)
            elif 'WhatsApp:Arrival Form' in p:
                sendWhatsApp4Weeks += get_four_weeks_bookings(database, bookingId=bookingId)
            elif 'WhatsApp:Guest Registration Form' in p:
                sendWhatsAppGuestReg += get_guest_registration_form_bookings(database, bookingId=bookingId)

    if sendAirbnb4Weeks:
        send_airbnb_arrival_form_messages(bookings=sendAirbnb4Weeks)
    
    if sendWhatsAppGuestReg:
        send_whatsapp_prompts_for_guest_registration_forms(bookings=sendWhatsAppGuestReg)

    if sendWhatsApp4Weeks:
        send_whatsapp_prompts_for_guest_arrival_forms(bookings=sendWhatsApp4Weeks)

    if updateVrboArrivals:
        update_from_vrbo()

    if reviewAirbnbGuests:
        review_airbnb_guests()

    for message in messages:
        message.delete()

    database.close()
    return f'Sent {len(sendAirbnb4Weeks)} Airbnb arrival form messages, {len(sendWhatsAppGuestReg)} ' \
           f'WhatsApp guest registration form messages, and {len(sendWhatsApp4Weeks)} WhatsApp ' \
           'arrival form messages.'