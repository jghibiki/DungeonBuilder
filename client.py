from interactive import ClientModule, LiveModule, InitModule
from viewport import Viewport
from state import State
import requests
import logging
import json
import hashlib

log = logging.getLogger('simple_example')

class Client(ClientModule, InitModule):
    def __init__(self, password, host="127.0.0.1", port=8080):
        self._host = host
        self._port = port
        self._previous_hash = None
        self._previous_feature_hashes = []
        self._password = password
        self._base_url = "http://%s:%s" % (self._host, self._port)
        self._username = ""

    def init(self, viewer):
        state = viewer.get_submodule(State)
        self._username = state.get_state("username")

    def connect(self):
        """Deprecated"""
        pass

    def disconnect(self):
        """Deprecated"""
        pass

    def update(self, viewer):
        log.debug("client.update called")

        hashes = self.make_request("/hash")

        submodules = viewer.get_submodules(LiveModule)

        updates = False
        for module in submodules:
            module_updates = module._update(viewer, hashes)
            updates = updates and module_updates

        return updates


    def make_request(self, url, payload=None):
        if not payload:
            log.debug("make_request GET %s" % url)
            r = requests.get(self._base_url + url, auth=("user", self._password))
        else:
            log.debug("make_request POST %s %s" % (url, payload))
            r = requests.post(self._base_url + url,
                              auth=(self._username, self._password),
                              headers={'content-type': 'application/json'},
                              data=json.dumps(payload))

        if r.status_code is not 200: # TODO: fix naiive checl
            log.warn("make_request http error: %s %s %s" % (url, r.status_code, r.text))

        # try to get json
        try:
            raw_data = r.json()
            return raw_data
        except:
            return None

