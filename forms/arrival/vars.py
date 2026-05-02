from utils import gen_hex


# Constants for form section IDs and question IDs
GUEST_DETAILS_SECTION = gen_hex(1, 0)
GUEST_FIRST_NAME = gen_hex(1, 1)
GUEST_LAST_NAME = gen_hex(1, 2)
GUEST_EMAIL_ADDRESS = gen_hex(1, 3)
GUEST_PHONE_NUMBER = gen_hex(1, 4)

ARRIVAL_METHOD_SECTION = gen_hex(2, 0)
ARRIVAL_METHOD = gen_hex(2, 1)

FLIGHT_DETAILS_SECTION = gen_hex(3, 0)
INBOUND_FLIGHT_NUMBER = gen_hex(3, 1)
INBOUND_FLIGHT_TIME = gen_hex(3, 2)
OUTBOUND_FLIGHT_NUMBER = gen_hex(3, 3)
OUTBOUND_FLIGHT_TIME = gen_hex(3, 4)
CAR_HIRE = gen_hex(3, 5)

NON_FLIGHT_DETAILS_SECTION = gen_hex(4, 0)
ARRIVAL_TIME = gen_hex(4, 1)
ARRIVAL_COMMENTS = gen_hex(4, 2)

AIRPORT_TRANSFER_SECTION = gen_hex(5, 0)
AIRPORT_TRANSFER_OPTION = gen_hex(5, 1)
CHILD_SEATS = gen_hex(5, 2)
EXCESS_BAGGAGE = gen_hex(5, 3)

EXTRAS_SECTION = gen_hex(6, 0)
WELCOME_PACK_OPTION = gen_hex(6, 1)
MID_STAY_CLEAN_OPTION = gen_hex(6, 2)
COT_OPTION = gen_hex(6, 3)
HIGHCHAIR_OPTION = gen_hex(6, 4)

OWNER_DETAILS_SECTION = gen_hex(7, 0)
TOTAL_ADULTS = gen_hex(7, 1)
TOTAL_CHILDREN = gen_hex(7, 2)
TOTAL_BABIES = gen_hex(7, 3)
CLEAN_OPTION = gen_hex(7, 4)
IS_FOR_OWNER = gen_hex(7, 5)

MEET_GREET_SECTION = gen_hex(8, 1)
MEET_GREET_OPTION = gen_hex(8, 2)

OWNER_COMMENTS_SECTION = gen_hex(9, 0)
OWNER_COMMENTS = gen_hex(9, 1)