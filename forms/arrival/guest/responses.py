from forms.arrival.responses import ArrivalFormResponses
from forms.arrival.vars import GUEST_PHONE_NUMBER

class GuestArrivalFormResponses(ArrivalFormResponses):
    """
    Handles responses from guest arrival forms.
    
    This class extends ArrivalFormResponses with guest-specific functionality
    including email and phone number handling.
    """
    _email: str | None = None
    _phone: str = '2716f7d4'
    
    def __init__(self, load: dict | None = None) -> None:
        """
        Initialize the GuestArrivalFormResponses object.
        
        Args:
            load: Dictionary containing form response data, or None.
        """
        super().__init__(load)

    @property
    def email(self) -> str | None:
        """
        Get the email address from the form responses.
        
        Returns:
            The respondent's email address or None if not available.
        """
        return self._values['respondentEmail']

    @property
    def phone(self) -> str | None:
        """
        Get the phone number from the form responses.
        
        Returns:
            The respondent's phone number or None if not available.
        """
        return self._get(GUEST_PHONE_NUMBER)

    def __str__(self) -> str:
        """
        Return a string representation of the GuestArrivalFormResponses instance.
        
        Returns:
            A formatted string showing email and phone information.
        """ 
        return super().__str__(
            [
                f'email: {self.email}',
                f'phone: {self.phone}',
            ]
        )