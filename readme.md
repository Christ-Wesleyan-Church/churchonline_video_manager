# Church Online Video Manager

## About

Church Online Video Manager is a simple script for automatically "unlisting" the most recent video with a specific title on YouTube at a specific time. This is useful for a live stream that you want to be public, but don't want to be available for on-demand access once the event is over. Using this script, unlisting videos requires no manual settings changes. 😃

A log handler is included that enables push notifications to a mobile device about the script's activity using Python's standard logging facilities and the Pushover app. 💪

The script should be run as a five-minute cron job. The script will only reach out to YouTube at the times specified in the configuration file.

## Setup

Clone the project, then install a virtual environment and dependencies using `pipenv install` (so, yes, you'll want to have pipenv installed).

Next, you'll need OAUTH client app secrets file from the Google Dev dashboard on a project permitted to access the YouTube Data API v3, and you'll need to authorize on the channel on which you want to hide videos. Put that client app secrets file somewhere the script will be able to find it (you can tell it where using the .env file as shown below).

You'll also want a Pushover secrets JSON file if you're intending to use Pushover, which should look like this:

```json
{
    "user-key": "<key_here>",
    "api-token": "<token_here>"
}
```

Next, you'll need to create a .env file in whatever directory you've pulled churchonline_video_manager into. The contents of this file should look something like this (customize to your environment as needed):

```python
# Configuration for the church online video manager script

# API Params
API_SERVICE_NAME=youtube
API_VERSION=v3
API_SCOPES=https://www.googleapis.com/auth/youtube.force-ssl # Comma separated

# Secret file locations
APP_SECRETS_PATH=secrets/APP_SECRETS.json
USER_SECRETS_PATH=secrets/USER_SECRETS.json
PUSHOVER_SECRETS_PATH=secrets/PUSHOVER_SECRETS.json

# Config file locations
SCRIPT_CONFIG=config/config.json
LOGGING_CONFIG=config/logging.json

# Local TimeZone (pytz format)
PYTZ_TIMEZONE=US/Eastern

# Debug variables
VM_DEBUG=true
VM_DEBUG_DOW=7
VM_DEBUG_HOUR=10
VM_DEBUG_MINUTE=35
```

Finally, you'll want to tweak the files in the config directory to your liking. With that done, you're ready to set up a cron job and go!

## Platform/Python Version Support.

I developed this on Windows and deployed to Linux. It works for me on Python 3.8. That's all I know. 😁