## Client-Server-Kommunikation

- Der Client verbindet sich mit dem Server per Websocket
- Zu Beginn sendet der client seine Platform und Version als json zum Server:
```json 
{
  "operation": "handshake",
  "data": {
    "platform": "python",
    "version": 999
  }
}
```

- Sollte der Server feststellen, dass der Client eine alte Version verwendet, sendet er diesem eine Update Aufforderung zurück:
```json 
{
  "operation": "notify-update"
}
```

- Sobald der Client in der Lage ist ein Pixel zu setzen schickt dieser ein `request-pixel` an den Server
```json 
{
  "operation": "request-pixel",
  "user": "<user-id">"
}
 ```

- Der Server antwortet dann mit dem zu setzenden Pixel als json, e.g.:
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

- Wenn kein Pixel existiert, wird `{}` zurückgesendet.
