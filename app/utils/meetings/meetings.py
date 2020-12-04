import datetime
import os
import pickle
from typing import Dict, List

from apiclient.discovery import build
from django.conf import settings

# SERVICE = build('calendar', 'v3', credentials=settings.GOOGLE_API_CREDENTIALS)
# CALENDAR_ID = SERVICE.calendarList().list().execute()['items'][0]['id']


def delete_google_calendar_event(event_id: str) -> bool:
    try:
        SERVICE.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
    except Exception:
        return False
    return True


def update_google_calendar_event(event_id: str, data: Dict) -> Dict:
    event = SERVICE.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()

    if data.get('start'):
        event['start']['dateTime'] = data.get('start').strftime('%Y-%m-%dT%H:%M:%S')
    if data.get('end'):
        event['end']['dateTime'] = data.get('end').strftime('%Y-%m-%dT%H:%M:%S')

    event['description'] = data.get('description') or event.get('description')
    event['attendees'] = data.get('attendees') or event.get('attendees')
    event['summary'] = data.get('summary') or event.get('summary')
    event['location'] = data.get('location') or event.get('location')

    return SERVICE.events().update(calendarId=CALENDAR_ID, eventId=event_id, body=event).execute()


def create_google_calendar_event(title: str, location: str, description: str,
                                 start_date: datetime.datetime, end_date: datetime.datetime,
                                 organizer_email: str, attendees: List[str] = [], create_meet: bool = True) -> Dict:
    event = {
        'summary': title,
        'location': location,
        'description': description,
        'start': {
            'dateTime': start_date.strftime('%Y-%m-%dT%H:%M:%S'),
            'timeZone': settings.DEFAULT_TIMEZONE,
        },
        'end': {
            'dateTime': end_date.strftime('%Y-%m-%dT%H:%M:%S'),
            'timeZone': settings.DEFAULT_TIMEZONE,
        },
        'attendees': [
                         {'email': attendee} for attendee in attendees
                     ] + [{'email': organizer_email}],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 30},
                {'method': 'popup', 'minutes': 10},
            ],
        },
        'visibility': 'private',
        "conferenceData": {
            "createRequest": {
                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                },
                "requestId": CALENDAR_ID,
            }
        }
    }
    return SERVICE.events().insert(calendarId=CALENDAR_ID, body=event,
                                   conferenceDataVersion=create_meet or None).execute()
