from apis.google.mail.message import GoogleMailMessage
from default.settings import TEST
from utils import Object


class ReadPlatformEmails(Object):
    """
    Class for reading, processing, and managing platform booking emails.
    
    Provides functionality to track which emails have been read and
    delete them once processed. Maintains separate lists for unprocessed
    and processed messages.
    
    Attributes:
        _all: List of unprocessed GoogleMailMessage objects
        _read: List of already processed GoogleMailMessage objects
    """
    
    def __init__(self, messages: list[GoogleMailMessage]):
        """
        Initialize with a list of platform emails to process.
        
        Parameters:
            messages: List of Google Mail messages to process
        """
        super().__init__()
        self._all: list[GoogleMailMessage] = messages
        self._read: list[GoogleMailMessage] = list()

    def deleteRead(self) -> 'ReadPlatformEmails':
        """
        Delete all messages that have been marked as read.
        
        In test mode, no messages are actually deleted.
        
        Returns:
            Self for method chaining
        """
        if TEST:
            return self
       
        for message in self._read: 
            message.delete()
        self._read = list()
        return self

    def _mark_as_read(self, i: int) -> 'ReadPlatformEmails':
        """
        Mark a message as read by moving it from the unprocessed to processed list.
        
        Parameters:
            i: Index of the message in the unprocessed list
            
        Returns:
            Self for method chaining
        """
        if i < len(self._all):
            self._read.append(self._all.pop(i))
        return self
    
    def __str__(self) -> str:
        """
        Get string representation showing the subjects of all unprocessed messages.
        
        Returns:
            Newline-separated list of message subjects
        """
        return '\n'.join([message.subject for message in self._all])