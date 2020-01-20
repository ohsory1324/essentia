#!/usr/bin/env python

# Copyright (C) 2006-2016  Music Technology Group - Universitat Pompeu Fabra
#
# This file is part of Essentia
#
# Essentia is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the Affero GNU General Public License
# version 3 along with this program. If not, see http://www.gnu.org/licenses/


from essentia_test import *
from essentia.streaming import *


class TestVectorRealToTensor(TestCase):

    def identityOperation(self, frameSize=1024, hopSize=512, patchSize=187,
                          lastPatchMode='discard', accumulate=False):

        batchHopSize = -1 if accumulate else 1

        filename = join(testdata.audio_dir, 'recorded', 'cat_purrrr.wav')

        ml = MonoLoader(filename=filename)
        fc = FrameCutter(frameSize=frameSize, hopSize=hopSize)
        vtt = VectorRealToTensor(shape=[batchHopSize, 1, patchSize, frameSize],
                                 lastPatchMode=lastPatchMode)
        ttv = TensorToVectorReal()

        pool = Pool()

        ml.audio   >> fc.signal
        fc.frame   >> vtt.frame
        fc.frame   >> (pool, "framesIn")
        vtt.tensor >> ttv.tensor
        ttv.frame  >> (pool, "framesOut")

        run(ml)

        return pool['framesOut'], pool['framesIn']


    def testFramesToTensorAndBackToFramesDiscard(self):
        # Patch size equal to number of frames
        numberOfFrames = 43
        found, expected = self.identityOperation(patchSize=numberOfFrames,
                                                 lastPatchMode='discard')
        self.assertAlmostEqualMatrix(found, expected, 1e-8)

        # Default patch size. The expected output is trimmed to the found
        # shape as with lastPatchMode='discard' the remaining frames not
        # fitting into a patch are discarded.
        found, expected = self.identityOperation(frameSize=256, hopSize=128,
                                                 lastPatchMode='discard')
        self.assertAlmostEqualMatrix(found, expected[:found.shape[0], :], 1e-8)

        # Increse aquire size
        found, expected = self.identityOperation(frameSize=256, hopSize=128,
                                                 patchSize=300, lastPatchMode='discard')
        self.assertAlmostEqualMatrix(found, expected[:found.shape[0], :], 1e-8)

    def testFramesToTensorAndBackToFramesDiscardAccumulate(self):
        # Repeat the tests in accumulate mode. Here the patches are stored
        # internally and pushed at once at the end of the stream.
        numberOfFrames = 43
        found, expected = self.identityOperation(patchSize=numberOfFrames,
                                                 lastPatchMode='discard',
                                                 accumulate=True)
        self.assertAlmostEqualMatrix(found, expected, 1e-8)

        found, expected = self.identityOperation(frameSize=256, hopSize=128,
                                                 lastPatchMode='discard',
                                                 accumulate=True)
        self.assertAlmostEqualMatrix(found, expected[:found.shape[0], :], 1e-8)

        found, expected = self.identityOperation(frameSize=256, hopSize=128,
                                                 patchSize=300, lastPatchMode='discard',
                                                 accumulate=True)
        self.assertAlmostEqualMatrix(found, expected[:found.shape[0], :], 1e-8)

    def testFramesToTensorAndBackToFramesRepeat(self):
        # Reapeat the experiments with lastPatchMode='repeat'. Now the found
        # patches will be equal or bigger then the expected ones. They will
        # be trimmed to fit the expected output. 
        numberOfFrames = 43
        found, expected = self.identityOperation(patchSize=numberOfFrames,
                                                 lastPatchMode='repeat')
        self.assertAlmostEqualMatrix(found, expected, 1e-8)

        found, expected = self.identityOperation(frameSize=256, hopSize=128,
                                                 lastPatchMode='repeat')
        self.assertAlmostEqualMatrix(found[:expected.shape[0], :], expected, 1e-8)

        found, expected = self.identityOperation(frameSize=256, hopSize=128,
                                                 patchSize=300, lastPatchMode='repeat')
        self.assertAlmostEqualMatrix(found[:expected.shape[0], :], expected, 1e-8)

    def testFramesToTensorAndBackToFramesRepeatAccumulate(self):
        # Repeat the text with lastPatchMode='repeat' and in accumulate mode.
        numberOfFrames = 43
        found, expected = self.identityOperation(patchSize=numberOfFrames,
                                                 lastPatchMode='repeat',
                                                 accumulate=True)
        self.assertAlmostEqualMatrix(found, expected, 1e-8)

        found, expected = self.identityOperation(frameSize=256, hopSize=128,
                                                 lastPatchMode='repeat',
                                                 accumulate=True)
        self.assertAlmostEqualMatrix(found[:expected.shape[0], :], expected, 1e-8)

        found, expected = self.identityOperation(frameSize=256, hopSize=128,
                                                 patchSize=300, lastPatchMode='repeat',
                                                 accumulate=True)
        self.assertAlmostEqualMatrix(found[:expected.shape[0], :], expected, 1e-8)

    def testInvalidParam(self):
        # VectorRealToTensor only supports single chanel data
        self.assertConfigureFails(VectorRealToTensor(), {'shape': [1, 2, 1, 1]})

        # dimensions have to be different from 0.
        self.assertConfigureFails(VectorRealToTensor(), {'shape': [0, 1, 1, 1]})
        self.assertConfigureFails(VectorRealToTensor(), {'shape': [1, 0, 1, 1]})
        self.assertConfigureFails(VectorRealToTensor(), {'shape': [1, 1, 0, 1]})
        self.assertConfigureFails(VectorRealToTensor(), {'shape': [1, 1, 0, 0]})

    def testRepeatMode(self):
        # Our test audio has 430 frames. If patchSize is set to 428 with
        # lastPatchMode='repeat' VectorRealToTensor will produce a second
        # patch of 428 frames by looping the last 2 spare samples.
        numberOfFrames = 428
        loopFrames = 430 - numberOfFrames
        
        found, expected = self.identityOperation(patchSize=numberOfFrames,
                                                 lastPatchMode='repeat')

        expected = numpy.vstack([expected[:numberOfFrames]] +  #  frames for the first patch
                                [expected[numberOfFrames:numberOfFrames + loopFrames]] *  # remaining frames for the second patch
                                (numberOfFrames // loopFrames))  # number of repetitions to fill the second patch

        self.assertAlmostEqualMatrix(found, expected, 1e-8)


suite = allTests(TestVectorRealToTensor)

if __name__ == '__main__':
    TextTestRunner(verbosity=2).run(suite)
