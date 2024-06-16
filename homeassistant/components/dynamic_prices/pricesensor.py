"""Sensor for Price Integration."""

from datetime import datetime as dt

from numpy import fix, mean

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
        self._prices_today: list[float] = []
        self._max = 0.0
        self._min = 0.0
        self._avg = 0.0
        self._last_download = None

    def getCurrentItem(self):
        """Get current instance from the data store."""
        if f"{DOMAIN}" not in self._hass.data:
            return None

        matches = []

        matches = list(
            filter(
                lambda v: dt_util.utcnow().date()
                == dt_util.as_utc(dt.fromisoformat(v.get("dateTime"))).date()
                and dt_util.as_utc(dt.fromisoformat(v.get("dateTime"))).hour
                == dt_util.utcnow().hour
                and fix(dt_util.as_utc(dt.fromisoformat(v.get("dateTime"))).minute / 15)
                == fix(dt_util.utcnow().minute / 15),
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

        if self._hass.data.get(f"{DOMAIN}"):
            self._prices_today = [
                x["price"]
                for x in list(
                    filter(
                        lambda v: dt_util.as_local(dt_util.utcnow()).date()
                        == dt_util.as_local(dt.fromisoformat(v.get("dateTime"))).date(),
                        self._hass.data.get(f"{DOMAIN}"),
                    )
                )
            ]
        else:
            self._prices_today = []

        if len(self._prices_today) > 0:
            self._max = max(self._prices_today)
        if len(self._prices_today) > 0:
            self._avg = mean(self._prices_today)
        if len(self._prices_today) > 0:
            self._min = min(self._prices_today)

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
            "prices_today": self._prices_today,
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
    def current_area(self):
        """Return Current Area Property."""

        if not self._attr_native_value:
            return ""
        if not self.avg:
            return ""

        return "below" if self._attr_native_value < self.avg else "above"
