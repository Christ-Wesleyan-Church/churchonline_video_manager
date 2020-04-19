"""Function library for Church Online Video Manager"""

import os
import json
import datetime
import math

import logging.config
import logging

import pytz

import google_auth_oauthlib
import google.oauth2.credentials
import googleapiclient

import dateutil.parser

import pushover

class VideoManager():

    def __init__(self):

        self.log = logging.getLogger('video_manager')
        self.config = get_config()

    def get_service(self):
        """Should we have a service video available?"""

        if os.getenv('VM_DEBUG').lower() == 'true':
            localnow = FakeDateTime(
                int(os.getenv('VM_DEBUG_DOW')),
                int(os.getenv('VM_DEBUG_HOUR')),
                int(os.getenv('VM_DEBUG_MINUTE'))
            )

            self.log.debug(f'Using FAKE reference time: {localnow}')

        else:
            localnow = datetime.datetime.now(pytz.timezone(os.getenv('PYTZ_TIMEZONE')))

            self.log.debug(f'Using REAL reference time: {localnow}')

        self.service = None

        for service in self.config['services']:

            if all([
                localnow.isoweekday() == service['dow'],
                localnow.hour == service['hour'],
                math.floor(localnow.minute/5) == math.floor(service['minute']/5)
            ]):

                self.service = service

                return self.service

    def get_youtube(self):
        """Instantiate a YouTube API Wrapper instance."""

        # Get credentials and create an API client
        if not os.path.exists(os.getenv('USER_SECRETS_PATH')):
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                os.getenv('APP_SECRETS_PATH'), os.getenv('API_SCOPES').split(','))

            credentials = flow.run_console()

            save_tokens = {
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
            }

            with open(os.getenv('USER_SECRETS_PATH'), 'w') as out_file:
                json.dump(save_tokens, out_file)

        else:

            with open(os.getenv('USER_SECRETS_PATH'), 'r') as in_file:
                save_tokens = json.load(in_file)

                credentials = google.oauth2.credentials.Credentials(None, **save_tokens)

        self.youtube = googleapiclient.discovery.build(
            os.getenv('API_SERVICE_NAME'), os.getenv('API_VERSION'), credentials=credentials)

        self.log.debug('Got YouTube API Wrapper instance.')

        return self.youtube

    def search_video(self, service):
        """Find most recent video with service title."""

        request = self.youtube.search().list( #pylint: disable=no-member
            part='snippet',
            forMine=True,
            type='video',
            order='date',
            q=service['title'],
        )
        
        response = request.execute()

        # Error: didn't find a video
        if len(response['items']) == 0:
            raise Exception(f'Fatal: Expected video for {service["title"]} but no search results found!')

        # Error: result has wrong title
        title = response['items'][0]['snippet']['title']
        if title != service['title']:
            raise Exception(f'Fatal: Expected video with title {service["title"]} as first result but got {title}!')

        # Error: result doesn't have today's date

        ## First, get all dates in local timezone
        video_ts_string = response['items'][0]['snippet']['publishedAt']
        local_tz = pytz.timezone(os.getenv('PYTZ_TIMEZONE'))
        local_video_date = dateutil.parser.isoparse(video_ts_string).astimezone(local_tz).date()
        date_now = datetime.datetime.now(local_tz).date()

        ## Now we compare. If video isn't from today, something is wrong.
        if not local_video_date == date_now:
            raise Exception(f'Fatal: Candidate video for unlisting ("{service["title"]}") has unexpected date: "{local_video_date}" (expected "{date_now}")')

        # We made it! Let's return the video we found.

        self.video_id = response['items'][0]['id']
        self.log.info(f'Identified video ID {self.video_id} ("{title}") for delisting.')

        return self.video_id

    def get_privacy_status(self, video_id):
        """Get the current privacy status of the video."""

        request = self.youtube.videos().list( #pylint: disable=no-member
            part='status',
            id=video_id['videoId']
        )
        
        response = request.execute()

        privacy_status = response['items'][0]['status']['privacyStatus']

        return privacy_status
    
    def delist_video(self, video_id):
        """Delists the specified video."""

        request = self.youtube.videos().update( #pylint: disable=no-member
            part='status',
            body={
                'id': video_id['videoId'],
                'status': {
                    'privacyStatus': 'unlisted',
                    'embeddable': False,
                    'publicStatsViewable': True,
                    'selfDeclaredMadeForKids': True
                }
            }
        )

        response = request.execute()

        return response['status']['privacyStatus']
    
    def run(self):
        service = self.get_service()

        if service:
            self.log.info(f'Identified service video to manage: "{self.service["title"]}"')

            self.get_youtube()

            video_id = self.search_video(service)

            old_privacy_status = self.get_privacy_status(video_id)

            new_privacy_status = self.delist_video(video_id)

            self.log.warning(
                f'Privacy status for video "{self.service["title"]}" ' \
                f'successfully changed from "{old_privacy_status.upper()}" to ' \
                f'"{new_privacy_status.upper()}".'
            )

class FakeDateTime():
    """A fake datetime object for debugging."""

    def __init__(self, weekday, hour, minute):
        self.weekday = weekday
        self.hour = hour
        self.minute = minute

    def isoweekday(self):
        """Imitate datetime isoweekday function."""

        return self.weekday

    def __str__(self):
        return f'<fakedatetime: weekday: {self.weekday}, hour: {self.hour}, minute: {self.minute}>'

class PushoverHandler(logging.Handler):
    """Emit logs directly to pushover."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open(os.getenv('PUSHOVER_SECRETS_PATH'), 'r') as fh:
            po_secrets = json.load(fh)

        self.client = pushover.Client(po_secrets['user-key'], api_token=po_secrets['api-token'])

    def emit(self, record):
        log_entry = self.format(record)

        return self.client.send_message(log_entry, 'Church Online Video Manager')

def get_config():
    """Load config from file."""

    with open(os.getenv('SCRIPT_CONFIG'), 'r') as fh:
        return json.load(fh)

def config_logger():
    """Config the logger object."""

    with open(os.getenv('LOGGING_CONFIG'), 'r') as fh:
        logging.config.dictConfig(json.load(fh))
