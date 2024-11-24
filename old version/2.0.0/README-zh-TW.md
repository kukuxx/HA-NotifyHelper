
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

# HA-Notifyhelper

- [English](/README.md) | [繁體中文](/README-zh-TW.md)

> 這是一個**Home assistan自訂整合**，可以保存和格式化已發送到行動應用程式的通知以便查看，
  支持配置多人專屬通知面板。

> 感謝 **Mark Wu** 提供的想法與測試

> [!NOTE]
> 如果在使用過程中遇到bug，請開啟issues

# 使用教學

- 建議使用**HACS**安裝如果想手動安裝請將 **notifyhelper** 資料夾放在 <br>
  **custom_components** 資料夾中，配置完 **configuration.yaml** 進行重啟

  [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kukuxx&repository=HA-NotifyHelper&category=Integration)

> [!NOTE]
> 通知只能保存**40**則超過會從最舊的開始刪除

- **configuration.yaml**配置:
```
    notifyhelper:
        devices:
            - mobile_app_*
            - mobile_app_your_device_id
            - mobile_app_other_device_id
```
> [!important]
> 裝置ID格式必須為 <b><i>mobile_app_* (*為設備id)</i></b>

- call service的方法和使用內建的**notify服務**一樣，以下是一個自動化範例:
```
    alias: test1
    description: ""
    triggers:
    - trigger: event
        event_type: ""
    conditions: []
    actions:
    - sequence:
        - action: notifyhelper.send
            data:
            title: Test Notification
            message: This is a test message.
            target:
            color: 
            data:
                image: /local/icon.png
    mode: single
```
> [!NOTE]
> **target: <i>如果要指定設備請填上ID，否則為群發</i>** <br>
  **color: <i>要指定訊息顏色請填上 Hex rgb，預設為#c753e8</i>**
   
- Markdown card 配置:
```
    type: markdown
    content: |
        {% set notifications =
        state_attr('sensor.mobile_app_*_log', 'notifications') %}
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
        target: mobile_app_*
    entity: input_button.read
    show_state: false
    hold_action:
    action: none
    icon_height: 60px
```
> [!NOTE]
> 不一定要建立button卡片來完成已讀，<br>
  也可以用自動化進行服務呼叫，<br>
  請按個人需求來配置。           

  

  



