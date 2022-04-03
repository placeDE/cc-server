## Client-Server-Kommunikation

- der Client verbindet sich mit dem Server per websocket
- zu Beginn sendet der client seine Platform und version als json zum server:
  ```json 
    {"platform":"python", "version":999}
    ```
- sobald der client in 0 Lage ist ein pixel zu setzen schickt dieser ein `request_pixel` an den server
    - der Server antwortet dann mit dem zu setzenden pixel als json, e.g.:
```json 
{
  "operation":"pixel",
  "data":{
    "x": 0,
    "y": 857,
    "color": 4,
    "priority": 1
    }
}
 ```
    - wenn kein Pixel existiert, wird `null` zurückgesendet.
