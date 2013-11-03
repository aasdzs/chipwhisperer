#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, Colin O'Flynn <coflynn@newae.com>
# All rights reserved.
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.assembla.com/spaces/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "Colin O'Flynn"

import sys
import os
#We always import PySide first, to force usage of PySide over PyQt
try:
    from PySide.QtCore import *
    from PySide.QtGui import *
except ImportError:
    print "ERROR: PySide is required for this program"
    sys.exit()

try:
    import pyqtgraph as pg
except ImportError:
    print "ERROR: PyQtGraph is required for this program"
    sys.exit()

from GraphWidget import GraphWidget
import PythonConsole

sys.path.append("traces")
from traces.TraceManager import TraceManagerDialog

class MainChip(QMainWindow):
    MaxRecentFiles = 4

    #Be sure to set things with:
    #QApplication()
    #app.setOrganizationName()
    #app.setApplicationName()
    #app.setWindowIcon()    
    
    openFile = Signal(str)
    saveFile = Signal()
    newFile = Signal()
    
    
    def __init__(self, name="Demo", imagepath="images/"):       
        super(MainChip, self).__init__()
        
        self.manageTraces = TraceManagerDialog(self)
        
        self.imagepath = imagepath
        self.name = name        
        self.filename = None
        self.dirty = True
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.initUI()
        self.lastMenuActionSection = None
        self.paramTrees = []
        
        #Fake widget for dock
        #TODO: Would be nice if this auto-resized to keep small, but not amount of playing
        #with size policy or min/max sizes has worked.
        fake = QWidget()
        self.setCentralWidget(fake)
        
        self.paramScripting = self.addConsole("Script Commands", visible=False)
        self.addPythonConsole()


    def restoreDockGeometry(self):
        """Needs to be called AFTER doing user-land setup"""
        
        #Settings
        settings = QSettings()
        self.restoreGeometry(settings.value("geometry"))
        self.restoreState(settings.value("state"))
        
    def addWindowMenuAction(self, action, section):
        
        #TODO: Should this be done with submenus?
        if section != self.lastMenuActionSection:
            self.windowMenu.addSeparator()
        
        self.lastMenuActionSection = section                
        self.windowMenu.addAction(action)
        
    def addDock(self, dockWidget, name="Settings", area=Qt.LeftDockWidgetArea, allowedAreas=Qt.TopDockWidgetArea |Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea| Qt.LeftDockWidgetArea, visible=True):
        """Add a widget (dockwidget) as a dock to the main window, and add it to the Windows menu"""                
        #Configure dock
        dock = QDockWidget(name)
        dock.setAllowedAreas(allowedAreas)
        dock.setWidget(dockWidget)
        dock.setObjectName(name)
        self.addDockWidget(area, dock)
        
        if visible == False:
            dock.toggleViewAction()
        
        #Add to "Windows" menu
        self.addWindowMenuAction(dock.toggleViewAction(), None)
        self.enforceMenuOrder()
        
        return dock
    
    def addSettings(self, tree, name):
        """Add a settings dock - same as addDock but defaults to left-hand side"""
        self.paramTrees.append(tree)
        dock = self.addDock(tree, name=name, area=Qt.LeftDockWidgetArea)
        return dock        
    
    def addTraceDock(self, name):
        """Add a new GraphWidget in a dock, you can get the GW with .widget() property of returned QDockWidget"""
        gw = GraphWidget(self.imagepath)
        return self.addDock(gw, name=name, area=Qt.RightDockWidgetArea)
        
    def addConsole(self, name="Debug Logging", visible=True):
        """Add a QTextBrowser, used as a console/debug window"""
        console = QTextBrowser()
        self.addDock(console, name, area=Qt.BottomDockWidgetArea, visible=visible) 
        return console    
    
    def addPythonConsole(self, name="Python Console", visible=False):
        wid = PythonConsole.QPythonConsole(self, locals())
        self.addDock(wid, name, area=Qt.BottomDockWidgetArea, visible=visible)
        return wid   
        
    def clearAllSettings(self):
        QSettings.remove("")
        
    def closeEvent(self, event):
        settings = QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
        
        if self.okToContinue():
            QMainWindow.closeEvent(self, event)
        else:
            event.ignore()

    def createFileActions(self):
        self.openAct = QAction(QIcon('open.png'), '&Open Project', self,
                               shortcut=QKeySequence.Open,
                               statusTip='Open Project File',
                               triggered=self._openProject)

        self.saveAct = QAction(QIcon('save.png'), '&Save Project', self,
                               shortcut=QKeySequence.Save,
                               statusTip='Save current project to Disk',
                               triggered=self._saveProject)

        self.newAct = QAction(QIcon('new.png'), '&New Project', self,
                               shortcut=QKeySequence.New,
                               statusTip='Create new Project',
                               triggered=self._newProject)

        for i in range(MainChip.MaxRecentFiles):
            self.recentFileActs.append(QAction(self, visible=False, triggered=self.openRecentFile))

    def jerkface(self):
        QMessageBox.question(self, 'Just Kidding', "Just kidding, this doesn't exist yet. Well good luck then, I better be going.", QMessageBox.No, QMessageBox.No)

    def createMenus(self):
        self.fileMenu= self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
#        self.fileMenu.addAction(self.importAct)
        self.separatorAct = self.fileMenu.addSeparator()
        for i in range(MainChip.MaxRecentFiles):
            self.fileMenu.addAction(self.recentFileActs[i])       
        
        self.projectMenu = self.menuBar().addMenu("&Project")
        self.traceManageAct = QAction('&Manage Traces', self, statusTip='Add/Remove Traces from Project', triggered=self.manageTraces.show)
        self.projectMenu.addAction(self.traceManageAct)
            
        self.toolMenu= self.menuBar().addMenu("&Tools")
            
        self.windowMenu = self.menuBar().addMenu("&Windows")        
                
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpManualAct = QAction('&Tutorial/User Manual', self, statusTip='Everything you need to know', triggered=self.jerkface)
        self.helpMenu.addAction(self.helpManualAct)
            
    def enforceMenuOrder(self):
        self.fakeAction = QAction('Does Nothing', self, visible=False)        
        self.projectMenu.addAction(self.fakeAction)
        self.toolMenu.addAction(self.fakeAction)
        self.windowMenu.addAction(self.fakeAction)
        self.helpMenu.addAction(self.fakeAction)
            
    def initUI(self):        
        self.statusBar()
        self.setWindowTitle(self.name)
        self.setWindowIcon(QIcon("../common/cwicon.png"))
        
        self.recentFileActs = []
        self.createFileActions()
        self.createMenus()

        self.updateRecentFileActions()       

        self.show()
        
    def updateTitleBar(self):
        if self.filename is not None:
            fname = os.path.basename(self.filename)
        else:
            fname = "Untitled"
        
        self.setWindowTitle("%s - %s[*]" %(self.name, fname))
        self.setWindowModified(self.dirty)


    def setCurrentFile(self, fname):
        self.filename = fname
        
        self.updateTitleBar()
        
        if fname is None:
            return
        
        settings = QSettings()
        files = settings.value('recentFileList', [" ", " ", " ", " "])
        
        try:
            files.remove(fname)
        except ValueError:
            pass

        files.insert(0, fname)
        del files[MainChip.MaxRecentFiles:]

        settings = QSettings()
        settings.setValue('recentFileList', files)
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, MainChip):
                widget.updateRecentFileActions()

    def updateRecentFileActions(self):
        settings = QSettings()
        files = settings.value('recentFileList')
        files_no = 0

        if files:
            files_no = len(files)

        numRecentFiles = min(files_no, MainChip.MaxRecentFiles)

        for i in range(numRecentFiles):
            text = "&%d %s" % (i + 1, self.strippedName(files[i]))
            self.recentFileActs[i].setText(text)
            self.recentFileActs[i].setData(files[i])
            self.recentFileActs[i].setVisible(True)

        for j in range(numRecentFiles, MainChip.MaxRecentFiles):
            self.recentFileActs[j].setVisible(False)

        self.separatorAct.setVisible((numRecentFiles > 0))

    def strippedName(self, fullFileName):
        (filepath, filename) = os.path.split(fullFileName)
        (base, toplevel) = os.path.split(filepath)
        return toplevel + "/" + filename
        
        #return QFileInfo(fullFileName).fileName()
                
    def _openProject(self, fname=None):
        #TODO: close etc
        
        if fname is None:
            fname, _ = QFileDialog.getOpenFileName(self, 'Open file','.','*.cwp')
        
        if fname is not None:
            self.openFile.emit(fname)
            self.setCurrentFile(fname)
       
                
    def _newProject(self):
        self.newFile.emit()

    def _saveProject(self):
        self.saveFile.emit()
                
    def openRecentFile(self):
        action = self.sender()
        if action:
            self.openFile.emit(action.data())      

    def okToContinue(self):
        if self.dirty:
            reply = QMessageBox.question(self, "%s - Unsaved Changes"%self.name, "Save unsaved changes?",QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                self.saveProject()
        return True
           
    def _setParameter_children(self, top, path, value, echo):
        """Descends down a given path, looking for value to set"""
        #print top.name()
        if top.name() == path[0]:
            if len(path) > 1:
                for c in top.children():
                    self._setParameter_children(c, path[1:], value, echo)
            else:
                #Check if this is a dictionary/list
                if "values" in top.opts:
                    try:
                        value = top.opts["values"][value]
                    except TypeError:
                        pass   
                    
                if echo == False:
                    top.opts["echooff"] = True
                    
                if top.opts["type"] == "action":
                    top.activate()           
                else:
                    top.setValue(value)
                    
                raise ValueError()
           
    def setParameter(self, parameter, echo=False):
        """Sets a parameter based on a list, used for scripting in combination with showScriptParameter"""
        path = parameter[:-1]
        value = parameter[-1]
        
        try:
            for t in self.paramTrees:
                for i in range(0, t.invisibleRootItem().childCount()):
                    self._setParameter_children(t.invisibleRootItem().child(i).param, path, value, echo)
            
            print "Parameter not found: %s"%str(parameter)
        except ValueError:
            #A little klunky: we use exceptions to tell us the system DID work as intended
            pass               
          
        #User might be calling these in a row, need to process all events
        QCoreApplication.processEvents()
            
    def showScriptParameter(self, param,  changes, topParam):
        """
        This function is used to tell the user what they should pass to setParameter
        in order to recreate a system. This will automatically be called if the module
        has done the following:
        
        * When calling ExtendedParameter.setupParameter(), have passed a reference to 'self' like this:
          
            ExtendedParameter.setupExtended(self.params, self)
              
        * Have a function called paramTreeChanged in the class which calls showScriptParameter (this function).
          Typically done like the following, where self.showScriptParameter is setup in the __init__() call. You
          might need to pass the reference to this instance down to lower modules.
          
            def paramTreeChanged(self, param, changes):
                if self.showScriptParameter is not None:
                    self.showScriptParameter(param, changes, self.params)                
        
        """
        for param, change, data in changes:
            ppath = topParam.childPath(param)
            if ppath is None:
                name = [param.name()]
            else:
                ppath.insert(0, topParam.name())
                name = ppath

            #Don't pollute script output with readonly things
            if param.opts["readonly"] == True:
                continue            
            
            if "echooff" in param.opts:
                if param.opts["echooff"] == True:
                    param.opts["echooff"] = False
                    continue             
            
            if "values" in param.opts:            
                if not hasattr(param.opts["values"], 'iteritems'):
                    name.append(data)
                else:    
                    for k, v in param.opts["values"].iteritems():
                        if v == data:
                            name.append(k)

                    
            else:
                name.append(data)   
            
           
            self.paramScripting.append(str(name))
           
                                                       
def main():    
    app = QApplication(sys.argv)
    app.setOrganizationName("ChipWhisperer")
    app.setApplicationName("Window Demo")
    ex = MainChip(app.applicationName())
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
