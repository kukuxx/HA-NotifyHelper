from __future__ import annotations

import os
import voluptuous as vol

DOMAIN = "notifyhelper"
NOTIFY_DOMAIN = "notify"
CONF_URL = "url"
CONF_ENTRY_NAME = "entry_name"
CONF_IOS_DEVICES = "ios_devices"
CONF_ANDROID_DEVICES = "android_devices"

SERVICES_LIST = [
    (NOTIFY_DOMAIN, "all_person"),
    (NOTIFY_DOMAIN, "notify_person"),
    (DOMAIN, "read"),
    (DOMAIN, "clear"),
]
DATA_PATH = "custom_components/notifyhelper"
HELPER_VER = "2.6.3"
UPDATE_EVENT = "update"
HELPER = "helper"
PERSON = "person"

BASE_URL = "/notify-helper"
SCRIPT_URL = "/notifications-card.js"
FRONTEND_URL = BASE_URL + SCRIPT_URL

ALL_PERSON_SCHEMA = vol.Schema({
    vol.Required("message"): str,
    vol.Optional("title", default=""): str,
    vol.Optional("color", default=""): str,
    vol.Optional("data", default={}): dict,
})

NOTIFY_PERSON_SCHEMA = vol.All(
    vol.Schema({
        vol.Required("message"): str,
        vol.Required("targets"): [vol.Match(r"^person\.\w+$")],
        vol.Optional("title", default=""): str,
        vol.Optional("color", default=""): str,
        vol.Optional("data", default={}): dict,
    })
)

READ_SCHEMA = vol.All(vol.Schema({
    vol.Required("targets"): [vol.Match(r"^person\.\w+$")],
}))

CLEAR_SCHEMA = vol.All(vol.Schema({
    vol.Required("targets"): [vol.Match(r"^person\.\w+$")],
}))

ALL_PERSON_DESCRIBE = {
    "name": "Notify all person",
    "description": "Notify all person",
    "fields": {
        "message": {
            "description": "Notification content",
            "example": "Test Notification",
            "required": True,
            "selector": {
                "text": ""
            }
        },
        "title": {
            "description": "Notification title",
            "example": "This is a test message",
            "required": False,
            "selector": {
                "text": ""
            }
        },
        "color": {
            "description": "Message color",
            "example": "#c753e8",
            "required": False,
            "selector": {
                "text": ""
            }
        },
        "data": {
            "description": "Other additional parameters",
            "example": {
                "image": "/local/image.png"
            },
            "required": False,
            "selector": {
                "object": {}
            }
        },
    },
}

NOTIFY_PERSON_DESCRIBE = {
    "name": "Notify designated person",
    "description": "Notify designated person",
    "fields": {
        "message": {
            "description": "Notification content",
            "example": "Test Notification",
            "required": True,
            "selector": {
                "text": ""
            }
        },
        "targets": {
            "description": "Designated person",
            "example": "[person.1,person.2]",
            "required": True,
            "selector": {
                "object": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        },
        "title": {
            "description": "Notification title",
            "example": "This is a test message",
            "required": False,
            "selector": {
                "text": ""
            }
        },
        "color": {
            "description": "Message color",
            "example": "#c753e8",
            "required": False,
            "selector": {
                "text": ""
            }
        },
        "data": {
            "description": "Other additional parameters",
            "example": {
                "image": "/local/image.png"
            },
            "required": False,
            "selector": {
                "object": {}
            }
        },
    },
}

# READ_DESCRIBE_SCHEMA = {
#     "name": "Read notifitaion",
#     "description": "Read notifitaion",
#     "fields": {
#         "targets": {
#             "description": "Designated person",
#             "example": "['person.1', 'person.2']",
#             "required": True,
#             "selector": {
#                 "object": {
#                     "type": "array",
#                     "items": {
#                         "type": "string"
#                     }
#                 }
#             }
#         },
#     }
# }
