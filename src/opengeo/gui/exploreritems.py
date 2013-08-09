from opengeo.core import util
from PyQt4 import QtGui, QtCore

class TreeItem(QtGui.QTreeWidgetItem): 
    def __init__(self, element, icon = None, text = None): 
        QtGui.QTreeWidgetItem.__init__(self) 
        self.element = element    
        self.setData(0, QtCore.Qt.UserRole, element)            
        text = text if text is not None else util.name(element)
        self.setText(0, text)      
        if icon is not None:
            self.setIcon(0, icon)   
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)               
            
    def refreshContent(self):
        self.takeChildren()
        self.populate()    
       
    def descriptionWidget(self, tree, explorer):                
        text = self.getDescriptionHtml(tree, explorer)
        self.description = QtGui.QTextBrowser()
        self.description.setOpenLinks(False)        

        self.description.connect(self.description, QtCore.SIGNAL("anchorClicked(const QUrl&)"), self.linkClicked)
        #self.description.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        #self.description.connect(self.description, QtCore.SIGNAL("linkClicked(const QUrl&)"), self.linkClicked)
        self.description.setHtml(text)   
        self.description.tree = tree
        self.description.explorer = explorer
        return self.description 
    
    def getDescriptionHtml(self, tree, explorer):
        html = self._getDescriptionHtml(tree, explorer)
        html = u"""
            <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
            <html>
            <head>
            <style type="text/css">
                .section { margin-top: 25px; }
                table.header th { background-color: #dddddd; }
                table.header td { background-color: #f5f5f5; }
                table.header th, table.header td { padding: 0px 10px; }
                table td { padding-right: 20px; }
                .underline { text-decoration:underline; }
            </style>
            </head>
            <body>
            %s <br>
            </body>
            </html>
            """ % html  
        return html      
        
    def _getDescriptionHtml(self, tree, explorer): 
        html = u'<div style="background-color:#ffffcc;"><h1>&nbsp; ' + self.text(0) + '</h1></div><ul>'               
        actions = self.contextMenuActions(tree, explorer)
        for action in actions:
            if action.isEnabled():
                html += '<li><a href="' + action.text() + '">' + action.text() + '</a></li>\n'
        html += '</ul>'
        return html 
    
    def linkClicked(self, url):
        actionName = url.toString()
        actions = self.contextMenuActions(self.description.tree, self.description.explorer)
        for action in actions:
            if action.text() == actionName:
                action.trigger()
                return            
    
    def contextMenuActions(self, tree, explorer):
        return []   
    
    def multipleSelectionContextMenuActions(self, tree, explorer, selected):
        return []
    
    def acceptDroppedItem(self, explorer, item):
        return []
    
    def startDropEvent(self):
        self.uris = []
        
    def finishDropEvent(self, explorer):
        return []
            
    def acceptDroppedUri(self, explorer, uri):
        pass