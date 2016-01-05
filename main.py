#!/usr/bin/env python
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
notebooks = noteStore.listNotebooks()
print "\nNotebooks:"
for n in notebooks:
    print "\t", n.name

# Get the notes
filter = NoteStore.NoteFilter()
filter.ascending = False

spec = NoteStore.NotesMetadataResultSpec()
spec.includeTitle = True

noteList = noteStore.findNotesMetadata(filter, 0, Limits.EDAM_USER_NOTES_MAX,
                                       spec)

print "\nNotes:"
for n in noteList.notes:
    note = noteStore.getNote(dev_token, n.guid, True, True, True, True)
    print '\t', n.title
    if note.resources:
        for r in note.resources:
            fileName = r.attributes.fileName
            if not fileName:
                fileName = 'None - ' + os.urandom(8)
                if r.mime:
                    if 'image/png' in r.mime:
                        fileName += '.png'
            with open(fileName, 'wb') as f:
                f.write(bytearray(r.data.body))
