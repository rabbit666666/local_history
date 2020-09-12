import wx
import wx.aui

from viewer import panel_frame
from viewer.ProportionalSplitter import ProportionalSplitter
from engine import db_util as du
from viewer.file_panel import FilesPanel
from table import file_content as fc
from viewer.time_panel import TimesPanel

class MainPanel(wx.Panel):
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent)

        self.mdb = du.init_db()
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.splitter2 = ProportionalSplitter(self, -1, 0.2)
        self.splitter1 = ProportionalSplitter(self.splitter2, -1, 0.1)

        self.code_panel = panel_frame.CodePanel(self.splitter1)
        self.time_list = TimesPanel(self.splitter1, self.mdb, self.code_panel)
        self.file_list = FilesPanel(self.splitter2, self.mdb, self.time_list)

        self.splitter1.SplitVertically(self.time_list, self.code_panel)
        self.splitter2.SplitVertically(self.file_list, self.splitter1)

        sizer.Add(self.splitter2, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.file_list.SetFocus()
        self.reload()

    def reload(self):
        self.file_list.reload_files()

class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "LocalHistoryViewer", size=(600, 400))
        self.Bind(wx.EVT_CLOSE, self.on_close)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_panel = MainPanel(self)
        sizer.Add(self.main_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.create_menu()
        self.Layout()
        self.Maximize()
        self.Show()

    def create_menu(self):
        menu_bar = wx.MenuBar()

        menu = wx.Menu()
        item = menu.Append(-1, "重新加载\tCtrl-R", "New File")
        self.Bind(wx.EVT_MENU, self.on_reload, item)
        menu_bar.Append(menu, "选项")

        self.SetMenuBar(menu_bar)

    def on_close(self, _evt):
        self.Destroy()

    def on_reload(self, _evt):
        self.main_panel.reload()
