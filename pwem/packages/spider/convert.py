# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (jmdelarosa@cnb.csic.es)
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
# *  e-mail address 'jmdelarosa@cnb.csic.es'
# *
# **************************************************************************
"""
This module contains converter functions related to Spider
"""

from pyworkflow.em.constants import NO_INDEX
from pyworkflow.em.convert import ImageHandler
from pyworkflow.utils.path import moveFile
from spider import SpiderDocFile, runSpiderTemplate
from os.path import splitext
   
    
def locationToSpider(index, filename):
    """ Convert an index and filename location
    to a string with @ as expected in Spider.
    """
    #TODO: Maybe we need to add more logic dependent of the format
    if index != NO_INDEX:
        return "%s@%d" % (filename, index)
    
    return filename

def spiderToLocation(spiderFilename):
    """ Return a location (index, filename) given
    a Spider filename with the filename@index structure. """
    if '@' in spiderFilename:
        filename, index = spiderFilename.split('@')
        return int(index), str(filename)
    else:
        return NO_INDEX, str(spiderFilename)


def writeSetOfImages(imgSet, stackFn, selFn):
    """ This function will write a SetOfMicrographs as a Spider stack and selfile.
    Params:
        imgSet: the SetOfMicrograph instance.
        stackFn: the filename where to write the stack.
        selFn: the filename of the Spider selection file.
    """
    ih = ImageHandler()
    doc = SpiderDocFile(selFn, 'w+')
    
    for i, img in enumerate(imgSet):
        ih.convert(img.getLocation(), (i+1, stackFn))
        doc.writeValues(i+1)
        
    doc.close()
    
    fn, ext = splitext(stackFn)
    # Change to BigEndian
    runSpiderTemplate("cp_endian.txt", ext[1:], {'particles': fn, 'numberOfParticles': imgSet.getSize()})
    
    moveFile(fn + '_big' + ext, stackFn)
    