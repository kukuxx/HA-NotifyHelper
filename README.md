
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

> Thanks to <b>Mark Wu</b> for some ideas and tests

> [!NOTE]
> If you encounter bugs during use, please open an issues

# Instructions for use  

- It is recommended to use <b>HACS</b> to install. If you want to install manually,
  <br>please put the <b>notifyhelper</b> folder in <b>custom_components</b> folder, 
  <br>and restart <b>Home assistant</b>.

  [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kukuxx&repository=HA-NotifyHelper&category=Integration)

> [!NOTE]
> Only <b>40</b> notifications can be saved.
  If more than <b>40</b> notifications are stored,
  <br>they will be <b>deleted</b> starting from the <b>oldest one</b>.

- The method of calling service is the same as using the 
  <b>built-in notify.mobile_app service.</b><br>
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
        - action: notifyhelper.send_yourname
            data:
            title: Test Notification
            message: This is a test message.
            color:
            data:
                image: /local/icon.png
    mode: single
```
> [!NOTE]
> <b>color: <i>To specify the message color please fill in Hex rgb,
  the default is #c753e8</i></b>
   
- Markdown card configuration:
```
    type: markdown
    content: |
        {% set notifications =
        state_attr('sensor.yourname_notification_log', 'notifications') %}
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
    perform_action: notifyhelper.read_yourname
    target: {}
    entity: input_button.read
    show_state: false
    hold_action:
    action: none
    icon_height: 60px
```
> [!NOTE]
> It is not necessary to create a button card to complete the reading，<br>
  service calls can also be made using automation. <br>
  Please configure according to personal needs.

# Achievements Display   

![gif](/doc/display.gif)

