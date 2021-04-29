#!./venv/bin/python
# encoding: utf-8

####!/usr/bin/env python3

import os
from os.path import getmtime
import time
import signal
# import signalindsat af PS
import subprocess
import sys

FILTERS = ['.swp']


def get_mtime(directory):
    """ Return a generator with all files modified time """
    def _yield():
        for dirname, _, files in os.walk('.'):
            for fname in files:
                fpath = os.path.join(dirname, fname)
                ext = '.' + fpath.split('.')[-1]
                if ext in FILTERS:
                    continue
                try:
                    t = getmtime(fpath)
                    yield t
                # except FileNotFoundError:
                #     continue
                except IOError:
                    continue
    return _yield()


def launch(command):
    """ Launch a command.

    Returns the process object to be able to terminate it.
    """
# The os.setsid() is passed in the argument preexec_fn so
# it's run after the fork() and before  exec() to run the shell.
#pro = subprocess.Popen(cmd, stdout=subprocess.PIPE,   shell=True, preexec_fn=os.setsid)

    command = ' '.join(command)
    process = subprocess.Popen(
            command,
            stdout=sys.stdout,
            stderr=sys.stderr,
            shell=True,
            preexec_fn=os.setsid)
            # Sidste linje indsat af PS

    return process


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('You must provide a command')
        print(('Example: ' + os.path.basename(sys.argv[0]) + ' <command> ≃ ./test.py '))
        sys.exit(1)

    try:
        print('Launching your command, CTRL+C to stop')
        process = launch(sys.argv[1:])
        mtime = max(get_mtime('.'))
        while True:
            time.sleep(0.5  )
            #time.sleep(1)
            newtime = max(get_mtime('.'))
            if newtime > mtime:
                print("\nReload, a file is modified, restarted")
                mtime = max(get_mtime('.'))
                process.terminate()
                process.kill()
                # indsat af PS
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Send the signal to all the process groups
                process = launch(sys.argv[1:])
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        process.terminate()
        process.kill()
        # indsat af PS
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Send the signal to all the process groups
        print('Done')
