from accounts.accounts import KevinAtABA, TeamAtABA, ThomasAtABA
from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from correspondence.drafts.functions import (
    get_guest_email_addresses,
    get_owner_email_addresses
)
from datetime import date
from default.google.mail.functions import get_user, send_email
from default.guest.guest import Guest
from default.property.property import Property
from interface.functions import get_location_criteria
from interfaces.interface import Interface
from utils import logerror


#######################################################
# MAIN FUNCTION
#######################################################

def send_draft_email_message() -> str:
    """
    Orchestrates the process of sending draft emails to multiple recipients.
    
    Guides the user through selecting an account, draft message, and recipient 
    criteria, then sends the emails to the selected recipients.
    
    Returns:
        Completion message
    """
    interface = Interface(title='draft email sender for multiple recipients')
    sections = interface.subsections()
    user = get_user_account(sections)
    message = get_draft_email_message(sections, user)
   
    criteria = {}
    criteria.update(get_recipients_criteria(sections))
    criteria.update(get_location_criteria(sections))
    criteria.update(get_group_criteria(sections))
    criteria.update(get_excluded_properties(sections))

    if 'guests' in criteria.values():
        sections.log('STARTING to send emails to guests...')
        recipients = get_guest_email_addresses(**criteria)
    else:
        sections.log('STARTING to send emails to owners...')
        recipients = get_owner_email_addresses(**criteria)

    send_messages(user, message, recipients, sections)    
    return sections.log('FINISHED sending all emails.')


#######################################################
# USER INTERACTION FUNCTIONS
#######################################################

def get_user_account(sections: Interface) -> GoogleMailMessages:
    """
    Gets the user account to send emails from.
    
    Parameters:
        sections: Interface object for user interaction
        
    Returns:
        The selected GoogleMailMessages object
    """
    sections.section('Email account to use')
    account = sections.option(('Kevin', 'Thomas', 'Team'))
    
    if account == 1: 
        return get_user(KevinAtABA())
    elif account == 2: 
        return get_user(ThomasAtABA())
    else: 
        return get_user(TeamAtABA())


def get_draft_email_message(sections: Interface, user: GoogleMailMessages) -> GoogleMailMessage:
    """
    Retrieves a draft email message from the given account.
    
    Parameters:
        sections: Interface object for user interaction
        user: GoogleMailMessages object to retrieve draft from
        
    Returns:
        The retrieved draft message
    """
    sections.section('Subject of email')
    subject = sections.text('Type draft email to retrieve subject here:')
    messages = user.drafts().subject(subject).list
    
    if messages: 
        if len(messages) > 1:
            sections.log('More than one draft found. Please be more specific.')
            return get_draft_email_message(sections, user)
        sections.log(f'Email successfully retrieved: {messages[0].subject}')
        return messages[0]
    else: 
        sections.log('Email NOT retrieved. Please try again.')
    
    return get_draft_email_message(sections, user)


#######################################################
# RECIPIENT SELECTION FUNCTIONS
#######################################################

def get_recipients_criteria(sections: Interface) -> dict[str, str | date | None]:
    """
    Gets criteria for selecting email recipients.
    
    Parameters:
        sections: Interface object for user interaction
        
    Returns:
        Dictionary containing recipient type and date range criteria
    """
    sections.section('Send Criteria')
    sections.section('Is this email for guests or owners?')
    recipient = sections.option(('Guests', 'Owners'))
    start = None
    end = None
    
    if recipient == 1:
        subsections = sections.subsections()
        subsections.section('What is the time period that the email concerns?')
        start = subsections.date('Type START date')
        end = subsections.date('Type END date')
    
    return {
        'recipient': 'guests' if recipient == 1 else 'owners', 
        'start': start, 
        'end': end
    }


def get_group_criteria(sections: Interface) -> dict[str, bool | None]:
    """
    Gets property group criteria for selecting email recipients.
    
    Parameters:
        sections: Interface object for user interaction
        
    Returns:
        Dictionary containing property group criteria
    """
    sections.section('Finally, is it for all KLT properties in given location or more specific?')
    group = sections.option(
        (
            'All KLT properties', 
            'Only ABA', 
            'Only KKLJ', 
            'Only AL Licensed'
        )
    )
    
    if group in (1, None):
        return {'weBook': None, 'hasAl': None}
    if group == 2:
        return {'weBook': True, 'hasAl': None}
    if group == 3:
        return {'weBook': False, 'hasAl': None}
    if group == 4:
        return {'weBook': None, 'hasAl': True}
    
    return logerror('Invalid group criteria. Please try again.')


def get_excluded_properties(sections: Interface) -> dict[str, list[str]]:
    """
    Gets list of properties to exclude from email recipients.
    
    Parameters:
        sections: Interface object for user interaction
        
    Returns:
        Dictionary containing list of properties to exclude
    """
    sections.section('Oh, and one last thought, are there any properties we should exclude?')
    excluded = sections.text('Type properties separated by comma')
    
    if excluded is None: 
        return {} 

    return {'notShortNames': [exc.upper() for exc in excluded.split(', ')]}


#######################################################
# EMAIL SENDING FUNCTIONS
#######################################################

def send_messages(
    user: GoogleMailMessages,
    message: GoogleMailMessage, 
    recipients: list[Property.owner] | list[Guest], 
    sections: Interface
) -> None:
    """
    Sends the email message to all recipients.
    
    Parameters:
        message: The email message to send
        recipients: List of recipient objects with email and name attributes
        sections: Interface object for user interaction
    """
    sections.log('PREPARING to send emails now...')
    done = []
    
    for recipient in recipients:
        address = recipient.email
        name = recipient.name
        
        if not address:
            sections.sublog(f'Got NO Email address for {name}. Skipping.')

        if address in done:
            continue
            
        message.to = address
        message.greeting.name = name
        send_email(user, message, checkSent=True)
        done.append(address)


#######################################################
# SCRIPT ENTRY POINT
#######################################################

if __name__ == '__main__':
    send_draft_email_message()