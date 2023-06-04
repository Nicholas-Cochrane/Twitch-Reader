from voicevox import Client
import pyaudio
import wave
import asyncio
import time
import os
import re
import socket

CHUNK = 1024
SERVER = 'irc.chat.twitch.tv'
PORT = 6667
NICKNAME = 'ChatReaderTest' #Bot's nickname here
TOKEN = 'PLACE TOKEN HERE' #format 'oauth:YOURTOKENHERE'
CHANNEL = 'PLACE CHANNEL NAME HERE WITH # AT FRONT'  #format '#Channelname'

globalMessageID = 0

async def chatLoop():
    pass


async def speakerList():
    async with Client() as client:
        for speaker in await client.fetch_speakers():
            print(speaker.name + " : " + speaker.uuid)
            for style in speaker.styles:
                print("   " + style.name + " : " + str(style.id))

async def readMessage(text, messageID, speakerID):
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
def parse(msg):
    isMessageRegex = r"^:[a-zA-Z0-9_]+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+\.tmi\.twitch\.tv PRIVMSG #[a-zA-Z0-9_]+ :.+$"
    messageRegex = r"PRIVMSG " + CHANNEL + r" :(.+)"
    if re.match(isMessageRegex, msg):
        global globalMessageID
        globalMessageID += 1
        return{
                'username': re.findall(r'^:([a-zA-Z0-9_]+)!', msg)[0],
                'message': re.findall(messageRegex, msg)[0],
                'ID': str(globalMessageID)
            }
    else:
        return None
    

if __name__ == "__main__":
    #asyncio.run(speakerList())
    if not (re.match(r'^oauth:([a-zA-Z0-9_]+)', TOKEN) and re.match(r'^#([a-zA-Z0-9_]+)', CHANNEL)):
        print("You did not properly set up the Token or Channel:")
        raise  Exception("Token or Channel name not formatted correctly. Token must be in 'oauth:*' format and channel musst be in '#CHANNELNAME' format.")
    
    sock = socket.socket()
    try:
        sock.connect((SERVER, PORT))
        sock.send(f"PASS {TOKEN}\n".encode('utf-8'))
        sock.send(f"NICK {NICKNAME}\n".encode('utf-8'))
        sock.send(f"JOIN {CHANNEL}\n".encode('utf-8'))
        response = sock.recv(2048).decode('utf-8')
    except socket.error as e:
        print(e)
        if re.match(r'\[WinError 10054\]'):
            print("Previous Crash forcibly closed connection. Please start this script again.")
            os._exit(10054)
    print(response)
    
    loop = True
    while loop:
        try:
            response = sock.recv(2048).decode("utf-8")
        except socket.error as e:
            print(e)
        
        if re.match(r'^PING :tmi\.twitch\.tv$', response):
            sock.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))
            time.sleep(1)
    
        elif len(response) > 0:
            #TODO add emoji support
            #print(response)
            messages = [parse(msg) for msg in filter(None, response.split('\r\n'))]
            messages = filter(None, messages)
            for msg in messages:
                    print(msg)
                    asyncio.run(readMessage(msg['message'], msg['ID'], 2))
            

    sock.close()
