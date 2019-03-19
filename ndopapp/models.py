"""
General models
"""

class NDOP_Error(Exception):
    def __init__(self, safe_message):
        super().__init__(safe_message)
        self.safe_message = safe_message
        
    status_code = 500


class NDOP_RequestError(NDOP_Error):
    pass


class NDOP_API_Error(NDOP_Error):
    pass


