#!/usr/bin/env python

from evernote.api.client import EvernoteClient

# Get the dev token
with open('dev_token.txt', 'r') as f:
    dev_token = f.read()

# Authenticate with Evernote
client = EvernoteClient(token=dev_token)
userStore = client.get_user_store()
user = userStore.getUser()
print user.username

# Get the notestore
noteStore = client.get_note_store()
notebooks = noteStore.listNotebooks()
for n in notebooks:
    print n.name

# Create a new note
noteStore = client.get_note_store()
note = Types.Note()
note.title = "I'm a test note!"
note.content = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
note.content += '<en-note>Hello, world!</en-note>'
note = noteStore.createNote(note)

# Create a new notebook
noteStore = client.get_note_store()
notebook = Types.Notebook()
notebook.name = "My Notebook"
notebook = noteStore.createNotebook(notebook)
print notebook.guid
