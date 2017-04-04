import doublyPeriodic
import numpy as np; from numpy import pi 
import time

class model(doublyPeriodic.model):
    def __init__(self, name = "linearizedBoussinesqEquationsExample", 
            # Grid parameters
            nx = 128, ny = None, Lx = 2.0*pi, Ly = None, 
            # Solver parameters
            t  = 0.0,  
            dt = 1.0e-2,                    # Numerical timestep
            step = 0, 
            timeStepper = "RK4",            # Time-stepping method
            nThreads = 1,                   # Number of threads for FFTW
            #
            # Near-inertial equation params: rotating and gravitating Earth 
            f0 = 1.0, 
            kappa = 4.0, 
            # Friction: 4th order hyperviscosity
            waveVisc = 1.0e-4,
            waveViscOrder = 2.0,
            waveDiff = 1.0e-4,
            waveDiffOrder = 2.0,
            meanVisc = 1.0e-4,
            meanViscOrder = 2.0,
        ):

        # Initialize super-class.
        doublyPeriodic.model.__init__(self, 
            physics = "single-mode hydrostatic Boussinesq equations" + \
                " linearized around two-dimensional turbulence",
            nVars = 4, 
            realVars = True,
            # Persistant doublyPeriodic initialization arguments 
            nx = nx, ny = ny, Lx = Lx, Ly = Ly, t = t, dt = dt, step = step,
            timeStepper = timeStepper, nThreads = nThreads, useFilter = useFilter,
        )

        # Physical parameters specific to the Physical Problem
        self.name = name
        self.f0 = f0
        self.kappa = kappa
        self.meanVisc = meanVisc
        self.meanViscOrder = meanViscOrder
        self.waveVisc = waveVisc
        self.waveViscOrder = waveViscOrder
        self.waveDiff = waveDiff
        self.waveDiffOrder = waveDiffOrder
            
        # Initialize the grid, transform methods, and problem-specific parameters
        self._init_model()
        
        ## Default vorticity initial condition: Gaussian vortex
        rVortex = self.Lx/20
        q0 = 0.1*self.f0 * exp( \
            - ( (self.XX-self.Lx/2.0)**2.0 + (self.YY-self.Ly/2.0)**2.0 ) \
            / (2*rVortex**2.0) \
                       )

        # Default wave initial condition: uniform velocity.
        u, v, p = self.make_plane_wave(4)
        self.set_uvp(u, v, p)
        self.set_q(q0)
        self.update_state_variables()
        
    # Methods - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def describe_physics(self):
        print("""
            This model solves the Boussinesq equations linearized around \n
            a two-dimensional barotropic flow for a single vertical mode. \n
            No viscosity or dissipation can be specified, since this is not \n
            required to stabilize the wave-field solutions. Arbitrary-order \n
            hyperdissipation can be specified for the two-dimensional flow. \n
            There are four prognostic variables: the two-dimensional flow, 
            the two horizontal velocity components u and v, and the pressure 
            field. The chosen vertical mode is represented by the single \n
            parameter kappa, which is the square root of the eigenvalue \n
            from the vertical mode eigenproblem.
        """)

    def _set_linear_coeff(self):
        """ Calculate the coefficient that multiplies the linear left hand
            side of the equation """
        # Two-dimensional turbulent viscosity.
        self.linearCoeff[:, :, 0] = -self.meanVisc \
            * (self.k**2.0 + self.l**2.0)**(self.meanViscOrder/2.0)

        self.linearCoeff[:, :, 1] = -self.waveVisc \
            * (self.k**2.0 + self.l**2.0)**(self.waveViscOrder/2.0)

        self.linearCoeff[:, :, 2] = -self.waveVisc \
            * (self.k**2.0 + self.l**2.0)**(self.waveViscOrder/2.0)

        self.linearCoeff[:, :, 3] = -self.waveDiff \
            * (self.k**2.0 + self.l**2.0)**(self.waveDiffOrder/2.0)

    def _calc_right_hand_side(self, soln, t):
        """ Calculate the nonlinear right hand side of PDE """
        # Views for clarity:
        qh = soln[:, :, 0]
        uh = soln[:, :, 1]
        vh = soln[:, :, 2]
        ph = soln[:, :, 3]

        # Physical-space things
        self.q = self.ifft2(qh)
        self.u = self.ifft2(uh)
        self.v = self.ifft2(vh)
        self.p = self.ifft2(ph)

        # Calculate streamfunction
        self.psih = -qh / self._divSafeKsq

        # Mean velocities
        self.U = -self.ifft2(self._jl*self.psih)
        self.V =  self.ifft2(self._jk*self.psih)

        # Mean derivatives
        self.Ux =  self.ifft2(self.l*self.k*self.psih)
        self.Uy =  self.ifft2(self.l**2.0*self.psih)
        self.Vx = -self.ifft2(self.k**2.0*self.psih)

        # Views to clarify calculation of A's RHS
        U = self.U
        V = self.V
        q = self.q
        u = self.u
        v = self.v
        p = self.p
        Ux = self.Ux                
        Uy = self.Uy
        Vx = self.Vx        

        # Solely nonlinear advection for q
        self.RHS[:, :, 0] = - self._jk*self.fft2(U*q) - self._jl*self.fft2(V*q)

        # Linear terms + advection for u, v, p, + refraction for u, v
        self.RHS[:, :, 1] =  self.f0*vh - self._jk*ph \
                                 - self._jk*self.fft2(U*u) - self._jl*self.fft2(V*u) \
                                 - self.fft2(u*Ux) - self.fft2(v*Uy)
        self.RHS[:, :, 2] = -self.f0*uh - self._jl*ph \
                                 - self._jk*self.fft2(U*v) - self._jl*self.fft2(V*v) \
                                 - self.fft2(u*Vx) + self.fft2(v*Ux)
        self.RHS[:, :, 3] = -self.cn**2.0 * ( self._jk*uh + self._jl*vh ) \
                                 - self._jk*self.fft2(U*p) - self._jl*self.fft2(V*p)
                               
        self._dealias_RHS()
         
    def _init_problem_parameters(self):
        """ Pre-allocate parameters in memory in addition to the solution """

        # Wavenumbers and products
        self._jk = 1j*self.k
        self._jl = 1j*self.l

        self._divSafeKsq = self.k**2.0 + self.l**2.0
        self._divSafeKsq[0, 0] = float('Inf')

        # Mode-n wave speed:
        self.cn = self.f0 / self.kappa
    
        # Vorticity and wave-field amplitude
        self.q = np.zeros(self.physVarShape, np.dtype('float64'))
        self.u = np.zeros(self.physVarShape, np.dtype('float64'))
        self.v = np.zeros(self.physVarShape, np.dtype('float64'))
        self.p = np.zeros(self.physVarShape, np.dtype('float64'))

        # Streamfunction transform
        self.psih = np.zeros(self.specVarShape, np.dtype('complex128'))
    
        # Mean and wave velocity components 
        self.U = np.zeros(self.physVarShape, np.dtype('float64'))
        self.V = np.zeros(self.physVarShape, np.dtype('float64'))

        self.Ux = np.zeros(self.physVarShape, np.dtype('float64'))
        self.Uy = np.zeros(self.physVarShape, np.dtype('float64'))
        self.Vx = np.zeros(self.physVarShape, np.dtype('float64'))
        
    def update_state_variables(self):
        """ Update diagnostic variables to current model state """
        # Views for clarity:
        qh = self.soln[:, :, 0]
        uh = self.soln[:, :, 1]
        vh = self.soln[:, :, 2]
        ph = self.soln[:, :, 3]
        
        # Streamfunction
        self.psih = - qh / self._divSafeKsq 

        # Physical-space PV and velocity components
        self.q = self.ifft2(qh)
        self.u = self.ifft2(uh)
        self.v = self.ifft2(vh)
        self.p = self.ifft2(ph)

        self.U = -self.ifft2(self._jl*self.psih)
        self.V =  self.ifft2(self._jk*self.psih)

    def set_q(self, q):
        """ Set model vorticity """

        self.soln[:, :, 0] = self.fft2(q)
        self._dealias_soln()
        self.update_state_variables()

    def make_plane_wave(self, kNonDim):
        """ Set linearized Boussinesq to a plane wave in x with speed 1 m/s
            and normalized wavenumber kNonDim """

        # Dimensional wavenumber and dispersion-relation frequency
        kDim = 2.0*pi/self.Lx * kNonDim
        sigma = self.f0*sqrt(1 + kDim/self.kappa)

        # Wave field amplitude. 
        #alpha = sigma**2.0 / self.f0**2.0 - 1.0
        a = 1.0 

        # A hydrostatic plane wave. s > sqrt(s^2+f^2)/sqrt(2) when s>f
        p = a * (sigma**2.0-self.f0**2.0) * cos(kDim*self.XX)
        u = a * kDim*sigma   * cos(kDim*self.XX)
        v = a * kDim*self.f0 * sin(kDim*self.XX)

        return u, v, p

    def set_uvp(self, u, v, p):
        """ Set linearized Boussinesq variables """

        self.soln[:, :, 1] = self.fft2(u)
        self.soln[:, :, 2] = self.fft2(v)
        self.soln[:, :, 3] = self.fft2(p)

        self._dealias_soln()
        self.update_state_variables()

    def describe_model(self):
        """ Describe the current model state """

        print("\nThis is a doubly-periodic spectral model for \n" + \
                "{:s} \n".format(self.physics) + \
                "with the following attributes:\n\n" + \
                "   Domain       : {:.2e} X {:.2e} m\n".format(self.Lx, self.Ly) + \
                "   Resolution   : {:d} X {:d}\n".format(self.nx, self.ny) + \
                "   Timestep     : {:.2e} s\n".format(self.dt) + \
                "   Current time : {:.2e} s\n\n".format(self.t) + \
                "The FFT scheme uses {:d} thread(s).\n".format(self.nThreads))
