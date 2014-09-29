from ..convergence import Spin0
from ..shear import Spin1

import numpy as np

from astropy.cosmology import w0waCDM
from astropy.units import km,s,Mpc,rad,deg
from astropy.io import fits

###########################################################
###############PotentialPlane class########################
###########################################################

class PotentialPlane(Spin0):

	"""
	Class handler of a lens potential plane, inherits from the parent Spin0 class; additionally it defines redshift and comoving distance attributes that are needed for ray tracing operations

	"""

	def __init__(self,data,angle,redshift,cosmology,unit=rad**2,masked=False):

		super(self.__class__,self).__init__(data,angle,masked)
		self.redshift = redshift
		self.comoving_distance = cosmology.comoving_distance(redshift)
		self.cosmology = cosmology
		self.unit = unit


	def save(self,filename,format="fits"):

		"""
		Saves the potential plane to an external file, of which the format can be specified (only fits implemented so far)

		:param filename: name of the file on which to save the plane
		:type filename: str.

		:param format: format of the file, only FITS implemented so far
		:type format: str.

		"""

		if format=="fits":
		
			#Create the hdu
			hdu = fits.PrimaryHDU(self.data)

			#Generate a header
			hdu.header["H0"] = (self.cosmology.H0.to(km/(s*Mpc)).value,"Hubble constant in km/s*Mpc")
			hdu.header["h"] = (self.cosmology.h,"Dimensionless Hubble constant")
			hdu.header["OMEGA_M"] = (self.cosmology.Om0,"Dark Matter density")
			hdu.header["OMEGA_L"] = (self.cosmology.Ode0,"Dark Energy density")
			hdu.header["W0"] = (self.cosmology.w0,"Dark Energy equation of state")
			hdu.header["WA"] = (self.cosmology.wa,"Dark Energy running equation of state")

			hdu.header["Z"] = (self.redshift,"Redshift of the lens plane")
			hdu.header["CHI"] = (hdu.header["h"] * self.comoving_distance.to(Mpc).value,"Comoving distance in Mpc/h")

			hdu.header["ANGLE"] = (self.side_angle.to(deg).value,"Side angle in degrees")

			#Save the plane
			hdulist = fits.HDUList([hdu])
			hdulist.writeto(filename,clobber=True)

		else:
			raise ValueError("Format {0} not implemented yet!!".format(format))


	@classmethod
	def load(cls,filename,format="fits"):

		"""
		Loads the potential plane from an external file, of which the format can be specified (only fits implemented so far)

		:param filename: name of the file from which to load the plane
		:type filename: str.

		:param format: format of the file, only FITS implemented so far
		:type format: str.

		:returns: PotentialPlane instance that wraps the data contained in the file

		"""

		if format=="fits":

			#Read the FITS file with the plane information
			hdu = fits.open(filename)

			#Retrieve the info from the header
			hubble = hdu[0].header["H0"] * (km/(s*Mpc))
			Om0 = hdu[0].header["OMEGA_M"]
			Ode0 = hdu[0].header["OMEGA_L"]
			w0 = hdu[0].header["W0"]
			wa = hdu[0].header["WA"]
			redshift = hdu[0].header["Z"]
			angle = hdu[0].header["ANGLE"] * deg

			#Build the cosmology object
			cosmology = w0waCDM(H0=hubble,Om0=Om0,Ode0=Ode0,w0=w0,wa=wa)

			#Instantiate the new PotentialPlane instance
			return cls(hdu[0].data.astype(np.float64),angle=angle,redshift=redshift,cosmology=cosmology,unit=rad**2)

		else:
			raise ValueError("Format {0} not implemented yet!!".format(format))


	
	def deflectionAngles(self):

		"""
		Computes the deflection angles for the given lensing potential by taking the gradient of the potential map

		"""

		#Compute the gradient of the potential map
		deflection_x,deflection_y = self.gradient()

		#Return the DeflectionPlane instance
		return DeflectionPlane(np.array([deflection_x,deflection_y])/self.resolution.to(self.unit**0.5).value,angle=self.side_angle,redshift=self.redshift,cosmology=self.cosmology,unit=self.unit**0.5)


	def density(self):

		"""
		Computes the projected density fluctuation by taking the laplacian of the potential; useful to check if the potential is reasonable

		:returns: Spin0 instance with the density fluctuation data 

		"""

		#Compute the laplacian
		hessian_xx,hessian_yy,hessian_xy = self.hessian()

		#The density is twice the trace of the hessian
		return Spin0(2.0*(hessian_xx + hessian_yy)/(self.resolution**2).to(self.unit).value,angle=self.side_angle)




#############################################################
################DeflectionPlane class########################
#############################################################

class DeflectionPlane(Spin1):

	"""
	Class handler of a lens deflection plane, inherits from the parent Spin1 class and holds the values of the deflection angles of the light rays that cross a potential plane

	"""

	def __init__(self,data,angle,redshift,cosmology,unit=rad):

		super(self.__class__,self).__init__(data,angle)
		self.redshift = redshift
		self.comoving_distance = cosmology.comoving_distance(redshift)
		self.cosmology = cosmology
		self.unit = unit



#######################################################
###############RayTracer class#########################
#######################################################

class RayTracer(object):

	"""
	Docstring
	"""
