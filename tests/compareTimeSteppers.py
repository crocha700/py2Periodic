import sys; sys.path.append('../py2Periodic/')
import twoDimensionalTurbulence
import numpy as np; from numpy import pi
import time
import matplotlib.pyplot as plt

answerRefinement = 1e2
nSteps = 1e3

commonParams = {
    'dt'        : 1.0e-1, 
    'nx'        : 128,
    'Lx'        : 2.0*pi, 
    'visc'      : 4.0e-4, 
    'viscOrder' : 4.0,
    'nThreads'  : 4,
}

# Instantiate models with various time-steppers.
answerParams = commonParams.copy(); del answerParams['dt']
m_answer = twoDimensionalTurbulence.model(timeStepper = 'RK4', 
    dt = commonParams['dt']/answerRefinement,
    **answerParams)

m_FE = twoDimensionalTurbulence.model(timeStepper = 'forwardEuler',
    **commonParams)

m_RK4 = twoDimensionalTurbulence.model(timeStepper = 'RK4',
    **commonParams)

m_RKW3 = twoDimensionalTurbulence.model(timeStepper = 'RKW3',
    **commonParams)

m_ETDRK4 = twoDimensionalTurbulence.model(timeStepper = 'ETDRK4',
    **commonParams)

# Define initial condition
q0 = np.random.standard_normal(m_FE.physSolnShape)

# Set the same initial condition for all models
m_FE.set_physical_soln(q0)
m_RK4.set_physical_soln(q0)
m_RKW3.set_physical_soln(q0)
m_ETDRK4.set_physical_soln(q0)

# Run the models
nSteps = 1e3

print("\nRunning 'answer model' with RK4 time-stepping.")
timer = time.time()
m_answer.run_nSteps(nSteps=nSteps*answerRefinement)
print("Total RK4 'answer model' time = {:.3f} s".format(time.time()-timer))

print("\nRunning model with forward Euler time-stepping.")
timer = time.time()
m_FE.run_nSteps(nSteps=nSteps)
print("Total forwardEuler time = {:.3f} s".format(time.time()-timer))

print("\nRunning model with RK4 time-stepping.")
timer = time.time()
m_RK4.run_nSteps(nSteps=nSteps)
print("Total RK4 time = {:.3f} s".format(time.time()-timer))

print("\nRunning model with RKW3 time-stepping.")
timer = time.time()
m_RKW3.run_nSteps(nSteps=nSteps)
print("Total RK4 time = {:.3f} s".format(time.time()-timer))

print("\nRunning model with ETDRK4 time-stepping.")
timer = time.time()
m_ETDRK4.run_nSteps(nSteps=nSteps)
print("Total ETDRK4 time = {:.3f} s".format(time.time()-timer))

# Update variables like vorticity, speed, etc
m_FE.update_state_variables()
m_RK4.update_state_variables()
m_ETDRK4.update_state_variables()
m_RKW3.update_state_variables()

# Plot the result
fig = plt.figure('Time-stepper comparison', figsize=(12, 12)); plt.clf()

plt.subplot(221)
plt.title('forward Euler')
plt.pcolormesh(m_FE.xx, m_FE.yy, np.abs(m_FE.q-m_answer.q), cmap='YlGnBu_r')

plt.subplot(222)
plt.title('RK4')
plt.pcolormesh(m_RK4.xx, m_RK4.yy, np.abs(m_RK4.q-m_answer.q), cmap='YlGnBu_r')

plt.subplot(223)
plt.title('ETDRK4')
plt.pcolormesh(m_ETDRK4.xx, m_ETDRK4.yy, np.abs(m_ETDRK4.q-m_answer.q), cmap='YlGnBu_r')

plt.subplot(224)
plt.title('RKW3')
plt.pcolormesh(m_RKW3.xx, m_RKW3.yy, np.abs(m_RKW3.q-m_answer.q), cmap='YlGnBu_r')

print("\nClose the figure to end the program")
plt.show()
