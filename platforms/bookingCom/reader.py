from datetime import date
import regex as re

from apis.google.mail.message import GoogleMailMessage
from platforms.functions import convert_date
from platforms.reader import ReadPlatformEmails


class ReadBookingComEmails(ReadPlatformEmails):
    """
    Class for reading and processing Booking.com notification emails.
    
    Extends ReadPlatformEmails to provide functionality specific to parsing
    Booking.com emails and extracting booking dates for different properties.
    """

    def __init__(self, messages: list[GoogleMailMessage]):
        """
        Initialize with a list of Booking.com emails to process.
        
        Parameters:
            messages: List of Google Mail messages from Booking.com
        """
        super().__init__(messages)

    #######################################################
    # PROPERTY DATE PROPERTIES
    #######################################################
    
    @property
    def quintaDaBarracudaDates(self) -> tuple[date | None, date | None]:
        """
        Get the earliest and latest booking dates for Quinta da Barracuda.
        
        Returns:
            Tuple of (earliest_date, latest_date) or (None, None) if no dates found
        """
        return self._get_property_dates('Algarve Beach Apartments', list(), 0)

    @property
    def clubeDoMonacoDates(self) -> tuple[date | None, date | None]:
        """
        Get the earliest and latest booking dates for Clube do Monaco.
        
        Returns:
            Tuple of (earliest_date, latest_date) or (None, None) if no dates found
        """
        return self._get_property_dates('Old Town Beach Apartments', list(), 0)

    @property
    def parqueDaCorcovadaDates(self) -> tuple[date | None, date | None]:
        """
        Get the earliest and latest booking dates for Parque da Corcovada.
        
        Returns:
            Tuple of (earliest_date, latest_date) or (None, None) if no dates found
        """
        return self._get_property_dates('Albufeira Corcovada Apartments', list(), 0)

    #######################################################
    # PRIVATE HELPER METHODS
    #######################################################

    def _get_property_dates(
        self, 
        name: str, 
        dates: list[date], 
        i: int
    ) -> tuple[date | None, date | None]:
        """
        Recursively collect booking dates for a specific property.
        
        Parameters:
            name: Property name to search for in email content
            dates: List of dates found so far
            i: Current index in the email list
            
        Returns:
            Tuple of (earliest_date, latest_date) or (None, None) if no dates found
        """
        if len(self._all) < i + 1: 
            return self._first_last_dates_only(dates)

        message = self._all[i]
        if not self._is_property(name, message): 
            return self._get_property_dates(name, dates, i + 1)

        self._mark_as_read(i)
        dates.append(self._get_date(message))
        return self._get_property_dates(name, dates, i)
    
    def _is_property(self, name: str, message: GoogleMailMessage) -> bool:
        """
        Check if an email is related to a specific property.
        
        Parameters:
            name: Property name to search for
            message: Email message to check
            
        Returns:
            True if the email contains the property name, False otherwise
        """
        return re.search(fr'{name}', message.body.plain().body)
    
    def _get_date(self, message: GoogleMailMessage) -> date:
        """
        Extract the booking date from an email message.
        
        Parameters:
            message: Email message to parse
            
        Returns:
            Date object representing the booking date
        """
        dateItemsInSubject = message.subject.split()[-3:]
        dateAsString = ' '.join(dateItemsInSubject)[:-1]
        return convert_date(dateAsString)
        
    def _first_last_dates_only(self, dates: list[date]) -> tuple[date | None, date | None]:
        """
        Extract the earliest and latest dates from a list of dates.
        
        Parameters:
            dates: List of date objects to process
            
        Returns:
            Tuple of (earliest_date, latest_date) or (None, None) if no dates
        """
        if not dates: 
            return None, None

        dates.sort()
        return dates[0], dates[-1]