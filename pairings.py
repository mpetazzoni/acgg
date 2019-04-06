#!/usr/bin/env python

# Utility for extracting pairing information from a MotorSportReg event and
# generating a printable pairing sheet.
#
# Copyright (C) 2019 AudiClub Golden Gate <theboard@audiclubgoldengate.org>

import argparse
from bs4 import BeautifulSoup
import logging
import pprint
import requests
import sys


ATTENDEES_URL = 'https://api.motorsportreg.com/rest/events/{}/attendees'
ASSIGNMENTS_URL = 'https://api.motorsportreg.com/rest/events/{}/assignments'


class Event(object):

    def __init__(self, session, event_id):
        self._event_id = event_id
        self._attendees = {}
        self._assignments = {}

        def f(*fields):
            return ' '.join([f.text for f in fields]).strip() or None

        def member_id(field):
            uri = f(field)
            return uri.split('/')[2] if uri else None

        logging.debug('Retrieving attendees for event %s', event_id)
        with session.get(ATTENDEES_URL.format(event_id)) as r:
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.find_all('attendee')
            logging.debug('Found %d attendees.', len(items))

        for item in items:
            self._attendees[member_id(item.memberuri)] = {
                'name': f(item.firstname, item.lastname),
                'status': f(item.status),
                'email': f(item.email),
                'first_timer': f(item.isfirstevent) == 'true',
            }

        logging.debug('Retrieving assignments for event %s', event_id)
        with session.get(ASSIGNMENTS_URL.format(event_id)) as r:
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.find_all('assignment')
            logging.debug('Found %d assignments.', len(items))

        for item in items:
            member = member_id(item.memberuri)
            instructor = member_id(item.instructoruri)
            if instructor and instructor not in self._attendees:
                logging.error(
                    'Cannot find instructor %s (%s) in attendees!',
                    instructor,
                    f(item.instructorfirstname, item.instructorlastname))

            self._assignments[item.id.text] = {
                'attendee': self._attendees[member],
                'group': f(item.groupshort),
                'class': f(item.classshort),
                'modifier': f(item.classmodifier),
                'car': f(item.make, item.model),
                'instructor': self._attendees.get(instructor),
            }

    @property
    def event_id(self):
        return self._event_id

    def _find(self, predicate):
        return filter(predicate, self._assignments.values())

    def get_group(self, group):
        return list(self._find(lambda x: x['group'] == group))

    def get_instructor_students(self, instructor):
        pass

    def render(self):
        print(self._assignments)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--org', help='Organization ID')
    parser.add_argument('-e', '--event', help='Event ID')
    parser.add_argument('-u', '--username', help='MotorSportReg username')
    parser.add_argument('-p', '--password', help='MotorSportReg password')
    parser.add_argument('-v', '--verbose', help='Verbose logging',
                        default=logging.INFO, action='store_const',
                        const=logging.DEBUG, dest='loglevel')
    options = parser.parse_args()

    logging.basicConfig(stream=sys.stderr, level=options.loglevel)

    session = requests.Session()
    session.auth = requests.auth.HTTPBasicAuth(options.username, options.password)
    session.headers = {'X-Organization-Id': options.org}
    event = Event(session, options.event)
    pprint.pprint(event.get_group('A'))
    pprint.pprint(event.get_group('B'))
    pprint.pprint(event.get_group('C'))
    pprint.pprint(event.get_group('D'))
