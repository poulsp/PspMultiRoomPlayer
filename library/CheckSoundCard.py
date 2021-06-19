#!./venv/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess
import platform

_PLATFORM_SYSTEM   = platform.system()
_PLATFORM_MACHINE  = platform.machine()


class CheckSoundCard():

	@staticmethod
	def checkSoundCard(soundCardDevice):

		soundCardDevice = soundCardDevice.replace("[", "\\[", 10)
		soundCardDevice = soundCardDevice.replace("]", "\\]", 10)

		# skal angives i config.json
		_cmd = f"aplay -l|grep '{soundCardDevice}'|cut -c 6-6"
		#_cmd = "aplay -l|grep '\[USB Audio Device\], device 0: USB Audio \[USB Audio\]'|cut -c 6-6"
		_cardNo = ""
		try:
			_cardNo = subprocess.check_output(
				_cmd,
				stderr=subprocess.STDOUT,
				shell=True
			).decode('utf-8').replace('\n','')

		except subprocess.CalledProcessError as e:
			_cardNo = ""
			print(f"################ subprocess.CalledProcessError; {e}")
			raise e

		if _cardNo != "":
			try:
				if _PLATFORM_MACHINE == "armv7l" or _PLATFORM_MACHINE == "armv6l":

					_cmd = f'sudo sed  -i "s/pcm \\"hw:.,0\\".\+#.Importent!, leave this comment so PspMultiRoomPlayer can check and changes this cardNo\./pcm \\"hw:{_cardNo},0\\"\ # Importent!, leave this comment so PspMultiRoomPlayer can check and changes this cardNo\./" /etc/asound.conf  > /dev/null 2>&1 &'
					os.system(_cmd)
				else:
					pass
			except Exception as e:
				#raise e
				print(f"################ Exception; {e}")

			return _cardNo
		else:
			return -1


