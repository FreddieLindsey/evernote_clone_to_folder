#!/usr/bin/env python
import json
import os

from evernote.api.client import EvernoteClient, NoteStore
from evernote.edam.limits import constants as Limits
from evernote.edam.type import ttypes as Types

# Get the dev token
with open('dev_token.txt', 'r') as f:
    dev_token = f.read()

# Authenticate with Evernote
client = EvernoteClient(token=dev_token)
userStore = client.get_user_store()
user = userStore.getUser()
print "Username:\t", user.username

# Get the notestore
noteStore = client.get_note_store()


def find_notebook_with_guid(guid):
    nbooks = noteStore.listNotebooks()
    for n in nbooks:
        if n.guid and n.guid is guid:
            return n
    pass


def get_notes_from_notebook(notebook):
    filter = NoteStore.NoteFilter()
    filter.ascending = True
    filter.notebookGuid = notebook.guid

    spec = NoteStore.NotesMetadataResultSpec()
    spec.includeTitle = True

    noteList = noteStore.findNotesMetadata(filter, 0,
                                           Limits.EDAM_USER_NOTES_MAX, spec)

    notes = []
    for n in noteList.notes:
        notes.append(noteStore.getNote(dev_token, n.guid, True, True, True,
                                       True))

    return notes


def write(notebook, notes):
    if not os.path.exists(notebook.name):
        os.mkdir(notebook.name)
    for n in notes:
        dir = '{parent}/{child}'.format(parent=notebook.name, child=n.title)
        if not os.path.exists(dir):
            os.mkdir(dir)
        title = n.title
        enml = n.content
        created = n.created
        updated = n.updated
        resources = n.resources
        with open('{dir}/info.json'.format(dir=dir), 'w') as f:
            info = { "title": title, "created": created, "updated": updated,
                     "enml?": enml == None }
            if (resources):
                info['resources_count'] = len(resources)
            f.write(json.dumps(info, indent=2, sort_keys=True))
        if (enml):
            with open('{dir}/content.html'.format(dir=dir), 'w') as f:
                f.write(enml)
    pass


def backup():
    print 'Backing up...\n'

    for n in noteStore.listNotebooks():
        notes = get_notes_from_notebook(n)
        write(n, notes)


if __name__ == '__main__':
    backup()
