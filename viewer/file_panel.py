import os
import wx
import json
import timestring
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
import multiprocessing as mp
import engine.listutil as lu

def convert_filter_text(filter_text):
    filter_lst = []
    if filter_text:
        for text in filter_text.split(';'):
            if not text:
                continue
            if text[0] != '*':
                text = '*{}'.format(text)
            if text[-1] != '*':
                text = '{}*'.format(text)
            filter_lst.append(text)
    return filter_lst

class FilterMessage:
    def __init__(self):
        self.include_lst = []
        self.exclude_lst = []
        self.date_from = -1
        self.date_to = -1

    def __str__(self):
        msg = {
            'include': self.include_lst,
            'exclude': self.exclude_lst,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return json.dumps(msg)

    @staticmethod
    def from_json_string(json_str):
        msg = json.loads(json_str)
        filter_msg = FilterMessage()
        filter_msg.include_lst = msg['include']
        filter_msg.exclude_lst = msg['exclude']
        filter_msg.date_from = msg['date_from']
        filter_msg.date_to = msg['date_to']
        return filter_msg

class FilterPanel(wx.Panel):
    INCLUDE_FILTER_BLANK_TEXT = "Include All"
    EXCLUDE_FILTER_BLANK_TEXT = "Exclude None"
    def __init__(self, db, file_panel):
        wx.Panel.__init__(self, file_panel, wx.ID_ANY, size=(-1, -1), style=wx.NO_BORDER)

        self.mdb = db
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.include_filter_text = wx.TextCtrl(self, -1, self.INCLUDE_FILTER_BLANK_TEXT, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_filter, self.include_filter_text)
        self.exclude_filter_text = wx.TextCtrl(self, -1, self.EXCLUDE_FILTER_BLANK_TEXT, style=wx.TE_PROCESS_ENTER)
        self.go_btn = wx.Button(self, wx.ID_ANY, "Filter", (0, 0), su.dpi_scale((80, -1)))
        self.go_btn.Bind(wx.EVT_BUTTON, self.on_filter)
        self.export_btn = wx.Button(self, wx.ID_ANY, "Export", (0, 0), su.dpi_scale((80, -1)))
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export)

        sizer2.Add(self.go_btn, 1, wx.LEFT | wx.CENTER)
        sizer2.Add(self.export_btn, 1, wx.LEFT | wx.CENTER)

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.cal_from_text = wx.TextCtrl(self, wx.ID_ANY, "Date From(yyyy-mm-dd)", (0, 0), su.dpi_scale((80, -1)))
        self.cal_to_text = wx.TextCtrl(self, wx.ID_ANY, "Date To(yyyy-mm-dd)", (0, 0), su.dpi_scale((80, -1)))

        sizer3.Add(self.cal_from_text, 1, wx.EXPAND)
        sizer3.Add(self.cal_to_text, 1, wx.EXPAND)

        sizer.Add(sizer2, 1, wx.EXPAND)
        sizer.Add(self.include_filter_text, 1, wx.EXPAND | wx.CENTER)
        sizer.Add(self.exclude_filter_text, 1, wx.EXPAND | wx.CENTER)
        sizer.Add(sizer3, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def date_to_timestamp(self, date):
        ts = -1
        try:
            ts = timestring.Date(date, '%y-%m-%d').to_unixtime()
            ts = int(ts)
        except:
            pass
        return ts

    def get_filter_text(self):
        include_text = ''
        exclude_text = ''
        if self.include_filter_text.GetValue() != self.INCLUDE_FILTER_BLANK_TEXT:
            include_text = self.include_filter_text.GetValue()
        if self.exclude_filter_text.GetValue() != self.EXCLUDE_FILTER_BLANK_TEXT:
            exclude_text = self.exclude_filter_text.GetValue()
        include_lst = convert_filter_text(include_text)
        exclude_lst = convert_filter_text(exclude_text)
        return include_lst, exclude_lst

    def on_filter(self, _evt):
        include_filter, exclude_filter = self.get_filter_text()
        date_from = self.cal_from_text.GetValue()
        date_to = self.cal_to_text.GetValue()
        ts1 = self.date_to_timestamp(date_from)
        ts2 = self.date_to_timestamp(date_to)
        msg = FilterMessage()
        msg.include_lst = include_filter
        msg.exclude_lst = exclude_filter
        msg.date_from = ts1
        msg.date_to = ts2
        pub.sendMessage("on_filter", message=str(msg))

    def on_export(self, _evt):
        pub.sendMessage("on_export")

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

class FilesPanel(wx.Panel):
    def __init__(self, parent, db, time_panel):
        wx.Panel.__init__(self, parent)

        self.record_lst = FileList(self, 1, db, time_panel)
        self.filter_panel = FilterPanel(db, self)
        self.mdb = db
        self.filter_msg = FilterMessage()

        info = ULC.UltimateListItem()
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info._checked = True
        info._format = 0
        info._kind = 1
        info._text = "File Path"
        self.num_proc = max(os.cpu_count() - 1, 1)
        self.pool = mp.Pool(processes=self.num_proc)

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
        self.filter_msg = FilterMessage.from_json_string(message)
        self.reload_files()

    @staticmethod
    def is_match_filter(file, filter_lst):
        if not filter_lst:
            return False
        match = False
        for filter_text in filter_lst:
            if strrmatch(file, filter_text):
                if file.find('.py') != -1:
                    print(file, filter_text, ', is matched')
                match = True
                break
        return match

    @staticmethod
    def filter_file(args):
        file_lst, include_filters, exclude_filters = args
        filterd_files = []
        for file in file_lst:
            if FilesPanel.is_match_filter(file, exclude_filters):
                continue
            if not include_filters:
                filterd_files.append(file)
            elif FilesPanel.is_match_filter(file, include_filters):
                filterd_files.append(file)
        return filterd_files

    def get_filtered_file(self):
        file_lst = fc.get_file_names(self.mdb, self.filter_msg.date_from, self.filter_msg.date_to)
        args = []
        for fs in lu.chunk_to_n_part(file_lst, self.num_proc):
            args.append((fs, self.filter_msg.include_lst, self.filter_msg.exclude_lst))
        filterd_files = []
        rst = self.pool.map(FilesPanel.filter_file, args)
        for files in rst:
            filterd_files.extend(files)
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
            if not content:
                assert False, '{} is empty'.format(dst_file)
            else:
                open(dst_file, 'wb').write(ctx.decompress(content))
        msg = 'Export Path: {}'.format(os.path.abspath(root_dir))
        wu.show_dialog('Export Success!', msg)
