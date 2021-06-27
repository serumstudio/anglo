
from anglo.routing import Router

class router:
    def __init__(self):
        self.routes = {}
    
    def get(self, path=None, callback=None, name=None):

        if callable(path): path, callback = None, path

        def deco(callback):
            self.routes[path] = callback
            return callback

        return deco(callback) if callback else deco

route = router()

@route.get("/")
def home():
    print("homepage")

r = Router()



