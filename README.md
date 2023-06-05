# Twitch Reader
A python VoiceVox based twitch reader for my friend.

## Requirements
If using Bouyomichan or VoiceVox via Bouyomichan
- Bouyomichan
- <https://github.com/yumimint/bouyomichan>

If using VoiceVox directly
- VoiceVox Engine
- pyaudio
- voicevoc-client <https://github.com/voicevox-client/python>
```py
pip install voicevox-client
pip install pyaudio
```

## Usage
Set the bot's nickname, your twitch API token and channel name
Note: Use channelname not display name
```py
NICKNAME = 'ChatReader' #Bot's nickname here
TOKEN = 'PLACE TOKEN HERE' #format 'oauth:YOURTOKENHERE'
CHANNEL = 'PLACE CHANNEL NAME HERE'  #format '#Channelname'
```

Changed the following variables how ever you like
```py
LIST_VOICEVOX_SPEAKERS_ON_START = False #Print a list of all availiable VoiceVox voices and their IDs
DEFAULT_VOICE = 9 #Default voice ID used for Bouyoumi or VoiceVox
DEBUG_INFO = False #Will desplay raw message data
PRINT_MESSAGES = True #Will print chat messages
REMOVE_EMOTE = True
IGNORE_ACTION_MESSAGES = False #Ignore messages that start with \001ACTION. Usually bot messages, When false, just removes SOH and ACTION. 
```

if using Bouyomichan set to true, if useing voiceVox directly set to false
```py
USE_BOUYOMICHAN = True
```

If you want some users to have custom voices create a file (voiceDict.txt) in the json format {"CHANNELNAME": VOICEID}
Note: Use channelname not display name
Ex:
```json
{"JonDoe001":16, "user_name123":2}
```
