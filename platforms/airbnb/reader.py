from apis.google.mail.message import GoogleMailMessage
from platforms.reader import ReadPlatformEmails
import regex as re


class ReadAirbnbEmails(ReadPlatformEmails):
    """
    Process Airbnb notification emails to extract booking information.
    
    This class parses Airbnb emails to identify new bookings, updated bookings,
    and cancelled bookings by extracting booking IDs from email subjects and bodies.
    """

    def __init__(self, messages: list[GoogleMailMessage]) -> None:
        """
        Initialize and process Airbnb email messages.
        
        Args:
            messages: A list of Google Mail messages from Airbnb.
        """
        super().__init__(messages)
        self._newBookings = self._get_ids_from_bodies('confirmed', dict(), 0)
        self._updatedBookings = self._get_ids_from_bodies('updated', list(), 0)
        self._updatedBookings += self._get_ids_from_bodies('change', list(), 0)
        self._cancelledBookings = self._get_ids_from_subjects('cancel', list(), 0)

    #######################################################
    # PROPERTY ACCESSORS
    #######################################################

    @property
    def newBookings(self) -> list[str]:
        """
        Get the list of new booking IDs.
        
        Returns:
            List of new booking IDs extracted from emails.
        """
        return self._newBookings
        
    @property
    def updatedBookings(self) -> list[str]:
        """
        Get the list of updated booking IDs.
        
        Returns:
            List of updated booking IDs extracted from emails.
        """
        return self._updatedBookings
    
    @property
    def cancelledBookings(self) -> list[str]:
        """
        Get the list of cancelled booking IDs.
        
        Returns:
            List of cancelled booking IDs extracted from emails.
        """
        return self._cancelledBookings

    #######################################################
    # EMAIL PARSING FUNCTIONS
    #######################################################
    
    def _get_ids_from_bodies(self, keyword: str, ids: list[str] | dict[str, str], i: int) -> list[str]:
        """
        Extract booking IDs from email bodies that contain a specific keyword.
        
        Args:
            keyword: The keyword to search for in email subjects.
            ids: Accumulator list of booking IDs.
            i: Current index in the email list.
            
        Returns:
            Updated list of booking IDs.
        """
        if len(self._all) < i + 1:
            return ids
            
        message: GoogleMailMessage = self._all[i]
        subject = message.subject
        
        if keyword not in subject.lower():
            return self._get_ids_from_bodies(keyword, ids, i + 1) 
            
        self._mark_as_read(i)
        booking_id = self.get_booking_id_from_body(message.body.plain().body)
        host_service_fee = self.get_host_service_fee_from_body(message.body.plain().body)
        
        if booking_id:
            if keyword == 'confirmed':
                ids[booking_id] = host_service_fee
            else:
               ids.append(booking_id)
            
        return self._get_ids_from_bodies(keyword, ids, i)
    
    def _get_ids_from_subjects(self, keyword: str, ids: list[str], i: int) -> list[str]:
        """
        Extract booking IDs from email subjects that contain a specific keyword.
        
        Args:
            keyword: The keyword to search for in email subjects.
            ids: Accumulator list of booking IDs.
            i: Current index in the email list.
            
        Returns:
            Updated list of booking IDs.
        """
        if len(self._all) < i + 1: 
            return ids
            
        subject = self._all[i].subject
        
        if keyword not in subject.lower(): 
            return self._get_ids_from_subjects(keyword, ids, i + 1) 
            
        self._mark_as_read(i)
        booking_id = self.get_booking_id_from_subject(subject)
        
        if booking_id:
            ids.append(booking_id)
            
        return self._get_ids_from_subjects(keyword, ids, i)

    def get_booking_id_from_subject(self, subject: str) -> str | None:
        """
        Extract a booking ID from an email subject line.
        
        Args:
            subject: The email subject to parse.
            
        Returns:
            The booking ID if found, None otherwise.
        """
        search = re.search(r'(HM[A-Z0-9]+)', subject)
        return search.group(1) if search else None
        
    def get_booking_id_from_body(self, body: str) -> str | None:
        """
        Extract a booking ID from an email body.
        
        Args:
            body: The email body text to parse.
            
        Returns:
            The booking ID if found, None otherwise.
        """
        search = re.search(r'/details/([A-Z0-9]+)\?', body)
        return search.group(1) if search else None

    def get_host_service_fee_from_body(self, body: str) -> str:
        """
        Extract the host service fee from an email body.
        
        Args:
            body: The email body text to parse.
        
        """
        search = re.search(r'Host service fee \(3.0%\) +\-€([\d\.,\s]+)\n', body)
        return search.group(1) if search else ''