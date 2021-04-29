#!./venv/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess


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
      #print(f"################ subprocess.CalledProcessError; {e}")
      raise e

    if _cardNo != "":
      try:
        _cmd = f'sudo sed  -i "s/pcm \\"hw:.,0\\"/pcm \\"hw:{_cardNo},0\\"/" /etc/asound.conf  > /dev/null 2>&1 &'
        os.system(_cmd)
      except Exception as e:
        #raise e
        print(f"################ subprocess.CalledProcessError; {e}")

      return _cardNo
    else:
      return -1



