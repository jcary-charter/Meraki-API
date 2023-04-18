import meraki
import os

class initOrg(object):
    """
    Object for Organization Record
    """
    def __init__(self, id=None, name=None, ) -> None:
        self.id = ""
        self.name = ""
        self.url = ""
        self.api_enabled = False
        self.licensing_model = ""
        
        pass