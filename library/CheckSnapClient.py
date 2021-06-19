import platform
#import shlex
import subprocess

# HELP TO DEVELOPMENT.
# sudo apt-get purge snapclient -y
# sudo systemctl status snapclient.service
# Test stream on machine where the snapserver are installed.
# ffmpeg -v 0 -y -rtbufsize 15M -i http://stream.srg-ssr.ch/m/rsj/aacp_96 -f u16le -acodec pcm_s16le -ac 2 -ar 48000 /dev/shm/snapfifo


#SNAP_CLIENT_RELEASE 	= '0.21.0'
SNAP_CLIENT_RELEASE  = '0.24.0'

_URL 			= 'https://github.com/badaix/snapcast/releases/download'
_WGET_URL = f"{_URL}/v{SNAP_CLIENT_RELEASE}/snapclient_{SNAP_CLIENT_RELEASE}"

_PLATFORM_SYSTEM   = platform.system()
_PLATFORM_MACHINE  = platform.machine()


class CheckSnapClient():


	#-----------------------------------------------
	@staticmethod
	def test4SnapClient():
		#print(f"################ In method test4SnapClient")
		try:
			subprocess.check_output(
				"dpkg-query -l snapclient",
				stderr=subprocess.STDOUT,
				shell=True
			).decode('utf-8').replace('\n','')

		except subprocess.CalledProcessError:
			# Install snapclient
			#print(f"################ In method test do installSnapclient")
			CheckSnapClient.installSnapClient()


	#-----------------------------------------------
	@staticmethod
	def installSnapClient():
		try:
			subprocess.check_output(
				"dpkg-query -l snapclient",
				stderr=subprocess.STDOUT,
				shell=True
			).decode('utf-8').replace('\n','')

		except subprocess.CalledProcessError:
			# Install snapclient

			if _PLATFORM_MACHINE == "x86_64":
				# print(f"####################################### _PLATFORM_MACHINE: {_PLATFORM_MACHINE } ")
				downloadUrl = f"{_WGET_URL}-1_amd64.deb"
				snapClientDeb = f"snapclient_{SNAP_CLIENT_RELEASE}-1_amd64.deb"

				# print(f"####################################### downloadUrl {downloadUrl } ")
				# print(f"####################################### snapClientDeb {snapClientDeb} ")

				subprocess.run(['sudo', 'apt-get', 'update'])
				subprocess.run(['wget', downloadUrl])
				subprocess.run(['sudo', 'dpkg', '-i', snapClientDeb])
				subprocess.run(['sudo', 'apt-get', '-f', 'install', '-y'])
				subprocess.run(['rm', snapClientDeb])
				subprocess.run(['sudo', 'systemctl', 'stop', 'snapclient'])
				subprocess.run(['sudo', 'systemctl', 'disable', 'snapclient'])


			elif _PLATFORM_MACHINE == "armv7l" or _PLATFORM_MACHINE == "armv6l":
				# print(f"####################################### _PLATFORM_MACHINE: {_PLATFORM_MACHINE } ")
				downloadUrl = f"{_WGET_URL}-1_armhf.deb"
				snapClientDeb = f"snapclient_{SNAP_CLIENT_RELEASE}-1_armhf.deb"

				#print(f"####################################### downloadUrl {downloadUrl } ")
				#print(f"####################################### snapclientDeb {snapClientDeb} ")

				subprocess.run(['sudo', 'apt-get', 'update'])
				subprocess.run(['wget', downloadUrl])
				subprocess.run(['sudo', 'dpkg', '-i', snapClientDeb])
				subprocess.run(['sudo', 'apt-get', '-f', 'install', '-y'])
				subprocess.run(['rm', snapClientDeb])
				subprocess.run(['sudo', 'systemctl', 'stop', 'snapclient'])
				#subprocess.run(sedCmd)
				#subprocess.run(sedCmd2)
				#subprocess.run(['sudo', 'rm', '/tmp/snapfifo'])
				#subprocess.run(['sudo', 'systemctl', 'restart', 'snapclient'])
				subprocess.run(['sudo', 'systemctl', 'disable', 'snapclient'])


	# #-----------------------------------------------
	# @staticmethod
	# def removeSnapclient():
	# 	subprocess.run(['sudo', 'systemctl', 'stop', 'snapclient'])
	# 	subprocess.run(['sudo', 'apt-get', 'purge', 'snapclient', '-y'])

