from correspondence.guest.arrival.four_weeks.run import send_airbnb_arrival_form_messages, get_four_weeks_bookings
from forms.registration.run import send_whatsapp_prompts_for_guest_registration_forms, get_guest_registration_form_bookings
from forms.arrival.guest.run import send_whatsapp_prompts_for_guest_arrival_forms, get_guest_arrival_form_bookings
from default.database.functions import get_database, search_updates
from default.update.wrapper import update
from default.update.dates import updatedates
from datetime import datetime

@update
def send_messages_from_updates_table(start: datetime = None, end: datetime = None) -> str:
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
    if not start or not end:
        start, end = updatedates.send_messages_from_updates_table_dates()

    updates_search = search_updates(start=start, end=end)
    where = updates_search.updates.where()
    where.messages().isNotNullEmptyOrFalse()
    where.emailSent().isNullEmptyOrFalse()
    updates = updates_search.fetchall()
    updates_search.close()

    if not updates:
        return 'Got no new messages to send locally!'
    
    database = get_database()
    airbnbBookings = list()
    whatsAppGuestReg = list()
    whatsAppArrivalForm = list()
   
    for update in updates:
        if update.messages == 'Airbnb:Arrival Form.':
            booking = get_four_weeks_bookings(database, bookingId=update.bookingId)
            if booking:
                airbnbBookings.append(booking)            
        elif update.messages == 'WhatsApp:Guest Registration Form.':
            booking = get_guest_registration_form_bookings(database, bookingId=update.bookingId)
            if booking:
                whatsAppGuestReg.append(booking)            
        elif update.messages == 'WhatsApp:Arrival Form.':
            booking = get_guest_arrival_form_bookings(database, bookingId=update.bookingId)
            if booking:
                whatsAppArrivalForm.append(booking)            
    
    if airbnbBookings:
        send_airbnb_arrival_form_messages(bookings=airbnbBookings)
    
    if whatsAppGuestReg:
        send_whatsapp_prompts_for_guest_registration_forms(bookings=whatsAppGuestReg)

    if whatsAppArrivalForm:
        send_whatsapp_prompts_for_guest_arrival_forms(bookings=whatsAppArrivalForm)

    return f'Sent {len(airbnbBookings)} Airbnb arrival form messages, {len(whatsAppGuestReg)} ' \
           f'WhatsApp guest registration form messages, and {len(whatsAppArrivalForm)} WhatsApp ' \
           'arrival form messages.'