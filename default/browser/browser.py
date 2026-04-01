import os

from default.settings import BROWSER_DIR, BROWSER_USER_DATA_DIR
from web.browser import Browser


class KLTBrowser(Browser):
    """
    A specialized browser for KLT applications that extends the base Browser class.
    Creates a persistent Chrome profile specific to the given website.
    """
    
    def __init__(self, website: str, visible: bool = True) -> None:
        """
        Initialize a new KLTBrowser instance for a specific website.
        
        Args:
            website: The website this browser instance will primarily be used for
            visible: Whether to show the browser window (True) or run headless (False)
        """
        user_data_dir = os.path.join(BROWSER_USER_DATA_DIR, f'chromium-user-{website.lower()}')
        super().__init__(visible, BROWSER_DIR, user_data_dir)
        self.website = website