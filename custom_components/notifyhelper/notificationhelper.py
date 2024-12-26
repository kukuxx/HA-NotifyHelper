import asyncio
import aiofiles
import json
import logging
import os
import pickle

from collections import deque
from urllib.parse import urlparse

from homeassistant.util.dt import now, as_timestamp

_LOGGER = logging.getLogger(__name__)


class NotificationHelper:

    def __init__(self, hass, ios_devices, android_devices, entry_id, entry_name):
        self.hass = hass
        self.entry_id = entry_id
        self.entry_name = entry_name.split(".")[1]
        self._lock = asyncio.Lock()
        self._notifications_dict: dict[str, list[deque, int]] = {}
        self._ios_devices_id = ios_devices
        self._android_devices_id = android_devices
        self.limit = 100

    async def save_notifications_dict(self):
        """保存字典(save dict)"""
        try:
            file_path = f"/config/custom_components/notifyhelper/notifications/{self.entry_id}.pkl"
            async with aiofiles.open(file_path, 'wb') as f:
                pkl_data = pickle.dumps(self._notifications_dict)
                await f.write(pkl_data)
            _LOGGER.debug(
                f"Successfully saved notifications dict for {self.entry_name} to {file_path}"
            )
        except (OSError, IOError) as e:
            # 硬碟空間不足
            _LOGGER.error(f"Error saving {self.entry_name} pickle file: {e}")
        except Exception as e:
            _LOGGER.error(f"Save {self.entry_name} dict Error: {e}")

    async def load_notifications_dict(self):
        """讀取字典(load dict)"""
        _dict = {}
        try:
            pkl_file_path = f"/config/custom_components/notifyhelper/notifications/{self.entry_id}.pkl"
            json_file_pash = f"/config/custom_components/notifyhelper/notifications/{self.entry_id}.json"

            if os.path.exists(pkl_file_path):
                # 優先讀取 Pickle 文件
                async with aiofiles.open(pkl_file_path, 'rb') as f:
                    contents = await f.read()
                    _dict = pickle.loads(contents)
                _LOGGER.debug(f"{self.entry_name}: Notification file loaded successfully.")

            elif os.path.exists(json_file_pash):
                async with aiofiles.open(json_file_pash, 'r', encoding='utf-8') as f:
                    contents = await f.read()
                    _dict = json.loads(contents)
                _LOGGER.debug(f"{self.entry_name}: Notification file loaded successfully.")
            else:
                _LOGGER.debug(f"{self.entry_name}: No notification file found.")

        except (EOFError, pickle.UnpicklingError) as e:
            # 文件損壞
            _LOGGER.error(f"Error reading {self.entry_name} pickle file: {e}")
        except json.JSONDecodeError as e:
            # json格式錯誤
            _LOGGER.error(f"{self.entry_name} Json Decode Error: {e}")

        return _dict

    async def start(self):
        """檢查是否有舊資料並建立字典(Check if there are old data and build a dict)"""
        try:
            old_dict = await self.load_notifications_dict()

            if old_dict:
                notifications = old_dict[self.entry_id][0]
                badge = old_dict[self.entry_id][1]
                self._notifications_dict[self.entry_id
                                         ] = [deque(notifications, maxlen=self.limit), badge]
            else:
                self._notifications_dict[self.entry_id] = [deque(maxlen=self.limit), 0]

            await self.update_notification_log()

        except Exception as e:
            _LOGGER.error(f"Initialization {self.entry_name} dict Error: {e}")

    async def stop(self):
        """刪除sensor(remove sensor)"""
        try:
            state_entity_id = f"sensor.{self.entry_name}_notifications"
            self.hass.states.async_remove(state_entity_id)
        except Exception as e:
            _LOGGER.error(f"Remove {self.entry_name} sensor Error: {e}")

    async def send_notification(self, data):
        """發送通知(send notification)"""
        try:
            _data = dict(data)
            _LOGGER.debug(f"{self.entry_name}: {_data}")
            if not _data.get("title", None):
                _data["title"] = "Notification"
            parameter_data = _data.setdefault("data", {})
            android_data = parameter_data.setdefault("android", {})
            ios_data = parameter_data.setdefault("ios", {})
            image = parameter_data.get("image", None)
            video = parameter_data.get("video", None)
            badge = self._notifications_dict[self.entry_id][1] + 1

            if not android_data and not ios_data:
                parameter_data.setdefault("push", {}).update({"badge": badge})
                _LOGGER.debug(f"{self.entry_name}: {_data}")
                devices = self._ios_devices_id + self._android_devices_id

                tasks = [
                    self.hass.async_create_task(
                        self.hass.services.async_call(
                            "notify", device_id, {
                                "message": _data.get("message", "No message"),
                                "title": _data.get("title"),
                                "data": _data.get("data")
                            }
                        )
                    ) for device_id in devices
                ]

            elif self._android_devices_id and android_data:
                image = android_data.get("image", None)
                video = android_data.get("video", None)

                android_tasks = [
                    self.hass.async_create_task(
                        self.hass.services.async_call(
                            "notify", device_id, {
                                "message": _data.get("message", "No message"),
                                "title": _data.get("title"),
                                "data": _data.get("data").get("android")
                            }
                        )
                    ) for device_id in self._android_devices_id
                ]

            if self._ios_devices_id and ios_data:
                ios_data.setdefault("push", {}).update({"badge": badge})
                _LOGGER.debug(f"{self.entry_name}: {_data}")
                image = ios_data.get("image", None)
                video = ios_data.get("video", None)

                ios_tasks = [
                    self.hass.async_create_task(
                        self.hass.services.async_call(
                            "notify", device_id, {
                                "message": _data.get("message", "No message"),
                                "title": _data.get("title"),
                                "data": _data.get("data").get("ios")
                            }
                        )
                    ) for device_id in self._ios_devices_id
                ]

            await self.save_notification(_data, badge, image, video)
            await self.update_notification_log()

        except KeyError as e:
            _LOGGER.error(f"Get {self.entry_name} data error: {e}")
        except Exception as e:
            _LOGGER.error(f"Failed to send notification for {self.entry_name}: {e}")

    async def save_notification(self, data, badge, image, video):
        """保存通知(save notification)"""
        try:
            async with self._lock:
                notifications_dq = self._notifications_dict.get(self.entry_id)[0]

                timestamp = as_timestamp(now())
                send_time = now().strftime("%Y-%m-%d %H:%M:%S")
                message = data.get("message", "No message")
                title = data.get("title", "Notification")
                color = data.get("color", None)
                # 建立通知
                notification_parts = [
                    f"<ha-alert alert-type='info'><strong>{title}</strong></ha-alert>",
                ]

                if not color:
                    notification_parts.append(f"<blockquote>{message}<br>")
                else:
                    notification_parts.append(
                        f"<blockquote><font color='{color}'>{message}</font><br>"
                    )

                if image:
                    if await self.check_url(image):
                        notification_parts.append(f"<br><img src='{image}'/><br>")
                    else:
                        notification_parts.append(
                            f"<br><img src='{image}?timestamp={timestamp}'/><br>"
                        )

                if video:
                    video_type, url_bool = await self.check_url(video)
                    if url_bool:
                        notification_parts.append(
                            f"<br><video controls preload='metadata'>"
                            f"<source src='{video}' type='video/{video_type}'>"
                            f"</video><br>"
                        )
                    else:
                        video_extension = video.split(".")[-1].lower()
                        notification_parts.append(
                            f"<br><video controls preload='metadata'>"
                            f"<source src='{video}?timestamp={timestamp}' type='video/{video_extension}'>"
                            f"</video><br>"
                        )

                notification_parts.append(f"<br><b><i>{send_time}</i></b></blockquote>")
                # 拼接成完整的字符串
                notification = ''.join(notification_parts)
                # 將新通知加入deque #
                notifications_dq.appendleft(notification)
                self._notifications_dict[self.entry_id][1] = badge
                await self.save_notifications_dict()

        except Exception as e:
            _LOGGER.error(f"Save {self.entry_name} notification Error: {e}")

    async def check_url(self, url):
        """check url"""
        result = urlparse(url)
        file_path = result.path
        video_type = file_path.split('.')[-1].lower() if '.' in file_path else None
        url_bool = result.scheme in ['http', 'https']
        return video_type, url_bool

    async def update_notification_log(self):
        """將通知列表更新到sensor(update sensor)"""
        try:
            async with self._lock:
                notification_dq = self._notifications_dict[self.entry_id][0].copy()

            if notification_dq:
                # notification_str = '\n'.join(notification_dq)
                # 更新 sensor
                self.hass.states.async_set(
                    f"sensor.{self.entry_name}_notifications",
                    f"{self.entry_name} notifications",
                    attributes={"notifications": list(notification_dq)}
                )
            else:
                self.hass.states.async_set(
                    f"sensor.{self.entry_name}_notifications", f"{self.entry_name} notifications"
                )
        except Exception as e:
            _LOGGER.error(f"Update {self.entry_name} notifications Error: {e}")

    async def read(self, data):
        """改成已讀狀態(change to read status)"""
        await self.read_notification()
        await self.update_notification_log()

        if self._ios_devices_id:
            tasks = [
                self.hass.async_create_task(
                    self.hass.services.async_call("notify", device_id, {"message": "clear_badge"})
                ) for device_id in self._ios_devices_id
            ]

    async def read_notification(self):
        """將通知中的 info 類型更改為 success 類型(change alert-type info to success)"""
        try:
            async with self._lock:
                notifications_dq = self._notifications_dict.get(self.entry_id)[0]
                # 如果該通知不為空
                if notifications_dq:
                    notifications_dq = [
                        notification.replace('alert-type=\'info\'', 'alert-type=\'success\'')
                        if 'alert-type=\'info\'' in notification else notification
                        for notification in notifications_dq
                    ]
                    self._notifications_dict[self.entry_id
                                             ] = [deque(notifications_dq, maxlen=self.limit), 0]
                    await self.save_notifications_dict()
                else:
                    _LOGGER.warning(f"No valid notifications found for {self.entry_name}")
        except Exception as e:
            _LOGGER.error(f"Error replacing {self.entry_name} notifications: {e}")
