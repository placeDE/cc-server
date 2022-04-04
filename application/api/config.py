from pydantic import BaseSettings


class ServerConfig(BaseSettings):
    remote_config_url: str = 'https://placede.github.io/pixel/pixel.json'
    canvas_update_interval: int = 10
    admin_password: str = "bea976c455d292fdd15256d3263cb2b70f051337f134b0fa9678d5eb206b4c45ebd213694af9cf6118700fc8488809be9195c7eae44a882c6be519ba09b68e47"
    influx_token: str = "b04zjucB13Ho5hjkzDsJX3E2at1n8RXHbwoQIHst"
    influx_url: str = "https://influx.place.dertiedemann.com"

def get_graphql_config():
    return {
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
