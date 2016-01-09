#!/usr/bin/env python
# -*- coding: utf-8 -*-
import binascii
import collections
import copy
import getopt
import json
import os
import random
import re
import string
import subprocess
import sys

import xmltodict as xmltodict
from evernote.api.client import EvernoteClient, NoteStore
from evernote.edam.error import ttypes as Types
from evernote.edam.limits import constants as Limits
from html5print import HTMLBeautifier


def EDAMError(error):
    if error.errorCode is Types.EDAMErrorCode.RATE_LIMIT_REACHED:
        print 'Rate Limit Exceeded:\tTry again in ', \
            error.rateLimitDuration / 60, ' minutes, ', \
            error.rateLimitDuration % 60, ' seconds.'
        sys.exit(1)
    else:
        print error


def parse_query_string(auth_url):
    uargs = auth_url.split('?')
    vals = {}
    if len(uargs) <= 1:
        raise Exception('Invalid Authorisation URL')
    for kv in uargs[1].split('&'):
        key, value = kv.split('=', 1)
        vals[key] = value
    return vals


def get_os() :
    p = sys.platform
    if (p == 'darwin'):
        return 'Mac OS X'
    elif (p == 'win32'):
        return 'Windows'
    else:
        return 'Linux or other'


def get_token():
    if os.path.exists('token.json'):
        with open('token.json', 'r') as f:
            return json.loads(f.read())
    return None


def get_client() :
    token = get_token()
    if not token:
        print 'Username:\t',
        username = raw_input()
        print 'Password:\t',
        password = raw_input()
        print '\n'
        client = EvernoteClient(
            consumer_key = 'freddieshoreditch-8876',
            consumer_secret = '13801fb7745664f3',
            sandbox = True
        )
        req_token = client.get_request_token('http://localhost')
        os_ = get_os()
        url_ = client.get_authorize_url(req_token)
        if (os_ == 'Mac OS X'):
            command = 'open {}'.format(url_)
        elif (os == 'Windows'):
            print 'Unimplemented for Windows.'
            sys.exit(3)
        elif (os == 'Linux or other'):
            print 'Unimplemented for Linux or other.'
            sys.exit(3)
        else:
            print 'Unimplemented for your operating system.'
            sys.exit(3)
        tries = 0
        exit_code = -1
        while (exit_code != 0 and tries < 5):
            tries += 1
            exit_code = subprocess.call(command, shell=True)
        if exit_code != 0:
            print 'Could not open authorisation url, please open it manually:',
            print url_
        print '\n\nPASTE the URL after logging in:\t'
        result = raw_input()
        vals = parse_query_string(result)
        token = client.get_access_token(
            req_token['oauth_token'],
            req_token['oauth_token_secret'],
            vals['oauth_verifier']
        )
        with open('token.json', 'w') as f:
            f.write(json.dumps(auth_token))
    return EvernoteClient(token=token), token


# Global variables
try:
    # Authenticate with Evernote
    client, token = get_client()
    userStore = client.get_user_store()

    # Get the notestore
    noteStore = client.get_note_store()

    notebooks = noteStore.listNotebooks()
except Types.EDAMSystemException as e:
    EDAMError(e)

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
    spec.includeUpdated = True

    noteList = noteStore.findNotesMetadata(filter, 0,
                                           Limits.EDAM_USER_NOTES_MAX, spec)
    while noteList.totalNotes > len(noteList.notes):
        appendNoteList = noteStore.findNotesMetadata(filter,
                                                     len(noteList.notes),
                                                     Limits.EDAM_USER_NOTES_MAX,
                                                     spec)
        noteList.notes += appendNoteList.notes

    return noteList.notes


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
                enmedia[u'@src'] = enmedia[u'@src'].decode('utf8')
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
    return xmltodict.unparse(html, encoding='utf8')


def note_has_updated(n, dir):
    if not os.path.exists(dir):
        return True
    elif not os.path.exists('{0}/info.json'.format(dir)):
        return True
    else:
        try:
            with open('{0}/info.json'.format(dir), 'r') as f:
                data = json.loads(f.read(), encoding='utf8')
                if u'updated' in data.keys():
                    return n.updated > data[u'updated'] or \
                           (u'success' not in data.keys())
                return True
        except:
            return True


def validate_filename(title):
    if title is not None:
        title = re.sub(r'[\/\\\n\\\r\\\t]', r' ', title)
    return title


def validate_filenames(data):
    if data is None:
        return
    for d in data:
        if hasattr(d, 'attributes'):
            d.attributes.fileName = validate_filename(d.attributes.fileName)


def write(notebook, notes, out_dir=''):
    notebook_name = notebook.name
    count = 0
    totalCount = len(notes)
    for n in notes:
        count += 1
        title = n.title
        print '\t\t{count} of {total}:\t{note}'.format(count=count,
                                                       total=totalCount,
                                                       note=title)
        title = validate_filename(title)
        dir = '{out_dir}{parent}/{child}'.format(parent=notebook_name,
                                                 child=title, out_dir=out_dir)
        note_updated = note_has_updated(n, dir)
        if note_updated is False:
            continue
        if not os.path.exists(dir):
            os.makedirs(dir)
        n = noteStore.getNote(token, n.guid, True, True, False, False)
        enml = n.content
        validate_filenames(n.resources)
        resources = n.resources
        tags = []
        if n.tagGuids:
            for i in n.tagGuids:
                tag = noteStore.getTag(i)
                tags.append(tag.name)

        # Print information about the note to file
        info = {"title": title, "created": n.created, "updated": n.updated,
                "enml?": enml != None, "tags": tags}
        outinfo = '{dir}/info.json'.format(dir=dir)
        if (resources):
            info['resources_count'] = len(resources)
        with open(outinfo, 'w') as f:
            f.write(json.dumps(info, indent=2, sort_keys=True))

        if (enml):
            html = process_enml_media(enml, resources)
            html_pretty = HTMLBeautifier.beautify(html, 2)
            with open('{dir}/content.html'.format(dir=dir), 'w') as f:
                f.write(html_pretty.encode('utf8'))
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
                    filename = add_filename_type(filename, r.mime)
                with open('{dir}/{filename}'.format(dir=dir,
                                                    filename=filename),
                          'wb') as f:
                    f.write(bytearray(r.data.body))
        info['success'] = True
        with open(outinfo, 'w') as f:
            out = json.dumps(info, indent=2, sort_keys=True)
            f.write(out.encode('utf8'))


def backup(settings):
    try:
        user = userStore.getUser()
        print 'Backing up for user {0}...\n'.format(user.username)
        print 'Notebooks backed up:'
        for n in notebooks:
            print '\r\t{name}'.format(name=n.name)
            notes = get_notes_from_notebook(n)
            write(n, notes, settings['out_dir'])
            print
    except Types.EDAMSystemException as e:
        EDAMError(e)


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
        else:
            assert False, "unhandled option"
    print 'Welcome to the cloning CLI for Evernote.\n' \
          'Use this program to clone and backup your Evernote notes and files.\n'
    backup(settings)


if __name__ == '__main__':
    main()
