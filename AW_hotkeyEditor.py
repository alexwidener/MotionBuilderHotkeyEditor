#   Copyright 2015 Alex Widener
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
  
"""
What this is:
A Hotkey Editor for Autodesk MotionBuilder.

See documentation here:
http://alexwidener.github.io/MotionBuilderHotkeyEditor/

Thanks:
Yi Liang Siew for sorting out my stupidity. http://www.sonictk.com/

modified 2018 Olaf Haag:
    - added Apache License 2.0 boilerplate notice
    - changed code to find config folders
"""
__author__ = "Alex Widener"
__copyright__ = "Alex Widener"
__credits__ = ["Yi Liang Siew"]
__email__ = "alexwidener # gmail"


import os
import time
from shutil import copy
from PySide import QtGui, QtCore
import webbrowser
from pyfbsdk import FBSystem

DEFAULTCONFIGSPATH = FBSystem().ConfigPath + 'Keyboard'
KEYBOARDCONFIGPATH = FBSystem().UserConfigPath + '/Keyboard'
ACTIONSCRIPTPATH = FBSystem().UserConfigPath + '/Scripts'
    
MAX = '3ds Max.txt'
LIGHTWAVE = 'Lightwave.txt'
MAYA = 'Maya.txt'
MOTIONBUILDERCLASSIC = 'MotionBuilder Classic.txt'
MOTIONBUILDER = 'MotionBuilder.txt'
SOFTIMAGE = 'Softimage.txt'
CUSTOMHOTKEYS = 'customHotkeys.txt'

parent = QtGui.QApplication.activeWindow()


class HotkeyEditor(object):
    widgets = []


class UI_HotkeyEditor(QtGui.QWidget):
    def __init__(self, parent):
        super(UI_HotkeyEditor, self).__init__()

        self.setObjectName('HotkeyEditor')
        self.setWindowTitle('AW_Hotkey Editor')
        self.resize(1280, 720)

        self.mbDefaultFile = os.path.join(DEFAULTCONFIGSPATH, 'MotionBuilder.txt')
        self.customKeysFile = os.path.join(KEYBOARDCONFIGPATH, CUSTOMHOTKEYS)
        self.actionScriptFile = os.path.join(ACTIONSCRIPTPATH, 'ActionScript.txt')

        self.customSettings = []

        if not os.path.isfile(self.customKeysFile):
            copy(self.mbDefaultFile, self.customKeysFile)

        if not os.path.isfile(self.actionScriptFile):
            self.createActionScriptFile()

        self._layouts()
        self._connections()
        HotkeyEditor.widgets.append(self)

    def _getCustomSettings(self):
        self.customSettings = []
        return [self.replacer(line) for line in open(self.customKeysFile)]

    def _layouts(self):
        self.main_layout = QtGui.QVBoxLayout()
        self.menu_bar = QtGui.QMenuBar()
        self.main_layout.addWidget(self.menu_bar)
        self.file_menu = self.menu_bar.addMenu('File')
        self.help_menu = self.menu_bar.addMenu('Help')
        self.doc_menu = self.help_menu.addAction('Documentation')
        self.reset_menu = self.file_menu.addMenu('Reset Hotkeys')

        self.mb_defaults_menu = self.reset_menu.addAction('MotionBuilder (default)')
        self.mbc_defaults_menu = self.reset_menu.addAction('MotionBuilder Classic')
        self.lightwave_menu = self.reset_menu.addAction('Lightwave')
        self.max_menu = self.reset_menu.addAction('3DS Max')
        self.maya_menu = self.reset_menu.addAction('Maya')
        self.softimage_menu = self.reset_menu.addAction('SoftImage')

        self.path_layout = QtGui.QHBoxLayout()
        self.customPathQLine = QtGui.QLineEdit()
        self.customPathQLine.setText(self.customKeysFile.replace('/', '\\'))
        self.customPathQLine.setEnabled(False)
        self.path_layout.addWidget(self.customPathQLine)

        self.main_layout.addLayout(self.path_layout)
        
        self.settingsLayout = QtGui.QHBoxLayout()
        self.settingsList = QtGui.QTableWidget()
        self.settingsList.setColumnCount(2)
        self.settingsList.setHorizontalHeaderLabels(['Action', 'Key Combination'])

        self.scriptsList = QtGui.QTableWidget()
        self.scriptsList.setColumnCount(2)
        self.scriptsList.setHorizontalHeaderLabels(['Script', 'Path to Script'])

        self.settingsLayout.addWidget(self.settingsList)
        self.settingsLayout.addWidget(self.scriptsList)

        self._fillTables()        
        self.main_layout.addLayout(self.settingsLayout)

        self.button_layout = QtGui.QHBoxLayout()
        self.submit_button = QtGui.QPushButton('Save Changes')
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.submit_button)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.main_layout)

    def _fillTables(self):
        
        allRows = self.settingsList.rowCount()
        for row in range(0, allRows):
            self.settingsList.removeRow(row)

        settingsRow = 0
        scriptsRow = 0
        settings = self._getCustomSettings()

        for line in settings:
            newRow = self.settingsList.insertRow(settingsRow)
            actionItem = QtGui.QTableWidgetItem(line.partition('=')[0])
            hotkeyItem = QtGui.QTableWidgetItem(line.partition('=')[2])
            self.settingsList.setItem(settingsRow, 0, actionItem)
            self.settingsList.setItem(settingsRow, 1, hotkeyItem)

            if 'action.global.script' in line.partition('=')[0]:
                agScript = line.partition('=')[0]
                num = agScript.partition('action.global.script')[2]
                scriptItem = QtGui.QTableWidgetItem('Script%s' % num)
                scriptPath = self.getPathFromFile(self.actionScriptFile, num)
                pathItem = QtGui.QTableWidgetItem(scriptPath)
                self.scriptsList.insertRow(scriptsRow)
                self.scriptsList.setItem(scriptsRow, 0, scriptItem)
                self.scriptsList.setItem(scriptsRow, 1, pathItem)
                scriptsRow += 1
            settingsRow += 1
        self.settingsList.resizeColumnsToContents()
        self.scriptsList.resizeColumnsToContents()

    def _connections(self):

        self.submit_button.clicked.connect(lambda: self.saveSettings())

        self.mb_defaults_menu.triggered.connect(lambda: self._replaceCustomFile(MOTIONBUILDER))
        self.mbc_defaults_menu.triggered.connect(lambda: self._replaceCustomFile(MOTIONBUILDERCLASSIC))
        self.lightwave_menu.triggered.connect(lambda: self._replaceCustomFile(LIGHTWAVE))
        self.max_menu.triggered.connect(lambda: self._replaceCustomFile(MAX))
        self.maya_menu.triggered.connect(lambda: self._replaceCustomFile(MAYA))
        self.softimage_menu.triggered.connect(lambda: self._replaceCustomFile(SOFTIMAGE))
        self.doc_menu.triggered.connect(lambda: self.openWebsite())


    def replacer(self, element):
        return element.strip().replace('\t', '')

    def createActionScriptFile(self):
        """
        Creates the user ActionScript file which will store the user's file paths to their scripts.
        If you want to increase it, increase the number from 13.
        """
        with open(self.actionScriptFile, 'w') as f:
            f.write('[ScriptFiles]\r\n')
            for i in range(1, 13):
                f.write('Script%d = \r\n' % i)

    def getPathFromFile(self, acFilePath, num):
        with open(acFilePath, 'r') as f:
            scriptcontents = f.readlines()
        for line in scriptcontents:
            if line.startswith('Script%s' % num):
                return line.partition(' = ')[2]

    def saveSettings(self):
        settingsRows = self.settingsList.rowCount()
        scriptsRows = self.scriptsList.rowCount()

        if os.path.isfile(self.customKeysFile):
            os.remove(self.customKeysFile)

        with open(self.customKeysFile, 'w') as f:
            for x in range(0, settingsRows):
                actionItem = self.settingsList.item(x, 0).text()
                keyItem = self.settingsList.item(x, 1).text()
                if '[' in actionItem and keyItem == '':
                    f.write(actionItem.strip() + '\r\n')                  
                elif actionItem != '' and keyItem != '':
                    f.write(actionItem.strip() + ' = ' + keyItem.strip() + '\r\n')
                elif actionItem != '' and keyItem == '':
                    f.write(actionItem.strip() + ' = \r\n')
                else:
                    f.write('\n')

        if os.path.isfile(self.actionScriptFile):
            os.remove(self.actionScriptFile)

        with open(self.actionScriptFile, 'w') as f:
            f.write('[ScriptFiles]\n')
            for y in range(0, scriptsRows):
                scriptItem = self.scriptsList.item(y, 0).text()
                pathItem = self.scriptsList.item(y, 1).text()
                f.write('{0} = {1} \r\n'.format(scriptItem.strip(), pathItem.rstrip()))

        main()               

    def _replaceCustomFile(self, replacement):
        """
        The replacement is whichever system the user chose to replace with.
        It will overwrite the user's current settings.
        But this allows the user to start their current settings from whatever system they want to start from.
        """
        copyFile = os.path.join(DEFAULTCONFIGSPATH, replacement)
        newFile = os.path.join(KEYBOARDCONFIGPATH, CUSTOMHOTKEYS)
        copy(copyFile, newFile)

        self.settingsList.clearContents()
        self.scriptsList.clearContents()

        while self.settingsList.rowCount() > 0:
            self.settingsList.removeRow(0)

        while self.scriptsList.rowCount() > 0:
            self.scriptsList.removeRow(0)

        self._fillTables()
        self.settingsList.resizeColumnsToContents()
        self.scriptsList.resizeColumnsToContents()

    def openWebsite(self):
        URL = 'http://alexwidener.github.io/MotionBuilderHotkeyEditor/'
        webbrowser.open_new_tab(URL)

def main():
    parent = QtGui.QApplication.instance()
    currentWidgets = parent.topLevelWidgets()
    for w in currentWidgets:
        if w.objectName() == 'HotkeyEditor':
            w.close()

# start working in the try/Except at some point
main()
HKE = UI_HotkeyEditor(parent)
HKE.show()