import os
import wx
import wx.lib.mixins.listctrl as listmix
from wx.lib.agw import ultimatelistctrl as ULC

from pubsub import pub
from table import file_content as fc
import viewer.screen_util as su
import viewer.ts_util as tu
from viewer.expor_dialog import ExportDialog
import viewer.wx_util as wu
import shutil
import zstandard
from viewer.kmp import strrmatch

class FileList(ULC.UltimateListCtrl, listmix.ColumnSorterMixin, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, columns, db, time_panel):
        ULC.UltimateListCtrl.__init__(self, parent, -1,
                                      agwStyle=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_HRULES | wx.LC_VRULES |
                                               ULC.ULC_SINGLE_SEL)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, columns)

        self.time_panel = time_panel
        self.mdb = db

        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)

    def GetListCtrl(self):
        return self

    def GetColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnItemSelected(self, event):
        row = event.GetIndex()
        file = self.GetPyData(row)
        new_times = fc.get_file_update_time(self.mdb, file)
        self.time_panel.add_new_times(file, new_times)

    def OnItemDeselected(self, event):
        event.Skip()

    def GetColumnSorter(self):
        return self.__ColumnSorter

    def autoSort(self):
        self._col = 1
        self.SortItems(self.GetColumnSorter())
        self._col = -1

    def insert_item(self, i, file_name):
        item = self.InsertStringItem(i, '')
        self.SetStringItem(i, 0, file_name)
        self.SetPyData(item, file_name)
        self.SetItemData(item, (file_name))

    def __ColumnSorter(self, data1, data2):
        col = self._col
        ascending = self._colSortFlag[col]
        item1 = data1
        item2 = data2
        cmp_value = (item1 > item2) - (item1 < item2)
        if ascending:
            return cmp_value
        else:
            return -cmp_value

class FilterPanel(wx.Panel):
    def __init__(self, db, file_panel):
        wx.Panel.__init__(self, file_panel, wx.ID_ANY, size=(-1, -1), style=wx.NO_BORDER)

        self.mdb = db
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.filter_text = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_filter, self.filter_text)
        self.go_btn = wx.Button(self, wx.ID_ANY, "Filter", (0, 0), su.dpi_scale((80, -1)))
        self.go_btn.Bind(wx.EVT_BUTTON, self.on_filter)
        self.export_btn = wx.Button(self, wx.ID_ANY, "Export", (0, 0), su.dpi_scale((80, -1)))
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export)

        sizer.Add(self.filter_text, 1, wx.EXPAND | wx.CENTER)
        sizer.Add(self.go_btn, 0, wx.LEFT | wx.CENTER)
        sizer.Add(self.export_btn, 0, wx.LEFT | wx.CENTER)
        self.SetSizer(sizer)

    def on_filter(self, _evt):
        filter = self.filter_text.GetValue()
        pub.sendMessage("on_filter", message=filter)

    def on_export(self, _evt):
        pub.sendMessage("on_export")

class FilesPanel(wx.Panel):
    def __init__(self, parent, db, time_panel):
        wx.Panel.__init__(self, parent)

        self.record_lst = FileList(self, 1, db, time_panel)
        self.filter_panel = FilterPanel(db, self)
        self.mdb = db
        self.filter_text = ""

        info = ULC.UltimateListItem()
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info._checked = True
        info._format = 0
        info._kind = 1
        info._text = "File Path"

        self.record_lst.InsertColumnInfo(0, info)
        self.record_lst.SetColumnWidth(0, 300)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.filter_panel, 0, wx.EXPAND)
        sizer.Add(self.record_lst, 1, wx.EXPAND)
        self.SetSizer(sizer)
        pub.subscribe(self.on_filter, "on_filter")
        pub.subscribe(self.start_export, "on_export")
        pub.subscribe(self.execute_export, "execute_export")

    def on_filter(self, message):
        if message:
            if message[0] != '*':
                message = '*{}'.format(message)
            if message[-1] != '*':
                message = '{}*'.format(message)
        self.filter_text = message
        self.reload_files()

    def get_filtered_file(self):
        file_lst = fc.get_file_names(self.mdb)
        filterd_files = []
        for file in file_lst:
            if not self.filter_text:
                filterd_files.append(file)
            elif strrmatch(file, self.filter_text):
                filterd_files.append(file)
        return filterd_files

    def reload_files(self):
        self.record_lst.DeleteAllItems()
        filterd_files = self.get_filtered_file()
        for i, file in enumerate(filterd_files[:256]):
            self.record_lst.insert_item(i, file)

    def start_export(self):
        filterd_files = self.get_filtered_file()
        files = []
        for f in filterd_files:
            files.append("'{}'".format(f))
        dt_lst = fc.get_file_datetimes(self.mdb, files)
        dlg = ExportDialog(self, dt_lst)
        dlg.ShowModal()

    def execute_export(self, ts):
        dt_label = tu.format_timestamp(ts).replace('/', '').replace(' ', '_').replace(':', '')
        root_dir = os.path.join('export', dt_label)
        if os.path.exists(root_dir):
            shutil.rmtree(root_dir, ignore_errors=True)
        os.makedirs(root_dir, exist_ok=True)
        ctx = zstandard.ZstdDecompressor()
        filterd_files = self.get_filtered_file()
        for f in filterd_files:
            content = fc.get_latest_content(self.mdb, f, ts)
            _, sub_path = os.path.splitdrive(f)
            sub_dir, fname = os.path.split(sub_path)
            dst_dir = os.path.join(root_dir, sub_dir[1:])
            os.makedirs(dst_dir, exist_ok=True)
            dst_file = os.path.join(dst_dir, fname)
            open(dst_file, 'wb').write(ctx.decompress(content))
        msg = 'Export Path: {}'.format(os.path.abspath(root_dir))
        wu.show_dialog('Export Success!', msg)
