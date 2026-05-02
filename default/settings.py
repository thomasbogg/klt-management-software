"""
Global settings and configuration values for the KLT application.

This module contains configuration settings, API credentials, and constants
used throughout the application.
"""
import os
from default.google.accounts import ThomasAtABA

try:
    # Check if running in deployed environment (e.g., on a server) 
    # where environment variables are set directly
    os.getenv('LOCAL').lower() == 'false'
    LOCAL: bool = False
except Exception:
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    LOCAL: bool = os.getenv('LOCAL', 'True').lower() == 'true'

#######################################################
# APPLICATION SETTINGS
#######################################################

# Debug/Test mode flag
TEST: bool = os.getenv('TEST', 'False').lower() == 'true'

# Website information
WEBSITE_LINK: str = 'https://www.algarvebeachapartments.com/'

# Default account for API operations
DEFAULT_ACCOUNT = ThomasAtABA()

# Default language
DEFAULT_LANGUAGE = 'EN-GB'


#######################################################
# FILESYSTEM SETTINGS
#######################################################

# Directory paths
DIR: str = os.getcwd()
LOCAL_STORAGE_DIR: str = os.path.abspath('cache')
BROWSER_DIR: str = '/snap/chromium/current/usr/lib/chromium-browser/'
BROWSER_USER_DATA_DIR: str = os.path.join(os.path.expanduser('~'), '.browser_data')

# Database configuration
DATABASE_NAME: str = os.getenv('DATABASE_NAME')
DATABASE_PATH: str = os.path.join(DIR, DATABASE_NAME)


#######################################################
# PROPERTY SETTINGS
#######################################################

# List of managed properties
PROPERTIES: tuple[str, ...] = (
    'Quinta da Barracuda', 
    'Clube do Monaco', 
    'Parque da Corcovada'
)

# Valid booking status values
VALID_BOOKING_STATUSES: tuple[str, ...] = (
    'Booking confirmed',
    'Guests have departed', 
    'Guests on-site', 
    'Holiday completed'
)


#######################################################
# BOOKING PLATFORM SETTINGS
#######################################################

# Supported booking platforms
PLATFORMS: tuple[str, ...] = (
    'Airbnb',
    'Booking.com',
    'Vrbo'
)

# Currency conversion rate
GBP_EUR_EXCHANGE_RATE: float = 1.1111


#######################################################
# PLATFORM CREDENTIALS
#######################################################

# Credentials loaded from environment variables
# These are now stored in the .env file (keep it private!)

# PIMS credentials
PIMS_USERNAME: str = os.getenv('PIMS_USERNAME', '')
PIMS_PASSWORD: str = os.getenv('PIMS_PASSWORD', '')

# Booking.com credentials
BOOKINGCOM_USERNAME: str = os.getenv('BOOKINGCOM_USERNAME', '')
BOOKINGCOM_PASSWORD: str = os.getenv('BOOKINGCOM_PASSWORD', '')

# VRBO credentials
VRBO_USERNAME: str = os.getenv('VRBO_USERNAME', '')
VRBO_PASSWORD: str = os.getenv('VRBO_PASSWORD', '')

# API Keys
DEEPL_AUTH_KEY: str = os.getenv('DEEPL_AUTH_KEY', '')

# TMT credentials
TMT_USERNAME: str = os.getenv('TMT_USERNAME', '')
TMT_PASSWORD: str = os.getenv('TMT_PASSWORD', '')