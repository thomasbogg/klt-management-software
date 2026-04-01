import datetime

from default.dates import dates
from utils import gen_hex

from apis.google.forms.form import GoogleForm


class GuestRegistrationFormResponses(GoogleForm.Responses):
    """
    A class that handles responses from guest registration forms.
    
    This class extends FormReponses to provide specific functionality for
    processing guest registration data, including conversion of data for
    SEF (Portuguese Immigration Service) submission format.
    
    Args:
        load (dict | None): Optional dictionary containing form response data.
            Defaults to None.
    """

    def __init__(self, load: dict | None = None) -> None:
        """
        Initialize the GuestRegistrationFormResponses instance.
        
        Args:
            load (dict | None): Optional dictionary containing form response data.
                Defaults to None.
        """
        super().__init__(load=load)
        self._guest: int = 0

    def _get(self, num: str) -> str:
        """
        Get a response value for the current guest using a question number.
        
        Args:
            num (str): The question number identifier.
            
        Returns:
            str: The response value for the specified question.
        """
        return super()._get(gen_hex(self._guest, num))

    @property
    def guest(self) -> int:
        """
        Get the current guest number.
        
        Returns:
            int: The current guest number.
        """
        return self._guest
    
    @guest.setter
    def guest(self, value: int) -> None:
        """
        Set the current guest number.
        Use only after checking if guest has a NIF number.
        
        Args:
            value (int): The guest number to set.
        """
        self._guest = value

    @property
    def hasNIFNumber(self) -> bool:
        """
        Check if the current guest has a NIF (Número de Identificação Fiscal).
        
        Returns:
            bool: True if the guest has a NIF number, False otherwise.
        """
        return self._get('0') == 'Yes'

    @property
    def firstName(self) -> str:
        """
        Get the first name of the current guest.
        
        Returns:
            str: The first name.
        """
        return self._get('1')

    @property
    def lastName(self) -> str:
        """
        Get the last name of the current guest.
        
        Returns:
            str: The last name.
        """
        return self._get('2')

    @property
    def dateOfBirth(self) -> datetime.date:
        """
        Get the date of birth of the current guest.
        
        Returns:
            datetime.date: The date of birth.
        """
        value = self._get('3')
        year, month, day = value.split('-')
        return dates.date(year, month, day)
    
    @property
    def dateOfBirthForSEF(self) -> str:
        """
        Get the date of birth formatted for SEF submission.
        
        Returns:
            str: The date of birth in ISO format.
        """
        return dates.convertToDateTime(self.dateOfBirth).isoformat()

    @property
    def placeOfBirth(self) -> str:
        """
        Get the place of birth of the current guest.
        
        Returns:
            str: The country name of birth.
        """
        return self._get('4').split(' - ')[0]

    @property
    def placeOfBirthForSEF(self) -> str:
        """
        Get the place of birth formatted for SEF submission.
        
        Returns:
            str: The country code of birth.
        """
        return self._get('4').split(' - ')[-1]

    @property
    def nationality(self) -> str:
        """
        Get the nationality of the current guest.
        
        Returns:
            str: The nationality country name.
        """
        return self._get('5').split(' - ')[0]

    @property
    def nationalityForSEF(self) -> str:
        """
        Get the nationality formatted for SEF submission.
        
        Returns:
            str: The nationality country code.
        """
        return self._get('5').split(' - ')[-1]

    @property
    def countryOfResidence(self) -> str:
        """
        Get the country of residence of the current guest.
        
        Returns:
            str: The country of residence name.
        """
        return self._get('6').split(' - ')[0]

    @property
    def countryOfResidenceForSEF(self) -> str:
        """
        Get the country of residence formatted for SEF submission.
        
        Returns:
            str: The country of residence code.
        """
        return self._get('6').split(' - ')[-1]

    @property
    def identificationType(self) -> str:
        """
        Get the type of identification document of the current guest.
        
        Returns:
            str: The identification type (e.g., 'Passport', 'ID Card').
        """
        return self._get('7')

    @property
    def identificationTypeForSEF(self) -> str:
        """
        Get the identification type formatted for SEF submission.
        
        Returns:
            str: The identification type code ('P' for Passport, 'B' for ID Card).
        """
        value = self._get('7')
        if value == 'Passport':
            return 'P'
        return 'B'

    @property
    def identificationNumber(self) -> str:
        """
        Get the identification number of the current guest.
        
        Returns:
            str: The identification document number.
        """
        return self._get('8')

    @property
    def identificationIssuer(self) -> str:
        """
        Get the issuer of the identification document.
        
        Returns:
            str: The issuing country name.
        """
        return self._get('9').split(' - ')[0]

    @property
    def identificationIssuerForSEF(self) -> str:
        """
        Get the identification issuer formatted for SEF submission.
        
        Returns:
            str: The issuing country code.
        """
        return self._get('9').split(' - ')[-1]
    
    @property
    def address(self) -> str | None:
        """
        Get the address of the lead guest only.
        
        Returns:
            str | None: The address if this is the lead guest (guest 1), 
                otherwise None.
        """
        if self._guest > 1:
            return None
        return self._get('10')