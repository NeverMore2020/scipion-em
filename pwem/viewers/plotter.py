# **************************************************************************
# *
# * Authors:     Josue Gomez Blanco (josue.gomez-blanco@mcgill.ca)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

from math import radians
try:
    from itertools import izip
except ImportError:
    izip = zip

from pyworkflow.gui.plotter import Plotter, plt
import pwem.metadata as md
import numbers


class EmPlotter(Plotter):
    """ Class to create several plots. """
    def __init__(self, x=1, y=1, mainTitle="", **kwargs):
        Plotter.__init__(self, x, y, mainTitle, **kwargs)

    def plotAngularDistribution(self, title, rot, 
                                tilt, weight=[], max_p=40, 
                                min_p=5, max_w=2, min_w=1, color='blue'):
        """ Create an special type of subplot, representing the angular
        distribution of weight projections. """
        if weight:
            max_w = max(weight)
            min_w = min(weight)
            a = self.createSubPlot(title,
                                   'Min weight=%(min_w).2f, Max weight=%(max_w).2f'
                                   % locals(), '', projection='polar')
            for r, t, w in izip(rot, tilt, weight):
                pointsize = int((w - min_w)/(max_w - min_w + 0.001) * (max_p - min_p) + min_p)
                a.plot(r, t, markerfacecolor=color, marker='.', markersize=pointsize)
        else:
            a = self.createSubPlot(title, 'Empty plot', '', projection='polar')
            for r, t in izip(rot, tilt):
                a.plot(r, t, markerfacecolor=color, marker='.', markersize=10)
                
    def plotAngularDistributionFromMd(self, mdFile, title, **kwargs):
        """ Read the values of rot, tilt and weights from
        the medata and plot the angular distribution.
        ANGLES are in DEGREES
        In the metadata:
            rot: MDL_ANGLE_ROT
            tilt: MDL_ANGLE_TILT
            weight: MDL_WEIGHT
        """
        angMd = md.MetaData(mdFile)
        rot = []
        tilt = []
        weight = []
        
        for row in md.iterRows(angMd):
            rot.append(radians(row.getValue(md.MDL_ANGLE_ROT)))
            tilt.append(row.getValue(md.MDL_ANGLE_TILT))
            weight.append(row.getValue(md.MDL_WEIGHT))
        return self.plotAngularDistribution(title, rot, tilt, weight, **kwargs)
        
    def plotHist(self, yValues, nbins, color='blue', **kwargs):
        """ Create an histogram. """
        self.hist(yValues, nbins, facecolor=color, **kwargs)

    def plotScatter(self, xValues, yValues, color='blue', **kwargs):
        """ Create an scatter plot. """
        self.scatterP(xValues, yValues, c=color, **kwargs)
  
    def plotMatrix(self, img
                       , matrix
                       , vminData
                       , vmaxData
                       , cmap='jet'
                       , xticksLablesMajor=None
                       , yticksLablesMajor=None
                       , rotationX=90.
                       , rotationY=0.
                       , **kwargs):
        interpolation = kwargs.get('interpolation', "none")
        plot = img.imshow(matrix, interpolation=interpolation, cmap=cmap,
                          vmin=vminData, vmax=vmaxData)
        if xticksLablesMajor is not None:
            plt.xticks(range(len(xticksLablesMajor)),
                       xticksLablesMajor[:len(xticksLablesMajor)],
                       rotation=rotationX)
        if yticksLablesMajor is not None:
            plt.yticks(range(len(yticksLablesMajor)),
                       yticksLablesMajor[:len(yticksLablesMajor)],
                       rotation=rotationY)
        return plot
    
    def plotData(self, xValues, yValues, color='blue', **kwargs):
        """ Shortcut function to plot some values.
        Params:
            xValues: list of values to show in x-axis
            yValues: list of values to show as values in y-axis
            color: color for the plot.
            **kwargs: keyword arguments that accepts:
                marker, linestyle
        """

        self.plot(xValues, yValues, color, **kwargs)
        
    def plotDataBar(self, xValues, yValues, width, color='blue', **kwargs):
        """ Shortcut function to plot some values.
        Params:
            xValues: list of values to show in x-axis
            yValues: list of values to show as values in y-axis
            color: color for the plot.
            **kwargs: keyword arguments that accepts:
                marker, linestyle
        """

        self.bar(xValues, yValues, width=width, color=color, **kwargs)

    @classmethod
    def createFromFile(cls, dbName, dbPreffix, plotType, columnsStr, colorsStr, linesStr,
                       markersStr, xcolumn, ylabel, xlabel, title, bins, orderColumn,
                       orderDirection):
        columns = columnsStr.split()
        colors = colorsStr.split()
        lines = linesStr.split()
        markers = markersStr.split()
        data = PlotData(dbName, dbPreffix, orderColumn, orderDirection)
        plotter = Plotter(windowTitle=title)
        ax = plotter.createSubPlot(title, xlabel, ylabel)
        xvalues = data.getColumnValues(xcolumn) if xcolumn else range(0, data.getSize())

        for i, col in enumerate(columns):
            yvalues = data.getColumnValues(col)
            color = colors[i]
            line = lines[i]
            colLabel = col if not col.startswith("_") else col[1:]
            if bins:
                yvalues = data._removeInfinites(yvalues)
                ax.hist(yvalues, bins=int(bins), color=color, linestyle=line, label=colLabel)
            else:
                if plotType == 'Plot':
                    marker = (markers[i] if not markers[i] == 'none' else None)
                    ax.plot(xvalues, yvalues, color, marker=marker, linestyle=line, label=colLabel)
                else:
                    ax.scatter(xvalues, yvalues, c=color, label=col, alpha=0.5)
        ax.legend()

        return plotter
        

class PlotData:
    """ Small wrapper around table data such as: sqlite or metadata
    files. """
    def __init__(self, fileName, tableName, orderColumn, orderDirection):
        self._orderColumn = orderColumn
        self._orderDirection = orderDirection
        
        if fileName.endswith(".db") or fileName.endswith(".sqlite"):
            self._table = self._loadSet(fileName, tableName)
            self.getColumnValues = self._getValuesFromSet
            self.getSize = self._table.getSize
        else:  # assume a metadata file
            self._table = self._loadMd(fileName, tableName)
            self.getColumnValues = self._getValuesFromMd
            self.getSize = self._table.size
            
    def _loadSet(self, dbName, dbPreffix):
        from pyworkflow.mapper.sqlite import SqliteFlatDb
        db = SqliteFlatDb(dbName=dbName, tablePrefix=dbPreffix)
        if dbPreffix:
            setClassName = "SetOf%ss" % db.getSelfClassName()
        else:
            setClassName = db.getProperty('self')  # get the set class name

        # FIXME: Check why the import is here
        from pwem import Domain
        setObj = Domain.getObjects()[setClassName](filename=dbName, prefix=dbPreffix)
        return setObj
    
    def _getValuesFromSet(self, columnName):
        return [self._getValue(obj, columnName) 
                for obj in self._table.iterItems(orderBy=self._orderColumn,
                                       direction=self._orderDirection)]
    @staticmethod
    def _removeInfinites(values):
        newValues = []
        for value in values:
            if isinstance(value, numbers.Number) and value < float("Inf"):
                newValues.append(value)
        return newValues

    def _loadMd(self, fileName, tableName):
        label = md.str2Label(self._orderColumn)
        tableMd = md.MetaData('%s@%s' % (tableName, fileName))
        tableMd.sort(label)  # FIXME: use order direction
        # TODO: sort metadata by self._orderColumn
        return tableMd
    
    def _getValuesFromMd(self, columnName):
        label = md.str2Label(columnName)
        return [self._table.getValue(label, objId) for objId in self._table]
    
    def _getValue(self, obj, column):
        if column == 'id':
            return obj.getObjId()
        
        return obj.getNestedValue(column)
