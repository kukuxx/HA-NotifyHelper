import logging
from urllib.parse import urlparse, parse_qs

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig

from .const import DOMAIN, SCRIPT_URL, FRONTEND_URL, HELPER_VER

_LOGGER = logging.getLogger(__name__)


async def async_setup_frontend(hass):
    """Setup the custom Lovelace card."""
    try:
        # Register the static resource for the custom card
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    FRONTEND_URL,
                    hass.config.
                    path(f"custom_components/{DOMAIN}{SCRIPT_URL}"),
                    False,
                )
            ]
        )
        _LOGGER.info(f"Registered static path for {FRONTEND_URL}")

        if (lovelace_data := hass.data.get("lovelace")) is None:
            _LOGGER.warning("Can not access the lovelace data")
            return

        resources = lovelace_data.resources
        frontend_added = False

        if not resources.loaded:
            await resources.async_load()
            resources.loaded = True

        for r in resources.async_items():
            if (r_url := r["url"]).startswith(FRONTEND_URL):
                frontend_added = True

                if version(r_url):
                    _LOGGER.info(
                        f"Resource {r_url} is already the latest version."
                    )
                    continue
                else:
                    new_url = FRONTEND_URL + f"?ver={HELPER_VER}"
                    await resources.async_update_item(
                        r["id"], {"url": new_url}
                    )
                    _LOGGER.info(
                        f"Updating existing resource: {r_url} to {new_url}"
                    )
                    
            elif r_url.startswith(SCRIPT_URL):
                await resources.async_delete_item(r["id"])
                _LOGGER.info(f"Deleted outdated resource: {r_url}")

        if not frontend_added:
            if getattr(resources, "async_create_item", None):
                await resources.async_create_item(
                    {
                        "res_type": "module",
                        "url": FRONTEND_URL + f"?ver={HELPER_VER}",
                    }
                )
                _LOGGER.info(
                    f"Added new resource with version {HELPER_VER}: {FRONTEND_URL}"
                )
    except Exception as e:
        _LOGGER.error(f"Failed to setup the custom card: {e}", exc_info=True)


async def async_del_frontend(hass):
    """Delete the custom Lovelace card resources."""
    try:
        if (lovelace_data := hass.data.get("lovelace")) is None:
            _LOGGER.warning("Can not access the lovelace data")
            return

        resources = lovelace_data.resources

        if not resources.loaded:
            await resources.async_load()
            resources.loaded = True

        for r in resources.async_items():
            if (r_url := r["url"]).startswith(FRONTEND_URL):
                await resources.async_delete_item(r["id"])
                _LOGGER.info(f"Deleted resource: {r_url}")
                return
    except Exception as e:
        _LOGGER.error(f"Failed to delete resources: {e}", exc_info=True)


def version(url):
    """Extract the version from the query string of a URL."""
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        # Default to 0 if 'ver' is missing
        ver_str = query_params.get("ver", ["0"])[0]
        return ver_str == HELPER_VER
    except Exception as e:
        _LOGGER.warning(f"Error checking version in URL: {url}, error: {e}")
        return False
