""" Unreal Engine Communications """
import logging
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)

class UnrealService:
    def __init__(self, restServer) -> None:
        """ Unreal Engine Communications Service """
        self.url = "http://{}".format(restServer)
        self.timeout = 3
        self.session = PrefixSession(url_prefix=self.url)

        # Assign the headers for the connection
        self.session.headers = {
            "Accept": "application/json"
        }

    def getProperty(self, objectPath, property=None):
        """ Get a property or the properties of an object """
        try:
            payload = {
                "objectPath": objectPath,
                "access": "READ_ACCESS"
            }

            if property:
                payload["propertyName"] = property

            request = self.session.put(
                "/remote/object/property",
                json=payload,
                timeout=self.timeout
            )
            return request.json()
        except Exception as e:
            logger.error("Failed to get unreal property. {}".format(e))
            return {}


class PrefixSession(requests.Session):
    """ Subclass the Session to include a common url_prefix """

    def __init__(self, *args, url_prefix=None, **kwargs):
        """ Init w/url_prefix """
        super().__init__(*args, **kwargs)
        self.url_prefix = url_prefix if url_prefix else ""

    def request(self, method, url, **kwargs):
        """ Override request with adjusted url """
        modified_url = urljoin(self.url_prefix, url)

        return super().request(method, modified_url, **kwargs)
