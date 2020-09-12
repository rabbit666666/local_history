import wx
import viewer.screen_util as su
import viewer.ts_util as tu
from pubsub import pub

class ExportDialog(wx.Dialog):
    def __init__(self, parent, ts_lst):
        wx.Dialog.__init__(self, parent, title="Please select the deadline", size=su.dpi_scale((-1, -1)), style=wx.DEFAULT_DIALOG_STYLE)

        self.ts_lst = ts_lst
        dt_lst = tu.timestamp_lst_to_date_lst(ts_lst)

        box1 = wx.BoxSizer(wx.HORIZONTAL)
        self.dt_combol = wx.ComboBox(self, wx.ID_ANY, dt_lst[0], (-1, -1), (-1, -1), dt_lst,
                                     wx.CB_DROPDOWN|wx.CB_READONLY)
        box1.Add(self.dt_combol, 1, wx.EXPAND)

        box2 = wx.BoxSizer(wx.HORIZONTAL)
        export_btn = wx.Button(self, wx.ID_OK, "Export", (0,0), su.dpi_scale((80, -1)))
        export_btn.Bind(wx.EVT_BUTTON, self.on_export)

        cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel", (0, 0), su.dpi_scale((80, -1)))

        box2.Add(export_btn, 0, wx.LEFT | wx.CENTER)
        box2.Add(cancel_btn, 0, wx.LEFT | wx.CENTER)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(box1, 0, wx.EXPAND, su.dpi_scale(5))
        sizer.Add(box2, 1, wx.EXPAND, su.dpi_scale(5))
        self.SetSizer(sizer)

        self.Fit()
        self.CenterOnScreen()

    def on_export(self, _evt):
        idx = self.dt_combol.GetCurrentSelection()
        ts = self.ts_lst[idx]
        pub.sendMessage("execute_export", ts=ts)
        self.Close()
