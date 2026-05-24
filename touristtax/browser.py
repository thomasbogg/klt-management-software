from default.browser.browser import KLTBrowser
from default.property.property import Property
from default.settings import TMT_USERNAME, TMT_PASSWORD, DEFAULT_ACCOUNT
from selenium.webdriver.common.by import By
from default.dates import dates
from typing import Self, Union

from libraries.utils import log, loginput, sublog


class TMTBrowser(KLTBrowser):
    """
    Tourist Tax Management Browser automation class.
    
    This class provides automated browser interactions for the Albufeira
    tourist tax management system (https://taxaturistica.cm-albufeira.pt).
    Inherits from KLTBrowser for base browser functionality.
    
    Args:
        visible (bool): Whether to run browser in visible mode (default: False)
    """
    
    def __init__(self, visible: bool = False) -> None:
        """Initialize the TMT browser with visibility setting."""
        super().__init__(website='TMT Albufeira', visible=visible)

    def goTo(self) -> Self:
        """Navigate to the TMT homepage.
        
        Returns:
            Self: Returns self for method chaining
        """
        return super().goTo('https://taxaturistica.cm-albufeira.pt/ptt/home')

    def login(self) -> Self:
        """Perform login to the TMT system.
        
        Uses credentials from TMT_USERNAME and TMT_PASSWORD settings.
        Clears existing values and enters credentials, then submits form.
        
        Returns:
            Self: Returns self for method chaining
        """
        # Clear and enter username
        self.element(By.ID, 'j_username').clear().input(TMT_USERNAME)
        # Clear and enter password
        self.element(By.ID, 'j_password').clear().input(TMT_PASSWORD)
        # Submit the login form
        self.element(By.XPATH, '//button[@type="submit"]').click()
        return self
    
    def goToPropertiesList(self) -> Self:
        """Navigate to the properties/establishments list page.
        
        Ensures we're at home first, then clicks the establishments list button.
        
        Returns:
            Self: Returns self for method chaining
        """
        # Ensure we're at the home page before navigating
        if not self.atHome:
            self.goTo()
        # Click the establishments list button
        #self.element(By.XPATH, '//a[@id="btnESTABLISHMENT_LIST"]').click()
        self.element(By.XPATH, '//div[@title="Estabelecimentos"]').click()
        return self
    
    def goToMonthlyDeclarations(self) -> Self:
        """Navigate to the monthly declarations page.
        
        Ensures we're at home first, then clicks the monthly declaration button.
        
        Returns:
            Self: Returns self for method chaining
        """
        # Ensure we're at the home page before navigating
        if not self.atHome:
            self.goTo()
        # Click the monthly declarations button
        #self.element(By.XPATH, '//a[@id="btnMONTHLY_DECLARATION"]').click()
        self.element(By.XPATH, '//div[@title="Declarações de Autoliquidação"]').click()
        return self
    
    def addNewProperty(self, property: Property) -> Self:
        """Add a new property to the TMT system.
        
        Fills out the complete property registration form with all required details
        including property information, address, contact details, and specifications.
        
        Args:
            property (Property): Property object containing all necessary details
            
        Returns:
            Self: Returns self for method chaining
        """
        # Click the add new property button
        self.element(By.XPATH, '//button[@id="j_idt68"]').click()

        # Basic property information
        self.element(By.ID, 'establishmentForm:desigInput').input(property.name)
        self.element(By.ID, 'establishmentForm:unitTypeInput_input').selectByValue('ALOJAMENTO_LOCAL').wait(2)
        self.element(By.ID, 'establishmentForm:lodgeTypeInput_input').selectByValue('APARTAMENTO')
        self.element(By.ID, 'establishmentForm:rnetOrRnatInput_input').input(property.alNumber)
        self.element(By.ID, 'establishmentForm:liquidTypeInput_input').selectByValue('MENSAL')
        self.element(By.ID, 'establishmentForm:activityInsDateInput_input').input(dates.euDate())
        
        # Address information
        self.element(By.ID, 'establishmentForm:addressStreetInput').click().input(property.address.street)
        self.element(By.ID, 'establishmentForm:addressDoorInput').input(property.shortName)
        # Set parish/freguesia (Albufeira)
        self.element(By.ID, 'establishmentForm:addressCodeInput').clear().input(property.address.postalCode)
        self.element(By.ID, 'establishmentForm:freguesiaInput_input').selectByValue('Freguesias{id=080106}')
        
        # Contact information (using default account details)
        email = DEFAULT_ACCOUNT.emailAddress
        phone = DEFAULT_ACCOUNT.withoutPrefix().phoneNumber
       
        self.element(By.ID, 'establishmentForm:emailInput').input(email)
        self.element(By.ID, 'establishmentForm:emailConfirmInput').input(email)
        self.element(By.ID, 'establishmentForm:telefoneInput').clear().input(phone)
        self.element(By.ID, 'establishmentForm:telemovelInput').clear().input(phone)
        
        self.element(By.ID, 'establishmentForm:nomeContactInput').input(DEFAULT_ACCOUNT.name)
        self.element(By.ID, 'establishmentForm:telefoneContactInput').clear().input(phone)
        self.element(By.ID, 'establishmentForm:telemovelContactInput').clear().input(phone)
        
        # Property specifications
        self.element(By.ID, 'establishmentForm:numRoomsInput_input').input(property.specs.bedrooms)
        # Estimate beds as half of max guests capacity
        self.element(By.ID, 'establishmentForm:numBedsInput_input').input(property.specs.maxGuests // 2)
        
        # Save as draft (submit button is commented out for safety)
        #self.element(By.ID, 'establishmentForm:saveRascunhoBtn').click()
        self.element(By.ID, 'establishmentForm:submitEstablishmentBtn').click()
        return self

    def declareMonthlyTax(self, property: Property, year: int, month: int, total: int) -> Self:
        """Declare monthly tax for a specific property.
        
        This method is a placeholder for monthly tax declaration functionality.
        Implementation needed for actual tax submission process.
        
        Args:
            property (Property): Property for which to declare tax
            year (int): Year for the tax declaration
            month (int): Month for the tax declaration (1-12)            
        Returns:
            Self: Returns self for method chaining
        """
        # Check if tax has already been paid for the specified period, and if so, skip declaration
        if self.checkPaid(property):
            sublog(f'Tourist tax for property {property.name} has already been paid for {month}/{year}, skipping declaration.')
            return self

        # Click the first result in the filtered establishments list (assuming it matches the property)
        self.element(By.ID, 'listEstablishmentForm:listEstablishmentTable:0:j_idt121').click()

        # Check if there is a saved draft of declaration for the selected month and year, and if so, click to edit it
        if self.hasElement(By.ID, 'rascunhoForm:deleteRascunhoBtn'):
            self.element(By.ID, 'rascunhoForm:deleteRascunhoBtn').click()

        # Fill out the monthly declaration form with the specified year, month, and total tax amount
        self.element(By.ID, 'doclarationForm:forYearInput_input').selectByValue(str(year))
        self.element(By.ID, 'doclarationForm:periodInput_input').selectByValue('Period{id=' + str(month) + '}')
        self.element(By.XPATH, '//input[@data-p-label="Total de Dorminas na época"]').clear().input(str(total))
        #self.element(By.ID, 'buttonsForm:saveRascunhoBtn').click() # Save as draft (submit button is commented out for safety)
        self.element(By.ID, 'buttonsForm:submitBtn').click()  # Confirm submission
        return self
    
    @property
    def isLoggedIn(self) -> bool:
        """Check if user is currently logged in to the TMT system.
        
        Determines login status by checking for the presence of the
        establishments list button, which is only visible when logged in.
        
        Returns:
            bool: True if logged in, False otherwise
        """
        return self.hasElement(By.XPATH, '//a[@id="btnESTABLISHMENT_LIST"]')
    
    @property
    def atHome(self) -> bool:
        """Check if currently at the TMT homepage.
        
        Uses the same logic as isLoggedIn since the establishments button
        is the key indicator of being on the authenticated home page.
        
        Returns:
            bool: True if at home page, False otherwise
        """
        return self.hasElement(By.XPATH, '//a[@id="btnESTABLISHMENT_LIST"]')
    
    def propertyExists(self, property: Union[Property, str]) -> bool:
        """Check if a property exists in the establishments list.
        
        Searches the establishments table for a property by name.
        Can accept either a Property object or a string name.
        
        Args:
            property (Union[Property, str]): Property object or property name string
            
        Returns:
            bool: True if property exists in the list, False otherwise
        """
        # Table body element ID for establishments list      
        if isinstance(property, Property):
            # Search by string name directly
            property = property.name
        return property in self.element(By.ID, 'listEstablishmentForm:listEstablishmentTable_data').text
    
    def checkPaid(self, property: Union[Property, str]) -> bool:
        """Check if the monthly tax has already been paid for a specific property and period.
        
        This method is a placeholder for checking payment status functionality.
        Implementation needed to verify if a declaration exists for the given property, year, and month.
        
        Args:
            property (Union[Property, str]): Property object or property name string
            
        Returns:
            bool: True if tax has already been paid for the specified period, False otherwise
        """
        # Get the index of the "Regularização" column in the declarations table to check payment status
        self.elements(By.TAG_NAME, 'th')
        count = 0
        for element in self._elements:
            if element.text.lower() == 'regularização':
                break
            count += 1
        self.elements(By.TAG_NAME, 'td')
        return self._elements[count].text.lower() == 'sim'
    
    def filerByName(self, name: str) -> Self:
        """Filter the establishments list by property name.
        
        Inputs the property name into the filter field to narrow down the list
        of establishments for easier selection.
        
        Args:
            name (str): The name of the property to filter

        Returns:
            Self: Returns self for method chaining
        """
        self.element(By.ID, 'listEstablishmentForm:listEstablishmentTable:globalFilter').clear().input(name).wait(2)
        self.element(By.ID, 'listEstablishmentForm:listEstablishmentTable:globalFilterBTN').click()
        return self