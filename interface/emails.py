from correspondence.guest.arrival.balance_payment.information.run import send_balance_payment_information_email
from correspondence.guest.arrival.balance_payment.reminder.run import send_balance_payment_emails
from correspondence.guest.arrival.four_weeks.run import send_guest_four_weeks_emails
from correspondence.guest.arrival.instructions.two_days.run import send_two_days_instructions_emails
from correspondence.guest.arrival.instructions.two_weeks.run import send_two_weeks_instructions_emails
from correspondence.guest.arrival.registration.run import send_guest_registration_emails
from correspondence.guest.arrival.security_deposit.run import send_security_deposit_request_emails
from correspondence.guest.arrival.warning.run import send_guest_warning_email
from correspondence.guest.departure.after_check_out.run import send_after_check_out_email
from correspondence.guest.departure.final_days.run import send_final_day_reminder_emails
from correspondence.guest.departure.goodbye.run import send_goodbye_emails
from correspondence.guest.departure.outbound_transfer.run import send_outbound_transfer_confirmation_email
from correspondence.internal.accountancy.security_deposits.run import send_security_deposit_returns_email
from correspondence.internal.management.arrivals.run import send_management_arrivals_emails
from correspondence.internal.management.cleans.run import send_management_cleans_emails
from correspondence.internal.management.transfers.run import send_airport_transfers_request_emails
from correspondence.owner.four_weeks.run import send_owner_four_weeks_emails
from default.booking.booking import Booking
from forms.arrival.guest.run import send_whatsapp_prompts as send_arrival_form_whatsapp_prompt
from forms.registration.run import send_whatsapp_prompts as send_guest_registration_whatsapp_prompt
from forms.registration.run import send_new_guest_registration_to_owner_email
from interfaces.interface import Interface


def send_emails(subsection: Interface, booking: Booking) -> None:
    """
    Send email communications for a specific booking.
    
    Presents a menu of email types that can be sent and processes the user's
    selection. Different email types are sent based on booking properties
    such as owner status and cleaning arrangements.
    
    Parameters:
        subsection: Interface object for user interaction
        booking: Booking object containing all booking information
    
    Returns:
        None if user exits, otherwise recursively continues sending emails
    """
    bookingId = booking.details.id
    emails = [
        'Balance Payment Due',
        'Balance Payment Information',
        'Arrival Questionnaire',
        'Security Deposit',
        'Arrival Information',
        'Guest Registration',
        'Check-in Instructions',
        'Guest Warning',
        'Outbound Airport Transfer Confirmation',
        'Final Days Reminder',
        'Staying After Check-out',
        'Goodbye',
        'Management',
        'Airport Transfers Request',
        'Security Deposit Return',
        'Send WhatsApp Prompt for Arrival Questionnaire',
        'Send WhatsApp Prompt for Guest Registration',
        'Guest Registration Form to Owner',
    ]
    
    subsection.section('Sending emails for selected booking. Which?')
    email = subsection.option(emails)
    
    if email is None:
        return None
    
    if email == 1:
        send_balance_payment_emails(bookingId=bookingId)
    elif email == 2:
        send_balance_payment_information_email(bookingId=bookingId)
    elif email == 3:
        if booking.details.isOwner:
            send_owner_four_weeks_emails(bookingId=bookingId)
        else:
            send_guest_four_weeks_emails(bookingId=bookingId)
    elif email == 4:
        send_security_deposit_request_emails(bookingId=bookingId)
    elif email == 5:
        send_two_weeks_instructions_emails(bookingId=bookingId)
    elif email == 6:
        send_guest_registration_emails(bookingId=bookingId)
    elif email == 7:
        send_two_days_instructions_emails(bookingId=bookingId)
    elif email == 8:
        send_guest_warning_email(bookingId=bookingId)
    elif email == 9:
        send_outbound_transfer_confirmation_email(bookingId=bookingId)
    elif email == 10:
        send_final_day_reminder_emails(bookingId=bookingId)
    elif email == 11:
        send_after_check_out_email(bookingId=bookingId)
    elif email == 12:
        send_goodbye_emails(bookingId=bookingId)
    elif email == 13:
        if booking.property.weClean:
            send_management_cleans_emails(bookingId=bookingId)
        else:
            send_management_arrivals_emails(bookingId=bookingId)
    elif email == 14:
        send_airport_transfers_request_emails(bookingId=bookingId)
    elif email == 15:
        send_security_deposit_returns_email(bookingId=bookingId)
    elif email == 16:
        send_arrival_form_whatsapp_prompt(bookingId=bookingId)
    elif email == 17:
        send_guest_registration_whatsapp_prompt(bookingId=bookingId)
    elif email == 18:
        send_new_guest_registration_to_owner_email(booking=booking)

    return send_emails(subsection, booking)


def update_emails(subsection: Interface, booking: Booking) -> None:
    """
    Update email status flags for a specific booking.
    
    Presents a menu of email types whose status can be modified and processes
    the user's selection. Allows for setting emails as sent or unsent, or pausing
    email communications entirely.
    
    Parameters:
        subsection: Interface object for user interaction
        booking: Booking object to update email status flags
    
    Returns:
        None if user exits, otherwise recursively continues updating email flags
    """
    emails = [
        'Balance Payment',
        'Arrival Questionnaire',
        'Security Deposit',
        'Arrival Information',
        'Guest Registration',
        'Check-in Instructions',
        'Final Days Reminder',
        'Goodbye',
        'Management',
        'Airport Transfers Request',
        'Guest Registration to Owner',
        'Pause Emails',
    ]
    
    subsection.section('Setting emails for selected booking. Which?')
    email = subsection.option(emails)
    
    if email is None:
        return None
    
    boolean = subsection.bool('Set email to sent (1) or unsent (0) ?')
    
    if email == 1:
        booking.emails.balancePayment = boolean
    elif email == 2:
        booking.emails.arrivalQuestionnaire = boolean
    elif email == 3:
        booking.emails.securityDepositRequest = boolean
    elif email == 4:
        booking.emails.arrivalInformation = boolean
    elif email == 5:
        booking.emails.guestRegistrationForm = boolean
    elif email == 6:
        booking.emails.checkInInstructions = boolean
    elif email == 7:
        booking.emails.finalDaysReminder = boolean
    elif email == 8:
        booking.emails.goodbye = boolean
    elif email == 9:
        booking.emails.management = boolean
    elif email == 10:
        booking.emails.airportTransfers = boolean
    elif email == 11:
        booking.emails.guestRegistrationFormToOwner = boolean
    elif email == 12:
        booking.emails.paused = boolean
    
    booking.update()
    
    return update_emails(subsection, booking)