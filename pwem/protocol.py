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
from glob import glob
from pyworkflow.object import String, Float
from pyworkflow.protocol import *
from pyworkflow.protocol.params import *
from constants import *
from data import * 
from pyworkflow.utils.path import removeBaseExt, join, basename, cleanPath



class EMProtocol(Protocol):
    """ Base class to all EM protocols.
    It will contains some common functionalities. 
    """
    def __init__(self, **args):
        Protocol.__init__(self, **args)
        
    def __createSet(self, SetClass, template, suffix):
        """ Create a set and set the filename using the suffix. 
        If the file exists, it will be delete. """
        setObj = SetClass()
        setFn = self._getPath(template % suffix)
        cleanPath(setFn)
        setObj.setFileName(setFn)
        return setObj
        
    def _createSetOfMicrographs(self, suffix=''):
        return self.__createSet(SetOfMicrographs, 'micrographs%s.sqlite', suffix)

    def _createSetOfCoordinates(self, suffix=''):
        return self.__createSet(SetOfCoordinates, 'coordinates%s.sqlite', suffix)
    
    def _createSetOfParticles(self, suffix=''):
        return self.__createSet(SetOfParticles, 'particles%s.sqlite', suffix)

    def _createSetOfClasses2D(self, suffix=''):
        return self.__createSet(SetOfClasses2D, 'classes2D%s.sqlite', suffix)

    def _createSetOfVolumes(self, suffix=''):
        return self.__createSet(SetOfVolumes, 'volumes%s.sqlite', suffix)
    
    def _createSetOfCTF(self, suffix=''):
        return self.__createSet(SetOfCTF, 'ctfs%s.sqlite', suffix)
    
    def _defineDataSource(self, srcObj, dstObj):
        """ Add a DATASOURCE relation between srcObj and dstObj """
        self.mapper.insertRelation(RELATION_DATASOURCE, self, srcObj, dstObj)
        #self.mapper.commit()
        
class ProtImportImages(EMProtocol):
    """Common protocol to import a set of images in the project"""

        
    def _defineParams(self, form):
        form.addSection(label='Input')
        form.addParam('pattern', StringParam, label="Pattern",
                      help="The pattern (with wildcard expansion) of the files to import\n"
                            "For example: \n*data/particles/***.spi* \n or \n*~/Micrographs/mic/***.mrc*")
        form.addParam('checkStack', BooleanParam, label="Check stack files?", default=False)
        form.addParam('voltage', FloatParam, default=200,
                   label='Microscope voltage (in kV)')
        form.addParam('sphericalAberration', FloatParam, default=2.26,
                   label='Spherical aberration (in mm)')
        form.addParam('ampContrast', FloatParam, default=0.1,
                      label='Amplitude Contrast',
                      help='It should be a positive number, typically between 0.05 and 0.3.')
        
    def importImages(self, createSetFunction, pattern, checkStack, voltage, sphericalAberration, amplitudeContrast):
        """ Copy images matching the filename pattern
        Register other parameters.
        """
        from pyworkflow.em import findClass
        filePaths = glob(pattern)
        
        imgSet = createSetFunction 
        # Setting Acquisition properties
        imgSet._acquisition.voltage.set(voltage)
        imgSet._acquisition.sphericalAberration.set(sphericalAberration)
        imgSet._acquisition.amplitudeContrast.set(amplitudeContrast)
        
        # Call a function that should be implemented by each subclass
        self._setOtherPars(imgSet)
        
        outFiles = [imgSet.getFileName()]
        imgh = ImageHandler()
        n = 1
        
        filePaths.sort()
        for f in filePaths:
            dst = self._getPath(basename(f))            
            shutil.copyfile(f, dst)
            if self.checkStack:
                x, y, x, n = imgh.getDimensions(dst)
            if n > 1:
                for i in range(1, n+1):
                    img = findClass(self._className)()
                    img.setFileName(dst)
                    img.setIndex(i)
                    imgSet.append(img)
            else:
                img = findClass(self._className)()
                img.setFileName(dst)
                imgSet.append(img)
            outFiles.append(dst)
        
        imgSet.write()
        args = {}
        outputSet = self._getOutputSet(self._className)
        args[outputSet] = imgSet
        self._defineOutputs(**args)
        
        return outFiles
  
    def _validate(self):
        errors = []
        if self.pattern.get() == "":
            errors.append('The *pattern* cannot be empty.')
        else:
            filePaths = glob(self.pattern.get())
        
            if len(filePaths) == 0:
                errors.append('There are no files matching the *pattern*')

        return errors
    
    def getFiles(self):
        return getattr(self, self._getOutputSet(self._className)).getFiles()
    
    def _summary(self):
        summary = []

        outputSet = self._getOutputSet(self._className)
        if not hasattr(self, outputSet):
            summary.append("Output " + self._className + "s not ready yet.") 
        else:
            summary.append("Import of %d " % getattr(self, outputSet).getSize() + self._className + "s from %s" % self.pattern.get())
            summary.append("Sampling rate : %f" % self.samplingRate.get())
        
        return summary
    
    def _getOutputSet(self, setName):
        return "output" + setName + "s"
        
        
class ProtImportMicrographs(ProtImportImages):
    """Protocol to import a set of micrographs in the project"""

    _className = 'Micrograph'
    
    def _defineParams(self, form):
        ProtImportImages._defineParams(self, form)
        form.addParam('samplingRateMode', EnumParam, default=SAMPLING_FROM_IMAGE,
                   label='Sampling rate mode',
                   choices=['From image', 'From scanner'])
        form.addParam('samplingRate', FloatParam, default=1, 
                   label='Sampling rate (A/px)', 
                   condition='samplingRateMode==%d' % SAMPLING_FROM_IMAGE)
        form.addParam('magnification', IntParam, default=60000,
                   label='Magnification rate', 
                   condition='samplingRateMode==%d' % SAMPLING_FROM_SCANNER)
        form.addParam('scannedPixelSize', FloatParam, default=7.0,
                   label='Scanned pixel size', 
                   condition='samplingRateMode==%d' % SAMPLING_FROM_SCANNER)
        
        
    def _defineSteps(self):
        self._insertFunctionStep('importImages', self._createSetOfMicrographs(), self.pattern.get(),
                                self.checkStack.get(), self.voltage.get(), self.sphericalAberration.get(),
                                self.ampContrast.get()) #, self.samplingRate.get(), 
                                #self.scannedPixelSize.get(), self.magnification.get())
                                
    def _setOtherPars(self, micSet):
        micSet._acquisition.magnification.set(self.magnification.get())
        if self.samplingRateMode == SAMPLING_FROM_IMAGE:
            micSet.setSamplingRate(self.samplingRate.get())
        else:
            micSet.setScannedPixelSize(self.scannedPixelSize.get())   
      

class ProtImportParticles(ProtImportImages):
    """Protocol to import a set of particles in the project"""
 
    _className = 'Particle'
        
    def _defineParams(self, form):
        ProtImportImages._defineParams(self, form)
        form.addParam('samplingRate', FloatParam,
                   label='Sampling rate (A/px)')
        
        
    def _defineSteps(self):
        self._insertFunctionStep('importImages', self._createSetOfParticles(), self.pattern.get(),
                                self.checkStack.get(), self.voltage.get(), self.sphericalAberration.get(),
                                self.ampContrast.get())
        
    def _setOtherPars(self, imgSet):
        imgSet.setSamplingRate(self.samplingRate.get())
    
    def getFiles(self):
        return self.outputParticles.getFiles()
        

class ProtImportVolumes(EMProtocol):
    """Protocol to import a set of volumes in the project"""
    _label = 'Import volumes'
    _path = join('Volumes', 'Import')
    
    def __init__(self, **args):
        EMProtocol.__init__(self, **args)         
        
    def _defineSteps(self):
        self._insertFunctionStep('importVolumes', self.pattern.get(), self.samplingRate.get())
       
    def _defineParams(self, form):
        form.addSection(label='Input')
        form.addParam('pattern', StringParam, label="Pattern")
        form.addParam('samplingRate', FloatParam,
                   label='Sampling rate (A/px)')
        
         
    def createVolume(self, volumePath):
        """ Copy the volume to WorkingDir and create
        the volumen object.
        """
        dst = self._getPath(basename(volumePath))            
        shutil.copyfile(volumePath, dst)
        vol = Volume()
        vol.setFileName(dst)
        vol.setSamplingRate(self.samplingRate.get())
        return vol
        
    def importVolumes(self, pattern, samplingRate):
        """ Copy volumes matching the filename pattern
        Register other parameters.
        """
        from glob import glob
        filePaths = glob(pattern)
        filePaths.sort()
        n = len(filePaths)
        
        if n == 0:
            raise Exception('importVolumes:There is not filePaths matching pattern')
        
        else:
            # Create a set of volumes
            volSet = self._createSetOfVolumes()
            volSet.setSamplingRate(self.samplingRate.get())
            filePaths.sort()
            for f in filePaths:
                volSet.append(self.createVolume(f))
            
            volSet.write()
            self._defineOutputs(outputVolumes=volSet)
        
    
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
        errors = []
        if self.pattern.get() == "":
            errors.append('Pattern cannot be EMPTY.')
        return errors
        

class ProtInitialVolume(EMProtocol):
    """Protocol base for Initial volumes protocols"""
    pass


class ProtCTFMicrographs(EMProtocol):
    """ Base class for all protocols that estimates the CTF"""
    def __init__(self, **args):
        EMProtocol.__init__(self, **args)
        self.stepsExecutionMode = STEPS_PARALLEL
        
    def _defineParams(self, form):
        form.addSection(label='CTF Estimation')
        
        form.addParam('inputMicrographs', PointerParam, important=True,
                      label="Input Micrographs", pointerClass='SetOfMicrographs')
#        form.addParam('ampContrast', FloatParam, default=0.1,
#                      label='Amplitude Contrast',
#                      help='It should be a positive number, typically between 0.05 and 0.3.')
        form.addParam('lowRes', FloatParam, default=0.05,
                      label='Lowest resolution',
                      help='Give a value in digital frequency (i.e. between 0.0 and 0.5). '
                           'This cut-off prevents the typically peak at the center of the PSD '
                           'to interfere with CTF estimation. The default value is 0.05, but for '
                           'micrographs with a very fine sampling this may be lowered towards 0.0')
        form.addParam('highRes', FloatParam, default=0.35,
                      label='Highest resolution', 
                      help='Give a value in digital frequency (i.e. between 0.0 and 0.5). '
                           'This cut-off prevents high-resolution terms where only noise exists '
                           'to interfere with CTF estimation. The default value is 0.35, but it should '
                           'be increased for micrographs with signals extending beyond this value. '
                           'However, if your micrographs extend further than 0.35, you should consider '
                           'sampling them at a finer rate.')
        form.addParam('minDefocus', FloatParam, default=0.5,
                      label='Minimum defocus to search (in microns)',
                      help=' Minimum defocus value (in microns) to include in defocus search. ' 
                      'Underfocus is represented by a positive number.',
                      expertLevel=LEVEL_ADVANCED)
        form.addParam('maxDefocus', FloatParam, default=10.,
                      label='Maximum defocus to search (in microns)',
                      help='Maximum defocus value (in microns) to include in defocus search. '
                           'Underfocus is represented by a positive number.',
                      expertLevel=LEVEL_ADVANCED)
        form.addParam('windowSize', IntParam, default=256,
                      label='Window size',
                      help='The PSD is estimated from small patches of this size. Bigger patches '
                           'allow identifying more details. However, since there are fewer windows, '
                           'estimations are noisier',
                      expertLevel=LEVEL_ADVANCED)
        
        form.addParallelSection(threads=2, mpi=1)       
         
    
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
                                
        self._params = {'voltage': self.inputMics._acquisition.voltage.get(),
                        'sphericalAberration': self.inputMics._acquisition.sphericalAberration.get(),
                        'magnification': self.inputMics._acquisition.magnification.get(),
                        'samplingRate': self.inputMics.getSamplingRate(),
                        'scannedPixelSize': self.inputMics.getScannedPixelSize(),
                        'windowSize': self.windowSize.get(),
                        'ampContrast': self.inputMics._acquisition.amplitudeContrast.get(),
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
            summary.append("No *Input Micrographs* selected.")
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

class ProtPreprocessVolumes(EMProtocol):
    pass


class ProtExtractParticles(EMProtocol):
    pass


class ProtProcessParticles(EMProtocol):
    """ This class will serve as a base for all protocol
    that performs some operation on Partices (i.e. filters, mask, resize, etc)
    It is mainly defined by an inputParticles and outputParticles.
    """
    def _defineParams(self, form):
        form.addSection(label='Input')
        
        form.addParam('inputParticles', PointerParam, important=True,
                      label="Input Particles", pointerClass='SetOfParticles')
        # Hook that should be implemented in subclasses
        self._defineProcessParams(form)
        form.addParallelSection(threads=2, mpi=1)
        
    def _defineProcessParams(self, form):
        """ This method should be implemented by subclasses
        to add other parameter relatives to the specific operation."""
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
            #TODO: MOVE following line to manual picking
            summary.append("Input micrographs: " + self.inputMicrographs.get().getNameId())
            summary.append("Number of particles picked: %d (from %d micrographs)" % (self.outputCoordinates.getSize(), self.inputMicrographs.get().getSize()))
        return summary


class ProtCreateMask(EMProtocol):
    """ For those protocols who create mask as output. """
    pass

class ProtAlign(EMProtocol):
    """ This class will serve as a base for all protocols that align a set of 2D images.
    All Align protocols receive as input:
        A set of partices
    and will allow the option to generate the aligned particles.
    """
    def _defineParams(self, form):
        form.addSection(label='Input')
        
        form.addParam('inputParticles', PointerParam, important=True,
                      label="Input Particles", pointerClass='SetOfParticles')
        form.addParam('writeAlignedParticles', BooleanParam, default=True,
                      label="Write aligned particles?", 
                      help="If set to *Yes*, the aligment will be applied to \n"
                           "input particles and a new aligned set will be created.")
        # Hook that should be implemented in subclasses
        self._defineAlignParams(form)
        
    def _defineAlignParams(self, form):
        """ This method should be implemented by subclasses
        to add other parameter relatives to the specific align protocol."""
        pass  


class ProtClassify(EMProtocol):
    pass

class ProtUserSelection(EMProtocol):
    pass


class ProtAlignClassify(EMProtocol):
    pass

class ProtInitialVolume(EMProtocol):
    pass

class ProtRefine3D(EMProtocol):
    pass

class ProtClassify3D(EMProtocol):
    pass

class ProtValidate3D(EMProtocol):
    pass

class ProtCreateMask3D(EMProtocol):
    pass
