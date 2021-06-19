#!./venv/bin/python
# -*- coding: utf-8 -*-


#  Copyright (c) 2021 Poul Spang
#
#  This file, PspMultiRoomPlayer.py, is part of Project PspMultiRoomPlayer.
#
#  Project PspMultiRoomPlayer is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>


## Synchronous multiroom audio player.
## Standalone for other systems not subject to ProjectAlice.
## Uses the excelent 'snapcast system' from "https://github.com/badaix/snapcast" by badaix.

import signal
import logging

import platform
import os
import paho.mqtt.client as mqtt
import json
import time
import threading
import psutil
import subprocess

from library.CheckSnapClient import(CheckSnapClient)
from library.CheckSoundCard import(CheckSoundCard)


# logging.basicConfig(
#  #format='%(asctime)s {%(pathname)s:%(lineno)d - [%(levelname)s] - %(message)s',
#  format='%(asctime)s - %(filename)s:%(lineno)d - [%(levelname)s] - %(message)s',
#  #level=logging.DEBUG,
#  level=logging.INFO,
# #level=logging.CRITICAL,
# )
# 	# ,
# 	# filename='/var/log/test.log',
# 	# filemode='w'

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


#-----------------------------------------------
def getMacAddrFromIp():
	cmd = "hostname -I|awk '{print $1}'"
	ip = subprocess.check_output(cmd, shell=True).decode('utf-8')[:-1]

	nics = psutil.net_if_addrs()
	for key in nics.keys():
		if nics.get(key)[0][1] == ip:
			return {'ip':ip, 'mac': nics.get(key)[2][1]}

#-----------------------------------------------
def getIdAndIp():
	ipMac = getMacAddrFromIp()
	return {'id': ipMac['mac'], 'ip': ipMac['ip']}



#===============================================
class MediaVolume():

	#-----------------------------------------------
	def __init__(self, soundCardNo="", mixerPlaybackName=""):
		self._soundCardNo       = soundCardNo
		self._mixerPlaybackName = mixerPlaybackName

		self._platform_system   = platform.system()
		self._platform_machine  = platform.machine()
		self._volumeControlType = "alsamixer"
		self.volume = 1


	#-----------------------------------------------
	#TODO
	def setMixerVolume(self, volume, physicalMixer=False, minVolume=0, maxVolume=100):
		volume = max(1, min(maxVolume, int(volume)))
		# logging.info(f"################## sætter volume til : {volume}")

		if self._volumeControlType == "alsamixer" or physicalMixer:
			if self._platform_machine == "x86_64":
				cmdSet = "amixer -D pulse sset Master {}%".format(volume)
			elif self._platform_machine == "armv7l" or self._platform_machine == "armv6l":
				cmdSet = f"amixer -M -c {self._soundCardNo} -- sset {self._mixerPlaybackName} {volume}%"

		else: # snapcast
			maxVolume= volume # 100
			if self._platform_machine == "x86_64":
				cmdSet = "amixer -D pulse sset Master {}%".format(maxVolume)
			elif self._platform_machine == "armv7l" or self._platform_machine == "armv6l":
				cmdSet = f"amixer -M -c {self._soundCardNo} -- sset {self._mixerPlaybackName} {maxVolume}%"

		os.popen(cmdSet).read()
		self.volume = volume


	#-----------------------------------------------
	def setVolumeControlType(self, control):
		self._volumeControlType = control


#-----------------------------------------------
class PspMultiRoomPlayer():

	_MULTIROOM_PLAYER_PLAY							= "psp/multiroom/player/play"
	_MULTIROOM_PLAYER_STOP							= "psp/multiroom/player/stop"
	_MULTIROOM_VOLUME 									= "psp/multiroom/volume"
	_MULTIROOM_VOLUME_CONTROL_TYPE_SET 	= "psp/multiroom/volume/controltype/set"
	_MULTIROOM_VOLUME_CONTROL_TYPE_GET 	= "psp/multiroom/volume/controltype/get"
	_MULTIROOM_VOLUME_OFFSET_SET 				= 'psp/multiroom/volume/offset/set'
	_MULTIROOM_VOLUME_OFFSET_GET 				= 'psp/multiroom/volume/offset/get'
	_MULTIROOM_CLIENT_LATENCY_SET 			= 'psp/multiroom/latency/set'

	#-----------------------------------------------
	#def __init__(self, mqttServer="localhost", mqttPort=1883):
	def __init__(self):
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
		self._latency           = 0
		self._volumeControlType = "alsamixer"


		self.onStart()


	#-----------------------------------------------
	def _readConfig(self):
		with open('config.json') as config_file:
				self._config = json.load(config_file)

		return self._config


	#-----------------------------------------------
	def _getConfig(self, configName: str):
		return self._config[configName]


	#-----------------------------------------------
	def _writeConfig(self):
		with open('config.json', 'w') as json_file:
			json.dump(self._config, json_file, indent=2 )


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
		self._latency           = int(self._getConfig('latency'.strip()))
		self._startVolume       = "40"
		self._startVolume       = self._getConfig('startVolume').strip()


		if self._autosoundCardNo:
			self._soundCardNo = CheckSoundCard.checkSoundCard(self._getConfig('soundCardDevice')).strip()
		else:
			self._soundCardNo = self._getConfig('soundCardHwNo').strip()

		self._snapClientOpt     = f"-s {self._asoundPcmName} -h {self._snapServerHost}"

		self.mediaVolume = MediaVolume(self._soundCardNo, self._mixerPlaybackName)
		self.mediaVolume.setMixerVolume(self._startVolume)

		self._mqttSetup()

		self._getVolumeControlType()

		self._idIp = getIdAndIp()
		logging.info(f"_self._idIp {self._idIp}")

		# TODO vi gemmer lige denne her under opstart.
		self._sendVolumeOffset()



	#-----------------------------------------------
	def onStop(self):
		self.mediaVolume.setMixerVolume(self._startVolume, physicalMixer=True)


	#-----------------------------------------------
	def _processSnapClient(self):
		startSnapClientCmd =  f"/usr/bin/snapclient {self._snapClientOpt} > /dev/null 2>&1 &"
		os.system(startSnapClientCmd)
		# logging.info(f"startSnapClientCmd: {startSnapClientCmd}")


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


	# # Original _radioPlay
	# #-----------------------------------------------
	# def _radioPlay(self, client, data, msg: mqtt.MQTTMessage):
	# 	#logging.info(f"In radioPlay payload: {payload}")
	# 	payload = json.loads(msg.payload.decode('utf-8'))
	# 	playSite = payload.get("playSite")
	# 	logging.info(f"In radioPlay playSitepayload: {playSite}")

	# 	if playSite == self.thisSite or playSite == 'everywhere':
	# 		self._startSnapClient()


	#-----------------------------------------------
	def _radioPlay(self, client, data, msg: mqtt.MQTTMessage):
		#logging.info(f"In radioPlay payload: {payload}")
		payload = json.loads(msg.payload.decode('utf-8'))
		playSite = payload.get("playSite")
		logging.info(f"In radioPlay playSitepayload: {playSite}")

		if self._volumeControlType != "alsamixer":
			self._setVolumeCentralize(self._startVolume, info='onHotwordToggleOff', physicalMixer=True)


		if playSite == self.thisSite or playSite == 'everywhere':
			self._startSnapClient()


		if self._volumeControlType != "alsamixer":
			self._setVolumeCentralize('100', info='onHotwordToggleON', physicalMixer=True)



	# # Orriginal _radioStop
	# #-----------------------------------------------
	# def _radioStop(self, client, data, msg: mqtt.MQTTMessage):
	# 	payload = json.loads(msg.payload.decode('utf-8'))
	# 	logging.info(f"In radioStop payload: {payload}")
	# 	#siteId = payload.get("siteId")
	# 	playSite = payload.get("playSite")
	# 	if playSite == self.thisSite or playSite == 'everywhere':
	# 		self.stopSnapClient()

	# 	self.mediaVolume.setMixerVolume(self._startVolume)


	#-----------------------------------------------
	def _radioStop(self, client, data, msg: mqtt.MQTTMessage):
		payload = json.loads(msg.payload.decode('utf-8'))
 		# logging.info(f"In radioStop payload: {payload}")
		#siteId = payload.get("siteId")
		playSite = payload.get("playSite")
		if playSite == self.thisSite or playSite == 'everywhere':
			self.stopSnapClient()

		if self._volumeControlType == "alsamixer":
			self.mediaVolume.setMixerVolume(self._startVolume, physicalMixer=True)
		else:
			self._setVolumeCentralize(self._startVolume, info='onHotwordToggleOff', physicalMixer=True)



	# # _setVolume original
	# #-----------------------------------------------
	# def _setVolume(self, client, data, msg: mqtt.MQTTMessage):
	# 	payload = json.loads(msg.payload.decode('utf-8'))

	# 	receivedVolume = payload['volume']

	# 	volume = str(int(receivedVolume) + int(self._volumeOffset))
	# 	self.mediaVolume.setMixerVolume(volume)
	# 	logging.info(f"In setVolume volume: {volume}  - receivedVolume: {receivedVolume}")


	#-----------------------------------------------
	def _setVolume(self, client, data, msg: mqtt.MQTTMessage):
		payload = json.loads(msg.payload.decode('utf-8'))
		info = None
		if 'info' in payload:
			info = payload['info']


		receivedVolume = payload['volume']

		volume = str(int(receivedVolume) + int(self._volumeOffset))
		# TODO

		if self._volumeControlType == "alsamixer":
			self.mediaVolume.setMixerVolume(volume)
		else:
			self._setVolumeCentralize(volume, info=info)


	#-----------------------------------------------
	def _setVolumeCentralize(self, volume, info=None, physicalMixer=False):
		logging.info(f"################################################# info: {info}")
		volume = str(int(volume))

		if info:

			if info and info == 'onHotwordToggleOff':
				self.mediaVolume.setMixerVolume(self._startVolume, physicalMixer=True)

			if info and info == 'onHotwordToggleOn':
				self.mediaVolume.setMixerVolume('100', physicalMixer=True)

		else:
			self.mediaVolume.setMixerVolume(volume)


	#-----------------------------------------------
	def _getVolumeControlType(self, ):
		self._mqttClient.publish(self._MULTIROOM_VOLUME_CONTROL_TYPE_GET, json.dumps({'to': 'VolumeManager'}))


	#-----------------------------------------------
	def _setVolumeControlType(self, client, data, msg: mqtt.MQTTMessage):
		payload = json.loads(msg.payload.decode('utf-8'))

		self._volumeControlType = payload['volumeControlType'] #'volumeControlType': 'alsamixer'
		self.mediaVolume.setVolumeControlType(self._volumeControlType)
		self.mediaVolume.setMixerVolume(payload['volume'])


	#-----------------------------------------------
	def _sendVolumeOffset(self):
		self._mqttClient.publish(self._MULTIROOM_VOLUME_OFFSET_SET, json.dumps({'clientSite': self.thisSite,
																																						'idIp': self._idIp,
																																						'volumeOffset': self._volumeOffset,
																																						'latency': str(self._latency)
																																						}
																																					))


	#-----------------------------------------------
	def _setClientLatency(self, client, data, msg: mqtt.MQTTMessage):
		payload = json.loads(msg.payload.decode('utf-8'))
		if payload.get('playSite') == self.thisSite and self._idIp.get('id') == payload.get('id'):
			self._readConfig()
			self._config['latency'] = payload.get('latency')
			self._writeConfig()
			self._latency = self._config['latency']


	#-----------------------------------------------
	def _getVolumeOffset(self, client, data, msg: mqtt.MQTTMessage):
			payload = json.loads(msg.payload.decode('utf-8'))
			logging.info(f"__getVolumeOffset {payload}")
			self._sendVolumeOffset()


	#-----------------------------------------------
	def onConnect(self, client, userData, flags, rc):
		subscribedEvents = [
			(self._MULTIROOM_PLAYER_PLAY, 0),
			(self._MULTIROOM_PLAYER_STOP, 0),
			(self._MULTIROOM_VOLUME, 0),
			(self._MULTIROOM_VOLUME_CONTROL_TYPE_SET, 0),
			(self._MULTIROOM_VOLUME_OFFSET_GET, 0),
			(self._MULTIROOM_CLIENT_LATENCY_SET,0)

		]

		self._mqttClient.subscribe(subscribedEvents)


	#-----------------------------------------------
	def _mqttSetup(self):

		self._mqttClient.on_connect = self.onConnect

		self._mqttClient.message_callback_add(self._MULTIROOM_PLAYER_PLAY, self._radioPlay)
		self._mqttClient.message_callback_add(self._MULTIROOM_PLAYER_STOP, self._radioStop)
		self._mqttClient.message_callback_add(self._MULTIROOM_VOLUME, self._setVolume)
		self._mqttClient.message_callback_add(self._MULTIROOM_VOLUME_CONTROL_TYPE_SET, self._setVolumeControlType)
		self._mqttClient.message_callback_add(self._MULTIROOM_VOLUME_OFFSET_GET, self._getVolumeOffset)
		self._mqttClient.message_callback_add(self._MULTIROOM_CLIENT_LATENCY_SET, self._setClientLatency)


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
