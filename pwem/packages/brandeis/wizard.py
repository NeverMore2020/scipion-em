# **************************************************************************
# *
# * Authors:     Jose Gutierrez (jose.gutierrez@cnb.csic.es)
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
This module implement some wizards
"""

import os
import Tkinter as tk
import ttk

from pyworkflow.em.constants import *
from constants import *

import pyworkflow.gui.dialog as dialog
from pyworkflow.em.wizard import *
from protocol_frealign import ProtFrealign

from pyworkflow import findResource


# class FrealignRadiiWizard(radiiWizard):
#     _targets = [(ProtFrealign, ['innerRadius', 'outerRadius'])]
#     
#     def _getProvider(self, protocol):
#         """ This should be implemented to return the list
#         of object to be displayed in the tree.
#         """
#         if protocol.input3DReferences.hasValue():
#             vols = []
#             vols.append(protocol.input3DReferences.get().clone())
#             return ListTreeProvider(vols)
#         return None
# 
# 
# class FrealignBandpassWizard(bandpassParticleWizard):
#     _targets = [(ProtFrealign, ['lowResolRefine', 'highResolRefine'])]
#     
#     def show(self, form):
#         protocol = form.protocol
#         provider = self._getProvider(protocol)
# 
#         if provider is not None:
#             self.mode = FILTER_LOW_PASS_NO_DECAY
#             
#             args = {'mode':  self.mode,                   
#                     'highFreq': protocol.highResolRefine.get(),
#                     'lowFreq': protocol.lowResolRefine.get(),
#                     'unit': UNIT_ANGSTROM
#                     }
#             
#             args['showDecay'] = False
# 
#             d = bandPassFilterDialog(form.root, provider, **args)
#             
#             if d.resultYes():               
#                 
#                 form.setVar('highResolRefine', 1/d.getHighFreq()*d.itemDim)
#                 form.setVar('lowResolRefine', 1/d.getLowFreq()*d.itemDim)
#                 
#         else:
#             dialog.showWarning("Input particles", "Select particles first", form.root)  
# 
# class FrealignVolBandpassWizard(bandpassVolumesWizard):
#     _targets = [(ProtFrealign, ['resolution'])]
#     
#     def _getProvider(self, protocol):
#         """ This should be implemented to return the list
#         of object to be displayed in the tree.
#         """
#         if protocol.input3DReferences.hasValue():
#             vols = []
#             vols.append(protocol.input3DReferences.get().clone())
#             return ListTreeProvider(vols)
#         return None
#     
#     def show(self, form):
#         protocol = form.protocol
#         provider = self._getProvider(protocol)
# 
#         if provider is not None:
#             self.mode = FILTER_LOW_PASS_NO_DECAY
#             
#             args = {'mode':  self.mode,                   
#                     'lowFreq': protocol.resolution.get(),
#                     'unit': UNIT_ANGSTROM
#                     }
#             
#             args['showHighFreq'] = False
#             args['showDecay'] = False
# 
#             d = bandPassFilterDialog(form.root, provider, **args)
#             
#             if d.resultYes():
# #                print "SAMPLING RATE !!", d.samplingRate
# #                print "ITEM DIM !!", d.itemDim
# #                1/self.hfSlider.get()*self.itemDim 
#                 
#                 form.setVar('resolution', 1/d.getLowFreq()*d.itemDim)
#                 
#         else:
#             dialog.showWarning("Input volumes", "Select volumes first", form.root)  
#     
#     @classmethod    
#     def getView(self):
#         return "wiz_volume_bandpass"   