from typing import List

from default.browser.browser import KLTBrowser
from default.google.mail.functions import get_inbox
from default.settings import VRBO_PASSWORD, VRBO_USERNAME
from datetime import date
from platforms.functions import convert_date, convert_dates, threeX
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from utils import log, logerror, loginput
from web.html import HTML
import regex as re


class BrowseVrbo(KLTBrowser):
    """
    Browser implementation for VRBO platform interactions.
    
    This class provides methods to login to VRBO, browse property listings,
    retrieve reservation data, and extract booking details.
    """
    
    _url: str = 'https://www.vrbo.com/en-gb/p/properties'
    
    def __init__(self) -> None:
        """
        Initialize the VRBO browser instance.
        """
        super().__init__('Vrbo', True)
        self._attempts: int = 0

    #######################################################
    # NAVIGATION AND LOGIN METHODS
    #######################################################

    def goTo(self) -> 'BrowseVrbo':
        """
        Navigate to the VRBO properties page.
        
        Returns:
            Self reference for method chaining
        """
        return super().goTo(self._url)
    
    def login(self) -> 'BrowseVrbo':
        """
        Login to VRBO using credentials from settings.
        
        Handles verification if required.
        
        Returns:
            Self reference for method chaining
        """        
        try:

            if 'show your human side' in self.html.lower():
                log('Anti-bot verification required. Please complete the verification steps in the browser.')
                loginput('Press Enter to continue after completing the verification steps...')
            
            self.element(By.XPATH, '//input[@name="email"]')
            self.clear()
            self.input(VRBO_USERNAME)
           
            self.element(By.XPATH, '//button[@type="submit"]')
            self.click()

            self.element(By.XPATH, '//input[@name="password"]')
            self.clear()
            self.input(VRBO_PASSWORD)

            #self.element(By.XPATH, '//button[@type="submit"]')
            #self.click()

            log('New login submitted, waiting for potential verification steps...')
            loginput('Press Enter to continue after completing any additional verification steps...')
            
        except (NoSuchElementException, TimeoutException) as e:
            return self
        
        #self._login_verification()
        return self
    
    def _login_verification(self) -> 'BrowseVrbo':
        """
        Handle the login verification step if required.
        This method checks for the security code input field and retrieves the code
        if it exists.

        Returns:
            Self reference for method chaining
        """
        try:
            self.element(By.XPATH, '//input[@id="loginFormEmailInput"]')
            self.clear()
            self.input(VRBO_USERNAME)
           
            self.element(By.XPATH, '//button[@type="submit"]')
            self.click()

            code = self._get_security_code()
            self.element(By.XPATH, '//input[@id="verify-sms-one-time-passcode-input"]')
            self.clear()
            self.input(code)
           
            self.element(By.XPATH, '//button[@type="submit"]')
            self.click()
        except (NoSuchElementException, TimeoutException):
            pass

        return self

    #######################################################
    # RESERVATION METHODS
    #######################################################

    @threeX
    def reservations(
        self, 
        propIdsDates: dict | None = None, 
        guestNamesDates: dict | None = None, 
        start: date | None = None, 
        end: date | None = None
    ) -> 'BrowseVrbo':
        """
        Navigate to reservations list page with optional filtering.
        
        Parameters:
            propIdsDates: Optional dictionary mapping property IDs to dates
            guestNamesDates: Optional dictionary mapping guest names to dates
            start: Optional start date for filtering reservations
            end: Optional end date for filtering reservations
            
        Returns:
            Self reference for method chaining
        """
        self._set(propIdsDates, guestNamesDates, start, end)
        super().goTo('https://www.vrbo.com/supply/inbox')
        self.wait(2.1)
        if self._error_message() in self.html:
            self.reset_user()
            self.goTo().login()
        self._expand_reservations_list()
        return self
        
    @threeX
    def completedReservations(self) -> 'BrowseVrbo':
        """
        Navigate to completed reservations page and filter for completed stays.
        
        Returns:
            Self reference for method chaining with HTML pages loaded
        """
        self.reservations()
        self.findElement('button', 'Filters')
        self.click()
        
        self.element(By.XPATH, '//*[@id="reservation.poststay"]')
        self.click()
        
        self.findElement('button', r'View [0-9]+ messages')
        self.script('arguments[0].click();')
        return self.htmlPages(howMany=4)

    @threeX
    def cancelledReservations(self) -> 'BrowseVrbo':
        """
        Navigate to cancelled reservations page and filter for cancelled bookings.
        
        Returns:
            Self reference for method chaining with HTML pages loaded
        """
        self.reservations()
        self.findElement('button', 'Filters')
        self.click()
       
        self.element(By.XPATH, '//*[@id="reservation.canceled"]')
        self.click()
       
        self.findElement('button', r'View [0-9]+ messages')
        self.script('arguments[0].click();')
        return self.htmlPages()

    @threeX
    def reservation(self, extension: str, valid: bool = True) -> 'BrowseVrbo':
        """
        Navigate to a specific reservation details page.
        
        Parameters:
            extension: URL extension for the specific reservation
            valid: Whether to expand payment details for valid reservations
            
        Returns:
            Self reference for method chaining
        """
        super().goTo(f'https://vrbo.com/{extension}')
        self.wait(1.2)
        if not valid:
            return self
       
        self.element(
            By.XPATH, '//button[text()[contains(., "View full payment details")]]')
        self.click()
        self.wait(.6)
        return self

    #######################################################
    # PAGINATION AND DATA PROPERTIES
    #######################################################

    @property
    def nextPage(self) -> bool:
        """
        Check if another page exists and navigate to it if it does.
        
        Returns:
            True if navigation to next page was successful, False otherwise
        """
        if self._are_more_pages():
            self._click_next_page()
            self._expand_reservations_list()
            return True
        return False

    @property
    def list(self) -> list[dict]:
        """
        Parse and retrieve reservation information from the current page.
        
        Returns:
            List of reservation dictionaries containing parsed data
        """
        parser = HTML(strainElement='tbody')
        reservations = []
        self._get(parser, reservations)
        for res in reservations:
            self._parse_reservation_page(res)
        return reservations

    #######################################################
    # PRIVATE HELPER METHODS
    #######################################################

    def _get(self, parser: HTML, reservations: List[dict]) -> 'BrowseVrbo':
        """
        Extract reservation data from the current page and add to parser.
        
        Parameters:
            parser: HTML instance to use for parsing the page
            
        Returns:
            Self reference for method chaining
        """
        parser.html = self.html
      
        for row in parser.tableRows():
            data = parser.rowData(row, includeHeader=False)
            if not data or len(data) < 2:
                continue
          
            reservation = self._parse_reservation(data)
            if reservation is not None:
                reservations.append(reservation)

        if self._got_enough_reservations(reservations):
            return self
                        
        if self.nextPage:
            return self._get(parser, reservations)
        return self
        
    def _set(
        self, 
        propIdsDates: dict | None = None, 
        guestNamesDates: dict | None = None, 
        start: date | None = None, 
        end: date | None = None
    ) -> 'BrowseVrbo':
        """
        Set filters for reservation searches.
        
        Parameters:
            propIdsDates: Dictionary mapping property IDs to dates
            guestNamesDates: Dictionary mapping guest names to dates
            start: Start date for reservation filtering
            end: End date for reservation filtering
            
        Returns:
            Self reference for method chaining
        """
        self._start, self._end = start, end
        self._propIdsDates = propIdsDates
        self._guestNamesDates = guestNamesDates
        self._total = 0

        if propIdsDates:
            self._total += propIdsDates['total']
       
        if guestNamesDates:
            self._total += guestNamesDates['total']
        return self
    
    def _parse_reservation(self, data: list) -> dict | None:
        """
        Parse a row of reservation data into a structured dictionary.
        
        Parameters:
            data: List of table cells containing reservation data
            
        Returns:
            Dictionary with parsed reservation data or None if invalid/out of range
        """
        status = data[2].text.strip()
        if not self._status_is_valid(status): 
            return None

        guestFirstNameEl = data[1].find('span', attrs={'data-stid': 'first-name'})
        guestLastNameEl = data[1].find('span', attrs={'data-stid': 'last-name'})
        if not guestFirstNameEl or not guestLastNameEl:
            return None

        guestFirstName = guestFirstNameEl.text.strip().title()
        guestLastName = guestLastNameEl.text.strip().split()[-1].title()

        checkIn, checkOut = data[3].text.split('–')
        arrivalDate, departureDate = convert_dates(checkIn, checkOut)

        propertyIdName = data[4].text.strip().split('Prop ID ')[-1]
        propertyId = propertyIdName.split(' · ')[0].strip()

        #propertyId, propertyName = propertyIdName.split(' · ')
        #propertyNumber = propertyName.strip().split()[-1]
        #propertyName = propertyName.replace(f'{propertyNumber}', f'- {propertyNumber}')

        if self._is_out_of_range(
                            propertyId, 
                            arrivalDate, 
                            departureDate, 
                            guestLastName.lower()):
            return None
        
        enquiryStatus = (
            'Booking confirmed' 
            if 'cancel' not in status.lower() 
            else 'Booking cancelled'
        )
        
        link = str(data[1].a['href']).split('?filters')[0]

        reservation = {
            'guestFirstName': guestFirstName,
            'guestLastName': guestLastName,
            'propertyId': propertyId,
            'arrivalDate': arrivalDate,
            'departureDate': departureDate,
            'enquiryStatus': enquiryStatus,
            'link': link
        }

        if self._is_updated_reservation(propertyId, arrivalDate, departureDate):
            reservation['isUpdated'] = True

        return reservation

    def _parse_reservation_page(self, reservation: dict) -> dict:
        """
        Extract detailed reservation information from the reservation page.
        
        Parameters:
            reservation: Dictionary to populate with reservation details
            
        Returns:
            Updated reservation dictionary with additional details
        """
        self.reservation(reservation['link'])
        text = HTML(self.html).text.lower()
        reservation['platformId'] = re.search(r'res id: ([\w-]+) ', text).group(1).upper()

        if 'cancelled' in reservation['enquiryStatus'].lower():
            return reservation
       
        enquiryDate = r'through vrbo [ \D,]+ ([0123]?[0-9] [a-z]{3}[a-z]?,?( 20[0-9]{2})?|[a-z]{3}[a-z]? [0123]?[0-9],?( 20[0-9]{2})?)'
        "Booked through Vrbo on Sun, 22 Sept 2024"
        reservation['enquiryDate'] = convert_date(re.search(enquiryDate, text).group(1))
        
        guests = r'(\d+) adult[s]?(?:, (\d+) child[ren]*)?(?:, (\d+) (?:babies|infants))?'
        adults, children, babies = re.search(guests, text).groups()
        reservation['guests'] = {
            'adults': 0 if not adults else int(adults),
            'children': 0 if not children else int(children),
            'babies': 0 if not babies else int(babies),
        }
            
        reservation['guestPhone'] = re.search(r' (\+[\d\- ]+) \D', text).group(1)
        reservation['guestEmail'] = re.search(r' ([\w\.\-_]+@[\w\.-]+) ', text).group(1)
        reservation['payoutTotal'] = float(re.search(r'total payout[\D ]+([0-9.]+)', text).group(1))
        reservation['platformFee'] = float(re.search(r'vrbo commission[\w ]+\-([0-9.]+)', text).group(1))
        return reservation

    def _expand_reservations_list(self) -> 'BrowseVrbo':
        """
        Expand the reservations list to show more entries.
        
        Returns:
            Self reference for method chaining
        """
        try:
            self.wait(1.5)
            self.element(By.TAG_NAME, 'select')
            self.selectByValue('50')
            self.wait(3.3)
            self.scroll()
        except NoSuchElementException:
            pass
        return self
    
    def _are_more_pages(self) -> bool:
        """
        Check if more pages of reservations are available.
        
        Returns:
            True if there are more pages, False otherwise
        """
        n = 0
        while n < 3:
            text = self.element(By.TAG_NAME, 'body').text
            search = re.search(r'[0-9]+ - ([0-9]+) of ([0-9]+) results', text)
            if search:
                return int(search.group(1)) < int(search.group(2))
            n += 1
            self.wait(1.1)
            self.scroll()
        return False

    def _click_next_page(self) -> 'BrowseVrbo':
        """
        Navigate to the next page of reservations.
        
        Returns:
            Self reference for method chaining
        """
        self.element(By.XPATH, '//button[@aria-label="Next records"]')
        self.script('arguments[0].click();')
        self._current_height = 0
        self.wait(2.1)
        self.scroll()
        return self
    
    def _is_out_of_range(
        self, 
        propertyId: str, 
        arrivalDate: date, 
        departureDate: date, 
        guestName: str
    ) -> bool:
        """
        Check if a reservation is outside the specified filter range.
        
        Parameters:
            propertyId: The property ID to check
            arrivalDate: The arrival date to check
            departureDate: The departure date to check
            guestName: The guest's last name
            
        Returns:
            True if the reservation is out of range, False otherwise
        """
        if self._start or self._end:
            if self._start and arrivalDate < self._start:
                return True
            
            if self._end and arrivalDate > self._end:
                return True
            return False

        if self._propIdsDates:
            if 'new' in self._propIdsDates and guestName in self._propIdsDates['new']:
                if (arrivalDate, departureDate) in self._propIdsDates['new'][guestName]:
                    return False
            
            if 'updated' in self._propIdsDates and guestName in self._propIdsDates['updated']:
                if (arrivalDate, departureDate) in self._propIdsDates['updated'][guestName]:
                    return False
            
            if 'cancelled' in self._propIdsDates and propertyId in self._propIdsDates['cancelled']:
                if (arrivalDate, departureDate) in self._propIdsDates['cancelled'][propertyId]:
                    return False
            
        guestName = guestName.capitalize()
        if self._guestNamesDates and guestName in self._guestNamesDates.keys():
            if (arrivalDate, departureDate) == self._guestNamesDates[guestName]:
                return False

        return True
    
    def _got_enough_reservations(self, reservations: list) -> bool:
        """
        Check if we've retrieved enough reservations based on filters.
        
        Parameters:
            reservations: List of reservations retrieved so far
            
        Returns:
            True if we have enough reservations, False if we need more
        """
        if self._start or self._end:
            return False
        if len(reservations) < self._total:
            return False
        return True
    
    def _status_is_valid(self, status: str) -> bool:
        """
        Check if a reservation status string indicates a valid booking status.
        
        Parameters:
            status: Status string to check
            
        Returns:
            True if the status is valid, False otherwise
        """
        for valid in ('confirmed', 'cancel', 'booked', 'arriving'):
            if valid in status.lower():
                return True
        return status.lower() in ('confirmed', 'cancelled', 'booked')
    
    def _open_reservation(self, link: str) -> 'BrowseVrbo':
        """
        Open a reservation in a new browser tab.
        
        Parameters:
            link: The reservation link to open
            
        Returns:
            Self reference for method chaining
        """
        self.tabs.new()
        self.reservation(link)
        self.wait(1.9)
        return self
    
    def _close_reservation(self) -> 'BrowseVrbo':
        """
        Close the reservation tab and return to the main tab.
        
        Returns:
            Self reference for method chaining
        """
        self.tabs.close()
        self.wait(.8)
        return self
    
    def _is_updated_reservation(
        self, 
        propertyId: str, 
        arrivalDate: date, 
        departureDate: date
    ) -> bool:
        """
        Check if a reservation is marked as updated in the property dates.
        
        Parameters:
            propertyId: The property ID to check
            arrivalDate: The arrival date to check
            departureDate: The departure date to check
            
        Returns:
            True if the reservation is updated, False otherwise
        """
        if not self._propIdsDates:
            return False
        if 'updated' not in self._propIdsDates.keys():
            return False
        if propertyId not in self._propIdsDates['updated'].keys():
            return False
        if (arrivalDate, departureDate) not in self._propIdsDates['updated'][propertyId]:
            return False
        return True
    
    def _get_security_code(self) -> str:
        """
        Retrieve the security code from the inbox for VRBO login.
        
        Returns:
            The security code as a string
        """
        emails = get_inbox(sender='vrbo@eg.vrbo.com')
        for email in emails:
            search = re.search(r'code is (\d{6})', email.subject.lower())
            if search:
                email.delete()
                return search.group(1)
        return ''

    def _error_message(self):
        return "Sorry! Something went wrong on our side and " \
        "we could not load the page. Please try again."