from __future__ import annotations

import asyncio
import logging
import os

from enum import Enum
from types import MappingProxyType
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader

from homeassistant.core import callback
from homeassistant.util.dt import now, as_timestamp
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .data import NotificationData
from .const import DOMAIN, DATA_PATH, UPDATE_EVENT

_LOGGER = logging.getLogger(__name__)


class CMD(Enum):
    SEND = "send"
    READ = "read"
    CLEAR = "clear"
    CLOSE = "close"


class NotificationHelper:

    def __init__(self, hass, entry_id, entry_name, ios_devices, android_devices, url, storage):
        self.hass = hass
        self.entry_id = entry_id
        self.entry_name = entry_name.split(".")[1]
        self._ios_devices_id = ios_devices
        self._android_devices_id = android_devices
        self._url = url
        self._store = storage
        self._limit = 500
        self._notifidata = None
        self._template = None
        self._queue = asyncio.Queue(maxsize=10)
        self._Initialized = asyncio.Event()

    async def async_initialize(self):
        """Check if there are old data and build a dataclass"""
        try:
            env = Environment(
                loader=FileSystemLoader(os.path.join(self.hass.config.config_dir, DATA_PATH)),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True
            )
            self._template = await self.hass.async_add_executor_job(env.get_template, "template.html")

            self._notifidata = NotificationData(maxlen=self._limit)

            old_data = await self._store.async_load()
            if old_data:
                self._notifidata.from_dict(old_data)
            else:
                _LOGGER.warning("No old data found for %s", self.entry_name)

            self._Initialized.set() 

        except Exception as e:
            _LOGGER.error("Initialization %s data Error: %s", self.entry_name, e)

    async def async_handle_commands(self):
        """handle commands"""
        try:
            while True:
                cmd, call_data = await self._queue.get()
                try:
                    msg_data = None

                    if cmd == CMD.CLOSE:
                        self._store.async_save(self._notifidata.to_dict())
                        break
                    elif cmd == CMD.SEND:
                        msg_data = await self._async_send(call_data)
                    elif cmd == CMD.READ:
                        msg_data = await self._async_read()
                    elif cmd == CMD.CLEAR:
                        msg_data = await self._async_clear()
                    
                    if self._queue.empty() and msg_data is not None:
                        await self._store.async_save(msg_data)
                except Exception as e:
                    _LOGGER.error("Failed to handle command %s: %s", cmd, e)
                finally:
                    self._queue.task_done()
        except asyncio.CancelledError:
            _LOGGER.debug("Command handler for %s closed", self.entry_name)
            raise

    async def async_put(
        self, cmd_data: tuple[CMD, MappingProxyType | dict | None]
    ):
        """put command in queue"""
        await self._queue.put(cmd_data)

    async def aclose(self):
        """close helper"""
        await self._queue.put((CMD.CLOSE, None))
        await self._queue.shutdown()
        await self._queue.join()
        _LOGGER.debug("Helper for %s closed", self.entry_name)

    async def _async_send(self, call_data) -> dict:
        """send notification"""
        def _create_send_task(devices, p_data):
            if not devices:
                return []

            if self._url:
                p_data.setdefault("url", self._url)

            notification_payload = {
                "message": message,
                "title": title,
                "data": p_data,
            }

            return [
                self.hass.services.async_call("notify", device_id, notification_payload)
                for device_id in devices
            ]


        try:
            _data = dict(call_data)
            title = _data["title"] = _data.get("title") or "Notification"
            message = _data["message"] = _data.get("message") or "No message"
            parameters_data = _data["data"] = _data.get("data") or {}
            color = _data.get("color")

            _LOGGER.debug("Send data to %s: %s", self.entry_name, _data)
            badge = self._notifidata.badge + 1
            tasks = []

            if "android" not in parameters_data and "ios" not in parameters_data:
                image = parameters_data.get("image")
                video = parameters_data.get("video")
                parameters_data.setdefault("push", {}).update({"badge": badge})
                tasks = _create_send_task(self._ios_devices_id + self._android_devices_id, parameters_data)
            else:
                android_data = parameters_data.get("android")
                ios_data = parameters_data.get("ios")
                image = (android_data and android_data.get("image")) or \
                        (ios_data and ios_data.get("image"))
                video = (android_data and android_data.get("video")) or \
                        (ios_data and ios_data.get("video"))

                if android_data:
                    android_tasks = _create_send_task(self._android_devices_id, android_data)
                    tasks.extend(android_tasks)

                if ios_data:
                    ios_data.setdefault("push", {}).update({"badge": badge})
                    ios_tasks = _create_send_task(self._ios_devices_id, ios_data)
                    tasks.extend(ios_tasks)

            await asyncio.gather(*tasks)
            data = await self._async_render(title, message, color, badge, image, video)
            return data
        except KeyError as e:
            _LOGGER.error("%s get call_data error: %s", self.entry_name, e)
        except Exception as e:
            _LOGGER.error("%s failed to send: %s", self.entry_name, e)

    async def _async_render(
            self, title, msg, color, badge, image, video
        ) -> dict:
        """render template"""
        def _check_url(url):
            valid_extensions = {"mp4", "avi", "mov", "png", "jpg", "jpeg", "gif", "webp"}
            result = urlparse(url)
            url_bool = result.scheme in ['http', 'https']
            path = result.path
            file_type = path.split('.')[-1].lower() \
                        if '.' in path and path.split('.')[-1].lower() in valid_extensions else None
            return file_type, url_bool


        try:
            timestamp = as_timestamp(now())
            send_time = now().strftime("%Y-%m-%d %H:%M:%S")

            video_type, video_is_url = _check_url(video) if video else (None, False)
            _, image_is_url = _check_url(image) if image else (None, False)

            rendered_html = self._template.render(
                title=title,
                message=msg,
                color=color,
                image=image,
                image_is_url=image_is_url,
                video=video,
                video_is_url=video_is_url,
                video_type=video_type,
                timestamp=timestamp,
                send_time=send_time
            )
            data = self._notifidata.add_message(rendered_html, badge)
            await self.async_trigger(data["msg"])
            return data
        except Exception as e:
            _LOGGER.error("%s failed to render template: %s", self.entry_name, e)

    async def _async_read(self) -> dict | None:
        """change to read status"""
        try:
            if not self._notifidata.messages:
                _LOGGER.warning(
                    "No valid notifications found for %s", self.entry_name
                )
                return None

            data = self._notifidata.read_messages()
            tasks = [
                self.async_trigger(data["msg"]),
            ]

            if self._ios_devices_id:
                tasks.extend([
                    self.hass.services.async_call("notify", device_id, {"message": "clear_badge"})
                    for device_id in self._ios_devices_id
                ])
                
            await asyncio.gather(*tasks)

            _LOGGER.debug("Read successfully")
            return data
        except Exception as e:
            _LOGGER.error("%s failed to read: %s", self.entry_name, e)

    async def _async_clear(self) -> dict | None:
        """clear notifications"""
        try:
            if not self._notifidata.messages:
                _LOGGER.warning(
                    "No valid notifications found for %s", self.entry_name
                )
                return None

            data = self._notifidata.clear_messages()
            tasks = [
                self.async_trigger(data["msg"]),
            ]

            if self._ios_devices_id:
                tasks.extend([
                    self.hass.services.async_call("notify", device_id, {"message": "clear_badge"})
                    for device_id in self._ios_devices_id
                ])

            await asyncio.gather(*tasks)

            _LOGGER.debug("Clear successfully")
            return data
        except Exception as e:
            _LOGGER.error("%s failed to clear: %s", self.entry_name, e)

    @callback
    async def async_trigger(self, msg=None):
        """trigger notifications update event"""
        try:
            if not self._Initialized.is_set():
                _LOGGER.debug("Waiting for initialization to complete...")
                await asyncio.wait_for(self._Initialized.wait(), timeout=15)
            
            async_dispatcher_send(
                self.hass, 
                f"{UPDATE_EVENT}_{self.entry_name}",
                {
                    "event_type": UPDATE_EVENT,
                    "person": str(self.entry_name),
                    "notifications": msg if msg is not None else list(self._notifidata.messages),
                }
            )
            _LOGGER.debug("%s Notification updated successfully: %s", self.entry_name, msg)
        except asyncio.TimeoutError:
            _LOGGER.error("%s Initialization timeout", self.entry_name)
        except Exception as e:
            _LOGGER.error("%s failed to trigger: %s", self.entry_name, e)
