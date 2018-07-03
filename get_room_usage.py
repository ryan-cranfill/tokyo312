from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import datetime
import pandas as pd
from pandas import to_datetime
from tqdm import tqdm


def get_now():
    return datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time


def get_next_week():
    now = datetime.datetime.utcnow()
    next_week = now + datetime.timedelta(weeks=1)
    return next_week.isoformat() + 'Z' # 'Z' indicates UTC time


def get_last_week():
    now = datetime.datetime.utcnow()
    last_week = now + datetime.timedelta(weeks=-1)
    return last_week.isoformat() + 'Z' # 'Z' indicates UTC time


def get_events_for_room(room_id, start=None, end=None):
    events_result = service.events().list(calendarId=room_id,
                                          timeMin=start,
                                          timeMax=end,
                                          maxResults=2500,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events


def prep_event(event):
    new_event = dict(
        start=to_datetime(event['start']['dateTime']),
        end=to_datetime(event['end']['dateTime']),
        location=get_location(event),
        name=event.get('summary', ''),
        description=event.get('description')
    )

    return new_event


def dataframe_from_events_list(events):
    prepped = []
    for e in events:
        prepped.append(prep_event(e))

    return pd.DataFrame(prepped)


def get_location(event):
    loc = event.get('location')
    if loc is not None:
        # todo: filter zoom out
        return loc

    attendees = event.get('attendees')
    if attendees is not None:
        rooms = [att['displayName'] for att in attendees if 'tokyo-' in att['displayName'].lower()]
        if rooms is not None:
            return ', '.join(rooms)

    organizer = event.get('organizer')
    if organizer is not None:
        if 'tokyo-' in organizer['displayName'].lower():
            return organizer['displayName']

    print(event)
    raise Exception


if __name__ == '__main__':
    # Setup the Calendar API
    SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # Get room calendar ids
    calendar_result = service.calendarList().list().execute()
    calendar_list = calendar_result.get('items', [])

    rooms = []
    group_cals = []
    for cal in calendar_list:
        if 'tokyo' in cal['summary'].lower() and 'resource' in cal['id']:
            rooms.append(cal)

        if 'group' in cal['id'] and 'tokyo' in cal['summary'].lower():
            group_cals.append(cal)

    all_events = []

    for cal in tqdm(rooms):
        all_events += get_events_for_room(cal['id'], get_last_week(), get_next_week())

    df = dataframe_from_events_list(all_events)

    print(df.shape)
