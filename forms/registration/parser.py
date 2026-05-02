from web.html import HTML


class PIMSGuestRegistrationParser(HTML):
    """
    Parser for PIMS guest registration HTML forms.
    
    This class extracts guest information from PIMS registration forms,
    particularly passport details and issuing authority.
    """
    
    def __init__(self, html: str | None = None, firstName: str | None = None, 
                lastName: str | None = None) -> None:
        """
        Initialize the PIMS guest registration parser.
        
        Args:
            html: HTML content to parse.
            firstName: Guest's first name to help identify the correct form fields.
            lastName: Guest's last name to help identify the correct form fields.
        """
        super().__init__(html, 'div', 'id', 'responsive-table')
        self._firstName = firstName
        self._lastName = lastName
        self._guest_number_in_form = None

    # Guest information properties
    @property
    def firstName(self) -> str | None:
        """
        Get the guest's first name.
        
        Returns:
            The guest's first name or None if not set.
        """
        return self._firstName

    @firstName.setter
    def firstName(self, value: str | None) -> None:
        """
        Set the guest's first name.
        
        Args:
            value: The first name to set.
        """
        self._firstName = value

    @property
    def lastName(self) -> str | None:
        """
        Get the guest's last name.
        
        Returns:
            The guest's last name or None if not set.
        """
        return self._lastName
    
    @lastName.setter
    def lastName(self, value: str | None) -> None:
        """
        Set the guest's last name.
        
        Args:
            value: The last name to set.
        """
        self._lastName = value

    # HTML content properties
    @property
    def html(self) -> str | None:
        """
        Get the HTML content being parsed.
        
        Returns:
            The HTML content or None if not set.
        """
        return self._html

    @html.setter
    def html(self, value: str | None) -> None:
        """
        Set the HTML content to parse, resetting any previous parsing state.
        
        Args:
            value: The HTML content to parse.
        """
        self._html = value
        self._guest_number_in_form = None
        self._soup = self._strain()
    
    # Guest registration data properties
    @property
    def hasInfo(self) -> bool:
        """
        Check if the form contains passport information.
        
        Returns:
            True if passport information is present, False otherwise.
        """
        for input_field in self.findAll('input', attrs={'type': 'text'}):
            if 'passportno' in input_field['name']: 
                return bool(input_field['value'])
        return False

    @property
    def passport(self) -> str | None:
        """
        Get the passport number from the form.
        
        Returns:
            The passport number or None if not found.
        """
        return self.soupValue('passportno_' + self._guest_number())
    
    @property
    def issuer(self) -> str | None:
        """
        Get the passport issuing authority from the form.
        
        Returns:
            The issuing authority or None if not found.
        """
        option = self.soupSelectedOption('issuedby_' + self._guest_number_in_form)
        return option.text if option else None

    # Private helper methods
    def _guest_number(self) -> str:
        """
        Get the guest number in the form, finding it if not already cached.
        
        Returns:
            The guest number string used in form field identifiers.
        """
        if not hasattr(self, '_guest_number_in_form') or self._guest_number_in_form is None:
            self._guest_number_in_form = self._find_guest_number()
        return self._guest_number_in_form
    
    def _find_guest_number(self) -> str:
        """
        Find the guest number by matching name variations in the form.
        
        Returns:
            The guest number string extracted from form field names.
        """
        for name in self._names():
            if not name:
                continue
                
            for version in self._versions_of_name(name):
                try: 
                    return self.find(attrs={'value': version})['name'].split('_')[-1]
                except Exception: 
                    continue
                    
        # Fallback to finding any text input field
        try:
            return self.find(attrs={'type': 'text'})['name'].split('_')[-1]
        except Exception:
            return "1"  # Default value if nothing can be found

    def _versions_of_name(self, name: str) -> tuple[str, str, str, str]:
        """
        Generate different case variations of a name.
        
        Args:
            name: The name to generate variations for.
            
        Returns:
            A tuple containing original, lowercase, capitalized, and uppercase versions.
        """
        return (
            name,
            name.lower(),
            name.capitalize(),
            name.upper(),
        )

    def _names(self) -> tuple[str | None, str | None]:
        """
        Get the first and last name as a tuple.
        
        Returns:
            A tuple containing the first and last name.
        """
        return (
            self.firstName,
            self.lastName,
        )