import os
from PyQt4 import QtGui, QtCore
from qgis.core import *
from opengeo.postgis.connection import PgConnection
from opengeo.gui.exploreritems import TreeItem
from opengeo.gui.layerdialog import PublishLayerDialog
from opengeo.postgis.postgis_utils import tableUri
from opengeo.gui.userpasswd import UserPasswdDialog
from opengeo.gui.importvector import ImportIntoPostGISDialog
from opengeo.gui.pgconnectiondialog import NewPgConnectionDialog

pgIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/pg.png")   
 
class PgConnectionsItem(TreeItem):

    def __init__(self):             
        TreeItem.__init__(self, None, pgIcon, "PostGIS connections") 
        
    def populate(self):        
        settings = QtCore.QSettings()
        settings.beginGroup(u'/PostgreSQL/connections')
        for name in settings.childGroups():
            settings.beginGroup(name)
            try:                                            
                conn = PgConnection(name, settings.value('host'), int(settings.value('port')), 
                                settings.value('database'), settings.value('username'), 
                                settings.value('password'))                 
                item = PgConnectionItem(conn)
                if conn.isValid:                              
                    item.populate()
                    #self.addChild(item)
                else:    
                    #if there is a problem connecting, we add the unpopulated item with the error icon
                    #TODO: report on the problem
                    wrongConnectionIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/wrong.gif")                 
                    item.setIcon(0, wrongConnectionIcon)
                    #item.setText(0, name + "[cannot connect]")
                self.addChild(item)
            except Exception, e:                
                pass
            finally:                            
                settings.endGroup()  
        
    def contextMenuActions(self, tree, explorer):         
        newConnectionAction = QtGui.QAction("New connection...", explorer)
        newConnectionAction.triggered.connect(lambda: self.newConnection(explorer))                                             
        return [newConnectionAction]
                 
    def newConnection(self, explorer):
        dlg = NewPgConnectionDialog(explorer)
        dlg.exec_()
        if dlg.conn is not None:
            item = PgConnectionItem(dlg.conn)
            if dlg.conn.isValid:                              
                item.populate()                
            else:                    
                wrongConnectionIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/wrong.gif")                 
                item.setIcon(0, wrongConnectionIcon)                
            self.addChild(item)
            
                  
class PgConnectionItem(TreeItem): 
    def __init__(self, conn):                      
        TreeItem.__init__(self, conn, pgIcon)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled)          
        
    def populate(self):
        if not self.element.isValid:
            dlg = UserPasswdDialog()
            dlg.exec_()
            if dlg.user is None:
                return
            self.element.reconnect(dlg.user, dlg.passwd)            
            if not self.element.isValid:
                QtGui.QMessageBox.warning(None, "Error connecting to DB", "Cannot connect to the database")
                return 
            self.setIcon(0, pgIcon)
        schemas = self.element.schemas()
        for schema in schemas:
            schemItem = PgSchemaItem(schema)
            schemItem.populate()
            self.addChild(schemItem)
            
    def contextMenuActions(self, tree, explorer): 
        if self.element.isValid:            
            newSchemaAction = QtGui.QAction("New schema...", explorer)
            newSchemaAction.triggered.connect(lambda: self.newSchema(explorer)) 
            sqlAction = QtGui.QAction("Run SQL...", explorer)
            sqlAction.triggered.connect(self.runSql)     
            importAction = QtGui.QAction("Import files...", explorer)
            importAction.triggered.connect(lambda: self.importIntoDatabase(explorer))                                        
            return [newSchemaAction, sqlAction, importAction]
        else:
            return []
        
    def _getDescriptionHtml(self, tree, explorer):  
        if not self.element.isValid:
            html = u'<div style="background-color:#ffffcc;"><h1>&nbsp; ' + self.text(0) + ' (GWC layer)</h1></div></br>'  
            html += ('<p>Cannot connect to this database. This might be caused by missing user/passwd credentials.'
                    'Try <a href="refresh">refreshing</a> the connection, to enter new credentials and retry to connect</p>')     
            return html
        else:
            return TreeItem._getDescriptionHtml(self, tree, explorer)

    def linkClicked(self, url):
        if not self.element.isValid:
            self.refreshContent()
        else:
            TreeItem.linkClicked(self, url)        
             
    def startDropEvent(self):
        self.uris = []        
        
    def acceptDroppedUri(self, explorer, uri):
        if self.element.isValid:
            self.uris.append(uri) 
    
    def finishDropEvent(self, explorer):
        if self.uris:
            files = []
            for uri in self.uris:
                try:
                    files.append(uri.split(":",3)[-1])
                except Exception, e:
                    pass            
            dlg = ImportIntoPostGISDialog(self.element, files = files)
            dlg.exec_()
            if dlg.files is not None:            
                for i, filename in enumerate(dlg.files):
                    explorer.progress.setValue(i)
                    explorer.run(importFile, "Import " + filename + "  into database " + self.element.name,
                    [],
                    filename, self.element, dlg.schema, dlg.tablename, not dlg.add)        
            return [self]
        else:
            return []
        
      
    def importIntoDatabase(self, explorer):           
        dlg = ImportIntoPostGISDialog(self.element)
        dlg.exec_()
        if dlg.ok:            
            for i, filename in enumerate(dlg.files):
                explorer.progress.setValue(i)
                explorer.run(importFile, "Import" + filename + " into database " + self.element.name,
                [],
                filename, self.element, dlg.schema, dlg.tablename, not dlg.add)
        self.refreshContent()
          
    def runSql(self):
        pass
    
    def newSchema(self, explorer):            
        text, ok = QtGui.QInputDialog.getText(explorer, "Schema name", "Enter name for new schema", text="schema")
        if ok:
            explorer.run(self.element.geodb.create_schema, 
                        "Create schema '" + text + "'",
                         [self], 
                         text) 
                    
class PgSchemaItem(TreeItem): 
    def __init__(self, schema): 
        pgIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/namespace.png")                        
        TreeItem.__init__(self, schema, pgIcon)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled)
        
    def populate(self):
        tables = self.element.tables()
        for table in tables:
            tableItem = PgTableItem(table)            
            self.addChild(tableItem)      

    def contextMenuActions(self, tree, explorer):                        
        newTableIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/new_table.png")                         
        newTableAction = QtGui.QAction(newTableIcon, "New table...", explorer)
        newTableAction.triggered.connect(lambda: self.newTable(explorer))                                                                  
        deleteAction= QtGui.QAction("Delete", explorer)
        deleteAction.triggered.connect(lambda: self.deleteSchema(explorer))  
        renameAction= QtGui.QAction("Rename...", explorer)
        renameAction.triggered.connect(lambda: self.renameSchema(explorer))
        importAction = QtGui.QAction("Import files...", explorer)
        importAction.triggered.connect(lambda: self.importIntoSchema(explorer))                            
        return [newTableAction, deleteAction, renameAction, importAction]

    def importIntoSchema(self, explorer):
        dlg = ImportIntoPostGISDialog(self.element.conn, self.element.name)
        dlg.exec_()
        if dlg.ok:            
            for i, filename in enumerate(dlg.files):
                explorer.progress.setValue(i)
                explorer.run(importFile, "Import " + filename + " into database " + self.element.conn.name,
                [],
                filename, self.element.conn, dlg.schema, dlg.tablename, not dlg.add)
        self.refreshContent()
        
    def deleteSchema(self, explorer):
        explorer.run(self.element.conn.geodb.delete_schema, 
                          "Delete schema '" + self.element.name + "'",
                          [self.parent()], 
                          self.element.name)
    
    def renameSchema(self, explorer):
        text, ok = QtGui.QInputDialog.getText(explorer, "Schema name", "Enter new name for schema", text="schema")
        if ok:
            explorer.run(self.element.conn.geodb.rename_schema, 
                          "Rename schema '" + self.element.name + "'  to '" + text + "'", 
                          [self.parent()], 
                          self.element.name, text)      
    
    def newTable(self, explorer):
        pass    
    
    def startDropEvent(self):
        self.uris = []        
        
    def acceptDroppedUri(self, explorer, uri):
        if self.element.isValid:
            self.uris.append(uri) 
    
    def finishDropEvent(self, explorer):
        if self.uris:
            files = []
            for uri in self.uris:
                try:
                    files.append(uri.split(":",3)[-1])
                except Exception, e:
                    pass            
            dlg = ImportIntoPostGISDialog(self.element, schema = self.element, files = files)
            dlg.exec_()
            if dlg.files is not None:            
                for i, filename in enumerate(dlg.files):
                    explorer.progress.setValue(i)
                    explorer.run(importFile, "Import" + filename + " into database " + self.element.name,
                    [],
                    filename, self.element.conn, dlg.schema, dlg.tablename, not dlg.add)        
            return [self]
        else:
            return []                
        
class PgTableItem(TreeItem): 
    def __init__(self, table):                               
        TreeItem.__init__(self, table, self.getIcon(table))
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled)
        
    def getIcon(self, table):        
        tableIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/table.png")
        viewIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/view.png")
        layerPointIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/layer_point.png")
        layerLineIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/layer_line.png")
        layerPolygonIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/layer_polygon.png")        
        layerUnknownIcon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/layer_unknown.png")
            
        if table.geomtype is not None:        
            if table.geomtype.find('POINT') != -1:
                return layerPointIcon
            elif table.geomtype.find('LINESTRING') != -1:
                return layerLineIcon
            elif table.geomtype.find('POLYGON') != -1:
                return layerPolygonIcon
            return layerUnknownIcon        

        if table.isView:
            return viewIcon
        
        return tableIcon
    
    def contextMenuActions(self, tree, explorer):        
        publishPgTableAction = QtGui.QAction("Publish...", explorer)
        publishPgTableAction.triggered.connect(lambda: self.publishPgTable(tree, explorer))            
        publishPgTableAction.setEnabled(len(tree.gsItem.catalogs()) > 0)    
        deleteAction= QtGui.QAction("Delete", explorer)
        deleteAction.triggered.connect(lambda: self.deleteTable(explorer))  
        renameAction= QtGui.QAction("Rename...", explorer)
        renameAction.triggered.connect(lambda: self.renameTable(explorer))                 
        vacuumAction= QtGui.QAction("Vacuum analyze", explorer)
        vacuumAction.triggered.connect(lambda: self.vacuumTable(explorer))
        return [publishPgTableAction, deleteAction, renameAction, vacuumAction]
           
    def vacuumTable(self, explorer):
        explorer.run(self.element.conn.geodb.vacuum_analyze, 
                  "Vacuum table " + self.element.name,
                  [self.parent()], 
                  self.element.name, self.element.schema)
    
    def deleteTable(self, explorer):
        explorer.run(self.element.conn.geodb.delete_table, 
                          "Delete table '" + self.element.name + "'",
                          [self.parent()], 
                          self.element.name)
    
    def renameTable(self, explorer):
        text, ok = QtGui.QInputDialog.getText(explorer, "Table name", "Enter new name for table", text="table")
        if ok:
            explorer.run(self.element.conn.geodb.rename_table, 
                          "Rename table '" + self.element.name + "' to '" + text + "'",
                          [self.parent()], 
                          self.element.name, text, self.element.schema)      
    
    
    def publishPgTable(self, tree, explorer):
        dlg = PublishLayerDialog(tree.gsItem.catalogs())
        dlg.exec_()      
        if dlg.catalog is None:
            return
        cat = dlg.catalog          
        catItem = tree.findAllItems(cat)[0]
        toUpdate = [catItem]                    
        explorer.run(self._publishTable,
                 "Publish table '" + self.element.name + "'",
                 toUpdate,
                 self.element, cat, dlg.workspace)
        
                
    def _publishTable(self, table, catalog = None, workspace = None):
        if catalog is None:
            pass       
        workspace = workspace if workspace is not None else catalog.get_default_workspace()        
        connection = table.conn 
        geodb = connection.geodb      
        catalog.create_pg_featurestore(connection.name,                                           
                                           workspace = workspace,
                                           overwrite = True,
                                           host = geodb.host,
                                           database = geodb.dbname,
                                           schema = table.schema,
                                           port = geodb.port,
                                           user = geodb.user,
                                           passwd = geodb.passwd)
        catalog.create_pg_featuretype(table.name, connection.name, workspace, "EPSG:" + str(table.srid))  
        
def importFile(filename, connection, schema, tablename, overwrite):

    pk = "id"
    geom = "geom" 
    providerName = "postgres" 
    
    layerName = QtCore.QFileInfo(filename).completeBaseName()
    if tablename is None:
        tablename = layerName

    geodb = connection.geodb
    uri = QgsDataSourceURI()    
    uri.setConnection(geodb.host, str(geodb.port), geodb.dbname, geodb.user, geodb.passwd)    
    uri.setDataSource(schema, tablename, geom, "", pk)

    options = {}
    if overwrite:
        options['overwrite'] = True
    else:
        options['append'] = True
        
    layer = QgsVectorLayer(filename, layerName, "ogr")    
    if not layer.isValid() or layer.type() != QgsMapLayer.VectorLayer:
        layer.deleteLater()
        raise WrongLayerFileError("Error reading file {} or it is not a valid vector layer file".format(filename))
                
    ret, errMsg = QgsVectorLayerImport.importLayer(layer, uri.uri(), providerName, layer.crs(), False, False, options)
    if ret != 0:
        raise Exception(errMsg)
    
    
    
 #==============================================================================
 #   if self.chkSinglePart.isEnabled() and self.chkSinglePart.isChecked():
 #      options['forceSinglePartGeometryType'] = True
 #   outCrs = None
 #   if self.chkTargetSrid.isEnabled() and self.chkTargetSrid.isChecked():
 #       targetSrid = int(self.editTargetSrid.text())
 #       outCrs = qgis.core.QgsCoordinateReferenceSystem(targetSrid)
 # 
 #   # update input layer crs and encoding
 #   if self.chkSourceSrid.isEnabled() and self.chkSourceSrid.isChecked():
 #       sourceSrid = int(self.editSourceSrid.text())
 #       inCrs = QgsCoordinateReferenceSystem(sourceSrid)
 #       self.inLayer.setCrs( inCrs )
 # 
 #   if self.chkEncoding.isEnabled() and self.chkEncoding.isChecked():
 #       enc = self.cboEncoding.currentText()
 #       self.inLayer.setProviderEncoding( enc )
 #==============================================================================

    # do the import!
    
class WrongLayerFileError(Exception):
    pass