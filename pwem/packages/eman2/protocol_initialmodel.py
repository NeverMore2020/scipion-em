# **************************************************************************
# *
# * Authors:     Josue Gomez Blanco (jgomez@cnb.csic.es)
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
# *  e-mail address 'jgomez@cnb.csic.es'
# *
# **************************************************************************
"""
This sub-package contains wrapper around EMAN initialmodel program
"""


from pyworkflow.em import *  
from pyworkflow.utils import * 
from pyworkflow.em.packages.eman2.data import *
import os
from data import *
from glob import glob
import eman2

class EmanProtInitModel(ProtInitialVolume):
    """No help?"""
    _label = 'initial model'
    
    def _defineParams(self, form):
        form.addSection(label='Input')
        form.addParam('inputClasses', PointerParam, label="Input classes", important=True, 
                      pointerClass='SetOfClasses2D', pointerCondition='hasAverages',
                      help='Select the input images from the project.'
                           'It should be a SetOfClasses2D class')
        form.addParam('numberOfIterations', IntParam, default=8,
                      label='Number of iterations to perform',
                      help='The total number of refinement to perform.')
        form.addParam('numberOfModels', IntParam, default=10,
                      label='Number of different initial models',
                      help='The number of different initial models to generate in search of a good one.')
        form.addParam('shrink', IntParam, default=1,expertLevel=LEVEL_ADVANCED,
                      label='shrink',
                      help='Optionally shrink the input particles by an integer amount prior to recontruction.' 
                           'Default = 1, no shrinking')
        form.addParam('symmetry', TextParam, default='c1',
                      label='Point group symmetry',
                      help='Specify the symmetry.Choices are: c(n), d(n), h(n), tet, oct, icos')        
        form.addParallelSection(threads=3, mpi=0)
        
    def _insertAllSteps(self):        
        eman2.loadEnvironment()
        self._prepareDefinition()
        self._insertSteps()

    def _prepareDefinition(self):

        # ToDo: create an Eman conversor and change this lines.
        image = self.getXmippStackFilename()
        imgsFn = os.path.abspath(image)
        
        #self._insertFunctionStep('genxmippstack')
        self._params = {'imgsFn': imgsFn,
                        'numberOfIterations': self.numberOfIterations.get(),
                        'numberOfModels': self.numberOfModels.get(),
                        'shrink': self.shrink.get(),
                        'symmetry': self.symmetry.get(),
                        'threads':self.numberOfThreads.get()
                       }

    def getXmippStackFilename(self):
        for cls in self.inputClasses.get():
            img = cls.getAverage()
            return img.getFileName()

    def _insertSteps(self):
        self._insertInitialModelStep()      
        self._insertFunctionStep('createOutput')

    def _insertInitialModelStep(self):
        self._enterWorkingDir()
        args = '--input %(imgsFn)s iter=%(numberOfIterations)d --tries=%(numberOfModels)d --sym=%(symmetry)s'
        if self.shrink > 1:
            args += ' --shrink=%(shrink)d'
        if self.numberOfThreads > 1:
            args += ' --parallel=thread:%(threads)d'
        program = eman2.getEmanProgram('e2initialmodel.py')
        self._insertRunJobStep(program, args % self._params)
                
    def createOutput(self):
        self._leaveWorkingDir()
        classes2DSet = self.inputClasses.get()
        #volumes = EmanSetOfVolumes(self._getPath('scipion_volumes.json'))
        volumes = self._createSetOfVolumes()
        volumes.setSamplingRate(self.inputClasses.get().getImages().getSamplingRate())
        
        for k in range(1, self.numberOfModels.get() + 1):
            volFn = self._getPath('initial_models/model_00_%02d.hdf' % k)
            vol = Volume()
            vol.setFileName(volFn)
            volumes.append(vol)

        self._defineOutputs(outputVolumes=volumes)
        self._defineSourceRelation(classes2DSet, volumes)
        
    def _summary(self):
        summary = []
        if not hasattr(self, 'outputVolumes'):
            summary.append("Output volumes not ready yet.")
        else:
            summary.append("Input Images: %s" % self.inputClasses.get().getNameId())
            summary.append("Output initials volumes: %s" % self.outputVolumes.get())
        return summary
