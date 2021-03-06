import sys, time
import numpy as np
import matplotlib.pyplot as plt
import h5py

sys.path.append('../../')
from py2Periodic.physics import hydrostaticWaveEqn_xy
from py2Periodic.physics import linearizedBoussinesq_xy
from numpy import pi

# Parameters:
Lx = 1600e3
(alpha, f0) = (1, 1e-4)
sigma = f0*np.sqrt(1+alpha)
kappa = 32.0*pi / (Lx*np.sqrt(alpha))

dt = 0.05 * 2.0*pi/f0
(waveVisc, waveViscOrder) = (1e24, 8.0)

stopTime = 256.0*pi/f0
nSteps = int(np.ceil(stopTime / dt))

saveTimes = np.array([0, 2, 4, 32, 128])*2.0*pi/sigma

# Generate param dictionaries, initialize models, and run.
hweParams = {
    'Lx'            : Lx,
    'waveVisc'      : waveVisc,
    'waveViscOrder' : waveViscOrder,
    'f0'          : f0,
    'sigma'       : sigma,
    'kappa'       : kappa, 
    'dt'          : dt, 
    'timeStepper' : 'ETDRK4', 
    'name'        : 'waveIsotropization',
}

lhbParams = {
    'Lx'          : Lx,
    'f0'          : f0,
    'kappa'       : kappa, 
    'dt'          : dt, 
    'timeStepper' : 'RK4', 
    'name'        : 'waveIsotropization',
}

hweItems = {'q': saveTimes, 'A': saveTimes}
lhbItems = {'q': saveTimes, 'u': saveTimes, 'v': saveTimes, 'p': saveTimes}

hwe = hydrostaticWaveEqn_xy.init_from_turb_endpoint(
        'strongTurbData.hdf5', 'ic_01', **hweParams)

lhb = linearizedBoussinesq_xy.init_from_turb_endpoint(
        'strongTurbData.hdf5', 'ic_01', **lhbParams)

hwe.run(nSteps=nSteps, nPlots=128, nLogs=128, runName='hwe', itemsToSave=hweItems)
lhb.run(nSteps=nSteps, nPlots=128, nLogs=128, runName='lhb', itemsToSave=lhbItems)
