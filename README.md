
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

> This is a <b>Home assistant custom integration</b> that can save and format
  notifications sent to mobile applications for viewing, and supports the configuration
  of multi-person exclusive notification panels.

> Thanks to <b>Mark Wu</b> for some ideas and tests.

> [!Important]
> <b>Since version 2.3.0 has changed a lot, please remember to go to Integration -- Integrated Entries -- Click Settings to reconfigure after the update:</b>
![image](/doc/update_settings1.png) <br>
![image](/doc/update_settings2.png)

> [!Important]
> If you keep getting notifications for old pictures or videos, please see 
<a href='https://community.home-assistant.io/t/home-assistant-sends-cached-images-in-ios-notification/520766'>here.</a>

> [!Tip]
> If you encounter a bug during use, <br>
> please enable <b>debug mode</b> in the integration and try the original operation, <br>
> then open issues and post the log.

## Instructions for use  

- It is recommended to use <b>HACS</b> to install. If you want to install manually,
  <br>please put the <b>notifyhelper</b> folder in <b>custom_components</b> folder, 
  <br>and restart <b>Home assistant</b>.

  [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kukuxx&repository=HA-NotifyHelper&category=Integration)

- After the restart is completed, search for notifyhelper in the integration and set it up:<br>
![image](/doc/settings.png)

> [!Tip]
> Only <b>100</b> notifications can be saved.<br>
> If more than <b>100</b> notifications are stored,
> <br>they will be <b>deleted</b> starting from the <b>oldest one</b>.

- The method of calling the service is similar to the built-in notify.mobile_app service.
  <br>The following is an automation example:
```
    alias: test1
    description: ""
    triggers:
    - trigger: event
        event_type: ""
    conditions: []
    actions:
    - sequence:
        - action: notify.notify_person
            data:
                title: Test Notification
                message: This is a test message.
                targets:
                    - person.you
                    - person.other
                color:
                data:
                    image: /local/icon.png
    mode: single
```
> [!Tip]
> <b>targets: <i>must be a list.</i></b><br>
> <b>color: <i>Optional, specify the message color please fill in Hex rgb,
> the default is None.</i></b><br>
> <b>data: <i>Optional, Refer to <a href='https://companion.home-assistant.io/docs/notifications/notifications-basic'>HA doc.</a></i></b>

- The data parameters accepted by Android and ios are different, if you want to set them separately, you can add <b>ios</b> and <b>android</b> to the data.
<br>The following is an automation example:
```
    alias: test1
    description: ""
    triggers:
    - trigger: event
        event_type: ""
    conditions: []
    actions:
    - sequence:
        - action: notify.notify_person
            data:
                title: Test Notification
                message: This is a test message.
                targets:
                    - person.you
                    - person.other
                color: 
                data:
                  ios:
                    image: /local/icon.png
                    push:
                        sound:
                        name: US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav
                        volume: 0.3
                        critical: 1
                  android:
                    image: /local/icon.png
    mode: single
```

> [!Tip]
> <b>If the set parameters are all universal,
you can use the first example without adding ios and android.<br>
> You can send different photos or videos for ios and android but the notification will only save one of them, please be aware of this. </b>

- Markdown card configuration:
```
    type: markdown
    content: |
        {% set notifications =
        state_attr('sensor.personname_notifications', 'notifications') %}
        {% if notifications %}
            
            <div><font size="5">{{ notifications }}</font></div>
            # "size" adjustable text size
        {% else %}
            <ha-alert alert-type="info">No notifications available.</ha-alert>
        {% endif %}
```

- Button card configuration:
```
    show_name: true
    show_icon: true
    type: button
    tap_action:
        action: perform-action
        perform_action: notify.read
        target: {}
        data:
            targets:
                - person.you
    entity: input_button.read
```
> [!Tip]
> <b>targets: <i>must be a list.</i></b>

> [!NOTE]
> It is not necessary to create a button card to complete the reading,<br>
  service calls can also be made using automation. <br>
  Please configure according to personal needs.

## Achievements Display   

![gif](/doc/display.gif)

