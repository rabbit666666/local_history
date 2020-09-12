import datetime
import os

import magic
import wx
import wx.lib.mixins.listctrl as listmix
import zstandard
from wx.lib.agw import ultimatelistctrl as ULC

import viewer.ts_util as tu
from table import file_content as fc

class TimeList(ULC.UltimateListCtrl, listmix.ColumnSorterMixin, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, columns, db, code_panel):
        ULC.UltimateListCtrl.__init__(self, parent, -1,
                                      agwStyle=wx.LC_REPORT | wx.BORDER_NONE | wx.LC_HRULES | wx.LC_VRULES |
                                               ULC.ULC_SINGLE_SEL)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, columns)

        self.code_panel = code_panel
        self.mdb = db
        self.zstd_ctx = zstandard.ZstdDecompressor()

        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)

    def GetListCtrl(self):
        return self

    def GetColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def get_display_content(self, file_path, ts, content):
        content = self.zstd_ctx.decompress(content)
        fname, fext = os.path.splitext(file_path)
        fname = os.path.split(fname)[1]
        dt = datetime.datetime.fromtimestamp(ts)
        new_file_name = '{}_{:04}-{:02}-{:01}_{}-{}-{}{}'.format(
            fname, dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, fext)
        mime = magic.from_buffer(content, mime=True)
        main_mime, sub_mime = mime.split('/')
        if main_mime != 'text':
            path = os.path.join('tmp', new_file_name)
            display_text = '无法显示, 请用应用程序打开:{}'.format(path)
            os.makedirs('tmp', exist_ok=True)
            open(path, 'wb').write(content)
        else:
            display_text = content.decode('utf-8')
        return display_text

    def OnItemSelected(self, event):
        self.curRow = event.GetIndex()
        (file_path, time) = self.GetPyData(self.curRow)
        content = fc.get_file_content(self.mdb, file_path, time)
        display_text = self.get_display_content(file_path, time, content)
        self.code_panel.SetInfo(display_text)

    def OnItemDeselected(self, event):
        self.editItemText = None
        event.Skip()

    def GetColumnSorter(self):
        return self.__ColumnSorter

    def autoSort(self):
        self._col = 1
        self.SortItems(self.GetColumnSorter())
        self._col = -1

    def insert_item(self, i, file, time):
        dt_label = tu.format_timestamp(time)
        item = self.InsertStringItem(i, '')
        self.SetStringItem(i, 0, dt_label)
        self.SetPyData(item, (file, time))
        self.SetItemData(item, (time))

    def __ColumnSorter(self, data1, data2):
        ascending = False
        item1 = data1
        item2 = data2
        cmp_value = (item1 > item2) - (item1 < item2)
        if ascending:
            return cmp_value
        else:
            return -cmp_value

class TimesPanel(wx.Panel):
    def __init__(self, parent, db, code_panel):
        wx.Panel.__init__(self, parent)

        self.time_lst = TimeList(self, 1, db, code_panel)

        info = ULC.UltimateListItem()
        info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info._checked = True
        info._format = 0
        info._kind = 1
        info._text = "时间"

        self.time_lst.InsertColumnInfo(0, info)
        self.time_lst.SetColumnWidth(0, 500)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.time_lst, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.index = 0

    def add_new_times(self, file, info_lst):
        self.time_lst.DeleteAllItems()
        i = 0
        for time in info_lst:
            self.time_lst.insert_item(i, file, time)
            i += 1
        self.time_lst.autoSort()
