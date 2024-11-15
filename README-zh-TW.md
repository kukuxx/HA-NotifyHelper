
 [![Contributors][contributors-shield]][contributors-url]
 [![Forks][forks-shield]][forks-url]
 [![Stargazers][stars-shield]][stars-url]
 [![Issues][issues-shield]][issues-url]
 [![License][license-shield]][license-url]

 [contributors-shield]: https://img.shields.io/github/contributors/kukuxx/HA-APP_Notification.svg?style=for-the-badge
 [contributors-url]: https://github.com/kukuxx/HA-APP_Notification/graphs/contributors

 [forks-shield]: https://img.shields.io/github/forks/kukuxx/HA-APP_Notification.svg?style=for-the-badge
 [forks-url]: https://github.com/kukuxx/HA-APP_Notification/network/members

 [stars-shield]: https://img.shields.io/github/stars/kukuxx/HA-APP_Notification.svg?style=for-the-badge
 [stars-url]: https://github.com/kukuxx/HA-APP_Notification/stargazers

 [issues-shield]: https://img.shields.io/github/issues/kukuxx/HA-APP_Notification.svg?style=for-the-badge
 [issues-url]: https://github.com/kukuxx/HA-APP_Notification/issues

 [license-shield]: https://img.shields.io/github/license/kukuxx/HA-APP_Notification.svg?style=for-the-badge
 [license-url]: https://github.com/kukuxx/HA-APP_Notification/blob/main/LICENSE

# HA-Notificationhelper

- [English](/README.md) | [繁體中文](/README-zh-TW.md)

> 這是一個**Home assistant自動化**，它使用 **AppDaemon** 來運行，
  保存和格式化已發送到行動應用程式的通知以便查看，支持配置多人專屬通知面板。

> 部分邏輯參考至 [這裡](https://forum.automata.id/t/topic/807) 

> 感謝 **Mark Wu** 提供的想法與測試

> [!NOTE]
> 關於AppDaemon的安裝和配置請參考[這裡](https://appdaemon.readthedocs.io/en/latest/INSTALL.html)

> [!NOTE]
> 如果在使用過程中遇到bug，請開啟issues

# 使用教學

- 安裝好AppDaemon之後開啟AD的資料夾找到**appdaemon.yaml**檔案並修改配置如下:
```
    appdaemon:
        latitude: 你的所在地緯度
        longitude: 你的所在地經度
        elevation: 你的所在地海拔
        time_zone: 你的時區
```
> [!NOTE]
> 關於appdaemon.yaml的其他配置請詳閱官網

- appdaemon.yaml如果配置完成將py檔放到AD資料夾下的**apps**資料夾並配置**apps.yaml**:
```
    notification_logger:
        module: notification_logger
        class: NotificationLogger
        device: ["your device", "other device", "and others", ....]
```
> [!important]
> 裝置ID格式必須為mobile_app_* (*為設備id)

- 之後到HA裡建立一個空白腳本名字必須為**ad_notify**:
```
    alias: ad_notify
    sequence: []
    description: ""
```

- 建立完成後就可以透過ad_notify開始傳送通知傳送的格式跟使用notify服務一樣:
```
    alias: test1
    description: ""
    triggers:
        - trigger: event
            event_type: ""
    conditions: []
    actions:
        - sequence:
            - action: script.ad_notify
            data:
                title: Test Notification
                message: This is a test message.
              # target: 預設群發不用加上target
              #         如要傳送單人通知請加上target: mobile_app_*
                data:
                    image: /local/1.jpg
                    # 無需設置badge helper會自動設置
    mode: single
```

- Markdown card 配置:
```
    type: markdown
    content: |
        {% set notifications =
        state_attr('sensor.mobile_app_*', 'notifications') %}
        {% if notifications %}
            
            <div><font size="5">{{ notifications }}</font></div>
            # size 可調整文字大小
        {% else %}
            <ha-alert alert-type="info">No notifications available.</ha-alert>
        {% endif %}
```

- Button card 配置:
```
    type: button
    tap_action:
        action: perform-action
        perform_action: input_button.press
        target:
            entity_id: input_button.mobile_app_*
        data: {}
    entity: input_button.mobile_app_*
```
> [!NOTE]
> 不一定要建立button卡片來完成已讀，
  也可以用自動化進行服務呼叫，
  保存的通知數和顏色可在code裡更改都有註釋，
  請按個人需求來配置。           

  

  



