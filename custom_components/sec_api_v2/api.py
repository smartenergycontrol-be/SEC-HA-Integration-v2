"""API class script."""

import logging
from urllib.parse import urlencode

import aiohttp

_LOGGER = logging.getLogger(__name__)
API_BASE_URL = "https://api.smartenergycontrol.be"

MONTHS_MAP = {
    "January": "jan",
    "February": "feb",
    "March": "mrt",
    "April": "apr",
    "May": "mei",
    "June": "jun",
    "July": "jul",
    "August": "aug",
    "September": "sep",
    "October": "okt",
    "November": "nov",
    "December": "dec",
}


class SmartEnergyControlAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        self.jaar = None
        self.maand = None

    async def authenticate(self):
        """Authenticate the API key asynchronously by fetching the latest year and month."""
        url = f"{API_BASE_URL}/month"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.jaar = data.get("jaar")
                        self.maand = data.get("maand")

                        return True
                    else:
                        _LOGGER.error(f"Failed to authenticate: {response.status}")
                        return False
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error during authentication: {e}")
            return False

    async def get_data(self, **params):
        """Fetch data from the Smart Energy Control API asynchronously using the latest year and month."""
        if params.get("jaar") in [None, "NULL"]:
            params["jaar"] = self.jaar
        if params.get("maand") in [None, "NULL"]:
            params["maand"] = self.maand
        else:
            params["maand"] = MONTHS_MAP[params["maand"]]
        url = f"{API_BASE_URL}/data?{urlencode(params)}"
        _LOGGER.info(url)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        _LOGGER.error(f"Failed to fetch data: {response.status}")
                        return None
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error fetching data: {e}")
            return None

    async def get_prijsonderdelen(self, **params):
        """Fetch data and return a flat list of all 'prijsonderdelen'."""
        data = await self.get_data(**params)
        if data is None:
            return None
        prijsonderdelen_list = []
        contracts_data = data.get("data", {})
        for contract_value in contracts_data.values():
            prijsonderdelen = contract_value.get("prijsonderdelen", [])
            prijsonderdelen_list.extend(prijsonderdelen)
        return prijsonderdelen_list

    async def get_constants(self, zip_code):
        """Fetch data from the Smart Energy Control API asynchronously using the latest year and month."""
        url = f"{API_BASE_URL}/constants?postcode={zip_code}"
        # _LOGGER.info(url)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        _LOGGER.error(f"Failed to fetch data: {response.status}")
                        return None
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Error fetching data: {e}")
            return None
