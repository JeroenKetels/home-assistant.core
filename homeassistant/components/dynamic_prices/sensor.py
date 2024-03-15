"""Platform for Eneco integration."""
from __future__ import annotations

from datetime import timedelta
import logging

import requests

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util

from .calculator import Calculator
from .const import DOMAIN, URL_DEFAULT_VALUE, URL_PARAM
from .pricesensor import PriceSensor

_LOGGER = logging.getLogger(__name__)


def getCurrentPriceSensor(hass: HomeAssistant) -> PriceSensor:
    """Get Current price sensor."""
    return hass.data[f"{DOMAIN}_currentPriceSensor"]


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Platform for Dynamic Prices integration."""
    # # We only want this platform to be set up via discovery.
    # if discovery_info is None:
    #     return

    hass.data[f"{DOMAIN}_currentPriceSensor"] = None

    async def handle_tariefUpdate(call):
        """Handle the service call."""
        currentPriceSensor = getCurrentPriceSensor(hass)
        currentPriceSensor.refresh()
        return True

    async def handle_download(call):
        """Handle the service call."""
        url = hass.data.get(URL_PARAM, URL_DEFAULT_VALUE)

        responseToday = await hass.async_add_executor_job(
            requests.get,
            f"{url}/{dt_util.as_local(dt_util.now()).strftime('%Y-%m-%d')}?crt={dt_util.now().timestamp()}",
        )

        responseTomorrow = await hass.async_add_executor_job(
            requests.get,
            f"{url}/{(dt_util.as_local(dt_util.now()) + timedelta(days=1)).strftime('%Y-%m-%d')}?crt={dt_util.now().timestamp()}",
        )

        if responseToday.ok and responseTomorrow.ok:
            # store data for later use
            hass.data[f"{DOMAIN}"] = responseToday.json() + responseTomorrow.json()
        else:
            hass.data[f"{DOMAIN}"] = responseToday.json()

        currPriceSensor = getCurrentPriceSensor(hass)
        currPriceSensor.refresh()

        calc = Calculator()
        curve_points = currPriceSensor.prices

        # Vind snijpunten
        all_intersections = calc.find_intersection_points(
            curve_points, currPriceSensor.avg
        )
        currPriceSensor.intersections = all_intersections
        currPriceSensor.last_download = dt_util.as_local(dt_util.now())

        # Return boolean to indicate that initialization was successful.
        return True

    hass.services.async_register(DOMAIN, "download", handle_download)
    hass.services.async_register(DOMAIN, "updateTarief", handle_tariefUpdate)

    async_track_time_change(hass, handle_download, hour=8, minute=30)

    hass.helpers.event.async_track_time_interval(
        handle_tariefUpdate, timedelta(seconds=10)
    )

    hass.data[f"{DOMAIN}_currentPriceSensor"] = PriceSensor(
        hass, "energy_current_price", "Current Energy Price"
    )

    async_add_entities({hass.data[f"{DOMAIN}_currentPriceSensor"]})

    await handle_download(dt_util.as_local(dt_util.now()))
    await handle_tariefUpdate(dt_util.as_local(dt_util.now()))
