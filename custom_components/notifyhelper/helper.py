from __future__ import annotations

import asyncio
import logging
import os
import orjson

from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader

from homeassistant.util.dt import now, as_timestamp
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .data import NotificationData
from .const import DOMAIN, DATA_PATH, UPDATE_EVENT

_LOGGER = logging.getLogger(__name__)


class NotificationHelper:

    def __init__(self, hass, entry_id, entry_name, ios_devices, android_devices, url):
        self.hass = hass
        self.entry_id = entry_id
        self.entry_name = entry_name.split(".")[1]
        self._ios_devices_id = ios_devices
        self._android_devices_id = android_devices
        self._url = url
        self.limit = 500
        self._dirpath = None
        self._default_file = None
        self._notifidata = None
        self._template = None
        self._lock = asyncio.Lock()

    async def async_start(self):
        """檢查是否有舊資料並建立dataclass(Check if there are old data and build a dataclass)"""
        try:
            self._dirpath = os.path.join(self.hass.config.config_dir, DATA_PATH)
            notifications_dir = f"{self._dirpath}/notifications"
            os.makedirs(notifications_dir, exist_ok=True)
            self._default_file = f"{self._dirpath}/notifications/{self.entry_id}.json"
            
            env = Environment(
                loader=FileSystemLoader(self._dirpath),
                autoescape=True
            )
            self._template = await self.hass.async_add_executor_job(env.get_template, "template.html")

            self._notifidata = NotificationData(maxlen=self.limit)

            old_data = await self.async_load_notifidata()
            if old_data:
                self._notifidata.from_dict(old_data)
                await self.async_trigger(old_data["msg"])
            else:
                await self.async_trigger([])  

        except Exception as e:
            _LOGGER.error(f"Initialization {self.entry_name} data Error: {e}")

    async def async_load_notifidata(self):
        """讀取資料(load data)"""
        def load():
            _dict = {}
            pkl_file = f"{self._dirpath}/notifications/{self.entry_id}.pkl"
            
            try:
                if os.path.exists(self._default_file):
                    with open(self._default_file, 'rb') as f:
                        _dict = orjson.loads(f.read())
                    _LOGGER.debug(f"{self.entry_name}: JSON loaded.")
                elif os.path.exists(pkl_file):
                    import pickle
                    with open(pkl_file, 'rb') as f:
                        pkl_data= pickle.loads(f.read())
                        _dict = {
                            "msg": list(pkl_data[self.entry_id][0]),
                            "badge": pkl_data[self.entry_id][1]
                        }
                    _LOGGER.debug(f"{self.entry_name}: Pickle loaded.")
                else:
                    _LOGGER.warning(f"{self.entry_name}: No existing data found.")
            except Exception as e:
                _LOGGER.error(f"{self.entry_name} load error: {e}")
        
            return _dict

        return await self.hass.async_add_executor_job(load)

    async def async_save_notifidata(self, data):
        """保存資料(save data)"""
        def save():
            try:
                with open(self._default_file, 'wb') as f:
                    f.write(orjson.dumps(data))

                _LOGGER.debug(f"{self.entry_name} data saved ")
            except Exception as e:
                _LOGGER.error(f"{self.entry_name} data save error: {e}")
        
        await self.hass.async_add_executor_job(save)

    async def async_send(self, call_data):
        """發送通知(send notification)"""

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
            async with self._lock:
                _data = dict(call_data)
                title = _data["title"] = _data.get("title") or "Notification"
                message = _data["message"] = _data.get("message") or "No message"
                parameters_data = _data["data"] = _data.get("data") or {}
                color = _data.get("color")

                _LOGGER.debug(f"{self.entry_name}: {_data}")
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

                await asyncio.gather(
                    self.async_render(title, message, color, badge, image, video),
                    *tasks
                )
        except KeyError as e:
            _LOGGER.error(f"{self.entry_name} get call_data error: {e}")
        except Exception as e:
            _LOGGER.error(f"{self.entry_name} failed to send: {e}")

    async def async_render(self, title, msg, color, badge, image, video):
        """訊息模板 (render template)"""
        def _check_url(url):
            """check url"""
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
            await self.async_save_notifidata(data)
        except Exception as e:
            _LOGGER.error(f"{self.entry_name} render Error: {e}")

    async def async_read(self):
        """改成已讀狀態(change to read status)"""
        try:
            async with self._lock:
                if not self._notifidata.messages:
                    _LOGGER.warning(f"No valid notifications found for {self.entry_name}")
                    return

                data = self._notifidata.read_messages()
                tasks = [
                    self.async_trigger(data["msg"]),
                    self.async_save_notifidata(data),
                ]

                if self._ios_devices_id:
                    tasks.extend([
                        self.hass.services.async_call("notify", device_id, {"message": "clear_badge"})
                        for device_id in self._ios_devices_id
                    ])
                    
                await asyncio.gather(*tasks)

                _LOGGER.debug(f"Read successfully")
        except Exception as e:
            _LOGGER.error(f"Error reading {self.entry_name} notifications: {e}")

    async def async_clear(self):
        """清空通知(clear notifications)"""
        try:
            async with self._lock:
                if not self._notifidata.messages:
                    _LOGGER.warning(f"No valid notifications found for {self.entry_name}")
                    return

                data = self._notifidata.clear_messages()
                tasks = [
                    self.async_trigger(data["msg"]),
                    self.async_save_notifidata(data),
                ]

                if self._ios_devices_id:
                    tasks.extend([
                        self.hass.services.async_call("notify", device_id, {"message": "clear_badge"})
                        for device_id in self._ios_devices_id
                    ])

                await asyncio.gather(*tasks)

                _LOGGER.debug(f"Clear successfully")
        except Exception as e:
            _LOGGER.error(f"Error clearing {self.entry_name} notifications: {e}")

    
    async def async_trigger(self, msg=None):
        """觸發通知更新事件(trigger notifications update event)"""
        try:
            async_dispatcher_send(
                self.hass, 
                f"{UPDATE_EVENT}_{self.entry_name}",
                {
                    "event_type": UPDATE_EVENT,
                    "person": str(self.entry_name),
                    "notifications": msg if msg is not None else list(self._notifidata.messages),
                }
            )
            _LOGGER.debug(f"{self.entry_name} Notification updated successfully: {msg}")
        except Exception as e:
            _LOGGER.error(f"Update {self.entry_name} notifications Error: {e}")