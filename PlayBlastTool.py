import os
import sys
import re
import shutil
import datetime
import subprocess
import pymel.core as pm

from PySide2 import QtWidgets, QtGui, QtCore


class PlayBlastTool(QtWidgets.QMainWindow):
    def __init__(self, parent=None, widthHeight=(320,400), format='image', compression='jpg', percent=100, quality=100):
        super(PlayBlastTool, self).__init__(parent)

        # Values
        self.widthHeight = (320, 720)
        self.format = format
        self.compression = compression
        self.percent = percent
        self.quality = quality
        self.output_dir = r'C:\Temp\{tFolder}\Playblast'.format(tFolder=self.get_date_time())
        self.make_dir(self.output_dir)

        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QtWidgets.QVBoxLayout(centralWidget)

        self.setWindowTitle('PlayBlastTool -- 1.0.0')

        # Grid Layout
        self.gridLayout = QtWidgets.QGridLayout()

        self.singleFile_radioBtn = QtWidgets.QRadioButton('Single File')
        self.multiFile_radioBtn = QtWidgets.QRadioButton('Multiple File')

        self.singleFile_radioBtn.toggled.connect(lambda: self.processFn(self.singleFile_radioBtn))
        self.multiFile_radioBtn.toggled.connect(lambda: self.processFn(self.multiFile_radioBtn))

        # adding to GridLayout
        self.gridLayout.addWidget(self.singleFile_radioBtn, 0, 0)
        self.gridLayout.addWidget(self.multiFile_radioBtn, 0, 1)

        mainLayout.addLayout(self.gridLayout)

        # Browse Label
        self.browse_lbl = QtWidgets.QLabel('Browse : ')

        # Browse LineEdit
        self.browse_lineEdit = QtWidgets.QLineEdit()

        # Browse Push Button
        self.browse_pushBtn = QtWidgets.QPushButton('...')

        # search Line Edit
        self.search_lineEdit = QtWidgets.QLineEdit()
        self.search_lineEdit.setPlaceholderText("Search File...")

        # Shot List Widget
        self.shots_ListWidget = QtWidgets.QListWidget()
        self.shots_ListWidget.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        self.shots_ListWidget.setStyleSheet(''' font-size: 13px; ''')
        self.shots_ListWidget.setAlternatingRowColors(True)

        # Submit Button
        self.submit_pushBtn = QtWidgets.QPushButton('SUBMIT')

        self.search_lineEdit.hide()
        self.shots_ListWidget.hide()

        # Button Connections
        self.browse_pushBtn.clicked.connect(self.browseFN)
        self.search_lineEdit.textChanged.connect(self.searchFN)
        self.submit_pushBtn.clicked.connect(self.submitBtnFN)

    def processFn(self, button):
        """
            Process of selecting which mode has to playblast
        param button: button widget
        return: None
        """

        self.gridLayout.addWidget(self.browse_lbl, 2, 0)
        self.gridLayout.addWidget(self.browse_lineEdit, 2, 1)
        self.gridLayout.addWidget(self.browse_pushBtn, 2, 2)
        self.gridLayout.addWidget(self.search_lineEdit, 3, 0, 3, 3)
        self.gridLayout.addWidget(self.shots_ListWidget, 6, 0, 4, 3)

        if button.text() == 'Single File':
            if button.isChecked() == True:
                self.search_lineEdit.hide()
                self.shots_ListWidget.hide()
                self.submit_pushBtn.hide()
                self.browse_lineEdit.setPlaceholderText("Browse For Maya File...")
                self.resize(300, 50)

        if button.text() == 'Multiple File':
            if button.isChecked() == True:
                self.search_lineEdit.show()
                self.shots_ListWidget.show()
                self.submit_pushBtn.show()
                self.browse_lineEdit.setPlaceholderText("Browse For Folder...")
                self.gridLayout.addWidget(self.submit_pushBtn, 10, 0, 2, 3)
                self.resize(500, 300)

    def browseFN(self):
        """
            Process of browsing files
        :return: None
        """

        self.batchFlag = False
        self.shots_ListWidget.clear()
        fileDialog = QtWidgets.QFileDialog()
        if self.singleFile_radioBtn.isChecked():
            self.filesPath = fileDialog.getOpenFileName(None, "Browse For Maya File", "", "*.ma")[0]
        else:
            self.batchFlag = True
            self.filesPath = fileDialog.getExistingDirectory(self, "Browse For Folder")

        self.browse_lineEdit.setText(str(self.filesPath))
        if self.batchFlag:
            self.multipleShotsFN(self.filesPath)
        else:
            self.makePlayblastFN(self.filesPath)

    def multipleShotsFN(self, folderPath):
        """
            Process of getting maya files in the selected folder and adding files in listwidget
        param folderPath: Folder path
        return: None
        """
        self.mayaFilesList = ['{}/{}'.format(root, f) for root, dirs, files in os.walk(folderPath) for f in files
                              if f.endswith(('.ma', '.mb'))]
        self.shots_ListWidget.addItems(self.mayaFilesList)

    def submitBtnFN(self):
        """
            Process of creating playblast
        return: None
        """

        selectionFilesLst = [str(e.text()) for e in self.shots_ListWidget.selectedItems()]
        if not selectionFilesLst:
            QtWidgets.QMessageBox.warning(self, 'Warning!!!', 'Select files and try again...')
            return

        for eachMayaFile in selectionFilesLst:
            self.makePlayblastFN(eachMayaFile)
        QtWidgets.QMessageBox.information(self, 'Success!!!', 'Successfully Created...')

    def makePlayblastFN(self, filePath):
        """
            Process of making playblast
        param filePath: maya file path
        return: None
        """

        pm.openFile(filePath, f=1, pmt=False)
        pm.refresh(su=1)
        self.starframe = pm.playbackOptions(q=1, min=1)
        self.endframe = pm.playbackOptions(q=1, max=1)
        self.playblast(self.get_all_cameras())
        self.compile_Mov(filePath)
        pm.refresh(su=0)
        pm.newFile(f=1)

    def playblast(self, cameras):
        """
            Process of creating playblast, create images
        param cameras: cameras lis
        return: Jpg output
        """

        all_outputs = []
        for camera in cameras:
            pm.lookThru(camera)
            print camera.getParent().name()
            output_img = self.make_playblast(camera.getParent().name())
            all_outputs.append(os.path.dirname(output_img))
        return all_outputs

    def make_playblast(self, camera_name):
        """
            Process of creating playblast
        param camera_name: camera name
        return: playblst directory
        """

        playblast_path = pm.playblast(
                            widthHeight=self.widthHeight,
                            format=self.format,
                            fo=1,
                            filename= '{}\{}\{}\{}'.format(self.output_dir, self.get_scene_name(fullPath=False), camera_name, camera_name),
                            sequenceTime=0,
                            clearCache=1,
                            viewer=0,
                            showOrnaments=1,
                            offScreen=True,
                            fp=4,
                            percent=self.percent,
                            compression=self.compression,
                            quality=self.quality)
        return playblast_path

    def searchFN(self):
        """
            Process of searching shots from listwidget
        return: None
        """

        searchTxt = str(self.search_lineEdit.text())
        for i in range(self.shots_ListWidget.count()):
            item = self.shots_ListWidget.item(i)
            if re.search(searchTxt, item.text(), re.IGNORECASE):
                item.setHidden(False)
            else:
                item.setHidden(True)

    def get_scene_name(self, fullPath=False):
        """
            Process of getting Scene Name
        param fullPath: scene fullpath
        return: file info
        """

        path = pm.sceneName()
        if not fullPath:
            return path.basename().splitext()[0]
        else:
            return path

    def get_all_cameras(self):
        """
            Process of getting all cameras in scene file
        return: Cameras list
        """

        return [pm.PyNode(cam).getShape() for cam in pm.listCameras()]

    def compile_Mov(self, eachMayaFile):
        """
            Process of creating mov from jpg
        param eachMayaFile: maya file
        return: None
        """

        path = r"{}\ffmpeg.exe".format(os.path.dirname(os.path.realpath(__file__)))
        fol_path = r'{}\{}'.format(self.output_dir, os.path.basename(eachMayaFile).split('.')[0])
        finalMovPath = r'{}\{}.mov'.format(self.output_dir, self.get_scene_name(fullPath=False))
        camereFol = list(set([os.path.dirname('{}/{}'.format(root, f)) for root, dirs, files in
                              os.walk(fol_path) for f in files]))

        imgFiles = " -i ".join(['{}/{}.%04d.jpg'.format(e, os.path.basename(e)).replace('\\', '/') for e in camereFol])
        command = """{fmeg} -i {fol} -frames "{frame}" -filter_complex "[0:v:0][1:v:0][2:v:0][3:v:0]hstack=inputs=4" {mov}""".format(fmeg=path,
                                            fol=imgFiles, frame=self.endframe, mov=finalMovPath.replace('\\', '/'))
        self.windowsless_subprocess(command)

    def windowsless_subprocess(self, command):
        """
            Process of running command with subprocess
        param command: command
        return: None
        """

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        processCommand = subprocess.Popen(command, shell=False, startupinfo=si)
        processCommand.wait()

    def make_dir(self, dirname, recreate=False):
        """
            Process os creating directory
        param dirname: directory name
        param recreate: flag
        return: None
        """

        if '.' in os.path.basename(dirname) or '.' in dirname:
            dirname = os.path.dirname(dirname)

        if recreate:
            shutil.rmtree(dirname)

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        return pm.Path(str(dirname))

    def get_date_time(self):
        """
            Process of timestamp
        :return: timestamp
        """

        return datetime.datetime.now().strftime(r'%Y_%m_%d_%H_%M_%S')


if __name__ == '__main__':
    app = QtGui.QApplication([])
    win = PlayBlastTool()
    win.show()
    sys.exit(app.exec_())