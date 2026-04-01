from datetime import date
import regex as re

from apis.google.mail.message import GoogleMailMessage
from platforms.functions import convert_dates
from platforms.reader import ReadPlatformEmails


class ReadVrboEmails(ReadPlatformEmails):
    """
    Class for reading and processing VRBO email notifications.
    
    Extends ReadPlatformEmails to provide functionality specific to parsing
    VRBO emails for new bookings, updates to existing bookings, and cancellations.
    
    Attributes:
        _newBookings: Dictionary containing new booking information
        _updatedBookings: Dictionary containing updated booking information
        _cancelledBookings: Dictionary containing cancelled booking information
    """

    def __init__(self, messages: list[GoogleMailMessage]) -> None:
        """
        Initialize with a list of VRBO emails to process.
        
        Automatically processes the emails to extract booking information.
        
        Parameters:
            messages: List of Google Mail messages from VRBO
        """
        super().__init__(messages)
        self._newBookings = self._get('instant', {'total': 0}, 0)
        self._updatedBookings = self._get('change', {'total': 0}, 0)
        self._cancelledBookings = self._get('cancel', {'total': 0}, 0)

    #######################################################
    # BOOKING PROPERTIES
    #######################################################
    
    @property
    def newBookings(self) -> dict[str, list[tuple[date, date]]]:
        """
        Get information about new bookings.
        
        Returns:
            Dictionary mapping property IDs to lists of arrival/departure date tuples
        """
        return self._newBookings
    
    @property
    def updatedBookings(self) -> dict[str, list[tuple[date, date]]]:
        """
        Get information about updated bookings.
        
        Returns:
            Dictionary mapping property IDs to lists of arrival/departure date tuples
        """
        return self._updatedBookings
    
    @property
    def cancelledBookings(self) -> dict[str, list[tuple[date, date]]]:
        """
        Get information about cancelled bookings.
        
        Returns:
            Dictionary mapping property IDs to lists of arrival/departure date tuples
        """
        return self._cancelledBookings
    
    #######################################################
    # PRIVATE HELPER METHODS
    #######################################################
    
    def _get(self, keyword: str, bookings: dict, i: int) -> dict[str, list[tuple[date, date]]]:
        """
        Recursively process emails to extract booking information by keyword.
        
        Parameters:
            keyword: String to search for in email subject (e.g., 'instant', 'change', 'cancel')
            bookings: Dictionary to populate with booking information
            i: Current index in the email list
            
        Returns:
            Dictionary containing booking information organized by property ID
        """
        if len(self._all) < i + 1: 
            return bookings
      
        subject = self._all[i].subject.lower()
        if keyword not in subject: 
            return self._get(keyword, bookings, i + 1)     
      
        self._mark_as_read(i)
        bookings['total'] += 1
        
        dates = self._get_dates(subject)    

        if keyword == 'cancel':
            propertyId = self._get_property_id(subject)

            if propertyId not in bookings: 
                bookings[propertyId] = [dates]
            else: 
                bookings[propertyId].append(dates)
        else:
            guestName = self._get_guest_last_name(subject)
        
            if guestName not in bookings: 
                bookings[guestName] = [dates]
            else: 
                bookings[guestName].append(dates)
      
        return self._get(keyword, bookings, i)
    
    def _get_property_id(self, subject: str) -> str:
        """
        Extract VRBO property ID from email subject line.
        
        Parameters:
            subject: Email subject line to parse
            
        Returns:
            Property ID string extracted from the subject
        """
        try: 
            return re.search(r'#([14][1-9][0-9][0-9]+)', subject).group(1)
        except: 
            return re.search(r'id ([14][1-9][0-9][0-9]+)', subject).group(1)

    def _get_guest_last_name(self, subject: str) -> str:
        """
        Extract guest last name from email subject line.
        
        Parameters:
            subject: Email subject line to parse
        Returns:
            Guest last name string extracted from the subject
        """
        return re.search(r'from (.+): ', subject).group(1).split(' ')[-1]

    def _get_dates(self, subject: str) -> tuple[date, date]:
        """
        Extract arrival and departure dates from email subject line.
        
        Parameters:
            subject: Email subject line to parse
            
        Returns:
            Tuple containing (arrival_date, departure_date)
        """
        startEndString = re.search(r': (.+ - .+ 20[0-9]{2})', subject).group(1)
        startString, endString = startEndString.split(' - ')
        return convert_dates(startString, endString)