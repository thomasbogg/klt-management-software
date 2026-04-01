import re
from typing import List

from correspondence.self.functions import new_security_code_email_to_self
from default.browser.browser import KLTBrowser
from default.settings import (
    BOOKINGCOM_PASSWORD,
    BOOKINGCOM_USERNAME
)
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from utils import logerror
from web.html import HTML


class BrowseBookingComExtranet(KLTBrowser):
    """
    Class for interacting with the Booking.com extranet.
    
    Provides functionality for logging in, navigating property pages,
    and retrieving reservation data.
    """

    _url: str = 'https://admin.booking.com/'
   
    def __init__(self, TEST = False) -> None:
        """Initialize a new Booking.com extranet browser instance."""
        if not TEST:
            super().__init__('Booking.com')

    #######################################################
    # NAVIGATION METHODS
    #######################################################

    def goTo(self, url: str | None = None, extension: str = '') -> 'BrowseBookingComExtranet':
        """
        Navigate to a specific URL in the browser.
        
        Parameters:
            url: The URL to navigate to. If None, uses the default URL.
            extension: Optional extension to append to the URL.
            
        Returns:
            Self reference for method chaining
        """
        if url is None:
            url = self._url
        url += extension
        return super().goTo(url)
    
    def login(self) -> 'BrowseBookingComExtranet':
        """
        Login to Booking.com extranet using credentials from settings.
        
        Handles verification if required.
        
        Returns:
            Self reference for method chaining
        """

        text = self.element(By.TAG_NAME, 'h1').text
        if 'password' not in text.lower() and 'sign in' not in text.lower():
            if 'homepage' in text.lower():
                return self
            if self.addAttempts().reachedLimitOfAttempts():
                return self
            return self.goTo().login()
            
        try:
            self.element(By.NAME, 'loginname').input(BOOKINGCOM_USERNAME, time=.51)
        except (NoSuchElementException, TimeoutException) as e:
            logerror(f"during login name input: {e}")
            return self.reload().login()
       
        self.element(By.XPATH, '//button[@type="submit"]').enter()
        self.element(By.NAME, 'password').input(BOOKINGCOM_PASSWORD, time=.67)
    
        try:
            self.element(By.XPATH, '//button[@type="submit"]').enter()
        except (NoSuchElementException, TimeoutException) as e:
            logerror(f"during password input: {e}")
            return self.reload().login()
        
        self._check_verification()
        return self

    def propertyPage(self, name: str) -> 'BrowseBookingComExtranet':
        """
        Navigate to a specific property page in the extranet.
        
        Parameters:
            name: The name of the property to navigate to
            
        Returns:
            Self reference for method chaining
        """
        properties = {
            'quinta da barracuda': '8715453',
            'parque da corcovada': '9330221',
            'clube do monaco': '8252517',
        }
        if len(self.tabs.all) > 1:
            self.tabs.close()

        self.scroll()
        
        while True:
            try:
                self.wait(4).findElement('a', properties[name.lower()]).click()
                break
            except:
                self.reload().login()
       
        self.tabs.switchTo(-1)
        return self

    def reservations(self, start: str | None = None, end: str | None = None) -> 'BrowseBookingComExtranet':
        """
        Search for reservations between the given dates.
        
        Parameters:
            start: Start date for reservation search. If None, returns without searching.
            end: End date for reservation search.
            
        Returns:
            Self reference for method chaining
        """
        if not start:
            return self
            
        self.wait(3).element(By.LINK_TEXT, 'Reservations').click()
        self.element(By.XPATH, '//*[@id="date_from"]').clear().input(start)
        self.element(By.XPATH, '//*[@id="date_to"]').clear().input(end)
        self.wait(2).element(By.XPATH, self._xpath_for_search_button()).click()
        self.wait(3).scroll()
        
        try:
            self.element(By.XPATH, '//select[@id="reservations_table_pagination"]')
            self.selectByValue('100')
        except:
            pass
            
        return self.wait(3).scroll()
    
    def acceptOneTrustPolicy(self) -> 'BrowseBookingComExtranet':
        """
        Accept the OneTrust cookie policy if present.
        
        Returns:
            Self reference for method chaining
        """
        try:
            self.element(By.XPATH, '//*[@id="onetrust-accept-btn-handler"]').click()
        except Exception as e:
            print(f"Error accepting OneTrust policy: {e}")
        return self

    #######################################################
    # DATA PARSING METHODS
    #######################################################

    @property
    def list(self) -> List[dict[str, str]]:
        """
        Parse the reservation list from the current page.
        
        Returns:
            List of reservation dictionaries containing reservation details
        """
        return self.list_reservations(self.html)

    def parse_guests(self, link: str, reservation: dict[str, str]) -> 'BrowseBookingComExtranet':
        """
        Parse guest contact information and add it to the reservation dictionary.
        
        Parameters:
            data: HTML data containing contact link
            reservation: Dictionary to store contact information
            
        Returns:
            Self reference for method chaining
        """
        self.element(By.XPATH, f'//a[@href="{link}"]').click().wait(3)
        self.tabs.switchTo(-1)

        reservation['Properties'] = {}

        parser = HTML(self.html)
        for property in parser.findAll('ul', {'aria-label': 'Check all details'}):
            titleEl = property.find('button')
            title = re.search(r'\(([A-Z \-0-9]+)\)', titleEl.text).group(1)
            occupancy = re.search(r'Booked occupancy ([\d\s,()\w"]+) Max occupancy', property.text).group(1)
            reservation['Properties'][title] = occupancy.strip()

        """
        self.findElement('button', 'Show phone number').click().wait(2)
        reservation['email'] = self.element(By.XPATH, '//a[contains(@href, "mailto:")]').text
        #reservation['phone'] = self.element(By.XPATH, '//a[contains(@href, "tel:")]').text
        """
        self.tabs.close()
        return self

    #######################################################
    # HELPER METHODS
    #######################################################

    def list_reservations(self, html: str, test: bool = False) -> List[dict[str, str]]:
        """
        Internal method to parse the reservation list from the current page.
        
        Parameters:
            html: HTML content of the page to parse.
        Returns:
            List of reservation dictionaries containing reservation details
        """
        parser = HTML(html, 'tbody', 'class', 'bui-table__body')
        
        for row in parser.tableRows():
            reservation = dict()
            for data in parser.rowData(row):
                if test:
                    print(data)
                    print('-----------')
                if 'data-heading' not in data.attrs:
                    continue
                key = data['data-heading'].split()[0].lower()
                value = data.text.strip()
                if test:
                    print(f"Key: {key}, Value: {value}")
                    print('--------------------------------------')
                reservation[key] = value
                
            if 'x' in reservation['rooms']:
                link = data.find('a')['href']
                print(link)
                self.parse_guests(link, reservation)
            
            parser.parsed = reservation
            
        return parser.parsed

    def _check_verification(self) -> 'BrowseBookingComExtranet':
        """
        Check if verification is required and handle it.
        
        Returns:
            Self reference for method chaining
        """
        h1 = self.element(By.TAG_NAME, 'h1').text
        if h1 and 'Sign in' in h1:
            self.addAttempts().login()
        elif h1 and 'method' in h1:
            if self.findElement('div', 'Text message (SMS)').isSet:
                self.click()
            else:
                return self
            self.wait()
            if self.findElement('button', 'Send verification code').isSet:
                self.click()
            else:
                return self
            self.element(By.NAME, 'sms_code')
            self.input(new_security_code_email_to_self(self.website))
            self.findElement('button', 'Verify now').click()
        return self
    
    def _xpath_for_search_button(self) -> str:
        """
        Get the XPath for the search button.
        
        Returns:
            XPath string for the search button
        """
        return '//*[@id="main-content"]/div/form/div[1]/fieldset/div/button[2]/span/span'                              