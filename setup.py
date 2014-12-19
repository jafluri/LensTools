import os,sys,glob,re
import platform
from distutils import config


#Names
name = "lenstools"
me = "Andrea Petri"
email = "apetri@phys.columbia.edu"
url = "http://www.columbia.edu/~ap3020/LensTools/html"
default_cfg = "setup.cfg"
external_dir = "extern"
external_support_dir = "cextern"
simulations_dir = "simulations"
observations_dir = "observations"

try:
	import numpy.distutils.misc_util 
except ImportError:
	print("Please install numpy!")
	sys.exit(1)


try:
	from setuptools import setup,Extension
except ImportError:
	from distutils.core import setup,Extension

def rd(filename):
	
	f = file(filename,"r")
	r = f.read()
	f.close()

	return r


#Check GSL installation, necessary for using the Design feature
def check_gsl(conf):
	
	gsl_location = conf.get("gsl","installation_path")
	gsl_required_includes = ["gsl_permutation.h","gsl_randist.h","gsl_rng.h","gsl_matrix.h"]
	gsl_required_links = ["libgsl.a","libgslcblas.a"]

	#Check for required GSL includes and links
	for include in gsl_required_includes:
	
		include_filename = os.path.join(gsl_location,"include","gsl",include)
		sys.stderr.write("Checking if {0} exists... ".format(include_filename))

		if os.path.isfile(include_filename):
			sys.stderr.write("[OK]\n")
		else:
			sys.stderr.write("[FAIL]\n")
			return None

	for lib in gsl_required_links:

		lib_filename = os.path.join(gsl_location,"lib",lib)
		sys.stderr.write("Checking if {0} exists... ".format(lib_filename))

		if os.path.isfile(lib_filename):
			sys.stderr.write("[OK]\n")
		else:
			sys.stderr.write("[FAIL]\n")
			return None

	return gsl_location


#Check fftw3 installation, required from NICAEA
def check_fftw3(conf):

	fftw3_location = conf.get("fftw3","installation_path")
	fftw3_required_includes = ["fftw3.h"]
	fftw3_required_links = ["libfftw3.a"]

	#Check for required GSL includes and links
	for include in fftw3_required_includes:
	
		include_filename = os.path.join(fftw3_location,"include",include)
		sys.stderr.write("Checking if {0} exists... ".format(include_filename))

		if os.path.isfile(include_filename):
			sys.stderr.write("[OK]\n")
		else:
			sys.stderr.write("[FAIL]\n")
			return None

	for lib in fftw3_required_links:

		lib_filename = os.path.join(fftw3_location,"lib",lib)
		sys.stderr.write("Checking if {0} exists... ".format(lib_filename))

		if os.path.isfile(lib_filename):
			sys.stderr.write("[OK]\n")
		else:
			sys.stderr.write("[FAIL]\n")
			return None

	return fftw3_location


#Check correctness of NICAEA installation
def check_nicaea(conf):

	nicaea_root = conf.get("nicaea","installation_path")

	#These are the include and lib directory
	nicaea_include = os.path.join(nicaea_root,"include","nicaea")
	nicaea_lib = os.path.join(nicaea_root,"lib")

	#Check for their existence
	sys.stderr.write("Checking for {0}...".format(nicaea_include))
	if os.path.isdir(nicaea_include):
		sys.stderr.write("[OK]\n")
	else:
		sys.stderr.write("[FAIL]\n")
		return None

	sys.stderr.write("Checking for {0}...".format(os.path.join(nicaea_lib,"libnicaea.a")))
	if os.path.isfile(os.path.join(nicaea_lib,"libnicaea.a")):
		sys.stderr.write("[OK]\n")
	else:
		sys.stderr.write("[FAIL]\n")
		return None
	
	return nicaea_include,nicaea_lib


############################################################
#####################Execution##############################
############################################################

#Read system dependent configuration file
conf = config.ConfigParser()
this = os.getenv("THIS")

if (this is not None) and (os.path.isfile(default_cfg+"."+this)):
	cfg_file = default_cfg+"."+this
else:
	cfg_file = default_cfg

print("Reading system dependent configuration from {0}".format(cfg_file))
conf.read([cfg_file])

vre = re.compile("__version__ = \"(.*?)\"")
m = rd(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "lenstools", "__init__.py"))
version = vre.findall(m)[0]

classifiers = [
		"Development Status :: 3 - Alpha",
		"Intended Audience :: Science/Research",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Programming Language :: C",
		"License :: OSI approved:: MIT"
	]

external_sources = dict()
external_support = dict()

#List external package sources here
external_sources["_topology"] = ["_topology.c","differentials.c","peaks.c","minkowski.c","coordinates.c","azimuth.c"]
external_sources["_gadget"] = ["_gadget.c","read_gadget_header.c","read_gadget_particles.c","write_gadget_particles.c","grid.c"]

######################################################################################################################################

#Decide if we can install the Design feature, if not throw a warning
gsl_location = check_gsl(conf)

if gsl_location is not None:
	print("[OK] Checked GSL installation, the Design feature will be installed")
	lenstools_includes = [ os.path.join(gsl_location,"include") ]
	lenstools_link = ["-lm","-L{0}".format(os.path.join(gsl_location,"lib")),"-lgsl","-lgslcblas"]
	external_sources["_design"] = ["_design.c","design.c"] 
else:
	raw_input("[FAIL] GSL installation not found, the Design feature will not be installed, please press a key to continue: ")
	lenstools_includes = list()
	lenstools_link = ["-lm"]


######################################################################################################################################

if conf.getboolean("nicaea","install_python_bindings"):

	#Decide if we can install the NICAEA bindings
	fftw3_location = check_fftw3(conf)
	nicaea_location = check_nicaea(conf)
	
	if (gsl_location is not None) and (fftw3_location is not None) and (nicaea_location is not None):
	
		print("[OK] Checked GSL,FFTW3 and NICAEA installations, the NICAEA bindings will be installed")
		
		#Add necessary includes and links
		lenstools_includes += [ os.path.join(fftw3_location,"include") , nicaea_location[0] ]
		lenstools_link += ["-L{0}".format(os.path.join(fftw3_location,"lib")) , "-lfftw3", "-L{0}".format(nicaea_location[1]) , "-lnicaea"]

		#Specify the NICAEA extension
		external_sources["_nicaea"] = ["_nicaea.c"]

	else:
		raw_input("[FAIL] NICAEA bindings will not be installed (either enable option or check GSL/FFTW3/NICAEA installations), please press a key to continue: ")


#################################################################################################
#############################Extensions##########################################################
#################################################################################################

#Extension objects
ext = list()

for ext_module in external_sources.keys():

	sources = list()
	for source in external_sources[ext_module]:
		sources.append(os.path.join(name,external_dir,source))

	#Append external support sources too
	if ext_module in external_support.keys():
		sources += external_support[ext_module]

	ext.append(Extension(ext_module,sources,extra_link_args=lenstools_link))

#################################################################################################
#############################Package data########################################################
#################################################################################################

#Data files on which the package depends on
package_data = dict()
package_data[name] = [ os.path.join("data",filename) for filename in os.listdir(os.path.join(name,"data")) if os.path.isfile(os.path.join(name,"data",filename)) ]
package_data["licenses"] = [ os.path.join("licenses","LICENSE.rst") ]
print(package_data)

#################################################################################################
#############################Additional includes#################################################
#################################################################################################

#Append numpy includes
lenstools_includes += numpy.distutils.misc_util.get_numpy_include_dirs()

#Append system includes (fix OSX clang includes)
if platform.system() in ["Darwin","darwin"]:
	lenstools_includes += ["/usr/local/include","/usr/include"]

#################################################################################################
#############################Scripts#############################################################
#################################################################################################

#package scripts
scripts = [ fname for fname in glob.glob(os.path.join("scripts","*")) if os.path.basename(fname)!="README.rst" ]
scripts_dir = "scripts"

#################################################################################################
#############################Setup###############################################################
#################################################################################################

setup(
	name=name,
	version=version,
	author=me,
	author_email=email,
	packages=[name,"{0}.{1}".format(name,external_dir),"{0}.{1}".format(name,simulations_dir),"{0}.{1}".format(name,observations_dir),"{0}.{1}".format(name,scripts_dir)],
	package_data=package_data,
	install_requires=["numpy","scipy","astropy","emcee"],
	url=url,
	license="MIT",
	description="Toolkit for Weak Gravitational Lensing analysis",
	long_description=rd(os.path.join("docs","source","index.rst")),
	scripts=scripts,
	classifiers=classifiers,
	ext_package=os.path.join(name,external_dir),
	ext_modules=ext,
	include_dirs=lenstools_includes,
	zip_safe=False,
)
