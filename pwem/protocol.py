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
In this module are protocol base classes related to EM.
Them should be sub-classes in the different sub-packages from
each EM-software packages.
"""

import os
import shutil
from pyworkflow.object import String, Float
from pyworkflow.protocol import *
from pyworkflow.protocol.params import *
from constants import *
from data import Micrograph, SetOfMicrographs, SetOfImages, Image, SetOfParticles, SetOfVolumes, Volume, SetOfCoordinates
from pyworkflow.utils.path import removeBaseExt, join, basename



class EMProtocol(Protocol):
    """ Base class to all EM protocols.
    It will contains some common functionalities. 
    """
    def __init__(self, **args):
        Protocol.__init__(self, **args)
        
    def _createSetOfMicrographs(self, suffix=''):
        micSet = SetOfMicrographs()
        micSet.setFileName(self._getPath('micrographs%s.sqlite' % suffix)) 
        return micSet

    def _createSetOfCoordinates(self, suffix=''):
        coordSet = SetOfCoordinates()
        coordSet.setFileName(self._getPath('coordinates%s.sqlite' % suffix)) 
        return coordSet
    
    def _createSetOfParticles(self, suffix=''):
        imgSet = SetOfParticles()
        imgSet.setFileName(self._getPath('particles%s.sqlite' % suffix)) 
        return imgSet

    def _createSetOfClasses2D(self, suffix=''):
        classes2DSet = SetOfClasses2D()
        classes2DSet.setFileName(self._getPath('classes2D%s.sqlite' % suffix)) 
        return classes2DSet

    def _createSetOfVolumes(self, suffix=''):
        volSet = SetOfVolumes()
        volSet.setFileName(self._getPath('volumes%s.sqlite' % suffix)) 
        return volSet


class DefImportMicrographs(Form):
    """Create the definition of parameters for
    the ImportMicrographs protocol
    """
    def __init__(self):
        Form.__init__(self)
    
        self.addSection(label='Input')
        self.addParam('pattern', StringParam, label="Pattern")
#         self.addParam('tiltPairs', BooleanParam, default=False, important=True,
#                    label='Are micrographs tilt pairs?')
        
 #       self.addSection(label='Microscope description')
        self.addParam('voltage', FloatParam, default=200,
                   label='Microscope voltage (in kV)')
        self.addParam('sphericalAberration', FloatParam, default=2.26,
                   label='Spherical aberration (in mm)')
        self.addParam('samplingRateMode', EnumParam, default=SAMPLING_FROM_IMAGE,
                   label='Sampling rate mode',
                   choices=['From image', 'From scanner'])
        self.addParam('samplingRate', FloatParam, default=1, 
                   label='Sampling rate (A/px)', 
                   condition='samplingRateMode==%d' % SAMPLING_FROM_IMAGE)
        self.addParam('magnification', IntParam, default=60000,
                   label='Magnification rate', 
                   condition='samplingRateMode==%d' % SAMPLING_FROM_SCANNER)
        self.addParam('scannedPixelSize', FloatParam, default=7.0,
                   label='Scanned pixel size', 
                   condition='samplingRateMode==%d' % SAMPLING_FROM_SCANNER)
        

class ProtImportMicrographs(EMProtocol):
    """Protocol to import a set of micrographs in the project"""
    _definition = DefImportMicrographs()
    _label = 'Import micrographs'
    _path = join('Micrographs', 'Import')
    
    def __init__(self, **args):
        EMProtocol.__init__(self, **args)         
        
    def _defineSteps(self):
        self._insertFunctionStep('importMicrographs', self.pattern.get(),
                                self.voltage.get(), self.sphericalAberration.get(),
                                self.samplingRate.get(), self.scannedPixelSize.get(),
                                self.magnification.get())
        
    def importMicrographs(self, pattern, voltage, sphericalAberration, 
                          samplingRate, scannedPixelSize, magnification):
        """ Copy micrographs matching the filename pattern
        Register other parameters.
        """
        from glob import glob
        filePaths = glob(pattern)
        
        if len(filePaths) == 0:
            raise Exception('importMicrographs:There is not filePaths matching pattern')
        
        micSet = self._createSetOfMicrographs() 
        # Setting microscope properties
        micSet._microscope.magnification.set(magnification)
        micSet._microscope.voltage.set(voltage)
        micSet._microscope.sphericalAberration.set(sphericalAberration)
        
        if self.samplingRateMode == SAMPLING_FROM_IMAGE:
            micSet.setSamplingRate(samplingRate)
        else:
            micSet.setScannedPixelSize(scannedPixelSize)
        outFiles = [micSet.getFileName()]
       
        filePaths.sort()
        for f in filePaths:
            dst = self._getPath(basename(f))            
            shutil.copyfile(f, dst)
            mic = Micrograph()
            mic.setFileName(dst)
            micSet.append(mic)
            outFiles.append(dst)
        
        micSet.write()
        self._defineOutputs(outputMicrographs=micSet)
        
        return outFiles
    
    def getFiles(self):
        return self.outputMicrographs.getFiles()

    def _summary(self):
        summary = []

        if not hasattr(self, 'outputMicrographs'):
            summary.append("Output micrographs not ready yet.") 
        else:
            summary.append("Import of %d micrographs from %s" % (self.outputMicrographs.getSize(), self.pattern.get()))
            summary.append("Sampling rate : %f" % self.samplingRate.get())
        
        return summary
    
    def _validate(self):
        validateMsgs = []
        if self.pattern.get() == "":
            validateMsgs.append('Pattern cannot be EMPTY.')
        return validateMsgs


class DefImportParticles(Form):
    """Create the definition of parameters for
    the ImportParticles protocol
    """
    def __init__(self):
        Form.__init__(self)
    
        self.addSection(label='Input')
        self.addParam('pattern', StringParam, 
                      label="Pattern")        
        self.addParam('samplingRate', FloatParam,
                   label='Sampling rate (A/px)')


class ProtImportParticles(EMProtocol):
    """Protocol to import a set of particles in the project"""
    _definition = DefImportParticles()
    _label = 'Import images'
    _path = join('Images', 'Import')
    
    def __init__(self, **args):
        EMProtocol.__init__(self, **args)         
        
    def _defineSteps(self):
        self._insertFunctionStep('importParticles', self.pattern.get(), self.samplingRate.get())
        
    def importParticles(self, pattern, samplingRate):
        """ Copy images matching the filename pattern
        Register other parameters.
        """
        from glob import glob
        filePaths = glob(pattern)
        if len(filePaths) == 0:
            raise Exception('importParticles:There are not filePaths matching pattern')
        imgSet = self._createSetOfParticles()
        imgSet.setSamplingRate(samplingRate)

        outFiles = [imgSet.getFileName()]
        
        for f in filePaths:
            dst = self._getPath(basename(f))            
            shutil.copyfile(f, dst)
            img = Image()
            img.setFileName(dst)
            imgSet.append(img)
            outFiles.append(dst)
                       
        imgSet.write()
        self._defineOutputs(outputParticles=imgSet)
        
        return outFiles
    
    def getFiles(self):
        return self.outputParticles.getFiles()


class DefImportVolumes(Form):
    """Create the definition of parameters for
    the ImportVolumes protocol
    """
    def __init__(self):
        Form.__init__(self)
    
        self.addSection(label='Input')
        self.addParam('pattern', StringParam, label="Pattern")
        self.addParam('samplingRate', FloatParam,
                   label='Sampling rate (A/px)')
        

class ProtImportVolumes(EMProtocol):
    """Protocol to import a set of volumes in the project"""
    _definition = DefImportVolumes()
    _label = 'Import volumes'
    _path = join('Volumes', 'Import')
    
    def __init__(self, **args):
        EMProtocol.__init__(self, **args)         
        
    def _defineSteps(self):
        self._insertFunctionStep('importVolumes', self.pattern.get(), self.samplingRate.get())
        
    def importVolumes(self, pattern, samplingRate):
        """ Copy volumes matching the filename pattern
        Register other parameters.
        """
        from glob import glob
        filePaths = glob(pattern)
        if len(filePaths) == 0:
            raise Exception('importVolumes:There is not filePaths matching pattern')
        
        volSet = self._createSetOfVolumes()
        
        outFiles = [volSet.getFileName()]
        
        filePaths.sort()
        for f in filePaths:
            dst = self._getPath(basename(f))            
            shutil.copyfile(f, dst)
            vol = Volume(dst)
            volSet.append(vol)
            outFiles.append(dst)  
        
        volSet.write()
        self._defineOutputs(outputVolumes=volSet)
        
        return outFiles
    
    def getFiles(self):
        return self.outputVolumes.getFiles()

    def _summary(self):
        summary = []

        if not hasattr(self, 'outputVolumes'):
            summary.append("Output volume not ready yet.") 
        else:
            summary.append("Import of %d volumes from %s" % (self.outputVolumes.getSize(), self.pattern.get()))
            summary.append("Sampling rate : %f" % self.samplingRate.get())
        
        return summary
    
    def _validate(self):
        validateMsgs = []
        if self.pattern.get() == "":
            validateMsgs.append('Pattern cannot be EMPTY.')
        return validateMsgs

class DefCTFMicrographs(Form):
    """ Create the definition of parameters for
    the XmippCtfMicrographs protocol.
    """
    def __init__(self):
        Form.__init__(self)
    
        self.addSection(label='CTF Estimation')
        
        self.addParam('inputMicrographs', PointerParam, important=True,
                      label="Input Micrographs", pointerClass='SetOfMicrographs')
        self.addParam('ampContrast', FloatParam, default=0.1,
                      label='Amplitude Contrast',
                      help='It should be a positive number, typically between 0.05 and 0.3.')
        self.addParam('lowRes', FloatParam, default=0.05,
                      label='Lowest resolution',
                      help='Give a value in digital frequency (i.e. between 0.0 and 0.5). '
                           'This cut-off prevents the typically peak at the center of the PSD '
                           'to interfere with CTF estimation. The default value is 0.05, but for '
                           'micrographs with a very fine sampling this may be lowered towards 0.0')
        self.addParam('highRes', FloatParam, default=0.35,
                      label='Highest resolution', 
                      help='Give a value in digital frequency (i.e. between 0.0 and 0.5). '
                           'This cut-off prevents high-resolution terms where only noise exists '
                           'to interfere with CTF estimation. The default value is 0.35, but it should '
                           'be increased for micrographs with signals extending beyond this value. '
                           'However, if your micrographs extend further than 0.35, you should consider '
                           'sampling them at a finer rate.')
        self.addParam('minDefocus', FloatParam, default=0.5,
                      label='Minimum defocus to search (in microns)',
                      help=' Minimum defocus value (in microns) to include in defocus search. ' 
                      'Underfocus is represented by a positive number.',
                      expertLevel=LEVEL_ADVANCED)
        self.addParam('maxDefocus', FloatParam, default=10.,
                      label='Maximum defocus to search (in microns)',
                      help='Maximum defocus value (in microns) to include in defocus search. '
                           'Underfocus is represented by a positive number.',
                      expertLevel=LEVEL_ADVANCED)
        self.addParam('windowSize', IntParam, default=256,
                      label='Window size',
                      help='The PSD is estimated from small patches of this size. Bigger patches '
                           'allow identifying more details. However, since there are fewer windows, '
                           'estimations are noisier',
                      expertLevel=LEVEL_ADVANCED)
        
        self.addParallelSection(threads=2, mpi=1)       


class ProtCTFMicrographs(EMProtocol):
    """ Base class for all protocols that estimates the CTF"""
    _definition = DefCTFMicrographs()

    def __init__(self, **args):
        EMProtocol.__init__(self, **args)
        self.stepsExecutionMode = STEPS_PARALLEL 
    
    def _getMicrographDir(self, mic):
        """ Return an unique dir name for results of the micrograph. """
        return self._getExtraPath(removeBaseExt(mic.getFileName()))        
        
    def _iterMicrographs(self):
        """ Iterate over micrographs and yield
        micrograph name and a directory to process.
        """
        for mic in self.inputMics:
            micFn = mic.getFileName()
            micDir = self._getExtraPath(removeBaseExt(micFn)) 
            yield (micFn, micDir, mic)  
        
    def _defineSteps(self):
        """ Insert the steps to perform ctf estimation on a set of micrographs.
        """
        # Get pointer to input micrographs 
        self.inputMics = self.inputMicrographs.get() 
                                
        self._params = {'voltage': self.inputMics._microscope.voltage.get(),
                        'sphericalAberration': self.inputMics._microscope.sphericalAberration.get(),
                        'magnification': self.inputMics._microscope.magnification.get(),
                        'samplingRate': self.inputMics.getSamplingRate(),
                        'scannedPixelSize': self.inputMics.getScannedPixelSize(),
                        'windowSize': self.windowSize.get(),
                        'ampContrast': self.ampContrast.get(),
                        'lowRes': self.lowRes.get(),
                        'highRes': self.highRes.get(),
                        # Convert from microns to Amstrongs
                        'minDefocus': self.minDefocus.get() * 1e+4, 
                        'maxDefocus': self.maxDefocus.get() * 1e+4
                       }
        
        self._prepareCommand()
        deps = [] # Store all steps ids, final step createOutput depends on all of them
        # For each micrograph insert the steps to process it
        for micFn, micDir, _ in self._iterMicrographs():
            # CTF estimation with Xmipp
            stepId = self._insertFunctionStep('_estimateCTF', micFn, micDir,
                                              prerequisites=[]) # Make estimation steps indepent between them
            deps.append(stepId)
        # Insert step to create output objects       
        self._insertFunctionStep('createOutput', prerequisites=deps)
            
    def _summary(self):
        summary = []
        if not self.inputMicrographs.hasValue():
            summary.append("No <Input Micrographs> selected.")
        else:
            summary.append("CTF estimation of %d micrographs." % self.inputMicrographs.get().getSize())
            summary.append("Input micrographs: " + self.inputMicrographs.get().getNameId())
        return summary
                
    def _prepareCommand(self):
        """ This function should be implemented to prepare the
        arguments template if doesn't change for each micrograph
        After this method self._program and self._args should be set. 
        """
        pass
    
    def _estimateCTF(self, micFn, micDir):
        """ Do the CTF estimation with the specific program
        and the parameters required.
        Params:
         micFn: micrograph filename
         micDir: micrograph directory
        """
        raise Exception("_estimateCTF should be implemented")


class ProtPreprocessMicrographs(EMProtocol):
    pass


class ProtExtractParticles(EMProtocol):
    pass


class DefProcessParticles(Form):
    """ Create the definition of parameters for
    the ProtProcessParticles protocol.
    """
    def __init__(self):
        Form.__init__(self)
    
        self.addSection(label='Input')
        
        self.addParam('inputParticles', PointerParam, important=True,
                      label="Input Particles", pointerClass='SetOfParticles')
        
        self._addProcessParam()
        
        self.addParallelSection(threads=2, mpi=1)
        
    def _addProcessParam(self):
        """ This method should be implemented by subclasses
        to add other parameter relatives to the specific operation."""
        pass  
        
        
class ProtProcessParticles(EMProtocol):
    """ This class will serve as a base for all protocol
    that performs some operation on Partices (i.e. filters, mask, resize, etc)
    It is mainly defined by an inputParticles and outputParticles.
    """
    pass


class ProtFilterParticles(ProtProcessParticles):
    """ This is the base for the branch of filters, 
    between the ProtPreprocessParticles """
    pass


class ProtParticlePicking(EMProtocol):

    def _summary(self):
        summary = []
        if not hasattr(self, 'outputCoordinates'):
            summary.append("Output coordinates not ready yet.") 
        else:
            summary.append("Input micrographs: " + self.inputMicrographs.get().getNameId())
            summary.append("Number of particles manually picked: %d (from %d micrographs)" % (self.outputCoordinates.getSize(), self.inputMicrographs.get().getSize()))
        return summary


class ProtAlign(EMProtocol):
    pass


class ProtClassify(EMProtocol):
    pass


class ProtAlignClassify(EMProtocol):
    pass

class ProtInitialVolume(EMProtocol):
    pass

class ProtRefine3D(EMProtocol):
    pass

class ProtClassify3D(EMProtocol):
    pass
