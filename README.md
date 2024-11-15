
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

> This is a **Home assistant automation** that uses **AppDaemon** to run,
  save and format notifications sent to mobile applications for easy viewing, 
  and support configuring multi-person notification panels.

> Part of the program code logic refers to [here](https://forum.automata.id/t/topic/807)

> Ideas and test provided by **Mark Wu**. Thanks!

> [!NOTE]
> Please refer [here](https://appdaemon.readthedocs.io/en/latest/INSTALL.html) 
  for the installation and configuration of AppDaemon.

> [!NOTE]
> If you encounter bugs during use, please open an issues

# Instructions for use  

- After installing AppDaemon, open the AD folder, 
  find the **appdaemon.yaml** file and modify the configuration as follows
```
    appdaemon:
        latitude: your location latitude
        longitude: your location longitude
        elevation: your location elevation
        time_zone: your time zone
```
> [!NOTE]
> For other configurations of appdaemon.yaml, please read the official website.

- If appdaemon.yaml is configured, place the py file in the **apps** folder under the AD folder and configure **apps.yaml**:
```
    notification_logger:
        module: notification_logger
        class: NotificationLogger
        device: ["your device", "other device", "and others", ....]
```
> [!important]
> The device ID format must be mobile_app_*

- After all configurations are completed, please create a blank script in HA. The name must be **ad_notify**:
```
    alias: ad_notify
    sequence: []
    description: ""
```

- After the script is created, you can call **ad_notify** to start sending notifications. 
  The format of the sending is the same as using the notify service:
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
            #   target: The default sending method is mass sending, and there is no need to add target.
            #       If you want to send a single notification, please add target: mobile_app _* (* is the device id)
                data:
                    image: /local/1.jpg
                    # No need to set the badge, helper will be set automatically
    mode: single
```

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
> It is not necessary to create a button card to complete the reading，
  Service calls can also be made using automation.
  The number and color of the notifications can be changed in the code, 
  and the code contains detailed comments.
  Please configure according to personal needs.          

