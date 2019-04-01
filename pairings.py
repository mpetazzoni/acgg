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


BASE_URL = 'https://api.motorsportreg.com/rest/events/{}/assignments'


def get_assignments(org_id, event_id, auth):
    logging.debug('Retrieving assignments for %s event %s', org_id, event_id)

    event_url = BASE_URL.format(event_id)
    headers = {'X-Organization-Id': org_id}
    with requests.get(event_url, auth=auth, headers=headers) as r:
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        items = soup.find_all('assignment')
        logging.debug('Found %d assignments.', len(items))

    def f(*fields):
        return ' '.join([f.text for f in fields]).strip() or None

    assignments = {}
    for item in items:
        assignments[item.id.text] = {
            'attendee': f(item.attendeeid),
            'class': f(item.classshort),
            'group': f(item.group),
            'name': f(item.firstname, item.lastname),
            'car': f(item.make, item.model),
            'instructor': f(item.instructorfirstname,
                            item.instructorlastname),
        }
    return assignments


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

    auth = requests.auth.HTTPBasicAuth(options.username, options.password)
    data = get_assignments(options.org, options.event, auth)
    pprint.pprint(data)
