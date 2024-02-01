from dataclasses import dataclass
from typing import Any, Dict, Union

import requests

from .base import Chain


@dataclass
class RemoteChain(Chain[Dict[str, Any], Union[str, Dict[str, Any]]]):
    """Chain that calls an API to generate a response.

    Adapted from langserve.RemoteRunnable.
    """

    def __init__(self, api_url: str):
        """Initialize the chain with the given API URL."""
        self.api_url = api_url

    @property
    def invoke_url(self):
        return self.api_url + "/invoke"

    def _call(
        self, x: Any, **kwargs: Any  # noqa: ARG002
    ) -> Union[str, Dict[str, Any]]:
        """Run the chain on the given input `x`."""
        try:
            response = requests.post(self.invoke_url, json={"input": x}, timeout=30)
        except requests.ReadTimeout as e:
            self._raise(e)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self._raise(e)
        return response.json()["output"]
