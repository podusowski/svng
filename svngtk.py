import svn
import gtk
import gobject
import pango
import os.path
import vte
import tempfile
import time
import iso8601

class Log(gtk.HBox):
    def __init__(self, branch):
        gtk.HBox.__init__(self)

        self.branch = branch
        self.__create_widget()

    def set_branch(self, branch):
        self.branch = branch
        self.__fill_treeview()

    def __create_widget(self):
        self.__create_treeview()
        self.__create_diffview()

    def __create_treeview(self):
        self.treeview_sw = gtk.ScrolledWindow()

        model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING);
        self.treeview = gtk.TreeView(model)

        renderer_text = gtk.CellRendererText()
        self.treeview.append_column(gtk.TreeViewColumn('Revision', renderer_text, text=0))
        self.treeview.append_column(gtk.TreeViewColumn('Author', renderer_text, text=1))
        self.treeview.append_column(gtk.TreeViewColumn('Date', renderer_text, text=2))
        self.treeview.append_column(gtk.TreeViewColumn('Commit message', renderer_text, text=3))

        selection = self.treeview.get_selection()
        selection.set_mode(gtk.SELECTION_BROWSE)
        selection.connect("changed", self.__selection_changed)

        self.treeview_sw.add(self.treeview)
        self.pack_start(self.treeview_sw)

        self.__fill_treeview()

    def __fill_treeview(self):
        model = self.treeview.get_model()
        model.clear()
        for rev in self.branch.get_revisions():
            it = model.append(None)
            d = iso8601.parse_date(rev.date)
            model.set(it, 0, rev.revision, 1, rev.author, 2, d.strftime("%d %b %H:%M"), 3, rev.msg)

    def __selection_changed(self, selection):
        model, it = selection.get_selected()
        if not it:
            return False

        rev = model.get_value(it, 0)
        self.selected_revision = self.branch.get_revision(rev)
        self.__render_diff(self.diffview.get_buffer(), self.selected_revision)

    def __render_diff(self, text_buffer, revision):
        text_buffer.set_text("")

        text_buffer.insert_with_tags_by_name(text_buffer.get_end_iter(), revision.revision + "\n", 'revision-info1')
        text_buffer.insert_with_tags_by_name(text_buffer.get_end_iter(), revision.author + "\n", 'revision-info2')
        text_buffer.insert_with_tags_by_name(text_buffer.get_end_iter(), revision.msg + "\n", 'revision-info3')

        for line in revision.get_diff_lines():
            if line[0] == '+':
                text_buffer.insert_with_tags_by_name(text_buffer.get_end_iter(), line, 'add')
            elif line[0] == '-':
                text_buffer.insert_with_tags_by_name(text_buffer.get_end_iter(), line, 'remove')
            elif line[0] == '@':
                text_buffer.insert_with_tags_by_name(text_buffer.get_end_iter(), line, 'lines')
            elif line[0] == '=':
                text_buffer.insert_with_tags_by_name(text_buffer.get_end_iter(), line, 'separator')
            elif line[:7] == 'Index: ':
                text_buffer.insert_with_tags_by_name(text_buffer.get_end_iter(), line, 'index')
            elif line[:21] == 'Property changes on: ':
                text_buffer.insert_with_tags_by_name(text_buffer.get_end_iter(), line, 'property')
            else:
                text_buffer.insert(text_buffer.get_end_iter(), line)

    def __create_diffview(self):
        self.diffview_sw = gtk.ScrolledWindow()

        diffview = gtk.TextView()
        self.diffview = diffview

        tb = diffview.get_buffer()
        tag = tb.create_tag('revision-info1', foreground="white", paragraph_background='#819FF7', size=20 * pango.SCALE)
        tag = tb.create_tag('revision-info2', foreground="white", paragraph_background='#819FF7', size=16 * pango.SCALE)
        tag = tb.create_tag('revision-info3', foreground="white", paragraph_background='#5882FA', size=10 * pango.SCALE)
        """tb.create_tag('add', foreground='darkgreen', paragraph_background="#ECF8E0")
        tb.create_tag('remove', foreground='red', paragraph_background="#FBEFEF")"""
        tb.create_tag('add', foreground='darkgreen')
        tb.create_tag('remove', foreground='red')
        tb.create_tag('lines', background="#eee", foreground='orange')
        tb.create_tag('index', paragraph_background="orange", foreground='white')
        tb.create_tag('property', paragraph_background="red", foreground='white')
        tb.create_tag('separator', foreground='orange')

        diffview.modify_font(pango.FontDescription('monospace'))
        diffview.set_editable(False)

        self.diffview_sw.add(diffview)
        self.pack_start(self.diffview_sw, expand=True)

        tb.set_text('<no revision selected>')

class Commit:
    def __init__(self, path):
        self.widget = self.__create_widget()

    def __create_widget(self):
        widget = gtk.HBox(True, 3)

        statusview = self.__create_statusview()
        widget.pack_start(treeview, expand=True)

        return widget

    def __create_statusview(self):
        self.statusview = gtk.TextView()

        text_buffer = self.statusview.get_buffer()

        wc = svn.WorkingCopy('.')
        text_buffer.set_text(wc.status_text)

class RemoteLog(gtk.VBox):
    def __init__(self, branch):
        gtk.VBox.__init__(self, False, 3)

        self.branch = branch

        self.__create_toolbar()
        self.__create_branch_view()
        """self.__create_terminal()"""

    def __go_button_clicked(self, button):
        self.branch = svn.Branch(self.repository_url_entry.get_text())
        self.branchview.set_branch(self.branch)

    def __create_toolbar(self):
        hbox = gtk.HBox()

        """
        button = gtk.Button()
        button.set_label("Merge (dry run)")
        button.connect("clicked", self.__merge_button_clicked)
        hbox.pack_start(button, False, False)

        button = gtk.Button()
        button.set_label("Move by patch")
        button.connect("clicked", self.__patch_button_clicked)
        hbox.pack_start(button, False, False)

        """
        button = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_BUTTON)
        button.set_image(image)
        button.connect("clicked", self.__close_button_clicked)
        hbox.pack_start(button, False, False)

        button = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
        button.set_image(image)
        button.connect("clicked", self.__refresh_button_clicked)
        hbox.pack_start(button, False, False)

        self.pack_start(hbox, False, False)

    def __close_button_clicked(self, button):
        self.closed()

    def __refresh_button_clicked(self, button):
        #self.branchview.resfresh()
        self.branchview.set_branch(self.branch)

    def __merge_button_clicked(self, button):
        self.__merge_from_revision(True)

    def __merge_from_revision(self, dry_run):
        self.terminal_expander.set_expanded(True)
        revision = self.branchview.selected_revision

        svn_bin = "/usr/bin/svn"
        svn_opts = [svn_bin]

        if dry_run:
            svn_opts.append("--dry-run")

        svn_opts.append("merge")
        svn_opts.append("-c")
        svn_opts.append(revision.revision)
        svn_opts.append(self.branchview.branch.url)

        self.terminal.fork_command(svn_bin, svn_opts)

    def __patch_from_revision(self):
        self.terminal_expander.set_expanded(True)
        revision = self.branchview.selected_revision

        f, script_filename = tempfile.mkstemp()
        print(script_filename)
        os.close(f)

        f = open(script_filename, "w")
        f.write("diff_file=`mktemp`\n")
        f.write("svn diff -c " + revision.revision + " > $diff_file\n")
        f.write("echo patch saved in $diff_file")
        f.flush()
        f.close()

        self.terminal.fork_command()
        self.terminal.feed_child("bash " + script_filename + "\n")

    def __patch_button_clicked(self, button):
        self.__patch_from_revision()

    def __create_branch_view(self):
        self.branchview = Log(self.branch)
        self.pack_start(self.branchview)

    def __create_terminal(self):
        self.terminal = vte.Terminal()
        self.terminal_expander = gtk.Expander(label="Terminal")
        self.terminal_expander.add(self.terminal)

        self.terminal.set_scrollback_lines(500)
        self.pack_start(self.terminal_expander, False, False)

class BranchSelect(gtk.VBox):
    def __init__(self, url):
        gtk.VBox.__init__(self)
        self.url = url
        self.path = ""
        self.repository = svn.Repository(url)
        self.__create_toolbar()
        self.__create_entry()
        self.__create_treeview()
        self.__fill_treeview()

    def __create_entry(self):
        self.entry = gtk.Entry()
        self.entry.set_text(self.url)
        self.entry.set_state(gtk.STATE_INSENSITIVE)
        self.pack_start(self.entry, False, False)

    def __create_treeview(self):
        sw = gtk.ScrolledWindow()

        model = gtk.TreeStore(gobject.TYPE_STRING)
        self.treeview = gtk.TreeView(model)

        renderer_text = gtk.CellRendererText()
        self.treeview.append_column(gtk.TreeViewColumn('Item', renderer_text, text=0))

        selection = self.treeview.get_selection()
        selection.set_mode(gtk.SELECTION_BROWSE)

        self.treeview.connect("row-activated", self.__row_activated)

        sw.add(self.treeview)
        self.pack_start(sw)

    def __fill_treeview(self):
        model = self.treeview.get_model()
        model.clear()
        for item in self.repository.ls(self.path):
            it = model.append(None)
            model.set(it, 0, item)

    def __row_activated(self, path, column, param):
        selection = self.treeview.get_selection()
        model, it = selection.get_selected()
        if not it:
            return False

        item = model.get_value(it, 0)
        self.path = self.path + item
        self.entry.set_text(self.url + "/" + self.path)
        self.__fill_treeview()

    def __create_toolbar(self):
        hbox = gtk.HBox()

        button = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)
        button.set_image(image)
        button.connect("clicked", self.__up_button_clicked)
        hbox.pack_start(button, False, False)

        button = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
        button.set_image(image)
        button.connect("clicked", self.__button_clicked)
        hbox.pack_start(button, False, False)

        self.pack_start(hbox, False, False)

    def __up_button_clicked(self, button):
        self.path = os.path.normpath(self.path + "/..")
        if self.path == ".":
            self.path = ""
        self.entry.set_text(self.url + "/" + self.path)
        self.__fill_treeview()

    def __button_clicked(self, button):
        self.branch_opened(self.url + "/" + self.path)


