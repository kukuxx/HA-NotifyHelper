
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

> 這是一個<b>Home assistan自訂整合</b>，可以一次向某人的所有行動裝置發送通知，並將通知顯示在定制的 Lovelace 卡片上，支持配置多人專屬通知面板。

> 感謝 <b>Mark Wu</b> 提供的一些想法與測試。

> [!Tip]
> 如果遇到通知一直收到舊圖片或影片請看 <a href='https://community.home-assistant.io/t/home-assistant-sends-cached-images-in-ios-notification/520766'>這裡。</a>

> [!Tip]
> 如果在使用過程中遇到bug，請先在整合裡<b>啟用偵錯</b>嘗試原本的操作之後，開啟issues把log貼上來。

## 變更日誌

> [CHANGELOG](/CHANGELOG.md)

## 使用教學

- 建議使用 <b>HACS</b> 安裝如果想手動安裝請將 <b>notifyhelper</b> 資料夾放在 <br>
  <b>custom_components</b> 資料夾中， 並重啟 <b>Home assistant</b>。

  [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kukuxx&repository=HA-NotifyHelper&category=Integration)

- 重啟完成到整合裡搜尋notifyhelper進行設定:<br>
![image](/doc/settings.png)

> [!Tip]
> 通知只能保存<b>500</b>則超過會從<b>最舊的開始刪除</b>。

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
> [!Important]
> <b>iOS badge會自動配置，無需手動設置。URL 可以在整合配置時設定，但如果在自動化中指定，將會覆蓋預設的 URL。</b>

> [!Tip]
> <b>targets: <i>必須為列表型式。</i></b><br>
> <b>color: <i>可選，要指定訊息顏色請填上 Hex rgb，預設為None。</i></b><br>
> <b>data: <i>可選， 參考<a href='https://companion.home-assistant.io/docs/notifications/notifications-basic'>HA文檔。</a></i></b><br>


- Android和ios可以接受的data參數都不一樣，如果想分別設置可以在data裡加上<b>ios</b>和<b>android</b>，以下是一個自動化範例:
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
> <b>如果設置的參數都是通用的可以使用第一個範例不需要加上ios和android。<br>
> 你可以針對ios和android傳送不同照片或影片但是通知只會保存其中一個，這點請注意。</b>

- Notifications card 配置:
```
    type: custom:notifications-card
    person_name: // 使用者名稱， 例:JHON
    font_size: 可選       // 文字大小，默認16px
    line_height: 可選     // 行間距比例，默認1.0

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
                - person.you
```
> [!Tip]
> <b>targets: <i>必須為列表型式。</i></b>

> [!NOTE]
> 不一定要建立button卡片來完成已讀，<br>
  也可以用自動化進行服務呼叫，<br>
  清空通知也是一樣，<br>
  請按個人需求來配置。    

## 成果展示

![gif](/doc/display.gif)

  

  



