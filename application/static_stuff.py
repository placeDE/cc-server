GRAPHQL_GET_CONFIG = {
    "id": "1",
    "type": "start",
    "payload": {
        "variables": {
            "input": {
                "channel": {
                    "teamOwner": "AFD2022",
                    "category": "CONFIG",
                }
            }
        },
        "extensions": {},
        "operationName": "configuration",
        "query": "subscription configuration($input: SubscribeInput!) {\n  subscribe(input: $input) {\n    id\n    ... on BasicMessage {\n      data {\n        __typename\n        ... on ConfigurationMessageData {\n          colorPalette {\n            colors {\n              hex\n              index\n              __typename\n            }\n            __typename\n          }\n          canvasConfigurations {\n            index\n            dx\n            dy\n            __typename\n          }\n          canvasWidth\n          canvasHeight\n          __typename\n        }\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",
    },
}


target_configuration_url = "https://placede.github.io/pixel/pixel.json"
CANVAS_UPDATE_INTERVAL = 10
