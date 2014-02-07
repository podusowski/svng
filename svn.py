import xml.dom.minidom
import os
import sys

def xml_get_text(xml_node):
    ret = ""
    if len(xml_node.childNodes) > 0:
        ret = xml_node.childNodes[0].nodeValue
    return ret

class Revision:
    def __init__(self, branch_url, revision, author, msg, date, paths):
        self.branch_url = branch_url
        self.revision = revision
        self.author   = author
        #self.nice_author = finger("127.0.0.1", author)
        self.msg      = msg
        self.date     = date
        self.paths    = paths
        self.short_summary = date + " " + author + ": " + msg

    def show_diff(self):
        os.system("svn diff -c " + self.revision + " " + self.branch_url + " > ~/.svntools.diff ; vim -R ~/.svntools.diff ; rm ~/.svntools.diff")

    def get_diff_text(self):
        fout = os.popen("svn diff -c " + self.revision + " " + self.branch_url)
        return fout.read()

    def get_diff_lines(self):
        fout = os.popen("svn diff -c " + self.revision + " " + self.branch_url)
        return fout.readlines()

    def get_paths(self):
        pass

    def pick(self):
        pass

class Branch:
    def __init__(self, url):
        self.url = url
        self.name = "branch"
        self.revisions = []

    def get_revisions(self):
        self.__fetch_if_needed()
        return self.revisions

    def get_revision(self, number):
        self.__fetch_if_needed()
        for r in self.revisions:
            if r.revision == number:
                return r

    def __fetch_if_needed(self):
        if len(self.revisions) == 0:
            self.__fetch()

    def __fetch(self):
        fout = os.popen("svn log -v --xml --stop-on-copy -l300 " + self.url)
        xml_log = xml.dom.minidom.parse(fout)
        self.revisions = []

        for xml_log_entry in xml_log.getElementsByTagName("logentry"):
            revision = "r" + str(xml_log_entry.getAttribute("revision"))
            author   = xml_log_entry.getElementsByTagName("author")[0].childNodes[0].nodeValue

            if len(xml_log_entry.getElementsByTagName("msg")[0].childNodes) > 0:
                msg = xml_log_entry.getElementsByTagName("msg")[0].childNodes[0].nodeValue
            else:
                msg = "<no commit message>"

            date = xml_log_entry.getElementsByTagName("date")[0].childNodes[0].nodeValue

            r = Revision(self.url, revision, author, msg, date, [])
            self.revisions.append(r)

class Info:
    def __init__(self, path):
        self.path = path
        fout = os.popen("svn info --xml " + self.path)
        xml_info = xml.dom.minidom.parse(fout)
        self.url = xml_get_text(xml_info.getElementsByTagName("url")[0])
        self.root = xml_get_text(xml_info.getElementsByTagName("root")[0])

class WorkingCopy:
    def __init__(self, path):
        self.path = path
        fout = os.popen("svn st --xml " + self.path)
        self.status_text = fout.read()

class Repository:
    def __init__(self, url):
        self.url = url

    def ls(self, path):
        fout = os.popen("svn ls " + self.url + "/" + path) 
        ret = []
        for line in fout.readlines():
            ret.append(line[:-1])

        return ret

