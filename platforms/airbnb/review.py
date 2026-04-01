import datetime
import regex as re

from apis.google.mail.message import GoogleMailMessage
from apis.google.mail.messages import GoogleMailMessages
from default.google.mail.functions import get_default_user
from default.update.dates import updatedates
from default.update.wrapper import update
from platforms.airbnb.browser import BrowseAirbnb
from platforms.functions import threeX
from utils import sublog


@update
def review_airbnb_guests(start: datetime.date = None, end: datetime.date = None) -> str:
    """
    Review Airbnb guests.

    Args:
        start (datetime.date, optional): Start date for the review. Defaults to None.
        end (datetime.date, optional): End date for the review. Defaults to None.

    Returns:
        str: Message indicating the status of the review process.
    """
    if not start or not end:
        start, end = updatedates.review_airbnb_guests_dates()

    messages = _get_airbnb_reviews_box(start, end)
    if not messages:
        return 'No reviews to be done today!'
    
    linksNames = []
    for message in messages:
        if message.date < start or message.date > end:
            if 'last chance' not in message.subject.lower():
                continue
        name_s = _get_name_s(message)
        if not name_s:
            sublog(f'No guest name found in message: {message.subject}')
            continue
        link = _get_link(message)
        linksNames.append((link, name_s, message))

    if not linksNames:
        return 'No reviews to be done today!'

    # Open the browser and navigate to the review page
    browser = BrowseAirbnb().goTo().login()
    for link, name_s, message in linksNames:
        _review_guest(browser, link, name_s, message)
    
    browser.quit()
    return 'Most recent guests have been reviewed!'


def _get_name_s(message: GoogleMailMessage) -> str:
    """
    Get the name(s) of the guest(s) from the email subject.
    
    Args:
        message (GoogleMailMessage): The email message object.
    
    Returns:
        str: The name(s) of the guest(s).
    """
    # Example subject lines:
    #Write a review for Kulapey’s group
    #Write a review for Jasmine and Callum
    string = message.subject
    search = string.split(' for ')
    if len(search) < 2:
        if 'wrote you' in string.lower():
            return None
        if 'last chance' not in string.lower():
            raise Exception(
                f'Guest name(s) not found in subject: {string}')
        search = string.split(' to review ')
  
    search = search[-1]
    apostrophe = re.search('(\'s|´s|’s)', search)
    if not apostrophe:
        return search
    return search.split(apostrophe.group(1))[0]


def _get_link(message: GoogleMailMessage) -> str:
    """
    Get the link to the guest review from the email body.

    Args:
        message (GoogleMailMessage): The email message object.
    
    Returns:
        str: The link to the guest review.

    Raises:
        Exception: If the link is not found in the email body.
    """
    string = message.body.body.lower()
    search = re.search(r'write a review\[(.*?)\]', string)
    if not search:
        search = re.search(r'Last chance to review\[(.*?)\]', string)
        return None
    return search.group(1)


def _get_airbnb_reviews_box(
    start: datetime.date, 
    end: datetime.date
) -> list[GoogleMailMessage]:
    """
    Get messages from 'Airbnb Reviews' folder in default user's email

    Args:
        start (datetime.date): Start date for the search
        end (datetime.date): End date for the search

    Returns:
        list (GoogleMailMessage): Messages matching the given dates
    """
    search: GoogleMailMessages = get_default_user()
    search.folder('Airbnb Reviews')
    search.sender('automated@airbnb.com')
    #search.start(start)
    #search.end(end)
    return search.list


@threeX
def _review_guest(
    browser: BrowseAirbnb, 
    link: str, 
    name_s: str, 
    message: GoogleMailMessage
) -> None:
    sublog(f'Reviewing guest(s): {name_s}')
    browser.reviewGuest(link, name_s)
    browser.wait(3)
    message.delete()