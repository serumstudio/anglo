

class RoutingError(Exception):
    def __init__(self, msg: str = None):
        if msg is None:
            msg = "An error occured within AngloRouting"
        
        super().__init__(msg)

class RouteNotFound(RoutingError):
    def __init__(self):
        super().__init__("The path you've given was not found.")


class FileBaseRoutingError(RoutingError):
    pass


