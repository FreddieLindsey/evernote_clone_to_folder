#!/usr/bin/env python

from evernote.api.client import EvernoteClient
from evernote.edam.notestore import NoteStore
from evernote.edam.limits import constants as Limits
from evernote.edam.type import constants as Types

# Get the dev token
with open('dev_token.txt', 'r') as f:
    dev_token = f.read()

# Authenticate with Evernote
client = EvernoteClient(token=dev_token)
userStore = client.get_user_store()
user = userStore.getUser()
print user.username

# Get the notestore
noteStore = client.get_note_store()
notebooks = noteStore.listNotebooks()
for n in notebooks:
    print n.name

# Get the notes
filter = NoteStore.NoteFilter()
filter.ascending = False

spec = NoteStore.NotesMetadataResultSpec()
spec.includeTitle = True

noteList = noteStore.findNotesMetadata(dev_token, filter, 0,
                                Limits.EDAM_USER_NOTES_MAX, spec)
for n in noteList.notes:
    print n.title
