
 [![Contributors][contributors-shield]][contributors-url]
 [![Forks][forks-shield]][forks-url]
 [![Stargazers][stars-shield]][stars-url]
 [![Issues][issues-shield]][issues-url]
 [![License][license-shield]][license-url]

 [contributors-shield]: https://img.shields.io/github/contributors/kukuxx/HA-NotifyHelper.svg?style=for-the-badge
 [contributors-url]: https://github.com/kukuxx/HA-NotifyHelper/graphs/contributors

 [forks-shield]: https://img.shields.io/github/forks/kukuxx/HA-NotifyHelper.svg?style=for-the-badge
 [forks-url]: https://github.com/kukuxx/HA-NotifyHelper/network/members

 [stars-shield]: https://img.shields.io/github/stars/kukuxx/HA-NotifyHelper.svg?style=for-the-badge
 [stars-url]: https://github.com/kukuxx/HA-NotifyHelper/stargazers

 [issues-shield]: https://img.shields.io/github/issues/kukuxx/HA-NotifyHelper.svg?style=for-the-badge
 [issues-url]: https://github.com/kukuxx/HA-NotifyHelper/issues

 [license-shield]: https://img.shields.io/github/license/kukuxx/HA-NotifyHelper.svg?style=for-the-badge
 [license-url]: https://github.com/kukuxx/HA-NotifyHelper/blob/main/LICENSE
 
![image](/doc/icon.png)

# HA-Notifyhelper

- [English](/README.md) | [繁體中文](/doc/README-zh-TW.md)

> 這是一個<b>Home assistan自訂整合</b>，可以保存和格式化已發送到行動應用程式的通知以便查看，
  支持配置多人專屬通知面板。

> 感謝 <b>Mark Wu</b> 提供的一些想法與測試

> [!NOTE]
> 如果在使用過程中遇到bug，請開啟issues

# 使用教學

- 建議使用 <b>HACS</b> 安裝如果想手動安裝請將 <b>notifyhelper</b> 資料夾放在 <br>
  <b>custom_components</b> 資料夾中， 並重啟 <b>Home assistant</b>。

  [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kukuxx&repository=HA-NotifyHelper&category=Integration)

> [!NOTE]
> 通知只能保存<b>100</b>則超過會從<b>最舊的開始刪除</b>。

- call service的方法和內建的notify.mobile_app服務類似，以下是一個自動化範例:
```
    alias: test1
    description: ""
    triggers:
    - trigger: event
        event_type: ""
    conditions: []
    actions:
    - sequence:
        - action: notifyhelper.notify
            data:
                title: Test Notification
                message: This is a test message.
                targets:
                    - entryname1
                    - other
                color: 
                data:
                    image: /local/icon.png
    mode: single
```
> [!important]
> <b>targets<i>必須為列表型式</i></b>

> [!NOTE]
> <b>color: <i>可選，要指定訊息顏色請填上 Hex rgb，預設為None</i></b><br>
  <b>data: <i>可選， 參考<a href='https://companion.home-assistant.io/docs/notifications/notifications-basic'>HA文檔</a></i></b>
   
- Markdown card 配置:
```
    type: markdown
    content: |
        {% set notifications =
        state_attr('sensor.yourname_notification_log', 'notifications') %}
        {% if notifications %}
            
            <div><font size="5">{{ notifications }}</font></div>
            # size 可調整文字大小
        {% else %}
            <ha-alert alert-type="info">No notifications available.</ha-alert>
        {% endif %}
```

- Button card 配置:
```
    show_name: true
    show_icon: true
    type: button
    tap_action:
        action: perform-action
        perform_action: notifyhelper.read
        target: {}
        data:
            targets:
                - entryname1
    entity: input_button.read
```
> [!important]
> <b>targets<i>必須為列表型式</i></b>

> [!NOTE]
> 不一定要建立button卡片來完成已讀，<br>
  也可以用自動化進行服務呼叫，<br>
  請按個人需求來配置。    

# 成果展示

![gif](/doc/display.gif)

  

  



