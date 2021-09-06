import glob
import wx
import wx.html
import os
import os.path
from os import path
from wx.lib.pubsub import pub

class ViewerFrame(wx.Frame):

    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, title="Galaxy Image Visual Inspection Tool")

        panel=ViewerPanel(self)
        self.folderPath = ""
        self.filePath = ""

        self.currentInd = 0
        self.ntotal = 0  # number of total sample
        self.ind = []   # array for index
        self.id = []    # array for galaxy id
        self.mor = []   # array for classification of general morphology
        self.feat = []  # array for classification of features

        self.contentNotSaved = False
        pub.subscribe(self.resizeFrame, 'resize')
        pub.subscribe(self.buttonClicked, 'button clicked')
        pub.subscribe(self.moveToNext, 'next')
        pub.subscribe(self.moveToPrev, 'prev')

        self.initToolbar()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        self.Show()
        self.sizer.Fit(self)
        self.Center()

        self.Bind(wx.EVT_SIZE, self.onResize)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.onKeyDown)


    def initToolbar(self):
        """
        Initialize the toolbar
        :return:
        """
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((16,16))

        open_ico = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, (16,16))
        openTool = self.toolbar.AddSimpleTool(wx.ID_ANY, open_ico, "Open", "Open a new/saved .vis file")

        save_ico = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, (16,16))
        saveTool = self.toolbar.AddSimpleTool(wx.ID_ANY, save_ico, "Save", "Save .vis file")

        save_as_ico = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, (16,16))
        saveAsTool = self.toolbar.AddSimpleTool(wx.ID_ANY, save_as_ico, "Save As", "Save as .vis file")

        help_ico = wx.ArtProvider.GetBitmap(wx.ART_HELP, wx.ART_TOOLBAR, (16, 16))
        helpTool = self.toolbar.AddSimpleTool(wx.ID_ANY, help_ico, "Help", "Help")

        # self.Bind(wx.EVT_MENU, self.onOpenDirectory, openTool)
        self.Bind(wx.EVT_MENU, self.onOpen, openTool)
        self.Bind(wx.EVT_MENU, self.onSave, saveTool)
        self.Bind(wx.EVT_MENU, self.onSaveAs, saveAsTool)
        self.Bind(wx.EVT_MENU, self.onHelp, helpTool)

        self.toolbar.Realize()

    def onOpen(self, event):

        if self.contentNotSaved:
            if wx.MessageBox("Current content has not been saved! Proceed?", "Please confirm",
                wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
                return

        # otherwise ask the user what new file to open
        with wx.FileDialog(self, "Open a \'.vis\' file",
                               wildcard="List files (*.vis)|*.vis",
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            pathname = fileDialog.GetPath()
            self.folderPath = os.path.dirname(pathname)
            self.filePath = pathname
            print(f'{self.folderPath} {self.filePath}')
            try:
                with open(pathname, 'r') as file:
                    self.doLoadData(file)
                    pub.sendMessage('filename', data=self.filePath)
            except IOError:
                wx.LogError("Cannot open file '%s'." % newfile)

    def onSave(self, event):
        pathtxt = self.filePath

        try:
            with open(pathtxt, 'w') as f:
                gal_list_value = ""
                gal_list_value += f'{self.currentInd} \n'
                for j in range(0, len(self.id)):
                    gal_list_value += f'{self.id[j]} {self.mor[j]} {self.feat[j]} \n'
                f.write(gal_list_value)
            self.contentNotSaved = False
        except:
            print("Save failed - Unknown reason")

    def onSaveAs(self, event):

        try:
            dlg = wx.FileDialog(self, "Save to file:", ".", "", "Vis (*.vis)|*.vis", wx.FD_SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                i = dlg.GetFilterIndex()
                if i == 0:  # Text format
                    try:
                        with open(dlg.GetPath(), 'w') as f:
                            gal_list_value = ""
                            gal_list_value += f'{self.currentInd} \n'
                            for j in range(0, len(self.id)):
                                gal_list_value += f'{self.id[j]} {self.mor[j]} {self.feat[j]} \n'
                            f.write(gal_list_value)
                        self.contentNotSaved = False
                        self.filePath = dlg.GetPath()
                        pub.sendMessage('filename', data=self.filePath)

                    except:
                        print("Save failed")
                else:
                    print("Save failed - Use .vis file suffix")
        except:
            print("Save failed - Unknown reason")

    def onClose(self, event):
        if self.contentNotSaved:
            if wx.MessageBox("Current content has not been saved! Proceed?", "Please confirm",
                wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
                return
            else:
                self.Destroy()
        else:
            self.Destroy()

    def onKeyDown(self, event):
        keycode = event.GetKeyCode()
        pub.sendMessage('key down', keycode=keycode)

    def onHelp(self, event):
        helpDlg = HelpDlg(None)
        helpDlg.Show()

    def doLoadData(self, file):
        self.currentInd = 0
        self.ntotal = 0  # number of total sample
        self.ind = []   # array for index
        self.id = []    # array for galaxy id
        self.mor = []   # array for classification of general morphology
        self.feat = []  # array for classification of features

        ind = -1
        start_ind = 0
        for line in file:
            if ind == -1:
                start_ind = int(line)
                ind += 1
                continue
            self.ind.append(ind)
            items = line.split(' ')
            self.id.append(items[0])
            if len(items) > 2:
                self.mor.append(int(items[1]))
                if len(items) > 3:
                    self.feat.append(int(items[2]))
                else:
                    self.feat.append(0)
            else:
                self.mor.append(0)
                self.feat.append(0)
            ind += 1
        self.currentInd = start_ind
        self.ntotal = ind

        print(f"{self.ntotal} {self.currentInd} {self.ind} {self.id} {self.mor} {self.feat}")
        pub.sendMessage('update list', data=self.id, extra1=self.mor, extra2=self.feat, extra3=self.currentInd)
        pub.sendMessage('update panel', data=self.folderPath, extra1=self.id[self.currentInd],
                        extra2=self.mor[self.currentInd], extra3=self.feat[self.currentInd])

    def moveToNext(self, rb1, rb2):
        self.mor[self.currentInd] = rb1
        print(f'moveToNext sendMessage {self.currentInd}')
        self.feat[self.currentInd] = rb2
        if self.currentInd + 1 == self.ntotal:
            if wx.MessageBox('This is the last one.\n Do you want to move to the first one?', 'Info', wx.YES_NO) == wx.YES:
                self.currentInd = 0
            else:
                return
        else:
            self.currentInd += 1
        pub.sendMessage('update list', data=self.id, extra1=self.mor, extra2=self.feat, extra3=self.currentInd)
        pub.sendMessage('update panel', data=self.folderPath, extra1=self.id[self.currentInd],
                        extra2=self.mor[self.currentInd], extra3=self.feat[self.currentInd])
        print(f'moveToNext sendMessage {self.mor[self.currentInd]} {self.feat[self.currentInd]}')

    def moveToPrev(self, rb1, rb2):
        self.mor[self.currentInd] = rb1
        self.feat[self.currentInd] = rb2
        if self.currentInd == 0:
            if wx.MessageBox('This is the first galaxy.\n Do you want to move to the last galaxy?', 'Info', wx.YES_NO) == wx.YES:
                self.currentInd = self.ntotal-1
            else:
                return
        else:
            self.currentInd -= 1
        print(f'{self.currentInd} {self.ntotal}')
        pub.sendMessage('update list', data=self.id, extra1=self.mor, extra2=self.feat, extra3=self.currentInd)
        pub.sendMessage('update panel', data=self.folderPath, extra1=self.id[self.currentInd],
                        extra2=self.mor[self.currentInd], extra3=self.feat[self.currentInd])

    def resizeFrame(self, msg):
        self.sizer.Fit(self)

    def onResize(self, event):
        frame_size = self.GetSize()
        pub.sendMessage('resize panel', data=frame_size)

    def buttonClicked(self, data):
        self.contentNotSaved = True
        if data > 9:
            self.feat[self.currentInd] = data - 10
        else:
            self.mor[self.currentInd] = data
        pub.sendMessage('update list', data=self.id, extra1=self.mor, extra2=self.feat, extra3=self.currentInd)

class HelpDlg(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="Help", size=(600, 600))
        html = wxHTML(self)
        html.SetPage(
            ''
            "<h2> Direction </h2>"
            "<p> 1. Open .vis file in the unzipped directory (e.g., '<unzipped_path>/A3558.vis') by clicking first icon on the toolbar on top of the screen.</p>"
            "<p> 2. Tool will load r-band (scaled following "
            '<a href="https://iopscience.iop.org/article/10.1086/345794/fulltext/"> Jarret+03</a>' 
                "), r-band (scaled following "
            '<a href="https://iopscience.iop.org/article/10.1086/345794/fulltext/"> asinh</a>'
                "), rgb (scaled following "
            '<a href="https://iopscience.iop.org/article/10.1086/345794/fulltext/"> sqrt</a>'
                " and combined u, g, r band as blue, green, and red color, respectively), "
                "rgb (scaled following "
            '<a href="https://iopscience.iop.org/article/10.1086/345794/fulltext/"> Jarret+03</a>'
                "), and GALAPAGOS fitting result.</p>"
            "<p> 3. If there is no corresponding image the blank (black) image will be loaded instead. </p>"
            "<p> 4. You can classify a galaxy by selecting two options of radio buttons titled 'General morphology' and 'Any features?' "
            " (You can select by pressing alphabet or numerical keyboard which is in the parenthesis.) </p>"
            "<p>   4.1 Feature description </p>"
            "<p>     4.1.1 'asymmetric' : not symmetric </p>"
            "<p>     4.1.2 'warped' :  disk is warped </p>"
            "<p>     4.1.3 'fan' : tidal shell looks like a spread-out fan </p>"
            "<p>     4.1.4 'interacting' : multiple galaxies are interacting each other </p>"
            "<p>     4.1.5 'bridge (or with companion)' : stellar streams from multiple galaxies are connected </p>"
            "<p>     4.1.6 'sheet or layer in halo' :  tidal shell or shells layered </p>"
            "<p> 5. A list of 'the galaxy ID' 'General morphology' 'Feature' will be loaded from the '.vis' file on the Text Control box next to the radio button boxes. </p>"
            "<p> 6. Default selection is set as 0 for both categories but you would find different value is assigned as you choose different radio button. </p>" 
            "<p> 7. Once you're done with the classification for a galaxy, you can move on to next or previous one by clicking the button below the radio buttons. "
            "(Again, you can press right/left keyboard instead) </p>"
            "<p> 8. You can save your inspection result by clicking second icon on the toolbar and load later by opening saved '.vis' file. "
            "Or, you can save as different name by clicking the third icon.</p>"
            "<p> </p>"
            "<p> Please email dhkim@kasi.re.kr for more information.</p>"

        )

class wxHTML(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        webbrower.open(link.GetHref())

class ViewerPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        width, height = wx.DisplaySize()

        # information about the current galaxy
        self.id = ""
        self.mor = 0
        self.feat = 0
        self.filename = ""

        # self.photoMaxSize = height - 200
        self.photoMaxSize = height/2 - 150
        pub.subscribe(self.updatePanel, 'update panel')
        pub.subscribe(self.updateList, 'update list')
        pub.subscribe(self.resizePanel, 'resize panel')
        pub.subscribe(self.fileName, 'filename')
        pub.subscribe(self.onKeyDown, 'key down')

        self.layout()

    def layout(self):

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.grid = wx.GridBagSizer(0, 0)
        # grid2 = wx.GridBagSizer(0, 0)
        # grid = wx.FlexGridSizer(0, 0)
        self.grid.SetFlexibleDirection(wx.BOTH)
        self.grid.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)


        self.vSizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.title = wx.StaticText(self, wx.ID_ANY, "")
        font = wx.Font(18, wx.DECORATIVE, wx.SLANT, wx.NORMAL)
        self.title.SetFont(font)
        self.title_fn = wx.StaticText(self, wx.ID_ANY, "")
        font = wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.title_fn.SetFont(font)
        # self.title.SetSize()

        self.gal_list = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)

        font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.NORMAL)

        self.title_img1 = wx.StaticText(self, wx.ID_ANY, "r-band 1")
        self.title_img2 = wx.StaticText(self, wx.ID_ANY, "r-band 2")
        self.title_img3 = wx.StaticText(self, wx.ID_ANY, "ugr composite (low zscale)")
        self.title_img4 = wx.StaticText(self, wx.ID_ANY, "ugr composite (high zscale)")
        self.title_img5 = wx.StaticText(self, wx.ID_ANY, "GALAPAGOS (original r-band, model, subtracted)")
        self.title_img1.SetFont(font)
        self.title_img2.SetFont(font)
        self.title_img3.SetFont(font)
        self.title_img4.SetFont(font)
        self.title_img5.SetFont(font)

        self.img1 = wx.Image(self.photoMaxSize, self.photoMaxSize)  # _r_jar
        self.img2 = wx.Image(self.photoMaxSize, self.photoMaxSize)  #_r_asinh
        self.img3 = wx.Image(self.photoMaxSize, self.photoMaxSize)  # _rgb_sqrt_0_01_big
        self.img4 = wx.Image(self.photoMaxSize, self.photoMaxSize)  # _jar_3
        self.img5 = wx.Image(self.photoMaxSize, self.photoMaxSize * 3)  # _gala

        self.imgCtl1 = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(self.img1))
        self.imgCtl2 = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(self.img2))
        self.imgCtl3 = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(self.img3))
        self.imgCtl4 = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(self.img4))
        self.imgCtl5 = wx.StaticBitmap(self, wx.ID_ANY, wx.Bitmap(self.img5))

        self.grid.Add(self.title_img1, wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.ALL | wx.ALIGN_CENTER, 5)
        self.grid.Add(self.title_img2, wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.ALL | wx.ALIGN_CENTER, 5)
        self.grid.Add(self.title_img3, wx.GBPosition(0, 2), wx.GBSpan(1, 1), wx.ALL | wx.ALIGN_CENTER, 5)
        self.grid.Add(self.title_img4, wx.GBPosition(0, 3), wx.GBSpan(1, 3), wx.ALL | wx.ALIGN_CENTER, 5)
        self.grid.Add(self.title_img5, wx.GBPosition(2, 0), wx.GBSpan(1, 3), wx.ALL | wx.ALIGN_CENTER, 5)

        self.grid.Add(self.imgCtl1, wx.GBPosition(1, 0), wx.GBSpan(1, 1), wx.ALL|wx.EXPAND, 5)
        self.grid.Add(self.imgCtl2, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALL|wx.EXPAND, 5)
        self.grid.Add(self.imgCtl3, wx.GBPosition(1, 2), wx.GBSpan(1, 1), wx.ALL|wx.EXPAND, 5)
        self.grid.Add(self.imgCtl4, wx.GBPosition(1, 3), wx.GBSpan(1, 3), wx.ALL|wx.EXPAND, 5)
        self.grid.Add(self.imgCtl5, wx.GBPosition(3, 0), wx.GBSpan(2, 3), wx.ALL|wx.EXPAND, 5)

        self.grid.Add(self.gal_list, wx.GBPosition(3, 5), wx.GBSpan(2, 1), wx.ALL|wx.EXPAND, 5)

        # Radio Boxes
        radioList1 = ['(E)lliptical', 'S0 (L)enticular', '(S)piral', '(I)rregular', '(N)/A']
        radioList2 = ['none (0)', 'asymmetric (1)', 'warped (2)', 'fan (3)', 'interacting (4)', 'bridge (or with companion) (5)',
                      'sheet or layer in halo (6)', 'jellyfish (7)']

        self.rb1 = wx.RadioBox(self, label="General morphology", choices=radioList1, majorDimension=1,
                         style=wx.RA_SPECIFY_COLS)
        self.rb2 = wx.RadioBox(self, label="Any features?", choices=radioList2, majorDimension=1,
                               style=wx.RA_SPECIFY_COLS)

        self.grid.Add(self.rb1, wx.GBPosition(3, 3), wx.GBSpan(1, 1), wx.ALL, 5)
        self.grid.Add(self.rb2, wx.GBPosition(3, 4), wx.GBSpan(1, 1), wx.ALL, 5)

        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox1, self.rb1)
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox2, self.rb2)

        btn1 = wx.Button(self, label="Previous")
        btn2 = wx.Button(self, label="Next")

        btn1.Bind(wx.EVT_BUTTON, self.onPrevious)
        btn2.Bind(wx.EVT_BUTTON, self.onNext)
        self.grid.Add(btn1, wx.GBPosition(4, 3), wx.GBSpan(1, 1), wx.ALL|wx.CENTER, 5)
        self.grid.Add(btn2, wx.GBPosition(4, 4), wx.GBSpan(1, 1), wx.ALL, 5)

        self.grid.AddGrowableRow(1)
        self.grid.AddGrowableRow(3)

        self.vSizer.Add(self.title_fn, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)
        self.vSizer.Add(self.title, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)
        self.vSizer.Add(self.grid, 0, wx.ALL, 5)
        self.vSizer.Fit(self)
        # hSizer.Add(self.logger)
        self.mainSizer.Add(self.vSizer, 1, 0, 0)
        # self.mainSizer.Add(btnSizer, 0, wx.CENTER)
        self.mainSizer.SetSizeHints(self)
        # self.mainSizer.Fit(self)
        self.SetSizerAndFit(self.mainSizer)

    def resizeImage(self, img):
        # scale the image, preserving the aspect ratio
        W = img.GetWidth()
        H = img.GetHeight()
        # if W > H:
        #     NewW = self.photoMaxSize
        #     NewH = self.photoMaxSize * H / W
        # else:
        #     NewH = self.photoMaxSize
        #     NewW = self.photoMaxSize * W / H
        NewH = self.photoMaxSize
        NewW = self.photoMaxSize * W / H

        return img.Scale(NewW, NewH)

    def loadImage(self, png_dir, id):
        self.img1 = wx.Image(png_dir + '/A3558/' + id + '_r_jar.png', wx.BITMAP_TYPE_ANY)
        self.img2 = wx.Image(png_dir + '/A3558/' + id + '_r_asinh.png', wx.BITMAP_TYPE_ANY)
        if path.exists(png_dir + '/A3558/' + id + '_rgb_sqrt_0_01_big.png'):
            self.img3 = wx.Image(png_dir + '/A3558/' + id + '_rgb_sqrt_0_01_big.png', wx.BITMAP_TYPE_ANY)
        else:
            self.img3 = wx.Image(self.photoMaxSize, self.photoMaxSize)
        # img3 = wx.Image(png_dir + '/' + id + '_rgb_sqrt_0_01_big.png', wx.BITMAP_TYPE_ANY)
        self.img4 = wx.Image(png_dir + '/A3558/' + id + '_rgb_jar_3.png', wx.BITMAP_TYPE_ANY)
        if path.exists(png_dir + '/A3558/' + id + '_gala.png'):
            self.img5 = wx.Image(png_dir + '/A3558/' + id + '_gala.png', wx.BITMAP_TYPE_ANY)
        else:
            self.img5 = wx.Image(self.photoMaxSize, self.photoMaxSize * 3)

        self.imgCtl1.SetBitmap(wx.Bitmap(self.resizeImage(img=self.img1)))
        self.imgCtl2.SetBitmap(wx.Bitmap(self.resizeImage(img=self.img2)))
        self.imgCtl3.SetBitmap(wx.Bitmap(self.resizeImage(img=self.img3)))
        self.imgCtl4.SetBitmap(wx.Bitmap(self.resizeImage(img=self.img4)))
        self.imgCtl5.SetBitmap(wx.Bitmap(self.resizeImage(img=self.img5)))

        print('grid.Fit')
        self.grid.Fit(self)
        print('vSizer.Fit')
        self.vSizer.Fit(self)
        print('mainSizer.Fit')
        self.mainSizer.Fit(self)

        print('Refresh')
        self.Refresh()
        # pub.sendMessage('resize', msg="")
        print(f'loadImage photoMaxSize {self.photoMaxSize}')

    def loadRadio(self, mor, feat):
        self.rb1.Select(mor)
        self.rb2.Select(feat)
        print(f'loadRadio {mor} {feat}')

    def EvtRadioBox1(self, event):
        self.mor = self.rb1.GetSelection()
        pub.sendMessage('button clicked', data=self.mor)

    def EvtRadioBox2(self, event):
        self.feat = self.rb2.GetSelection()
        pub.sendMessage('button clicked', data=self.feat + 10)

    def EvtText(self, event):
        self.logger.AppendText('EvtText: %s\n' % event.GetString())

    def update(self, event):
        self.nextPicture()

    def updateList(self, data, extra1, extra2, extra3):
        gal_list_value = ""
        for i in range(0, len(data)):
            if i == extra3:
                gal_list_value = gal_list_value + '-> '
            gal_list_value = gal_list_value + f'{data[i]} {extra1[i]} {extra2[i]} \n'
        self.gal_list.SetValue(gal_list_value)
        self.title.SetLabel(f'ID:{data[extra3]},   {extra3+1} / {len(data)}')

    def updatePanel(self, data, extra1, extra2, extra3):
        self.id = extra1
        self.mor = extra2
        self.feat = extra3
        self.loadImage(png_dir=data, id=extra1)
        self.loadRadio(extra2, extra3)
        print(f'updatePanel {extra1} {extra2} {extra3}')
        self.Refresh()

    def resizePanel(self, data):
        width = data[0]
        height = data[1]

        self.photoMaxSize = height / 2 - 100

        self.imgCtl1.SetBitmap(wx.Bitmap(self.resizeImage(img=self.img1)))
        self.imgCtl2.SetBitmap(wx.Bitmap(self.resizeImage(img=self.img2)))
        self.imgCtl3.SetBitmap(wx.Bitmap(self.resizeImage(img=self.img3)))
        self.imgCtl4.SetBitmap(wx.Bitmap(self.resizeImage(img=self.img4)))
        self.imgCtl5.SetBitmap(wx.Bitmap(self.resizeImage(img=self.img5)))

        self.grid.Fit(self)
        self.vSizer.Fit(self)
        self.mainSizer.Fit(self)

        self.Refresh()
        print(f'resizePanel photoMaxSize {self.photoMaxSize}')


    def onNext(self, event):
        pub.sendMessage('next', rb1 = self.rb1.GetSelection(), rb2 = self.rb2.GetSelection())

    def onPrevious(self, event):
        pub.sendMessage('prev', rb1 = self.rb1.GetSelection(), rb2 = self.rb2.GetSelection())

    def onKeyDown(self, keycode):

        if keycode == wx.WXK_RIGHT:
            self.onNext(event='')
        elif keycode == wx.WXK_LEFT:
            self.onPrevious(event='')
        elif keycode == ord('E'):
            self.mor = 0
            self.rb1.Select(0)
            pub.sendMessage('button clicked', data=self.mor)
        elif keycode == ord('L'):
            self.mor = 1
            self.rb1.Select(1)
            pub.sendMessage('button clicked', data=self.mor)
        elif keycode == ord('S'):
            self.mor = 2
            self.rb1.Select(2)
            pub.sendMessage('button clicked', data=self.mor)
        elif keycode == ord('I'):
            self.mor = 3
            self.rb1.Select(3)
            pub.sendMessage('button clicked', data=self.mor)
        elif keycode == ord('N'):
            self.mor = 4
            self.rb1.Select(4)
            pub.sendMessage('button clicked', data=self.mor)
        elif keycode == ord('0'):
            self.feat = 0
            self.rb2.Select(0)
            pub.sendMessage('button clicked', data=self.feat + 10)
        elif keycode == ord('1'):
            self.feat = 1
            self.rb2.Select(1)
            pub.sendMessage('button clicked', data=self.feat + 10)
        elif keycode == ord('2'):
            self.feat = 2
            self.rb2.Select(2)
            pub.sendMessage('button clicked', data=self.feat + 10)
        elif keycode == ord('3'):
            self.feat = 3
            self.rb2.Select(3)
            pub.sendMessage('button clicked', data=self.feat + 10)
        elif keycode == ord('4'):
            self.feat = 4
            self.rb2.Select(4)
            pub.sendMessage('button clicked', data=self.feat + 10)
        elif keycode == ord('5'):
            self.feat = 5
            self.rb2.Select(5)
            pub.sendMessage('button clicked', data=self.feat + 10)
        elif keycode == ord('6'):
            self.feat = 6
            self.rb2.Select(6)
            pub.sendMessage('button clicked', data=self.feat + 10)
        elif keycode == ord('7'):
            self.feat = 7
            self.rb2.Select(7)
            pub.sendMessage('button clicked', data=self.feat + 10)

    def fileName(self, data):
        self.filename = data
        self.title_fn.SetLabel(f'{self.filename}')
        self.Refresh()

class App(wx.App):
    def OnInit(self):
        frame = ViewerFrame()
        frame.Show()
        return True

if __name__ == '__main__':
    app = App()
    app.MainLoop()
