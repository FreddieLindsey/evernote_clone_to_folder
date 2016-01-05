#!/usr/bin/env python
import binascii
import collections
import copy
import getopt
import json
import os
import random
import string
import sys

import shutil
import xmltodict as xmltodict
from evernote.api.client import EvernoteClient, NoteStore
from evernote.edam.limits import constants as Limits
from html5print import HTMLBeautifier

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

# Set a default HTML template
html_template = xmltodict.parse(
    "<?xml version=\"1.0\" encoding=\"UTF-8\"?><html><body></body></html>"
)


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


def add_filename_type(filename, mime):
    if mime == 'image/png':
        filename += '.png'
    elif mime == 'application/json':
        filename += '.json'
    elif mime == 'application/pdf':
        filename += '.pdf'
    return filename


def find_replace_enmedia_hash(enmedia, resources):
    if u'@hash' in enmedia:
        for i in resources:
            hexhash = binascii.hexlify(i.data.bodyHash)
            if hexhash == enmedia[u'@hash']:
                filename = i.attributes.fileName
                if not filename:
                    if u'@alt' in enmedia:
                        filename = enmedia[u'@alt']
                    else:
                        filename = hexhash

                    if i.mime:
                        filename = add_filename_type(filename, i.mime)
                    elif u'@type' in enmedia:
                        filename = add_filename_type(filename, enmedia[
                            u'@type'])

                    i.attributes.fileName = filename
                enmedia[u'@src'] = 'attachments/{filename}'.format(
                    filename=filename)
                del enmedia[u'@hash']
                break


def render_files_in_xml(content, html, resources):
    if isinstance(content, list):
        for i in content:
            render_files_in_xml(i, html, resources)
    elif isinstance(content, collections.OrderedDict):
        for i in content.keys():
            if isinstance(content[i], str) or isinstance(content[i], unicode):
                continue
            elif i == u'en-media':
                find_replace_enmedia_hash(content[i], resources)
                content[u'img'] = content[i]
                del content[i]
            elif i == u'en-note':
                body = html[u'html'][u'body']
                render_files_in_xml(content[i], html, resources)
                div = content[i]
                if u'div' in body.keys():
                    if isinstance(body[u'div'], list):
                        body[u'div'].append(div)
                    else:
                        temp = body[u'div']
                        body[u'div'] = [temp, div]
                else:
                    body[u'div'] = div
            else:
                render_files_in_xml(content[i], html, resources)


def process_enml_media(enml, resources):
    content = xmltodict.parse(enml)
    html = copy.deepcopy(html_template)
    html[u'html'][u'body'] = collections.OrderedDict()
    render_files_in_xml(content, html, resources)
    return xmltodict.unparse(html)


def write(notebook, notes, out_dir=''):
    notebook_name = notebook.name
    for n in notes:
        title = n.title
        dir = '{out_dir}{parent}/{child}'.format(parent=notebook_name,
                                                 child=title, out_dir=out_dir)
        if not os.path.exists(dir):
            os.makedirs(dir)
        enml = n.content
        resources = n.resources
        tags = []
        if n.tagGuids:
            for i in n.tagGuids:
                tag = noteStore.getTag(i)
                tags.append(tag.name)
        with open('{dir}/info.json'.format(dir=dir), 'w') as f:
            info = {"title": title, "created": n.created, "updated": n.updated,
                    "enml?": enml == None, "tags": tags}
            if (resources):
                info['resources_count'] = len(resources)
            f.write(json.dumps(info, indent=2, sort_keys=True))
        if (enml):
            html = process_enml_media(enml, resources)
            with open('{dir}/content.html'.format(dir=dir), 'w') as f:
                html_pretty = HTMLBeautifier.beautify(html, 2)
                f.write(html_pretty)
        if (resources):
            dir = '{dir}/attachments'.format(dir=dir)
            if not os.path.exists(dir):
                os.makedirs(dir)
            for r in resources:
                filename = r.attributes.fileName
                if not filename:
                    filename = ''.join(random.SystemRandom().choice(
                        string.ascii_uppercase + string.digits) for _ in
                                       range(10))
                    if r.mime == 'image/png':
                        filename += '.png'
                    else:
                        print 'Unimplemented option:\t{type}'.format(
                            type=r.mime)
                with open('{dir}/{filename}'.format(dir=dir,
                                                    filename=filename),
                          'wb') as f:
                    f.write(bytearray(r.data.body))
    pass


def backup(settings):
    print 'Backing up...\n'

    for n in noteStore.listNotebooks():
        notes = get_notes_from_notebook(n)
        write(n, notes, settings['out_dir'])


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:v", ["output="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        sys.exit(2)
    settings = {'verbose': False, 'out_dir': ''}
    for o, a in opts:
        if o == "-v":
            settings['verbose'] = True
        elif o in ("-o", "--output"):
            out_dir = str(a) + "/"
            settings['out_dir'] = out_dir
            shutil.rmtree(out_dir, ignore_errors=True)
        else:
            assert False, "unhandled option"
    backup(settings)


if __name__ == '__main__':
    main()
