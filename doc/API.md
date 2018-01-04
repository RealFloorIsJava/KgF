# API Documentation

The API can be reached via the `/api` endpoints.

*Note: Not every action is currently supported via the API.*

## Response on failure

When the API protocol or requirements are violated, the API serves the
following response:

### Example

```
> POST /api/choose (handId=abc)
{
  "error": "not authenticated"
}
```

## /api/list

|Requirements|Request Type|
|---|---|
|Logged in|GET|

Retrieves a list of all matches.

### Response format

Returns a JSON array of objects of the following format:

|Key|Type|Description|
|---|---|---|
|id|number|The ID of the match. No two matches with the same ID may exist simultaneously.|
|owner|string|The name of the owner of the match.|
|participants|number|The number of participants in the match.|
|canJoin|`true` or `false`|Whether joining is possible right now.|
|seconds|number|The number of seconds until the next match phase begins.|

### Example

```
> GET /api/list
[
  {
    "id": 3,
    "owner": "PlayerX",
    "participants": 4,
    "canJoin": false,
    "seconds": 27
  },
  {
    "id": 4,
    "owner": "XYZ",
    "participants": 2,
    "canJoin": true,
    "seconds": 51
  }
]
```

## /api/status

|Requirements|Request Type|
|---|---|
|Logged in and in match|GET|

Retrieves information about the current match.

**Note:** This API endpoint also refreshes the participant's timeout and thus
should be called regularly (1-10 seconds) while a participant is active.

### Response format

Returns a JSON object of the following format:

|Key|Type|Description|
|---|---|---|
|timer|number|The number of seconds to the next match phase.|
|status|string|A human-readable string describing the match's status.|
|ending|`true` or `false`|Whether the match is ending.|
|hasCard|`true` or `false`|Whether the match currently has a statement card selected.|
|allowChoose|`true` or `false`|Whether choosing hand cards is currently allowed.|
|allowPick|`true` or `false`|Whether picking a played card set is currently allowed.|
|gaps|number|The number of gaps on the match's statement card.|
|cardText|string|**(Only if `hasCard` is `true`)** The text of the match's statement card.|

### Example

```
> GET /api/status
{
  "timer": 27,
  "status": "Players are choosing cards...",
  "ending": false,
  "hasCard": true,
  "allowChoose": true,
  "allowPick": false,
  "gaps": 2,
  "cardText": "The _ of the state|ment _."
}
```

## /api/chat

|Requirements|Request Type|
|---|---|
|Logged in and in match|GET or POST|

Retrieves the match's chat messages (optionally starting at a given message offset).

### Parameters

|Name|Optional?|Description|
|---|---|---|
|offset|Yes|The ID offset from which to begin loading chat messages.|

### Response format

Returns a JSON array of objects of the following format:

|Key|Type|Description|
|---|---|---|
|id|number|The ID of the chat message.|
|type|string|The type of the chat message. Currently either `SYSTEM` or `USER`|
|message|string|The actual text of the message (might contain HTML).|

### Example

```
> GET /api/chat
[
  {
    "id": 0,
    "type": "SYSTEM",
    "message": "Match was created."
  },
  {
    "id": 1,
    "type": "SYSTEM",
    "message": "XYZ joined."
  },
  {
    "id": 2,
    "type": "USER",
    "message": "<b>XYZ</b>: abcd"
  }
]

> POST /api/chat (offset=2)
[
  {
    "id": 2,
    "type": "USER",
    "message": "<b>XYZ</b>: abcd"
  }
]
```

## /api/chat/send

|Requirements|Request Type|
|---|---|
|Logged in and in match|POST|

Sends a chat message.

*Note: There exist anti-spam measures to prevent chatting too quickly.*

### Parameters

|Name|Optional?|Description|
|---|---|---|
|message|No|The message to send. May not be empty. At most 199 characters.|

### Response format

A JSON object is returned.

|Key|Type|Description|
|---|---|---|
|error|string|A short message indicating the result of the operation. `OK` on success.|

### Example

```
> POST /api/chat/send (message=abc)
{
  "error": "OK"
}

> POST /api/chat/send (message=def)
{
  "error": "spam rejected"
}

> POST /api/chat/send (message=)
{
  "error": "invalid size"
}
```

## /api/participants

|Requirements|Request Type|
|---|---|
|Logged in and in match|GET|

Retrieves a list of all participants in the current match.

### Response format

Returns a JSON array of objects of the following format:

|Key|Type|Description|
|---|---|---|
|id|string|The ID of the participant.|
|name|string|The nickname of the participant. Can't be changed while in the match.|
|score|number|The score of the participant.|
|picking|`true` or `false`|Whether the participant is currently picking.|

### Example

```
> GET /api/participants
[
  {
    "id": "xyz-123",
    "name": "PlayerX",
    "score": 0,
    "picking": false
  },
  {
    "id": "abc-987",
    "name": "PlayerZ",
    "score": 0,
    "picking": false
  }
]
```

## /api/cards

|Requirements|Request Type|
|---|---|
|Logged in and in match|GET|

Retrieves the hand cards of the client and the played cards of the match.

### Response format

Returns a JSON object of the following format:

|Key|Type|Description|
|---|---|---|
|hand|object|Hand object, described below.|
|played|array|The played cards of the match, described below.|

#### Hand object

|Key|Type|Description|
|---|---|---|
|OBJECT|object|Object of hand cards, see next table.|
|VERB|object|Object of hand cards, see next table.|

Objects of hand cards have hand card IDs as keys, mapping to objects of the
following layout:

|Key|Type|Description|
|---|---|---|
|text|string|The text of the hand card.|
|chosen|number or `null`|The choice index of the card (0-indexed) or `null` if the card is not selected.|

#### Played Array

Contains arrays of card sets for match participants. There might be more sets
than there are participants.

Each of the arrays contains objects of the following format:

|Key|Type|Description|
|---|---|---|
|redacted|`true` or absent|When `true`, this card is redacted due to it not being visible to the participant.|
|type|string|The type of the card. Only present if `redacted` is not present.|
|text|string|The text on the card. Only present if `redacted` is not present.|

### Example

```
> GET /api/cards
{
  "hand": {
    "OBJECT": {
      "1": {
        "text": "An object",
        "chosen": 0
      },
      "2": {
        "text": "Example card",
        "chosen": null
      }
    },
    "VERB": {
      "9": {
        "text": "Doing something",
        "chosen": null
      }
    }
  },
  "played": [
    [],
    [
      {
        "redacted": true
      },
      {
        "redacted": true
      }
    ],
    [],
    [
      {
        "text": "An object",
        "type": "OBJECT"
      }
    ]
  ]
}
```

## /api/choose

|Requirements|Request Type|
|---|---|
|Logged in, in match and can currently choose|POST|

Chooses or unchooses a hand card.

### Parameters

|Name|Optional?|Description|
|---|---|---|
|handId|No|The ID of the hand card (the numeric key in the hand object).|

### Response format

|Key|Type|Description|
|---|---|---|
|error|string|A short status describing the result. `OK` on success.|

### Example

```
> POST /api/choose (handId=9)
{
  "error": "OK"
}
```

## /api/pick

|Requirements|Request Type|
|---|---|
|Logged in, in match and is the current picker|POST|

Picks a winner from the set of played cards.

### Parameters

|Name|Optional?|Description|
|---|---|---|
|playedId|No|The 0-indexed offset in the played array of the card data for the set.|

### Response format

|Key|Type|Description|
|---|---|---|
|error|string|A short status describing the result. `OK` on success.|

### Example

```
> POST /api/pick (playedId=1)
{
  "error": "OK"
}
```
