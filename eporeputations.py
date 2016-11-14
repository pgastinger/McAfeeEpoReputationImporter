# -*- coding: utf-8 -*-
"""
This simple interface calculates md5/sha1 hashes for multiple files in a chosen directory and send them with a
specified reputation via WEB API to the EPO server

doku
https://kc.mcafee.com/corporate/index?page=content&id=KB81322
https://kc.mcafee.com/corporate/index?page=content&id=PD24810

"""
__author__ = "Peter Gastinger"
__copyright__ = "Copyright 2016, Raiffeisen Informatik GmbH"
__credits__ = [""]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Peter Gastinger"
__email__ = "peter.gastinger@r-it.at"
__status__ = "Development"

# load oder modules
import base64
import datetime
import getpass
import gettext
import hashlib
import json
import os
import os.path
import sys
import configparser
from tkinter import N, W, E, X, SUNKEN, DISABLED, NORMAL, INSERT, END, IntVar, Frame
from tkinter import Tk, OptionMenu, StringVar, messagebox, Button, Label, Text, Checkbutton, Entry
from tkinter.filedialog import askdirectory, asksaveasfile

# tested with Python 3.5.2
try:
    assert sys.version_info >= (3, 5)
except Exception:
    messagebox.showerror("Error", "You need at least Python 3.5 to run this program")
    sys.exit()

# load mcafee_epo, check if requests module available
try:
    import mcafee_epo
except ImportError as exception:
    messagebox.showerror("Error", "Could not load module mcafee_epo: %s" % exception)
    sys.exit()

# REVISION
REVISION = "2016-11-14 12:00:00"

# config file
CONFIGFILE = 'epo.cfg'

# if running as pyinstaller exe
if hasattr(sys, '_MEIPASS'):
    CONFIGFILE = sys._MEIPASS + os.path.sep + 'epo.cfg'

# check if config files exists
if not os.path.isfile(CONFIGFILE):
    messagebox.showerror("Error", "Configuration file %(configfile)s not found" % {"configfile": CONFIGFILE})
    sys.exit()

# read config file
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIGFILE)

# get default language
LOCALEDIR = os.path.dirname(__file__) + os.path.sep + "locale"

# if running as pyinstaller exe
if hasattr(sys, '_MEIPASS'):
    LOCALEDIR = sys._MEIPASS + os.path.sep + "locale"

# install language
try:
    DEFAULT_LANG = gettext.translation('epo', localedir=LOCALEDIR,
                                       languages=[CONFIG.get("DEFAULT", "default_language")])
    DEFAULT_LANG.install()
except FileNotFoundError:
    gettext.bindtextdomain('epo', localedir=LOCALEDIR)
    _ = gettext.gettext

# get EPO credentials from config file
try:
    USERNAME = CONFIG.get("EPO", "username")
    PASSWORD = CONFIG.get("EPO", "password")
    URL = CONFIG.get("EPO", "url")
    TIMEOUT = int(CONFIG.get("EPO", "requests_timeout"))
    HASHESPERREQUEST = int(CONFIG.get("EPO", "hashes_per_request"))
    DEFAULTREPUTATION = CONFIG.get("EPO", "default_reputation")
except configparser.NoOptionError as exception:
    messagebox.showerror("Error", _("Configuration options not found: %(details)s") % {"details": exception})
    sys.exit()
except Exception as exception:
    messagebox.showerror("Error", _("Unknown error reading config file values: %(details)s") % {"details": exception})
    sys.exit()

# reputation values, from
REPUTATIONVALUES = {_("Known trusted"): "99", _("Most likely trusted"): "85", _("Might be trusted"): "70",
                    _("Unknown"): "50", _("Might be malicious"): "30", _("Most likely malicious"): "15",
                    _("Known malicious"): "0"}

# different file types
FILETYPEVALUES = {_("all"): [], _("exe"): ["exe"], _("dll"): ["dll"], _("exe +dll"): ["exe", "dll"]}


class StatusBar(Frame):
    """
    StatusBar class
    """

    def __init__(self, master):
        Frame.__init__(self, master)
        self.label = Label(self, bd=1, relief=SUNKEN, anchor=W)
        self.label.pack(fill=X)

    def set(self, formatval, *args):
        """
        set value
        """
        self.label.config(text=formatval % args)
        self.label.update_idletasks()

    def clear(self):
        """
        clear value
        """
        self.label.config(text="")
        self.label.update_idletasks()


class McAfeeEpoGUI(object):
    """
    gui class
    """

    def __init__(self, master):
        self.master = master
        self.master.title(
            _("McAfee EPO Reputation GUI (Revision: %(revision)s)") % {
                'revision': REVISION})

        self.hashlistdict = list()
        try:
            self.localuser = getpass.getuser()
        except:
            self.localuser = "UNKNOWN"

        self.opendir_button = Button(master, text=_("Open Directory"), command=self.open_directory)
        self.opendir_button.grid(row=0, column=0, sticky=N + W + E)

        self.send_button = Button(master, text=_("Send Files to EPO"), state=DISABLED, command=self.send_to_epo)
        self.send_button.grid(row=1, column=0, sticky=N + W + E)

        self.save_button = Button(master, text=_("Save as CSV"), state=DISABLED, command=self.save_file_as_csv)
        self.save_button.grid(row=2, column=0, sticky=N + W + E)

        self.check_ssl_val = IntVar(master)
        self.check_ssl_val.set(0)
        self.check_ssl = Checkbutton(master, text=_("Verify Server Cert"), variable=self.check_ssl_val)
        self.check_ssl.grid(row=10, column=0, sticky=W)

        self.reputation_label = Label(master, text=_("Reputation:"))
        self.reputation_label.grid(row=4, column=0, sticky=W)

        self.reputation_value = StringVar(master)
        self.reputation_value.set(_("Known trusted"))
        self.reputation_list = OptionMenu(master, self.reputation_value, *sorted(REPUTATIONVALUES.keys()))
        self.reputation_list.grid(row=5, column=0, sticky=W + E)

        self.filetype_label = Label(master, text=_("File-Types:"))
        self.filetype_label.grid(row=6, column=0, sticky=W)

        self.filetype_label_value = StringVar(master)
        self.filetype_label_value.set(_("exe"))
        self.filetype_label_options = OptionMenu(master, self.filetype_label_value, *sorted(FILETYPEVALUES.keys()))
        self.filetype_label_options.grid(row=7, column=0, sticky=W + E)

        self.infofield = Text(master)
        self.infofield.grid(row=0, column=1, rowspan=40, sticky=W + E)
        self.infofield.insert(INSERT, _("McAfee EPO Reputation GUI \n\nfor setting reputation values for all the files "
                                        "in a chosen directory\n\n"))
        self.infofield.insert(INSERT, _('Steps:\n'))
        self.infofield.insert(INSERT, _('1.) Open directory\n'))
        self.infofield.insert(INSERT, _('2.) Optional: change default values\n'))
        self.infofield.insert(INSERT, _('3.) Optional: send file hashes to EPO server\n'))
        self.infofield.insert(INSERT, _('4.) Optional: download hashes as csv file\n\n\n'))
        self.infofield.insert(INSERT, _('Current user: %(username)s\n') % {"username": self.localuser})
        self.infofield.configure(state=DISABLED)

        self.statusbar = StatusBar(master)
        self.statusbar.grid(row=40, column=1, sticky=W + E)
        self.statusbar.set(_("Ready for loading files"))

        self.userurl_label = Label(master, text=_("EPO-URL:"))
        self.userurl_label.grid(row=11, column=0, sticky=W)
        self.userurl_value = Entry(master)
        self.userurl_value.insert(0, URL)
        self.userurl_value.grid(row=12, column=0, sticky=W + E)

        self.username_label = Label(master, text=_("EPO-Username:"))
        self.username_label.grid(row=13, column=0, sticky=W)
        self.username_value = Entry(master)
        self.username_value.insert(0, USERNAME)
        self.username_value.grid(row=14, column=0, sticky=W + E)

        self.userpass_label = Label(master, text=_("EPO-Password:"))
        self.userpass_label.grid(row=15, column=0, sticky=W)
        self.userpass_value = Entry(master, show="*")
        self.userpass_value.insert(0, PASSWORD)
        self.userpass_value.grid(row=16, column=0, sticky=W + E)

    def open_directory(self):
        """
        open directory
        """
        folder = askdirectory(title=_("Choose a directory"))
        if folder:
            self.hashlistdict = list()
            self.get_values(folder, REPUTATIONVALUES.get(self.reputation_value.get(), DEFAULTREPUTATION),
                            FILETYPEVALUES.get(self.filetype_label_value.get(), []))
            self.infofield.configure(state=NORMAL)
            self.infofield.delete("1.0", END)
            if len(self.hashlistdict) == 0:
                messagebox.showerror(_("File"), _("No suitable files found"))
                self.send_button.configure(state=DISABLED)
                self.save_button.configure(state=DISABLED)
                return
            self.infofield.insert(INSERT, _("Number of files found: %(numberoffiles)s\n\n") % {
                "numberoffiles": len(self.hashlistdict)})
            for item in self.hashlistdict:
                md5 = base64.b64decode(item["md5"]).hex()
                sha1 = base64.b64decode(item["sha1"]).hex()
                self.infofield.insert(INSERT, "%s\n\tmd5: %s\n\tsha1:%s\n" % (item["name"], md5, sha1))

            self.infofield.configure(state=DISABLED)
            self.send_button.configure(state=NORMAL)
            self.save_button.configure(state=NORMAL)
            # print(REPUTATIONVALUES.get(self.reputation_value.get(), REPUTATIONDEFAULT))
        else:
            messagebox.showerror(_("Directory"), _("Please pick a directory"))

    def send_to_epo(self):
        """
        send hash values to EPO server
        """
        # get SSL check value
        verifyssl = self.check_ssl_val.get() == 1

        # update reputation value
        reputation = REPUTATIONVALUES.get(self.reputation_value.get(), DEFAULTREPUTATION)
        for item in self.hashlistdict:
            item["reputation"] = reputation

        # get access credentials
        epo_url = self.userurl_value.get()
        epo_username = self.username_value.get()
        epo_password = self.userpass_value.get()

        # check if at least there are values
        if not epo_url or not epo_username or not epo_password:
            messagebox.showerror(_("Error"), _("EPO credentials missing"))
            return

        # create client
        client = mcafee_epo.Client(epo_url, epo_username, epo_password, verify=verifyssl, timeout=TIMEOUT)

        # send hashes
        try:
            # if there are more than HASHESPERREQUEST hashes, send them in multiple requests
            if len(self.hashlistdict) > HASHESPERREQUEST:
                for part in range(0, len(self.hashlistdict), HASHESPERREQUEST):
                    self.statusbar.set(_("Sending hashes %(current)d of %(total)d") %
                                       dict(current=part, total=len(self.hashlistdict)))
                    result = client('tie.setReputations',
                                    params=dict(fileReps=json.dumps(self.hashlistdict[part:part + HASHESPERREQUEST])))
            else:
                result = client('tie.setReputations', params=dict(fileReps=json.dumps(self.hashlistdict)))
        except Exception as exception:
            messagebox.showerror(_("Error"), _("Error sending hashes: %(error)s") % {"error": exception})
        else:
            self.statusbar.set(_("Hashes sent to EPO"))
            if result:
                messagebox.showinfo(_("Success"), _("Hashes successfully sent to EPO"))
            else:
                messagebox.showinfo(_("Error"), _("Something went wrong"))

    def save_file_as_csv(self):
        """
        save file hashes as csv file
        :return:
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        filepointer = asksaveasfile(defaultextension=".csv", initialfile="output_%s.csv" % (timestamp),
                                    filetypes=((_("CSV Files"), "*.csv"),))
        if filepointer:
            filepointer.write(_("filename;comment;md5 hash;sha1 hash;reputation\n"))
            for item in self.hashlistdict:
                md5 = base64.b64decode(item["md5"]).hex()
                sha1 = base64.b64decode(item["sha1"]).hex()
                filepointer.write("%s;%s;%s;%s;%s\n" % (item["name"], item["comment"], md5, sha1, item["reputation"]))
            filepointer.close()
        else:
            messagebox.showerror(_("File"), _("Please specify a filename"))

    def get_values(self, folder, reputation, filetypes):
        """
        get all the files for the folder and set reputation value
        :param folder: chosen by askdirectory popup
        :param reputation: chosen from gui value
        :param filetypes: chosen from gui value
        """
        for root, _, files in os.walk(folder):
            for file in files:
                if len(filetypes) > 0 and file.split(".")[-1] not in filetypes:
                    continue
                fname = root + "/" + file
                filecontent = ""
                with open(fname, 'rb') as filepointer:
                    filecontent = filepointer.read()
                md5 = hashlib.md5(filecontent).digest()
                sha1 = hashlib.sha1(filecontent).digest()
                fdict = {"name": "%s" % file,
                         "comment": "%s %s@WebAPI" % (datetime.datetime.now().strftime("%Y-%m-%d"), self.localuser),
                         "md5": base64.b64encode(md5).decode("utf-8"),
                         "sha1": base64.b64encode(sha1).decode("utf-8"), "reputation": reputation}
                self.hashlistdict.append(fdict)


# main
ROOT = Tk()
ROOT.resizable(width=False, height=False)
McAfeeEpoGUI(ROOT)
ROOT.mainloop()

