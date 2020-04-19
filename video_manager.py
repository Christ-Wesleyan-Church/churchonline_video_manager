# -*- coding: utf-8 -*-

# Sample Python code for youtube.channels.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/guides/code_samples#python

import os
import sys
import json

import dotenv

import google_auth_oauthlib.flow
import google.oauth2.credentials
import googleapiclient.discovery
import googleapiclient.errors

import logging

from lib import VideoManager
from lib import config_logger

# Bootstrap
## Get env vars
dotenv.load_dotenv()

## Build/configure logger
log = logging.getLogger('video_manager')
config_logger()

def main():

    log.debug('Beginning VideoManager execution.')

    vm = VideoManager()
    vm.run()

    log.debug('VideoManager exectution ending.')

if __name__ == "__main__":
    if os.getenv('VM_DEBUG').lower() == 'true':
        main()
    else:
        try:
            main()
        except Exception as e:
            log.critical(f'Fatal error running video manager: {e}')