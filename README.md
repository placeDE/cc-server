## Client-Server-Kommunikation

- Der Client verbindet sich mit dem Server per websocket
- Zu Beginn sendet der client seine Platform und version als json zum server:
```json 
{
  "operation": "handshake",
  "data": {
    "platform": "python",
    "version": 999
  }
}
```

- Sollte der Server feststellen, dass der Client eine alte Version verwendet, sendet er diesem eine Update aufforderung zurück:
```json 
{
  "operation": "notify-update"
}
```

- sobald der client in 0 Lage ist ein pixel zu setzen schickt dieser ein `request-pixel` an den server
```json 
{
  "operation": "request-pixel",
  "user": "<user-id">"
}
 ```

- der Server antwortet dann mit dem zu setzenden pixel als json, e.g.:
```json 
{
  "operation": "place-pixel",
  "data": {
    "x": 0,
    "y": 857,
    "color": 4,
    "priority": 1
  },
  "user": "<user-id">"
}
 ```

- wenn kein Pixel existiert, wird `{}` zurückgesendet.
