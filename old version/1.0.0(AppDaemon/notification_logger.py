import appdaemon.plugins.hass.hassapi as hass
import asyncio
import json


class NotificationLogger(hass.Hass):

    def initialize(self):
        # 監聽 call_service 事件
        self.listen_event(self.send_notification, event="call_service", service="ad_notify")
        self.listen_event(
            self.button_pressed, event="call_service", domain="input_button", service="press"
        )
        self._lock = asyncio.Lock()
        self._notifications_dict: dict[str, list[list, int]] = {}
        # self._notify_action_id = self.get_notify_actions("mobile_app") or []
        self._notify_action_id = self.args.get("device", [])
        self.button_list = self.create_button()
        self.create_task(asyncio.sleep(0.5), callback=self.start)

    # def get_notify_actions(self, prefix):
    #     """取得Notify action ID"""
    #     try:
    #         services = self.list_services()
    #         match_actions = [
    #             action['service'] for action in services
    #             if action['domain'] == 'notify' and action['service'].startswith(prefix)
    #         ]
    #         return match_actions

    #     except Exception as e:
    #         self.log(f"Get notify actions Error: {e}", level="ERROR")

    def create_button(self):
        """創建button"""
        buttons = []
        for action_id in self._notify_action_id:
            entity_id = f"input_button.{action_id}"
            self.set_state(entity_id, state=f"{action_id}")
            buttons.append(entity_id)
        return buttons

    def save_notifications_dict(self):
        """保存字典"""
        try:
            # self.set_state(
            #     f"sensor.notifications_dict",
            #     state=f"notification log",
            #     attributes={"notifications": self._notifications_dict},
            #     namespace="notification"
            # )
            with open('notifications.json', 'w', encoding='utf-8') as f:
                json.dump(self._notifications_dict, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.log(f"Save dict Error: {e}", level="ERROR")

    def load_notifications_dict(self):
        """讀取字典"""
        try:
            with open('notifications.json', 'r', encoding='utf-8') as f:
                _dict = json.load(f)
            return _dict
        except FileNotFoundError:
            # json不存在
            _dict = {}
            self.log(f"Dict Not Found", level="WARNING")
            return _dict
        except json.JSONDecodeError:
            # json格式錯誤
            _dict = {}
            self.log(f"Dict Decode Error", level="WARNING")
            return _dict

    async def start(self, kwargs):
        """初始化,檢查是否有舊資料並建立字典"""
        try:
            # old_dict = await self.get_state(
            #     "sensor.notifications_dict", namespace="notification", attribute="all"
            # )
            old_dict = self.load_notifications_dict()

            if old_dict:
                # self._notifications_dict = old_dict.get("attributes", {}).get("notifications", {})
                self._notifications_dict = old_dict
                # 檢查是否有增加新設備
                for key in self._notify_action_id:
                    self._notifications_dict.setdefault(key, [None, 0])
                for k in list(self._notifications_dict.keys()):
                    if k not in self._notify_action_id:
                        self._notifications_dict.pop(k, None)
            else:
                for key in self._notify_action_id:
                    self._notifications_dict[key] = [None, 0]

            if self._notify_action_id:
                tasks = [
                    self.update_notification_log(action_id) for action_id in self._notify_action_id
                ]
                await asyncio.gather(*tasks)
        except Exception as e:
            self.log(f"Initialization dict Error: {e}", level="ERROR")

    async def send_notification(self, event_name, data, kwargs):
        """發送通知"""
        try:
            save_tasks = []
            update_tasks = []
            data = data["service_data"]
            if "data" not in data:
                data["data"] = {}
            action_id = data.get("target", None)

            if action_id is None:
                for _action_id in self._notify_action_id:
                    _data = data
                    badge = self._notifications_dict[_action_id][1] + 1
                    _data["data"]["push"] = {
                        "badge": badge,
                    }
                    # self.set_value(f"input_number.{_action_id}", badge)
                    self.call_service(
                        f"notify/{_action_id}",
                        title=_data.get("title", "Notification"),
                        message=_data.get("message", "No message"),
                        data=_data["data"]
                    )
                    save_tasks.append(self.save_notification(_action_id, _data))
                    update_tasks.append(self.update_notification_log(_action_id))

                await asyncio.gather(*save_tasks)
                async with self._lock:
                    self.save_notifications_dict()
                await asyncio.gather(*update_tasks)

            elif action_id in self._notify_action_id:
                badge = self._notifications_dict[action_id][1] + 1
                data["data"]["push"] = {
                    "badge": badge,
                }
                # self.set_value(f"input_number.{action_id}", badge)
                self.call_service(
                    f"notify/{action_id}",
                    title=data.get("title", "Notification"),
                    message=data.get("message", "No message"),
                    data=data["data"]
                )
                await self.save_notification(action_id, data)
                async with self._lock:
                    self.save_notifications_dict()
                await self.update_notification_log(action_id)
            else:
                badge = 1
                data["data"]["push"] = {
                    "badge": badge,
                }
                # self.set_value(f"input_number.{action_id}", badge)
                self.call_service(
                    f"notify/{action_id}",
                    title=data.get("title", "Notification"),
                    message=data.get("message", "No message"),
                    data=data["data"]
                )

        except KeyError as e:
            self.log(f"Get dict Error: {e}", level="ERROR")
        except Exception as e:
            self.log(f"Send notification Error: {e}", level="ERROR")

    async def save_notification(self, action_id, data):
        """保存通知"""
        try:
            notifications_list = self._notifications_dict[action_id][0] if self._notifications_dict[
                action_id][0] is not None else []
            time = await self.datetime()
            send_time = time.strftime("%Y-%m-%d %H:%M:%S")
            message = data.get("message", "No message")
            title = data.get("title", "Notification")
            image = data.get("data", {}).get("image", None)
            badge = data.get("data") and data["data"].get("push", {}).get("badge", 1) or 1
            # 建立通知
            if image is None:
                notification = (
                    f"<ha-alert alert-type='info'><strong>{title}</strong></ha-alert>"
                    f"<blockquote><font color='#c753e8'>{message}</font><br>"  #Text color can be customized
                    f"<br><b><i>{send_time}</i></b></blockquote>"
                )
            else:
                notification = (
                    f"<ha-alert alert-type='info'><strong>{title}</strong></ha-alert>"
                    f"<blockquote><font color='#c753e8'>{message}</font><br>"  #Text color can be customized
                    f"<br><img src='{image}'/><br>"
                    f"<br><b><i>{send_time}</i></b></blockquote>"
                )
            # 將新通知加入列表 # Delete the oldest notification when the number of saved notifications is greater than 30
            notifications_list.insert(0, notification)
            if len(notifications_list) > 30:
                notifications_list.pop()
            async with self._lock:
                self._notifications_dict[action_id] = [notifications_list, badge]

        except KeyError as e:
            self.log(f"Get dict Error: {e}", level="ERROR")
        except Exception as e:
            self.log(f"Notification_log Error: {e}", level="ERROR")

    async def update_notification_log(self, action_id):
        """將通知列表更新到 sensor"""
        notification_log = self._notifications_dict[action_id][0]

        if notification_log is not None:
            notification_str = '\n'.join(notification_log)
            # 更新 sensor
            self.set_state(
                f"sensor.{action_id}_log",
                state=f"{action_id} notification log",
                attributes={"notifications": notification_str}
            )
        else:
            self.set_state(f"sensor.{action_id}_log", state=f"{action_id} notification log")

    async def button_pressed(self, event_name, data, kwargs):
        """改成已讀狀態"""
        entity = data["service_data"]["entity_id"]
        for entity_id in entity:
            if entity_id in self.button_list:
                action_id = entity_id.split('.')[-1]
                await self.read_notification(action_id)
                # self.set_value(f"input_number.{action_id}", 0)
                self.call_service(f"notify/{action_id}", message="clear_badge")
                await self.update_notification_log(action_id)

    async def read_notification(self, action_id):
        """將通知中的 info 類型更改為 success 類型"""
        try:
            notifications_list = self._notifications_dict.get(action_id, [])[0]
            # 如果該通知列表不為空且為列表型態
            if notifications_list and isinstance(notifications_list, list):
                for index, notification in enumerate(notifications_list):
                    if 'alert-type=\'info\'' in notification:
                        # 將 'info' 替換為 'success'
                        new_notification = notification.replace(
                            'alert-type=\'info\'', 'alert-type=\'success\''
                        )
                        notifications_list[index] = new_notification
                async with self._lock:
                    self._notifications_dict[action_id] = [notifications_list, 0]
                    self.save_notifications_dict()
            else:
                self.log(f"No valid notifications found for {action_id}", level="WARNING")

        except Exception as e:
            self.log(f"Error replacing notifications: {e}", level="ERROR")
