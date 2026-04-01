sfrom default.accountancy.functions import FetchAccountancySheetBookings


class FetchEnquiries(FetchAccountancySheetBookings):
    def __init__(self, start, end, property=None):
        super().__init__()

        self.Stays().Selection().Set(
            [
                'enquiry_date',
            ]
        )
        
        self.Stays().Conditions().Set(

            enquiry_start=start,
            enquiry_end=end,
        
        )

        self.Properties().Conditions().Set(

            shorthand_name=property,

        )



class FetchGuestEnquiries(FetchEnquiries):
    def __init__(self, start, end, property=None):
        super().__init__(start, end, property=property)

        self.Stays().Conditions().Set(

            owner_booking=False,
        
        )



class FetchOwnerEnquiries(FetchEnquiries):
    def __init__(self, start, end, property=None):
        super().__init__(start, end, property=property)

        self.Stays().Conditions().Set(

            owner_booking=True,
        
        )



class FetchArrivals(FetchAccountancySheetBookings):
    def __init__(self, start, end, property=None):
        super().__init__()

        self.Owners().Selection().Set(
            [
                'rental_invoice',
            ]
        )
        
        self.Stays().Conditions().Set(
         
            arrival_start=start,
            arrival_end=end,
        
        )

        self.Properties().Conditions().Set(

            shorthand_name=property,
            
        )



class FetchGuestArrivals(FetchArrivals):
    def __init__(self, start, end, property=None):
        super().__init__(start, end, property=property)

        self.Stays().Conditions().Set(

            owner_booking=False,

        )



class FetchOwnerArrivals(FetchArrivals):
    def __init__(self, start, end, property=None):
        super().__init__(start, end, property=property)

        self.Stays().Selection().Set(

            [
                'enquiry_date',
            ]

        )

        self.Stays().Conditions().Set(

            owner_booking=True,

        )