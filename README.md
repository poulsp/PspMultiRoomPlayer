# PspMultiRoomPlayer
This is a standalone program there play Internet radio and music in companion with skill_PspRadioManager.

It belongs to the synchronous multiroom audio system i am building.
Uses the excelent [snapcast system](https://github.com/badaix/snapcast) by badaix.

It is an Internet radiostation/music player that plays in sync (like sonos) with other PspMultiRoomPlayers.

The PspMultiRoomPlayer is used as a satellite player e.g. on a ProjectAlice satellite or another hardware.

Run ./setup.sh
to create the virtual python environment.

Insert at the buttom of /etc/asound.conf or where your config is, if you have one that not for sure.



    pcm.snapcastSpeaker {
       type plug
       slave {
          pcm "hw:X,0"
       }
    }

You don't need to set the X to be the real cardNo, just leave the X.

And then use snapcastSpeaker in config.json 'mixerDeviceName'


For now I use a 1.5 USD USB sound card as snapcastSpeaker (cheap between 1 USD and 1.5 USD).


Be sure to edit the PspMultiRoomPlayer.service


config.json example

    {
        "thisSite": "office",
        "asoundPcmName": "snapcastSpeaker",
        "mixerPlaybackName": "Speaker",
        "soundCardDevice": "Device [USB Audio Device], device 0: USB Audio [USB Audio]",
        "volumeOffset": "0",
        "mqttHost": "<MqttHostIp>",
        "mqttport": "1883",
        "snapServerHost": "<SnapcastServerIp>"
    }



"snapServerHost": "<SnapcastServerIp>" is ProjectAlice Ip.
"mixerPlaybackName": "Speaker" can be seen in alsamixer -c X, X from aplay -l cardNo

e.g "soundCardDevice": "Device [USB Audio Device], device 0: USB Audio [USB Audio]"



On my Ubuntu 20.04 AMD the config looks like this

    {
        "thisSite": "default",
        "asoundPcmName": "pulse",
        "mixerPlaybackName": "Master",
        "soundCardDevice": "Generic [HD-Audio Generic], device 0: ALC887-VD Analog [ALC887-VD Analog]",
        "volumeOffset": "11",
        "mqttHost": "192.168.xx.xx",
        "mqttport": "1883",
        "snapServerHost": "192.168.xx.xx"
    }

Sure to edit PspMultiRoomPlayer.service

