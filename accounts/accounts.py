from libraries.google.account import GoogleAccount
import os

try:
    # Check if running in deployed environment (e.g., on a server) 
    # where environment variables are set directly
    os.getenv('LOCAL', 'None').lower() == 'false'
except Exception:
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()

CREDS_DIR = os.path.abspath(os.getenv('CREDS_DIR', None))

class ThomasAtABA(GoogleAccount):
    """
    Google Account for Thomas at Algarve Beach Apartments.
    
    This class represents Thomas Bogg's Google account with contact information
    and credentials for API access.
    """

    _details: list = os.environ.get('ThomasAtABA').split(';')

    
    def __init__(self, pathToCredentials: str = CREDS_DIR) -> None:
        """
        Initialize the Thomas Bogg Google Account.
        
        Args:
            pathToCredentials: Directory path where API credentials are stored.
        """
        super().__init__()
        self.name: str = self._details[0]
        self.emailAddress: str = self._details[1]
        self.phoneNumber: str = self._details[2]
        self.details: list[str] = self._details[3:]
        self.pathToCredentials: str = pathToCredentials


class KevinAtABA(GoogleAccount):
    """
    Google Account for Kevin at Algarve Beach Apartments.
    
    This class represents Kevin Bogg's Google account with contact information
    and credentials for API access.
    """

    _details: list = os.environ.get('KevinAtABA').split(';')
    
    def __init__(self, pathToCredentials: str = CREDS_DIR) -> None:
        """
        Initialize the Kevin Bogg Google Account.
        
        Args:
            pathToCredentials: Directory path where API credentials are stored.
        """
        super().__init__()
        self.name: str = self._details[0]
        self.emailAddress: str = self._details[1]
        self.phoneNumber: str = self._details[2]
        self.details: list[str] = self._details[3:]
        self.pathToCredentials: str = pathToCredentials


class TeamAtABA(GoogleAccount):
    """
    Google Account for the Management Team at Algarve Beach Apartments.
    
    This class represents the shared account for the management team with contact
    information and credentials for API access.
    """

    _details: list = os.environ.get('TeamAtABA').split(';')
    
    def __init__(self, pathToCredentials: str = CREDS_DIR) -> None:
        """
        Initialize the Management Team Google Account.
        
        Args:
            pathToCredentials: Directory path where API credentials are stored.
        """
        super().__init__()
        self.name: str = self._details[0]
        self.emailAddress: str = self._details[1]
        self.phoneNumber: str = self._details[2]
        self.details: list[str] = self._details[3:]
        self.pathToCredentials: str = pathToCredentials