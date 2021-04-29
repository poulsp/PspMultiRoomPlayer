# PspMultiRoomPlayer
This is a standalone program there play Internet radio and music in companion with skill_PspRadioManager.

It belongs to the synchronous multiroom audio system i am building.
Uses the excelent [snapcast system](https://github.com/badaix/snapcast) by badaix.

It is an Internet radiostation/music player that plays in sync (like sonos) with other PspMultiRoomPlayers.

The PspMultiRoomPlayer is used as a satellite player e.g. on a ProjectAlice satellite or another hardware.

Run ./setup.sh
to create the virtual python environment.

Insert at the buttom of /etc/asound.conf or where your config is. replace the X "hw:X,0" with your soundcard number. show the soundcard and number with aplay -l


    pcm.snapcastSpeaker {
       type plug
       slave {
          pcm "hw:X,0"
       }
    }

And then use snapcastSpeaker in config.json 'mixerDeviceName'

The problem the X "hw:X,0" can change after a reboot, so I vill find a solution.

For now I use a 1.5 USD USB sound card as snapcastSpeaker (cheap between 1 USD and 1.5 USD).


Be sure to edit the PspMultiRoomPlayer.service


config.json example

    {
        "thisSite": "office",
        "asoundPcmName": "snapcastSpeaker",
        "mixerPlaybackName": "Speaker",
        "soundCardHwNo": "1",
        "volumeOffset": "0",
        "mqttHost": "<MqttHostIp>",
        "mqttport": "1883",
        "snapServerHost": "<SnapcastServerIp>"
    }

"snapServerHost": "<SnapcastServerIp>" is ProjectAlice Ip.
"mixerPlaybackName": "Speaker" can be seen in alsamixer -c X



On my Ubuntu 20.04 AMD the config looks like this

    {
        "thisSite": "default",
        "asoundPcmName": "pulse",
        "mixerPlaybackName": "Master",
        "soundCardHwNo": "1",
        "volumeOffset": "11",
        "mqttHost": "192.168.xx.xx",
        "mqttport": "1883",
        "snapServerHost": "192.168.xx.xx"
    }

Sure to edit PspMultiRoomPlayer.service

