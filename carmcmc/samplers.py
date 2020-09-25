"""
This file contains the class definition for the sampler MCMCSample classes.
"""

__author__ = 'Brandon C. Kelly'

import numpy as np
from matplotlib import pyplot as plt
import scipy.stats
import acor


class MCMCSample(object):
    """
    Class for parameter samples generated by a yamcmc++ sampler. This class contains a dictionary of samples
    generated by an MCMC sampler for a set of parameters, as well as methods for plotting and summarizing the results.

    In general, the MCMCSample object is empty upon instantiation. One adds parameters to the dictionary through the
    AddStep method of a Sampler object. Running a Sampler object then fills the dictionary up with the parameter values.
    After running a Sampler object, the MCMCSample object will contain the parameter values, which can then be analyzed
    further.

    Alternatively, one can load the parameters and their values from a file. This is done through the method
    generate_from_file. This is helpful if one has a set of MCMC samples generated by a different program.
    """

    def __init__(self, filename=None, logpost=None, trace=None):
        """
        Constructor for an MCMCSample object. If no arguments are supplied, then this just creates an empty dictionary
        that will contain the MCMC samples. In this case parameters are added to the dictionary through the addstep
        method of a Sampler object, and the values are generated by running the Sampler object. Otherwise, if a
        filename is supplied then the parameter names and MCMC samples are read in from that file.

        :param filename: A string giving the name of an asciifile containing the MCMC samples.
        """
        self._samples = dict()  # Empty dictionary. We will place the samples for each tracked parameter here.

        if logpost is not None:
            self.set_logpost(logpost)

        if trace is not None:
            self.generate_from_trace(trace)
        elif filename is not None:
            # Construct MCMCSample object by reading in MCMC samples from one or more asciifiles.
            self.generate_from_file([filename])

    def get_samples(self, name):
        """
        Returns a copy of the numpy array containing the samples for a parameter. This is safer then directly
        accessing the dictionary object containing the samples to prevent one from inadvertently changes the values of
        the samples output from an MCMC sampler.

        :param name: The name of the parameter for which the samples are desired.
        """
        return self._samples[name].copy()

    def generate_from_file(self, filename):
        """
        Build the dictionary of parameter samples from an ascii file of MCMC samples. The first line of this file
        should contain the parameter names.

        :param filename: The name of the file containing the MCMC samples.
        """
        # TODO: put in exceptions to make sure files are ready correctly
        for fname in filename:
            file = open(fname, 'r')
            name = file.readline()
            # Grab the MCMC output
            trace = np.genfromtxt(fname, skip_header=1)
            if name not in self._samples:
                # Parameter is not already in the dictionary, so add it. Otherwise do nothing.
                self._samples[name] = trace

    def autocorr_timescale(self, trace):
        """
        Compute the autocorrelation time scale as estimated by the `acor` module.

        :param trace: The parameter trace, a numpy array.
        """
        acors = []
        for i in range(trace.shape[1]):
            tau, mean, sigma = acor.acor(trace[:, i].real)  # Warning, does not work with numpy.complex
            acors.append(tau)
        return np.array(acors)

    def effective_samples(self, name):
        """
        Return the effective number of independent samples of the MCMC sampler.

        :param name: The name of the parameter to compute the effective number of independent samples for.
        """
        if name not in self._samples:
            print("WARNING: sampler does not have", name)
            return
        else:
            print("Calculating effective number of samples")

        traces = self._samples[name]  # Get the sampled parameter values
        npts = traces.shape[0]
        timescale = self.autocorr_timescale(traces)
        return npts / timescale

    def plot_trace(self, name, doShow=False):
        """
        Plot the trace of the values, a time series showing the evolution of the parameter values for the MCMC sampler.
        Only a single parameter element trace is shown per plot, and all plots are shown on the same plotting window. In
        particular, if a parameter is array-valued, then the traces for each element of its array are plotted on a
        separate subplot.

        :param name: The parameter name.
        :param doShow: If true, then show the plot.
        """
        if name not in self._samples:
            print("WARNING: sampler does not have", name)
            return
        else:
            print("Plotting Trace")
            fig = plt.figure()

        traces = self._samples[name]  # Get the sampled parameter values
        ntrace = traces.shape[1]
        spN = plt.subplot(ntrace, 1, ntrace)
        spN.plot(traces[:,-1], ".", markersize=2)
        spN.set_xlabel("Step")
        spN.set_ylabel("par %d" % (ntrace-1))
        for i in range(ntrace-1):
            sp = plt.subplot(ntrace, 1, i+1, sharex=spN)
            sp.plot(traces[:,i], ".", markersize=2)
            sp.set_ylabel("par %d" % (i))
            plt.setp(sp.get_xticklabels(), visible=False)
        plt.suptitle(name)
        if doShow:
            plt.show()

    def plot_1dpdf(self, name, doShow=False):
        """
        Plot histograms of the parameter values generated by the MCMC sampler. If the parameter is array valued then
        histograms of all of the parameter's elements will be plotted.

        :param name: The parameter name.
        :param doShow: If true, then show the plot.
        """
        if name not in self._samples:
            print("WARNING: sampler does not have", name)
            return
        else:
            print("Plotting 1d PDF")
            fig = plt.figure()

        traces = self._samples[name]  # Get the sampled parameter values
        ntrace = traces.shape[1]
        for i in range(ntrace):
            sp = plt.subplot(ntrace, 1, i+1)
            sp.hist(traces[:,i], bins=50, normed=True)
            sp.set_ylabel("par %d" % (i))
            if i == ntrace-1:
                sp.set_xlabel("val")
        plt.suptitle(name)
        if doShow:
            plt.show()

    def plot_2dpdf(self, name1, name2, pindex1=0, pindex2=0, doShow=False):
        """
        Plot joint distribution of the parameter values generated by the MCMC sampler. 

        :param name1: The parameter name along x-axis
        :param name2: The parameter name along y-axis
        :param pindex1: Which element of the array to plot
        :param pindex2: Which element of the array to plot
        :param doShow: Call plt.show()
        """
        if (name1 not in self._samples) or (name2 not in self._samples) :
            print("WARNING: sampler does not have", name1, name2)
            return

        if pindex1 >= self._samples[name1].shape[1]:
            print("WARNING: not enough data in", name1)
            return
        if pindex2 >= self._samples[name2].shape[1]:
            print("WARNING: not enough data in", name2)
            return

        print("Plotting 2d PDF")
        fig    = plt.figure()
        trace1 = self._samples[name1][:,pindex1]
        trace2 = self._samples[name2][:,pindex2]

        # joint distribution
        axJ = fig.add_axes([0.1, 0.1, 0.7, 0.7])               # [left, bottom, width, height]
        # y histogram
        axY = fig.add_axes([0.8, 0.1, 0.125, 0.7], sharey=axJ) 
        # x histogram
        axX = fig.add_axes([0.1, 0.8, 0.7, 0.125], sharex=axJ) 
        axJ.plot(trace1, trace2, 'ro', ms=1, alpha=0.5)  
        axX.hist(trace1, bins=100)
        axY.hist(trace2, orientation='horizontal', bins=100)
        axJ.set_xlabel("%s %d" % (name1, pindex1))
        axJ.set_ylabel("%s %d" % (name2, pindex2))
        plt.setp(axX.get_xticklabels()+axX.get_yticklabels(), visible=False)
        plt.setp(axY.get_xticklabels()+axY.get_yticklabels(), visible=False)
        if doShow:
            plt.show()

    def plot_2dkde(self, name1, name2, pindex1=0, pindex2=0, 
                   nbins=100, doPlotStragglers=True, doShow=False):
        """
        Plot joint distribution of the parameter values generated by the MCMC sampler using a kernel density estimate.

        :param name1: The parameter name along x-axis
        :param name2: The parameter name along y-axis
        :param pindex1: Which element of the array to plot
        :param pindex2: Which element of the array to plot
        :param doShow: Call plt.show()
        :param nbins: Number of bins along each axis for KDE
        :param doPlotStragglers: Plot individual data points outside KDE contours.  Works poorly for small samples.
        """
        if (name1 not in self._samples) or (name2 not in self._samples) :
            print("WARNING: sampler does not have", name1, name2)
            return

        if pindex1 >= self._samples[name1].shape[1]:
            print("WARNING: not enough data in", name1)
            return
        if pindex2 >= self._samples[name2].shape[1]:
            print("WARNING: not enough data in", name2)
            return

        print("Plotting 2d PDF w KDE")
        fig    = plt.figure()
        trace1 = self._samples[name1][:,pindex1].real # JIC we get something imaginary?
        trace2 = self._samples[name2][:,pindex2].real
        npts = trace1.shape[0]
        kde = scipy.stats.gaussian_kde((trace1, trace2))
        bins1 = np.linspace(trace1.min(), trace1.max(), nbins)
        bins2 = np.linspace(trace2.min(), trace2.max(), nbins)
        mesh1, mesh2 = np.meshgrid(bins1, bins2)
        hist = kde([mesh1.ravel(), mesh2.ravel()]).reshape(mesh1.shape)

        clevels = []
        for frac in [0.9973, 0.9545, 0.6827]:
            hfrac = lambda level, hist=hist, frac=frac: hist[hist>=level].sum()/hist.sum() - frac
            level = scipy.optimize.bisect(hfrac, hist.min(), hist.max())
            clevels.append(level)

        # joint distribution
        axJ = fig.add_axes([0.1, 0.1, 0.7, 0.7])               # [left, bottom, width, height]
        # y histogram
        axY = fig.add_axes([0.8, 0.1, 0.125, 0.7], sharey=axJ) 
        # x histogram
        axX = fig.add_axes([0.1, 0.8, 0.7, 0.125], sharex=axJ) 
        cont = axJ.contour(mesh1, mesh2, hist, clevels, linestyles="solid", cmap=plt.cm.jet)
        axX.hist(trace1, bins=100)
        axY.hist(trace2, orientation='horizontal', bins=100)
        axJ.set_xlabel(name1 + '[' + str(pindex1) + ']')
        axJ.set_ylabel(name2 + '[' + str(pindex2) + ']')
        plt.setp(axX.get_xticklabels()+axX.get_yticklabels(), visible=False)
        plt.setp(axY.get_xticklabels()+axY.get_yticklabels(), visible=False)

        # Note to self: you need to set up the contours above to have
        # the outer one first, for collections[0] to work below.
        # 
        # Also a note: this does not work if the outer contour is not
        # fully connected.
        if doPlotStragglers:
            outer = cont.collections[0]._paths
            sx = []
            sy = []
            for i in range(npts):
                found = [o.contains_point((trace1[i], trace2[i])) for o in outer]
                if not (True in found):
                    sx.append(trace1[i])
                    sy.append(trace2[i])
            axJ.plot(sx, sy, 'k.', ms = 1, alpha = 0.1)
        if doShow:
            plt.show()

    def plot_autocorr(self, name, acorrFac = 10.0, doShow=False):
        """
        Plot the autocorrelation functions of the traces for a parameter. If the parameter is array-value then
        autocorrelation plots for each of the parameter's elements will be plotted.

        :param name: The parameter name.
        :param acorrFac: The maximum number of lags to plot, in terms of the autocorrelation time scale of the MCMC
            samples. The default is 10 autocorrelation time scales.
        :param doShow:
        """
        if name not in self._samples:
            print("WARNING: sampler does not have", name)
            return
        else:
            print("Plotting autocorrelation function (this make take a while)")
            fig = plt.figure()

        traces = self._samples[name]  # Get the sampled parameter values
        mtrace = np.mean(traces, axis=0)
        ntrace = traces.shape[1]
        acorr  = self.autocorr_timescale(traces)

        for i in range(ntrace):
            sp = plt.subplot(ntrace, 1, i+1)
            lags, acf, not_needed1, not_needed2 = plt.acorr(traces[:, i] - mtrace[i], maxlags=traces.shape[0]-1, lw=2)
            sp.set_xlim(-0.5, acorrFac * acorr[i])
            sp.set_ylim(-0.01, 1.01)
            sp.axhline(y=0.5, c='k', linestyle='--')
            sp.axvline(x=acorr[i], c='r', linestyle='--')
            sp.set_ylabel("par %d autocorr" % (i))
            if i == ntrace-1:
                sp.set_xlabel("lag")
        plt.suptitle(name)
        if doShow:
            plt.show()

    def plot_parameter(self, name, pindex=0, doShow=False, figname="", dpi=None):
        """
        Simultaneously plots the trace, histogram, and autocorrelation of this parameter's values. If the parameter
        is array-valued, then the user must specify the index of the array to plot, as these are all 1-d plots on a
        single plotting window.

        :param name: The name of the parameter that the plots are made for.
        :param pindex: If the parameter is array-valued, then this is the index of the array that the plots are made
                       for.
        :param doShow: Call plt.show().
        """
        if name not in self._samples:
            print("WARNING: sampler does not have", name)
            return
        else:
            print("Plotting parameter summary")
            fig = plt.figure()

        traces = self._samples[name]
        plot_title = name
        if traces.ndim > 1:
            # Parameter is array valued, grab the column corresponding to pindex
            if traces.ndim > 2:
                # Parameter values are at least matrix-valued, reshape to a vector
                traces = traces.reshape(traces.shape[0], np.prod(traces.shape[1:]))
            traces = traces[:, pindex]
            plot_title = name + "[" + str(pindex) + "]"
        # Modification perso 03/10/2016: Changement de titre pour certaines variables
        if name=="mu":
            plot_title="$\mu$"
        if name=="sigma":
            plot_title="$\sigma$"
        if name=="var":
            plot_title="the process variance"
        if name=="log_omega":
            plot_title="$\log$"+"("+"$\\alpha$"+")"
        # Fin modification perso
        # First plot the trace
        plt.subplot(211)
		# Modification perso 02/08/2016: ajout de zorder
        plt.plot(traces, '.', markersize=2, alpha=0.5, rasterized=(len(traces) > 1e4),zorder=1)
		# Fin Modification perso
        plt.xlim(0, traces.size)
        plt.xlabel("Iteration")
        plt.ylabel("Value")
		# Modification perso 02/08/2016: ajout de "Marginal distribution"
        plt.title("Marginal distribution of "+plot_title)
		# Fin modification perso

        # Now add the histogram of values to the trace plot axes
        pdf, bin_edges = np.histogram(traces, bins=25)
        bin_edges = bin_edges[0:pdf.size]
        # Stretch the PDF so that it is readable on the trace plot when plotted horizontally
        pdf = pdf / float(pdf.max()) * 0.34 * traces.size
        # Add the histogram to the plot
		# Modification perso 02/08/2016: ajout de zorder et alpha
        plt.barh(bin_edges, pdf, height=bin_edges[1] - bin_edges[0], alpha=0.5, color='DarkOrange', zorder=2)
		# Fin Modification perso

        # Finally, plot the autocorrelation function of the trace
        plt.subplot(212)
        centered_trace = traces - traces.mean()
        lags, acf, not_needed1, not_needed2 = plt.acorr(centered_trace, maxlags=traces.size - 1, lw=2)
        plt.ylabel("ACF")
        plt.xlabel("Lag")

        # Compute the autocorrelation timescale, and then reset the x-axis limits accordingly
        acf_timescale = self.autocorr_timescale(traces[:, np.newaxis])
        plt.xlim(0, np.min([5 * acf_timescale[0], len(traces)]))
        # Ajout perso 02/06/2016 (+ajout de "figname" dans les inputs)
        if(figname!=""):
            plt.savefig(figname,dpi=dpi)
            if doShow:
                plt.show()
            else:
                plt.close()
        elif doShow:
            plt.show()
        # Fin ajout perso

    def posterior_summaries(self, name, mypath, flag):
        """
        Print out the posterior medians, standard deviations, and 68th, 95th, and 99th credibility intervals.

        :param name: The name of the parameter for which the summaries are desired.
        """
        traces = self._samples[name]  # Get the sampled parameter values
        effective_nsamples = self.effective_samples(name)  # Get the effective number of independent samples
        if traces.ndim == 1:
            # Parameter is scalar valued, so this is easy
            print("Posterior summary for parameter", name)
            print("----------------------------------------------")
            print("Effective number of independent samples:", effective_nsamples)
            print("Median:", np.median(traces))
            print("Standard deviation:", np.std(traces))
            print("68% credibility interval:", np.percentile(traces, (16.0, 84.0)))
            print("95% credibility interval:", np.percentile(traces, (2.5, 97.5)))
            print("99% credibility interval:", np.percentile(traces, (0.5, 99.5)))
        else:
            if traces.ndim > 2:
                # Parameter values are at least matrix-valued, reshape to a vector.
                traces = traces.reshape(traces.shape[0], np.prod(traces.shape[1:]))
            for i in range(traces.shape[1]):
                # give summary for each element of this parameter separately
                # Parameter is scalar valued, so this is easy
                print("Posterior summary for parameter", name, " element", i)
                print("----------------------------------------------")
                print("Effective number of independent samples:", effective_nsamples[i])
                print("Median:", np.median(traces[:, i]))
                print("Standard deviation:", np.std(traces[:, i]))
                print("68% credibility interval:", np.percentile(traces[:, i], (16.0, 84.0)))
                print("95% credibility interval:", np.percentile(traces[:, i], (2.5, 97.5)))
                print("99% credibility interval:", np.percentile(traces[:, i], (0.5, 99.5)))

    def newaxis(self):
        for key in list(self._samples.keys()):
            if len(self._samples[key].shape) == 1:
                self._samples[key] = self._samples[key][:,np.newaxis]
