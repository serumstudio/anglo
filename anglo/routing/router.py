
#               Copyright (c) 2021 Serum Studio.

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import re
import os
from .errors import *
from .route import route_builders

RE_CC_TO_UNDERSCORE_ = re.compile("(.)([A-Z][a-z]+)") # Regular Expression for converting CamelCase to underscored text.
RE_CC_TO_UNDERSCORE = re.compile("([a-z0-9])([A-Z])") # Regular Expression for converting CamelCase to underscored text.



def build_route(pattern, finishing, kwargs, name, builders):
    if not finishing:
        assert not name
    
    for _build_route in builders:
        route = _build_route(pattern, finishing, kwargs, name)
        if route:
            return route
    else:
        raise LookupError("No matching route factory found")


def route_name(handler):
    """
    Give the route name with handler.
    """

    try:
        name = handler.__name__
    
    except AttributeError:
        name = handler.__class__.__name__

    _name = RE_CC_TO_UNDERSCORE_.sub(r"\1_\2", name)
    return RE_CC_TO_UNDERSCORE.sub(r"\1_\2", _name).lower()    



class BaseRouter:

    """
    A main class for Router. It holds matching, url/route tables
    and more, as well as adding routes.

    Arguments:
        builders (route_builders):
            A route builder rule for the router. It returns the default
            value which is `route_builders`

    """

    __slots__ = (
        "builders",
        "match_map",
        "mapping",
        "route_map",
        "inner_route_map"
    )

    def __init__(self, builders=None):
        
        #: A route builder rule for the router.
        #: It return the default route_builders.
        self.builders           = builders or route_builders

        
        #: A matching map for the routes where all matching routes stored.
        self.match_map          = {}
        
        #: Just a mapping where it stores data. Typically a list.
        self.mapping            = []
        
        self.route_map          = {}
        self.inner_route_map    = {}

    def add_route(self, pattern, handler, name=None, kwargs=None):
        """
        Add the route to the routing table.
        """

        name = name or route_name(name)

        route = build_route(pattern, True, kwargs, name, self.builders)

        self.route_map[name] = route.path

        if route.exact_matches:
            for pattern, kwargs in route.exact_matches:
                if pattern in self.match_map:  # the route or pattern already exist
                    print(f"{pattern} Already exists. Overriding..")

                self.match_map[pattern] = (handler, kwargs)

            route.exact_matches = None

        else:
            self.mapping.append((route.match, handler))


    def include(self, pattern, included, kwargs=None):
        """
        Includes nested routes below the current. Example of nested routes:
        /user/{some_user}/
        """
        # try build intermediate route
        
        route = build_route(pattern, False, kwargs, None, self.builders)
        
        if not isinstance(included, BaseRouter):
            router = BaseRouter(self.builders)
            router.add_routes(included)
            included = router
        
        if route.exact_matches:

            for p, kwargs in route.exact_matches:
                for k, v in included.match_map.items():
                    k = p + k
                    if k in self.match_map: 
                        print(f"{pattern} Already exists. Overriding..")

                    h, kw = v
                    self.match_map[k] = (h, dict(kwargs, **kw))
            route.exact_matches = None
            included.match_map = {}

            if included.mapping:
                self.mapping.append((route.match, included))

        else:
            self.mapping.append((route.match, included))
        route_path = route.path

        for name, path in included.route_map.items():
            if name in self.inner_route_map:  
                print(f"{pattern} Already exists. Overriding..")

            self.inner_route_map[name] = (route_path, path)
        included.route_map = None

        for name, paths in included.inner_route_map.items():
            if name in self.inner_route_map:  
                print(f"{pattern} Already exists. Overriding..")

            self.inner_route_map[name] = tuple([route_path] + list(paths))
        included.inner_route_map = None
        

    def add_routes(self, routes):
        """
        Same at add_route but instead it accepts a list of tuples.
        """

        for r in routes:
            length = len(r)
            kwargs, name = None, None

            if length == 2:
                pattern, handler = r

            elif length == 3:
                pattern, handler, kwargs = r

            else:
                pattern, handler, kwargs, name = r

            if isinstance(handler, (tuple, list, BaseRouter)):
                self.include(pattern, handler, kwargs)
            
            else:
                self.add_route(pattern, handler, name, kwargs)


    def match(self, path):
        """
        Match the given path to the routing table
        """
        if path in self.match_map:
            return self.match_map[path]

        for match, handler in self.mapping:
            print(match, handler)
            matched, kwargs = match(path)
            if matched >= 0:
                # TODO: isinstance(handler, BaseRouter)

                match = getattr(handler, "match", None)
                if not match:
                    return handler, kwargs
                handler, kwargs_inner = match(path[matched:])
                if handler:
                    if not kwargs:
                        return handler, kwargs_inner
                    if kwargs_inner:
                        kwargs = dict(kwargs, **kwargs_inner)
                    
                    return handler, kwargs

                    

        return None, {}


    def path_name(self, name, **kwargs):
        """
        Returns the url for the given route name
        """

        if name in self.route_map:
            return self.route_map[name](kwargs)

        else:
            return "".join(
                [path(kwargs) for path in self.inner_route_map[name]]
            )


class Router(BaseRouter):
    """
    A main routing for Anglo. 

        Methods:
            add_route():
                Add route for the route given.
            
            include():
                Include nested routes to the routing table

            add_routes():
                Same as add_route but instead accept list of tuples.
        
            match():
                Match the given route to the routing table

            path_name():
                Get the url for the given route name.

    """
    def __init__(self, builders=None):
        BaseRouter.__init__(self, builders=builders)

        self.routes = {}

    def __match_routes(self, route):
        pass

    def get(self, path=None, callback=None, name=None):

        if callable(path): path, callback = None, path

        def deco(callback):
            
            self.routes[path] = callback
            self.add_routes([(path, callback)])
            self.__match_routes()

            return callback

        return deco(callback) if callback else deco


class FileBasedRouter(BaseRouter):
    """
    A file based router. Inherited by `:BaseRouter:`
    """

    def __init__(self, folder, index_path, ignore_files=[], builders=None):
        super().__init__(builders=builders)

        if not os.path.isdir(folder):
            raise FileBaseRoutingError(f"{folder} is not a valid folder name. Please specify one")


        
