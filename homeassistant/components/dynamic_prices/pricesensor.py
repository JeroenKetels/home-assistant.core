"""Sensor for Price Integration."""

from datetime import UTC, datetime as dt

from numpy import mean

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN


class PriceSensor(NumberEntity):
    """Sensor for Price Integration."""

    def __init__(self, hass: HomeAssistant | None, key, name) -> None:
        """Initialise the Price sensor."""
        self._name = name
        self._hass = hass
        self._attr_native_unit_of_measurement = "€/MWh"
        self._attr_native_max_value = 999
        self._attr_native_min_value = -999
        self.entity_id = f"{DOMAIN}.{key}"
        self._prices: list[float] = []
        self._intersections: list[tuple[float, str]] = []
        self._max = 0.0
        self._min = 0.0
        self._avg = 0.0
        self._last_download = None

    def getCurrentItem(self):
        """Get current instance from the data store."""
        if f"{DOMAIN}" not in self._hass.data:
            return

        matches = []

        matches = list(
            filter(
                lambda v: dt_util.now(UTC).date()
                == dt.fromisoformat(v.get("dateTime")).date()
                and dt.fromisoformat(v.get("dateTime")).hour == dt_util.now(UTC).hour,
                self._hass.data[f"{DOMAIN}"],
            )
        )

        if len(matches) == 1:
            return matches[0]
        return None

    def refresh(self):
        """Refresh the state of this sensor."""
        curr = self.getCurrentItem()
        if curr:
            self._attr_native_value = curr["price"]

        if self._hass.data.get(f"{DOMAIN}") is not None:
            self._prices = [x["price"] for x in self._hass.data.get(f"{DOMAIN}")]

        prices_today = [
            x["price"]
            for x in list(
                filter(
                    lambda v: dt_util.now(UTC).date()
                    == dt.fromisoformat(v.get("dateTime")).date(),
                    self._hass.data.get(f"{DOMAIN}"),
                )
            )
        ]

        if len(prices_today) > 0:
            self._max = max(prices_today)
        if len(prices_today) > 0:
            self._avg = mean(prices_today)
        if len(prices_today) > 0:
            self._min = min(prices_today)

        self._hass.data[f"{DOMAIN}_currentPriceSensor"] = self

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {
            "min": self._min,
            "max": self._max,
            "avg": self._avg,
            "last_download": self._last_download,
            "current_area": self.current_area,
        }

    @property
    def name(self):
        """Return Name Property."""
        return self._name

    @property
    def last_download(self):
        """Return LastDownload Property."""
        return self._last_download

    @last_download.setter
    def last_download(self, value):
        self._last_download = value

    @property
    def min(self) -> float:
        """Return Min Property."""
        return self._min

    @property
    def avg(self) -> float:
        """Return Avg Property."""
        return self._avg

    @property
    def max(self) -> float:
        """Return Max Property."""
        return self._max

    @property
    def prices(self) -> list[float]:
        """Return Prices Property."""
        return self._prices

    @prices.setter
    def prices(self, value: list[float]):
        self._prices = value

    @property
    def intersections(self):
        """Return Intersections Property."""
        return self._intersections

    @intersections.setter
    def intersections(self, value):
        self._intersections = value

    @property
    def current_area(self):
        """Return Current Area Property."""
        if len(self._intersections) == 0:
            return ""

        f = list(
            filter(
                lambda v: dt_util.as_local(dt_util.now()).hour >= int(v[0]),
                self._intersections,
            )
        )
        f.sort(reverse=True)

        if len(f) == 0:
            return ""

        return f[0][1]
