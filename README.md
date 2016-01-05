# Clone Evernote to folder

A Python-based CLI tool for cloning your Evernote account locally.

N.B. - It takes a long time to do, regardless of connection speed!

###Prerequisites

This tool has been written on a Mac, and should work with similar UNIX-based machines (Linux).

You will need a developer token from Evernote for your account. You can get this from [Evernote](https://www.evernote.com/api/DeveloperToken.action) - please save it in a file 'token.txt' in the root folder of the repository that you clone

Prior to running, there are some dependencies that the application has. To install these, run the following commands:

```
pip install -r requirements.txt
```

N.B. You may wish to use `virtualenv` to create a virtual environment in which you can use the tool. Otherwise, you may have to use `sudo` to install the prerequisites system-wide.

###Usage

To use the program, the following options are available:

- Output folder (`-o`, `--output=`)

For general use:

```
./main.py -o evernote_backup
```

Where `evernote_backup` is the folder in which the backup will be made. Note that it does not currently sychronise from Evernote, but downloads and overwrites whatever is currently in that folder should it already exist. PLEASE USE WITH CAUTION.
