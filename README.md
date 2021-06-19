
# PspMultiRoomPlayer
This is a standalone program there play Internet radio and music in companion with [skill_MultiRoomMediaVolume](https://github.com/poulsp/skill_MultiRoomMediaVolume) and [skill_MultiRoomRadioManager](https://github.com/poulsp/skill_MultiRoomRadioManager).

It belongs to the synchronous multiroom audio system i am building.
Uses the excelent [snapcast system](https://github.com/badaix/snapcast) by badaix.

It is an Internet radiostation/music player that plays in sync (like sonos) with other PspMultiRoomPlayers.

The PspMultiRoomPlayer is used as a satellite player e.g. on a ProjectAlice satellite or another hardware.

Run ./setup.sh
to create the virtual python environment.

Insert at the buttom of /etc/asound.conf or where your config is, if you have one that not for sure.



```sh
pcm.snapcastSpeaker {
   type plug
   slave {
      pcm "hw:X,0" # Importent!, leave this comment so PspMultiRoomPlayer can check and changes this cardNo.
   }
}
```


If you set "autosoundCardNo": false - You have to set the X to you real cardNo showing in aplay -l.

if "autosoundCardNo": true - You don't need to set the X to be the real cardNo, just leave the X. It will change automatically.
If you have a a respeaker 2 for example, then you should insert thispcm.snapcastSpeaker in the bottom /etc/voicecard/asound_2mic.conf.

the "startVolume" Is used when you stop the MultiRoomPlayer you mixer will then be set to this volume.

And then use snapcastSpeaker in config.json 'mixerDeviceName'


For now, I use a about 1 USD, USB sound card as a snapcast speaker (cheaply between $ 1 and $ 1.5). However, you can use RPi's built-in bcm2835 headphones as long as it is not used by other hardware.

Be sure to edit the PspMultiRoomPlayer.service


config.json example
```json
{
    "thisSite": "office",
    "asoundPcmName": "snapcastSpeaker",
    "mixerPlaybackName": "Speaker",
    "soundCardDevice": "Device [USB Audio Device], device 0: USB Audio [USB Audio]",
    "autosoundCardNo" : false,
    "soundCardHwNo": "1",
    "volumeOffset": "0",
    "mqttHost": "<MqttHostIp>",
    "mqttport": "1883",
    "snapServerHost": "<SnapcastServerIp>",
    "latency": 0,
    "startVolume": "50"
}
```

"snapServerHost": "<SnapcastServerIp>" is ProjectAlice Ip.

"mixerPlaybackName": "Speaker" can be seen in alsamixer -c X, X from aplay -l cardNo

e.g "soundCardDevice": "Device [USB Audio Device], device 0: USB Audio [USB Audio]" or
    "soundCardDevice": "Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones [bcm2835 Headphones]"



On my Ubuntu 20.04 AMD the config looks like this, I don't have an etc/asound.conf.
```json
{
    "thisSite": "office",
    "asoundPcmName": "pulse",
    "mixerPlaybackName": "Master",
    "soundCardDevice": "Generic [HD-Audio Generic], device 0: ALC887-VD Analog [ALC887-VD Analog]",
    "autosoundCardNo" : false,
    "soundCardHwNo": "1",
    "volumeOffset": "6",
    "mqttHost": "192.168.xx.xx",
    "mqttport": "1883",
    "snapServerHost": "192.168.xx.xx",
    "latency": 0,
    "startVolume": "50"
}
```
