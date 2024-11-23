
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

> This is a **Home assistant custom integration** that can save and format
  notifications sent to mobile applications for viewing, and supports the configuration
  of multi-person exclusive notification panels.

> Ideas and test provided by **Mark Wu**. Thanks!

> [!NOTE]
> If you encounter bugs during use, please open an issues

# Instructions for use  

- It is recommended to use **HACS** installation. If you want to install manually, 
  <br>please put the **notifyhelper** folder in **custom_components** folder, 
  <br>restart after configuring **configuration.yaml**

  [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kukuxx&repository=HA-NotifyHelper&category=Integration)

> [!NOTE]
> Only **40** notifications can be saved. If more than **40** notifications are stored,
  <br>they will be deleted starting from the oldest one.

- **configuration.yaml** configuration:
```
    notifyhelper:
        devices:
            - mobile_app_*
            - mobile_app_your_device_id
            - mobile_app_other_device_id
```
> [!important]
> The device ID format must be <b><i>mobile_app_* (* is the device ID)</i></b>

- The method of calling service is the same as using the built-in notify service. <br>
  The following is an automation example:
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
> **target: <i>If you want to specify a device, fill in the ID,</i>**
  **<i>otherwise it will be sent to all devices.</i>** <br>
  **color: <i>To specify the message color please fill in Hex rgb, the default is #c753e8**</i>
   
- Markdown card configuration:
```
    type: markdown
    content: |
        {% set notifications =
        state_attr('sensor.mobile_app_*', 'notifications') %}
        {% if notifications %}
            
            <div><font size="5">{{ notifications }}</font></div>
            # "size" adjustable text size
        {% else %}
            <ha-alert alert-type="info">No notifications available.</ha-alert>
        {% endif %}
```

- Button card configuration:
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
> It is not necessary to create a button card to complete the reading，<br>
  service calls can also be made using automation. <br>
  Please configure according to personal needs.          

