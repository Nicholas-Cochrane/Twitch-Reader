
import wave
import asyncio
import time
import os
import re
import json
import socket

CHUNK = 1024
SERVER = 'irc.chat.twitch.tv'
PORT = 6667
NICKNAME = 'ChatReader' #Bot's nickname here
TOKEN = 'PLACE TOKEN HERE' #format 'oauth:YOURTOKENHERE'
CHANNEL = 'PLACE CHANNEL NAME HERE WITH # IN FRONT'  #format '#Channelname'

USE_BOUYOMICHAN = True
if USE_BOUYOMICHAN:
    import bouyomichan
else:
    from voicevox import Client
    import pyaudio

BOUYOMI_VOLUME = 50
LIST_VOICEVOX_SPEAKERS_ON_START = False #Print a list of all availiable VoiceVox voices and their IDs
DEFAULT_VOICE = 9 #Default voice ID used for Bouyoumi or VoiceVox
DEBUG_INFO = False #Will desplay raw message data
PRINT_MESSAGES = True #Will print chat messages
REMOVE_EMOTE = True
IGNORE_ACTION_MESSAGES = False #Ignore messages that start with \001ACTION. Usually bot messages, When false, just removes SOH and ACTION. 


async def chatLoop():
    pass


async def speakerList():
    async with Client() as client:
        for speaker in await client.fetch_speakers():
            print(speaker.name + " : " + speaker.uuid)
            for style in speaker.styles:
                print("   " + style.name + " : " + str(style.id))

async def readMessageVoiceVox(text, messageID, speakerID):
    fileName = messageID + ".wav"
    async with Client() as client:
        audio_query = await client.create_audio_query(
            text, speaker=speakerID
        )
        with open(fileName, "wb") as wf:
            wf.write(await audio_query.synthesis(speaker=speakerID))
        with wave.open(fileName, "rb") as rf:
            p = pyaudio.PyAudio()

            # Open stream (2)
            stream = p.open(format=p.get_format_from_width(rf.getsampwidth()),
                            channels=rf.getnchannels(),
                            rate=rf.getframerate(),
                            output=True)

            # Play samples from the wave file (3)
            while len(data := rf.readframes(CHUNK)):  # Requires Python 3.8+ for :=
                stream.write(data)

            # Close stream (4)
            stream.close()

            # Release PortAudio system resources (5)
            p.terminate()

        os.remove(fileName)

async def readMessageBouyomi(text, speakerID):
    bouyomichan.talk(text, voice=speakerID, volume=BOUYOMI_VOLUME)
        
def parse(msg):
    isMessageRegex = r"^(@\S+)? :[a-zA-Z0-9_]+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+\.tmi\.twitch\.tv PRIVMSG #[a-zA-Z0-9_]+ :.+$"
    privmessageRegex = r"PRIVMSG " + CHANNEL + r" :(.+)"
    if re.match(isMessageRegex, msg):

        splitMsg = msg.split(' ', 1) #split message into tags[0] and the message[1]
        rawMsg = re.findall(privmessageRegex, splitMsg[1])[0]
        
        displayName = splitMsg[0].split('display-name=',1)[1].split(';',1)[0]
        ID = splitMsg[0].split('id=',1)[1].split(';',1)[0]
        emoteTag = splitMsg[0].split('emotes=',1)[1].split(';',1)[0]
        emoteLists = re.findall(r'([0-9]+-[0-9]+)', emoteTag)
        emoteLists = [pair.split('-') for pair in emoteLists]
        emoteLists.sort(key=lambda x: int(x[0]))
        if REMOVE_EMOTE:
            formatedMsg = ''
            prevInx = 0;
            for pair in emoteLists:
                formatedMsg = formatedMsg + rawMsg[prevInx:int(pair[0])]
                prevInx = int(pair[1])+1
            formatedMsg = formatedMsg + rawMsg[prevInx:]
        else:
            formatedMsg = rawMsg

        if re.match('^\001ACTION', formatedMsg):
            if IGNORE_ACTION_MESSAGES:
                return None
            formatedMsg = formatedMsg[7:-1] 
        
        return{
                'username': re.findall(r'^:([a-zA-Z0-9_]+)!', splitMsg[1])[0],
                'displayname' : displayName,
                'rawMessage': rawMsg,
                'message' : formatedMsg,
                'ID': ID,
                'tags' : splitMsg[0],
                'emotePosList' : emoteLists
            }
    else:
        return None
    

if __name__ == "__main__":
    if LIST_VOICEVOX_SPEAKERS_ON_START:
        asyncio.run(speakerList())
        
    if not (re.match(r'^oauth:([a-zA-Z0-9_]+)', TOKEN) and re.match(r'^#([a-zA-Z0-9_]+)', CHANNEL)):
        print("You did not properly set up the Token or Channel:")
        raise  Exception("Token or Channel name not formatted correctly. Token must be in 'oauth:*' format and channel musst be in '#CHANNELNAME' format.")
    try:
        with open('voiceDict.txt', 'r') as fp:
            voiceDict = json.load(fp)
    except FileNotFoundError:
        print("No Voice Dictionary Found, all voices will be default")
        voiceDict = {}

        
    sock = socket.socket()
    
    try:
        sock.connect((SERVER, PORT))
        sock.send("CAP REQ :twitch.tv/tags\n".encode('utf-8'))
        sock.send(f"PASS {TOKEN}\n".encode('utf-8'))
        sock.send(f"NICK {NICKNAME}\n".encode('utf-8'))
        sock.send(f"JOIN {CHANNEL}\n".encode('utf-8'))
        response = sock.recv(2048).decode('utf-8')
    except socket.error as e:
        print('Socket error before loop:')
        print(e)
        if re.match(r'\[WinError 10054\]',str(e)):
            print("Previous Crash or interupt forcibly closed connection. Please start this script again.")
            os._exit(10054)
            
    print(response)

    loop = True
    trailingMessage=''
    while loop:
        try:
            rawResponse = sock.recv(4096)
            response = rawResponse.decode("utf-8")
        except UnicodeDecodeError:
            try:
                rawResponse = rawResponse + sock.recv(4096)
                response = rawResponse.decode("utf-8")
            except UnicodeDecodeError:
                response = ''
            except socket.error as e:
                print('Socket error in loop in unicode Decode Catch:')
                print(e)
        except socket.error as e:
            print('Socket error in loop:')
            print(e)
            if re.match(r'\[WinError 10053\]', str(e)):
                print(" Please start this script again.")
                os._exit(10053)
        
        if re.match(r'PING :tmi.twitch.tv', response):
            sock.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
            time.sleep(1)
    
        elif len(response) > 0:
            if DEBUG_INFO:
                print('------------------------')
                print(response)
                print('<><><><><><><><><><><><><>')
            response = trailingMessage + response
            trailingMessage = ''
            if response[-2:] != "\r\n":#split in message (does not end in return new line
                lastNewLine = response.rindex("\r\n")
                trailingMessage = response[lastNewLine:]
                response = response[:lastNewLine]
                if DEBUG_INFO:
                    print('trailing line')
                
            messages = [parse(msg) for msg in filter(None, response.split('\r\n'))]
            messages = filter(None, messages)
            speech = []

            try:
                msg = next(messages)
            except StopIteration: #if filter is empty do nothing
                pass
            else: # else process first msg and note its ID
                name = msg['displayname']
                if msg['displayname'] != msg['username']:
                    name = name + ' (' + msg['username'] + ')'
                if PRINT_MESSAGES: 
                    print(name + ": " + msg['message'])
                    if DEBUG_INFO:
                        print("Length: " + len(msg['message'].replace(" ", "")))
                voice = voiceDict.get(msg['username'], DEFAULT_VOICE)
                speech.append([msg['message'].replace(" ", "") + '。', msg['ID'],voice])
                            
            for msg in messages:
                name = msg['displayname']
                if msg['displayname'] != msg['username']:
                    name = name + ' (' + msg['username'] + ')'
                if PRINT_MESSAGES: 
                    print(name + ": " + msg['message'])
                    if DEBUG_INFO:
                        print("Length: " + len(msg['message'].replace(" ", "")))
                voice = voiceDict.get(msg['username'], DEFAULT_VOICE)
                if len(msg['message'].replace(" ", "")) > 0:
                    if voice != speech[-1][2]:
                        speech.append([msg['message'] + '。', msg['ID'], voice])
                    else:
                        speech[-1][0] = speech[-1][0] +  msg['message'] + '。'

            for linePair in speech:
                if len(linePair[0]) > 0:
                    if DEBUG_INFO:
                        print("sent: " + linePair[0])
                    if USE_BOUYOMICHAN:
                        asyncio.run(readMessageBouyomi(linePair[0], linePair[2]))
                    else:
                        asyncio.run(readMessageVoiceVox(linePair[0],  linePair[1], linePair[2]))
            
    sock.close()