from datetime import date
from random import randint
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from typing import List

from correspondence.self.functions import new_security_code_email_to_self
from default.browser.browser import KLTBrowser
from default.settings import DEFAULT_ACCOUNT
from platforms.functions import convert_date
from web.html import HTML


class BrowseAirbnb(KLTBrowser):
    """
    Browser implementation for Airbnb platform interactions.
    
    This class provides methods to login to Airbnb, browse listings,
    manage reservations, access messages, and extract booking information.
    """

    #######################################################
    # INITIALIZATION
    #######################################################

    def __init__(self) -> None:
        """
        Initialize the Airbnb browser.
        """
        super().__init__('Airbnb', True)

    #######################################################
    # NAVIGATION AND LOGIN
    #######################################################

    def goTo(self, extension: str = 'hosting/') -> 'BrowseAirbnb':
        """
        Navigate to an Airbnb page.
        
        Parameters:
            extension: URL extension to navigate to after the base URL
            
        Returns:
            Self for method chaining
        """
        return super().goTo(f'https://www.airbnb.com/{extension}')

    def login(self) -> 'BrowseAirbnb':
        """
        Login to Airbnb using credentials from DEFAULT_ACCOUNT.
        
        This method handles multiple login flows, including phone authentication
        and security code verification if needed.
        
        Returns:
            Self for method chaining
        """
        try: 
            (
                self
                .wait(1)
                .element(By.XPATH, '//input[@name="phoneInputphone-login"]')
                .clear()
                .input(DEFAULT_ACCOUNT.noPrefix().phoneNumber)
                .element(By.XPATH, '//button[@type="submit"]')
                .click()
                .wait(4)
            )
        except (NoSuchElementException, TimeoutException):
            try:
                (
                    self
                    .element(By.XPATH, '//button[contains(@data-testid, "login")]')
                    .click()
                    .wait(2)
                )
            except (NoSuchElementException, TimeoutException): 
                return self.wait(4)
        
        if (
            self
            .hasElement(By.XPATH, '//input[@maxlength="6"]')
        ):
            code = new_security_code_email_to_self(self.website, DEFAULT_ACCOUNT)
            (
                self
                .element(By.XPATH, '//input[@maxlength="6"]')
                .clear()
                .input(code)
                .wait(2)
                .goTo()
            )
            
        return self._check_text_challenge()

    #######################################################
    # RESERVATION ACCESS METHODS
    #######################################################

    def validReservations(
        self, 
        ids: list[str] | None = None, 
        start: date | None = None, 
        end: date | None = None
    ) -> 'BrowseAirbnb':
        """
        Navigate to upcoming valid reservations page.
        
        Parameters:
            ids: Optional list of reservation IDs to filter for
            start: Optional start date to filter reservations
            end: Optional end date to filter reservations
            
        Returns:
            Self for method chaining
        """
        return (
            self
            ._set(ids, start, end, valid=True)
            .resetPages()
            .goTo('hosting/reservations/upcoming')
            .wait(2)
            .scroll()
        )

    def cancelledReservations(
        self, 
        ids: list[str] | None = None, 
        start: date | None = None, 
        end: date | None = None
    ) -> 'BrowseAirbnb':
        """
        Navigate to cancelled reservations page.
        
        Parameters:
            ids: Optional list of reservation IDs to filter for
            start: Optional start date to filter reservations
            end: Optional end date to filter reservations
            
        Returns:
            Self for method chaining
        """
        return (
            self
            ._set(ids, start, end, valid=False)
            .resetPages()
            .goTo('hosting/reservations/canceled')
            .wait(2)
            .scroll()
        )

    def completedReservations(
        self, 
        ids: list[str] | None = None, 
        start: date | None = None, 
        end: date | None = None
    ) -> 'BrowseAirbnb':
        """
        Navigate to completed reservations page.
        
        Parameters:
            ids: Optional list of reservation IDs to filter for
            start: Optional start date to filter reservations
            end: Optional end date to filter reservations
            
        Returns:
            Self for method chaining
        """
        return (
            self
            ._set(ids, start, end, valid=True)
            .resetPages()
            .goTo('hosting/reservations/completed')
            .wait(2)
            .scroll()
        )

    def reservation(self, id: str) -> 'BrowseAirbnb':
        """
        Navigate to a specific reservation details page.
        
        Parameters:
            id: The reservation ID to view
            
        Returns:
            Self for method chaining
        """
        return (
            self
            .goTo(f'hosting/reservations?confirmationCode={id}')
            .wait(1.5)
            .scroll()
        )

    #######################################################
    # MESSAGE FUNCTIONALITY
    #######################################################
        
    def messages(self) -> 'BrowseAirbnb':
        """
        Navigate to the messages section.
        
        Returns:
            Self for method chaining
        """
        return (
            self
            .findElement('a', 'Messages')
            .click()
            .wait(3)
            .element(By.XPATH, '//button[@aria-label="Search"]')
            .click()
            .wait(1)
        )

    def guest(self, guestName: str) -> 'BrowseAirbnb':
        """
        Navigate to a conversation with a specific guest.
        
        Parameters:
            guestName: The name of the guest to find
            
        Returns:
            Self for method chaining
        """
        return (
            self
            .element(By.XPATH, '//input[@id="inbox-query"]')
            .clear()
            .input(guestName)
            .wait(6)
            .findElement('a', guestName.split()[0])
            .click()
            .wait(3)
            ._check_text_challenge()
        )

    def sendMessage(
        self, 
        name: str | None = None, 
        content: str | None = None
    ) -> 'BrowseAirbnb':
        """
        Send a message to a guest.
        
        Parameters:
            name: Optional quick reply template name to use
            content: Optional custom message content to send
            
        Returns:
            Self for method chaining
        """
        if name is None and content is None: 
            return self
            
        if name is not None:
            (
                self
                .element(By.XPATH, '//button[contains(@aria-label, "quick repl")]')
                .click()
                .findElement('button', name)
                .click()
                .element(By.XPATH, '//div[@role="textbox"]')
            )
        elif content is not None: 
            self.element(By.XPATH, '//div[@role="textbox"]').clear()
            self.input(content)
            
        self._element.send_keys(Keys.CONTROL, Keys.ENTER)
        self.wait(1)
        return self
    

    ########################################################
    # REVIEW FUNCTIONALITY
    ########################################################
    def reviewGuest(self, link: str, nameS: str) -> 'BrowseAirbnb':
        """
        Review a guest's stay.
        
        Parameters:
            link: The review link to open
            nameS: The name of the guest to review
            
        Returns:
            Self for method chaining
        """
        submit = lambda: (
            self
            .element(By.XPATH, '//button[@type="submit"]')
            .click(wait=1.5)
        )
        
        # Open review page and skip to review start
        linkSuffix = link.split('com/')[1]
        self.goTo(extension=linkSuffix)
        submit()
     
        # Review Cleanliness, Respectfulness, and Communication 
        for i in range(3):
            self.element(By.XPATH, '//input[@value="5"]')
            self.click(wait=1.5)
            submit()

        # Write public review, recommend guest, write private review
        textReviews = [
            self._public_review_text(nameS),
            None, # to recommend guest to other hosts: default is Yes
            self._private_review_text(nameS)
        ]
        for text in textReviews:
            if text is not None:
                self._insert_text_review(text)
            submit()

        return self

    #######################################################
    # PAGINATION AND DATA PROPERTIES
    #######################################################
    
    @property
    def nextPage(self) -> bool:
        """
        Check and navigate to the next page if available.
        
        Returns:
            True if navigation to next page was successful, False otherwise
        """
        if self.scroll().findElement('button', f'{super().nextPage}').isSet:
            self.click().wait(2).scroll()
            return True
        return False

    @property
    def list(self) -> list[dict[str, str]]:
        """
        Parse and retrieve reservation information from the current page.
        
        Returns:
            List of reservation dictionaries containing parsed data
        """
        parser = HTML(strainElement='tbody')
        self._get(parser)
        return parser.parsed

    #######################################################
    # PRIVATE HELPER METHODS
    #######################################################
    
    def _insert_text_review(self, text: str) -> 'BrowseAirbnb':
        """
        Insert text into a review textarea.
        
        Parameters:
            text: The text to insert
            
        Returns:
            Self for method chaining
        """
        return (
            self
            .element(By.TAG_NAME, 'textarea')
            .clear()
            .input(text, time=0)
        )
    
    def _public_review_text(self, nameS: str) -> str:
        """
        Generate a public review text with random positive phrases.
        
        Parameters:
            nameS: The guest's name to include in the review
            
        Returns:
            Generated public review text
        """
        adjective = (
            'wonderful', 
            'excellent', 
            'great', 
            'lovely'
        )
        closing = (
            'I cannot recommend them highly enough!',
            'I would recommend hosting them any time!'
        )
        strings = [
            f'It has been {adjective[randint(0, 3)]} hosting {nameS}\'s group',
            f'over the last days. {closing[randint(0, 1)]}',
        ]
        return ' '.join(strings)

    def _private_review_text(self, nameS: str) -> str:
        """
        Generate a private review text for the host's eyes only.
        
        Parameters:
            nameS: The guest's name to include in the review
            
        Returns:
            Generated private review text
        """
        strings = [
            f'Thank you so much, {nameS}!',
            'It was a great pleasure. Feel free to stay',
            'in touch and contact me directly for any future interest.',
            'All the best for now!'
        ]
        return ' '.join(strings)
        
    def _get(self, parser: HTML) -> 'BrowseAirbnb':
        """
        Extract reservation data from the current page and add to parser.
        
        Parameters:
            parser: HTML instance to use for parsing the page
            
        Returns:
            Self for method chaining
        """
        parser.html = self.html
        for row in parser.tableRows():
            data = parser.rowData(row, includeHeader=False)
            if not data or len(data) < 3:
                continue
         
            reservation = self._parse_reservation_row(data, {})
            if reservation is not None:
                parser.parsed = reservation
            if self._checkingIds:
                if len(parser.parsed) == len(self._ids):
                    return self
                    
        if not self.nextPage:
            return self
        return self._get(parser)
    
    def _set(self, ids: List[str] | None, start: date | None, 
            end: date | None, valid: bool = True) -> 'BrowseAirbnb':
        """
        Set filters for reservation searches.
        
        Parameters:
            ids: Optional list of reservation IDs to filter for
            start: Optional start date to filter reservations
            end: Optional end date to filter reservations
            valid: Whether to search for valid (True) or invalid (False) reservations
            
        Returns:
            Self for method chaining
        """
        self._ids, self._checkingIds = ids, bool(ids)
        self._start, self._end = start, end
        self.valid = valid
        return self

    def _check_text_challenge(self) -> 'BrowseAirbnb':
        """
        Check and handle security text challenge if presented.
        
        Returns:
            Self for method chaining
        """
        if not self.findElement('h1', 'Let us know it\'s').isSet: 
            return self
            
        self.findElement('button', 'Text message').click().wait(2)
        code = new_security_code_email_to_self(self.website)
        self.element(By.TAG_NAME, 'input').input(code).enter()
        return self

    def _parse_reservation_row(
        self, 
        data: list, 
        reservation: dict[str, str]
    ) -> dict[str, str] | None:
        """
        Parse a row of reservation data into a structured dictionary.
        
        Parameters:
            data: List of table cells containing reservation data
            reservation: Dictionary to populate with parsed data
            
        Returns:
            Dictionary with parsed reservation data or None if out of range
        """

        platformId = data[7].text.strip()
        arrivalDate = convert_date(data[3].text.strip())
        
        if self._is_out_of_range(platformId, arrivalDate):
            return None
            
        reservation['platformId'] = platformId
        reservation['arrivalDate'] = arrivalDate
        reservation['departureDate'] = convert_date(data[4].text.strip())
        reservation['guestNames'] = data[1].find('a').text.strip()
        reservation['guests'] = data[1].find('div').text.strip()
        reservation['guestPhone'] = data[2].text.strip()
        
        enquiryDateAndTime = data[5]
        enquiryTime = enquiryDateAndTime.find('div').text
        enquiryDate = enquiryDateAndTime.text.split(enquiryTime)[0]
        reservation['enquiryDate'] = convert_date(enquiryDate)
        
        reservation['propertyName'] = data[6].text.strip()
        payoutTotal = data[8].text.split('\xa0')[-1].strip()
        reservation['payoutTotal'] = payoutTotal
        
        if self.valid:
            reservation['enquiryStatus'] = 'Booking confirmed'
        if self.valid or payoutTotal != '0.00':
            self.wait(2)
            #reservation['platformFee'] = self._parse_service_fee(reservation['platformId'])
            if not self.valid:
                reservation['enquiryStatus'] = 'Booking cancelled with fees'
        else:
            reservation['enquiryStatus'] = 'Booking cancelled'
            
        return reservation
    
    def _parse_service_fee(self, platformId: str) -> str:
        """
        Parse the service fee from a reservation details page.
        
        Parameters:
            platformId: The reservation ID to check
            
        Returns:
            The service fee as a string or empty string if not found
        """
        self._open_reservation(platformId)
        parser = HTML(self.html, 'div', 'aira-label', 'Reservation Details')
        
        for section in parser.findAll('section'):
            sectionHeader = section.find('h2')
            if not sectionHeader:
                continue
                
            sectionHeaderText = sectionHeader.text.lower()
            if not 'host payout' in sectionHeaderText:
                continue
                
            sectionDivisions = section.find_all('div')
            for i in range(len(sectionDivisions)):
                sectionDivision = sectionDivisions[i].text.lower()
                if not 'host service' in sectionDivision:
                    continue
                    
                sectionValue = sectionDivisions[i+1].text
                charge = sectionValue.split('\xa0')[-1]
                self._close_reservation()
                return charge
                
        return self.wait(1)

    def _is_out_of_range(self, platformId: str, arrivalDate: date) -> bool:
        """
        Check if a reservation is outside the specified filter range.
        
        Parameters:
            platformId: The reservation ID to check
            arrivalDate: The arrival date to check
            
        Returns:
            True if the reservation is out of range, False otherwise
        """
        if self._checkingIds and platformId not in self._ids: 
            return True
        if self._start and arrivalDate < self._start: 
            return True
        if self._end and arrivalDate > self._end: 
            return True
        return False
    
    def _open_reservation(self, platformId: str) -> 'BrowseAirbnb':
        """
        Open a reservation in a new browser tab.
        
        Parameters:
            platformId: The reservation ID to open
            
        Returns:
            Self for method chaining
        """
        #self.tabs.new()
        self.reservation(platformId).wait(2)#.scroll()
        return self
    
    def _close_reservation(self) -> 'BrowseAirbnb':
        """
        Close the reservation tab and return to the main tab.
        
        Returns:
            Self for method chaining
        """
        self.element(By.XPATH, '//button[@aria-label="Close"]').click().wait(1)
        #self.tabs.close()
 