#!./venv/bin/python
# -*- coding: utf-8 -*-


## Synchronous multiroom audio player.
## Standalone for other systems not subject to ProjectAlice.
## Uses the excelent 'snapcast system' from "https://github.com/badaix/snapcast" by badaix.

import sys
import signal
import logging

import platform
import os
import subprocess
import paho.mqtt.client as mqtt
import json
import time
import threading
from datetime import timedelta

from library.CheckSnapClient import(CheckSnapClient)
from library.CheckSoundCard import(CheckSoundCard)


# logging.basicConfig(
#  #format='%(asctime)s {%(pathname)s:%(lineno)d - [%(levelname)s] - %(message)s',
#  format='%(asctime)s - %(filename)s:%(lineno)d - [%(levelname)s] - %(message)s',
#  #level=logging.DEBUG,
#  level=logging.INFO,
# #level=logging.CRITICAL,
# )
#   # ,
#   # filename='/var/log/test.log',
#   # filemode='w'

#-----------------------------------------------
class ConfigurationError(Exception):
	pass

#-----------------------------------------------
class ProgramKilled(Exception):
	pass


#-----------------------------------------------
def signalHandler(signum, frame):
		raise ProgramKilled

signal.signal(signal.SIGTERM, signalHandler)
signal.signal(signal.SIGINT, signalHandler)


#===============================================
class MediaVolume():

	#-----------------------------------------------
	def __init__(self, soundCardNo="", mixerPlaybackName=""):
		self._soundCardNo       = soundCardNo
		self._mixerPlaybackName = mixerPlaybackName

		self._platform_system   = platform.system()
		self._platform_machine  = platform.machine()
		self.volume = 1
		self.setMixerVolume('40')

	#-----------------------------------------------
	def setMixerVolume(self, volume, minVolume=0, maxVolume=94):

		if int(volume) <= minVolume:
			volume = minVolume
		elif int(volume) >= maxVolume:
			volume = maxVolume

		if self._platform_machine == "x86_64":
			cmdSet = "amixer -D pulse sset Master {}%".format(volume)
		elif self._platform_machine == "armv7l" or self._platform_machine == "armv6l":
			cmdSet = f"amixer -M -c {self._soundCardNo} -- sset {self._mixerPlaybackName} {volume}%"

		#logging.info(f"cmdSet: {cmdSet}")
		os.popen(cmdSet).read()
		self.volume = volume


#-----------------------------------------------
class PspMultiRoomPlayer():

	_MULTIROOM_PLAYER_PLAY      = "psp/multiroom/player/play"
	_MULTIROOM_PLAYER_STOP      = "psp/multiroom/player/stop"
	_MULTIROOM_VOLUME           = "psp/multiroom/volume"

	#-----------------------------------------------
	#def __init__(self, mqttServer="localhost", mqttPort=1883):
	def __init__(self, ):
			#super().__init__()

		CheckSnapClient.test4SnapClient()

		self._mqttClient = mqtt.Client()
		self._mqttServer = None
		self._mqttPort   = "1883"


		self._config = None
		self.thisSite = None
		self.mediaVolume = None
		self._startVolume = ""


		self._timerStartSnapClient = None
		self._radioPlaying  = False
		self._process       = None
		self._snapClientOpt = None

		self._asoundPcmName     = ""
		self._soundCardNo       = ""
		self._volumeOffset      = ""
		self._snapServerHost    = ""
		self._mixerPlaybackName = ""

		self.onStart()


	#-----------------------------------------------
	def _readConfig(self):
		with open('config.json') as config_file:
				self._config = json.load(config_file)

	#-----------------------------------------------
	def _getConfig(self, configName: str):
		return self._config[configName]


	#-----------------------------------------------
	def onStart(self):
		self._readConfig()


		self._mqttServer        = self._getConfig('mqttHost').strip()
		self._mqttPort          = int(self._getConfig('mqttport').strip())
		self._snapServerHost = self._getConfig('snapServerHost').strip()
		if self._getConfig('snapServerHost') == "<SnapcastServerIp>":
			raise ConfigurationError('you must edit the config.json file.')

		self._asoundPcmName     = self._getConfig('asoundPcmName').strip()
		self._volumeOffset      = self._getConfig('volumeOffset').strip()
		self._snapServerHost    = self._getConfig('snapServerHost').strip()
		self._mixerPlaybackName = self._getConfig('mixerPlaybackName').strip()
		self.thisSite           = self._getConfig('thisSite').strip()
		self._autosoundCardNo   = self._getConfig('autosoundCardNo')
		self._startVolume       = "40"

		if self._autosoundCardNo:
			self._soundCardNo = CheckSoundCard.checkSoundCard(self._getConfig('soundCardDevice')).strip()
		else:
			self._soundCardNo = self._getConfig('soundCardHwNo')


		self._snapClientOpt     = f"-s {self._asoundPcmName} -h {self._snapServerHost}"


		self.mediaVolume = MediaVolume(self._soundCardNo, self._mixerPlaybackName)
		self.mediaVolume.setMixerVolume(self._startVolume)

		self._mqttSetup()

	#-----------------------------------------------
	def onStop(self):
		self.mediaVolume.setMixerVolume(self._startVolume)

	#-----------------------------------------------
	def _processSnapClient(self):
		startSnapClientCmd =  f"/usr/bin/snapclient {self._snapClientOpt} > /dev/null 2>&1 &"
		os.system(startSnapClientCmd)
		logging.info(f"startSnapClientCmd: {startSnapClientCmd}")


	#-----------------------------------------------
	def _startSnapClient(self):
		if self._radioPlaying:
			return

		self._radioPlaying = True

		# # wait a few seconds to start
		timer = threading.Timer(3, self._processSnapClient)
		timer.start()


	#-----------------------------------------------
	def stopSnapClient(self):
		cmdKill = "/usr/bin/killall -2 snapclient >/dev/null 2>&1"
		os.system(cmdKill)
		self._radioPlaying = False


	#-----------------------------------------------
	def _radioPlay(self, client, data, msg: mqtt.MQTTMessage):
		topic = msg.topic
		#logging.info(f"In radioPlay payload: {payload}")
		payload = json.loads(msg.payload.decode('utf-8'))
		playSite = payload.get("playSite")
		logging.info(f"In radioPlay playSitepayload: {playSite}")

		if playSite == self.thisSite or playSite == 'everywhere':
			self._startSnapClient()


	#-----------------------------------------------
	def _radioStop(self, client, data, msg: mqtt.MQTTMessage):
		topic = msg.topic
		payload = json.loads(msg.payload.decode('utf-8'))
		logging.info(f"In radioStop payload: {payload}")
		#siteId = payload.get("siteId")
		playSite = payload.get("playSite")
		if playSite == self.thisSite or playSite == 'everywhere':
			self.stopSnapClient()

		self.mediaVolume.setMixerVolume(self._startVolume)


	#-----------------------------------------------
	def _setVolume(self, client, data, msg: mqtt.MQTTMessage):
		topic = msg.topic
		payload = json.loads(msg.payload.decode('utf-8'))

		receivedVolume = payload['volume']

		volume = str(int(receivedVolume) + int(self._volumeOffset))
		self.mediaVolume.setMixerVolume(volume)
		logging.info(f"In setVolume volume: {volume}  - receivedVolume: {receivedVolume}")


	#-----------------------------------------------
	def onConnect(self, client, userData, flags, rc):
		subscribedEvents = [
			(self._MULTIROOM_PLAYER_PLAY, 0),
			(self._MULTIROOM_PLAYER_STOP, 0),
			(self._MULTIROOM_VOLUME, 0)
		]

		self._mqttClient.subscribe(subscribedEvents)


	#-----------------------------------------------
	def _mqttSetup(self):

		self._mqttClient.on_connect = self.onConnect

		self._mqttClient.message_callback_add(self._MULTIROOM_PLAYER_PLAY, self._radioPlay)
		self._mqttClient.message_callback_add(self._MULTIROOM_PLAYER_STOP, self._radioStop)
		self._mqttClient.message_callback_add(self._MULTIROOM_VOLUME, self._setVolume)

		#self.mqttClient.on_message = self.onMessage
		self._mqttClient.connect(self._mqttServer, self._mqttPort)
		self._mqttClient.loop_start()


	#-----------------------------------------------
	def mqttStop(self):
		self._mqttClient.loop_stop()
		self._mqttClient.disconnect()


#-----------------------------------------------
if __name__ == "__main__":
	pspMultiRoomPlayer = PspMultiRoomPlayer()

	try:
		while True:
			time.sleep(0.1)
	except ProgramKilled:
		print("\nProgram killed: running cleanup code")
		pspMultiRoomPlayer.onStop()
		pspMultiRoomPlayer.stopSnapClient()
		pspMultiRoomPlayer.mqttStop()
