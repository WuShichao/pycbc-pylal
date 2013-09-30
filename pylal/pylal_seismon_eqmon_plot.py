#!/usr/bin/python

"""
%prog

Michael Coughlin (coughlim@carleton.edu)

This program checks for earthquakes.

"""

import os, time, glob, matplotlib, math
import numpy as np
import scipy.optimize
from mpl_toolkits.basemap import Basemap
matplotlib.use("AGG")
matplotlib.rcParams.update({'font.size': 18})
from matplotlib import pyplot as plt
from matplotlib import cm

import pylal.pylal_seismon_eqmon

import gwpy.time, gwpy.timeseries
import gwpy.spectrum, gwpy.spectrogram
import gwpy.plotter

# =============================================================================
#
#                               DEFINITIONS
#
# =============================================================================

def restimates(params,attributeDics,plotName):
    """@restimates plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param plotName
        name of plot    
    """

    ifo = pylal.pylal_seismon_utils.getIfo(params)

    gps = []
    magnitudes = []
    for attributeDic in attributeDics:

        if "Restimate" not in attributeDic["traveltimes"][ifo]:
            continue

        travel_time = attributeDic["traveltimes"][ifo]["Restimate"] - attributeDic["traveltimes"][ifo]["RthreePointFivetimes"][-1]

        gps.append(travel_time)
        magnitudes.append(attributeDic["Magnitude"])

    if magnitudes == []:
        return

    gps = np.array(gps)
    magnitudes = np.array(magnitudes)

    plt.figure()
    plt.plot(magnitudes,gps, 'k*')
    plt.xlim([min(magnitudes)-0.5, max(magnitudes)+0.5])
    plt.xlabel('Magnitude')
    plt.ylabel("\Delta T")
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def earthquakes_timeseries(params,data,plotName):
    """@earthquakes timeseries plot

    @param params
        seismon params dictionary
    @param data
        list of data structures
    @param plotName
        name of plot
    """

    if len(data["earthquakes"]["tt"]) == 0:
        return

    earthquakes_tt = data["earthquakes"]["tt"]
    amp = np.log10(data["earthquakes"]["data"])
    indexes = np.isinf(amp)
    amp[indexes] = -250
    earthquakes_amp = amp

    threshold = -8

    plot = gwpy.plotter.Plot(auto_refresh=True,figsize=[14,8])
    plot.add_scatter(earthquakes_tt,earthquakes_amp, marker='o', zorder=1000, color='b',label='predicted')

    colors = cm.rainbow(np.linspace(0, 1, len(data["channels"])))
    count=0
    for key in data["channels"].iterkeys():
        label = key.replace("_","\_")

        channel_ttStart = data["channels"][key]["timeseries"]["ttStart"]
        channel_ttEnd = data["channels"][key]["timeseries"]["ttEnd"]

        amp = np.log10(data["channels"][key]["timeseries"]["data"])
        indexes = np.isinf(amp)
        amp[indexes] = -250
        channel_amp = amp

        color = colors[count]
        plot.add_scatter(channel_ttStart,channel_amp,marker='*', zorder=1000, label=label,color=color)
        count=count+1

    xlim = [plot.xlim[0],plot.xlim[1]]
    ylim = [plot.ylim[0],plot.ylim[1]]
    plot.add_line(xlim,[threshold,threshold],label='threshold')

    plot.ylim = [-10,-3]
    #plot.epoch = epoch
    plot.ylabel = 'Velocity [log10(m/s)]'
    plot.add_legend(loc=1,prop={'size':10}) 

    plot.xlim = [params["gpsStart"],params["gpsEnd"]]

    plot.save(plotName,dpi=200)
    plot.close()

def earthquakes_psd(params,data,plotName):
    """@earthquakes psd plot

    @param params
        seismon params dictionary
    @param data
        list of data structures
    @param plotName
        name of plot
    """

    if len(data["earthquakes"]["tt"]) == 0:
        return

    earthquakes_tt = data["earthquakes"]["tt"]
    amp = np.log10(data["earthquakes"]["data"])
    indexes = np.isinf(amp)
    amp[indexes] = -250
    earthquakes_amp = amp

    threshold = -8

    plot = gwpy.plotter.Plot(auto_refresh=True,figsize=[14,8])
    plot.add_scatter(earthquakes_tt,earthquakes_amp, marker='o', zorder=1000, color='b',label='predicted')

    colors = cm.rainbow(np.linspace(0, 1, len(data["channels"])))
    count=0
    for key in data["channels"].iterkeys():
        label = key.replace("_","\_")

        channel_ttStart = data["channels"][key]["psd"]["ttStart"]
        channel_ttEnd = data["channels"][key]["psd"]["ttEnd"]

        amp = np.log10(data["channels"][key]["psd"]["data"])
        indexes = np.isinf(amp)
        amp[indexes] = -250
        channel_amp = amp

        color = colors[count]
        plot.add_scatter(channel_ttStart,channel_amp,marker='*', zorder=1000, label=label,color=color)
        count=count+1

    xlim = [plot.xlim[0],plot.xlim[1]]
    ylim = [plot.ylim[0],plot.ylim[1]]
    plot.add_line(xlim,[threshold,threshold],label='threshold')

    plot.ylim = [-10,-3]
    #plot.epoch = epoch
    plot.ylabel = 'Mean PSD 0.02-0.1 Hz'
    plot.add_legend(loc=1,prop={'size':10})

    plot.xlim = [params["gpsStart"],params["gpsEnd"]]

    plot.save(plotName,dpi=200)
    plot.close()

def prediction(data,plotName):
    """@prediction plot

    @param data
        list of data structures
    @param plotName
        name of plot
    """

    if len(data["prediction"]["ttStart"]) == 0:
        return

    prediction_ttStart = data["prediction"]["ttStart"]
    prediction_ttEnd = data["prediction"]["ttEnd"]
    amp = np.log10(data["prediction"]["data"])
    indexes = np.isinf(amp)
    amp[indexes] = -250
    prediction_amp = amp

    threshold = -8

    plot = gwpy.plotter.Plot(auto_refresh=True,figsize=[14,8])
    plot.add_scatter(prediction_ttStart, prediction_amp, marker='o', zorder=1000, color='b',label='predicted')
    #for i in xrange(len(prediction_ttStart)):
    #    plot.add_line([prediction_ttStart[i],prediction_ttEnd[i]],[prediction_amp[i],prediction_amp[i]],color='b',label='predicted')

    colors = cm.rainbow(np.linspace(0, 1, len(data["channels"])))
    count = 0
    for key in data["channels"].iterkeys():
        label = key.replace("_","\_")

        channel_ttStart = data["channels"][key]["timeseries"]["ttStart"]
        channel_ttEnd = data["channels"][key]["timeseries"]["ttEnd"]

        amp = np.log10(data["channels"][key]["timeseries"]["data"])
        indexes = np.isinf(amp)
        amp[indexes] = -250
        channel_amp = amp

        color = colors[count]
        plot.add_scatter(channel_ttStart,channel_amp,marker='*', zorder=1000, label=label,color=color)
        count=count+1

    xlim = [plot.xlim[0],plot.xlim[1]]
    ylim = [plot.ylim[0],plot.ylim[1]]
    #plot.add_line(xlim,[threshold,threshold],label='threshold')

    plot.ylim = [-10,-4]
    plot.ylabel = 'Velocity [log10(m/s)]'
    plot.add_legend(loc=1,prop={'size':10})

    plot.save(plotName,dpi=200)
    plot.close()

def residual(data,plotName):
    """@residual plot

    @param data
        list of data structures
    @param plotName
        name of plot
    """

    if len(data["prediction"]["ttStart"]) == 0:
        return

    prediction_ttStart = data["prediction"]["ttStart"]
    prediction_ttEnd = data["prediction"]["ttEnd"]
    amp = np.log10(data["prediction"]["data"])
    indexes = np.isinf(amp)
    amp[indexes] = -250
    prediction_amp = amp

    threshold = -8

    indexes = np.where(prediction_amp >= threshold)
    prediction_ttStart = prediction_ttStart[indexes]
    prediction_amp = prediction_amp[indexes]

    plot = gwpy.plotter.Plot(auto_refresh=True,figsize=[14,8])
    plot.add_scatter(prediction_ttStart, prediction_amp, marker='o', zorder=1000, color='b',label='predicted')

    for key in data["channels"].iterkeys():
        label = key.replace("_","\_")

        channel_ttStart = data["channels"][key]["timeseries"]["ttStart"]
        channel_ttEnd = data["channels"][key]["timeseries"]["ttEnd"]

        amp = np.log10(data["channels"][key]["timeseries"]["data"])
        indexes = np.isinf(amp)
        amp[indexes] = -250
        channel_amp = amp

        if len(channel_ttStart) == 0:
            continue

        channel_amp_interp = np.interp(prediction_ttStart,channel_ttStart,channel_amp)
        residual = channel_amp_interp - prediction_amp

        label = "%s residual"%key.replace("_","\_")
        plot.add_scatter(prediction_ttStart,residual,marker='*', zorder=1000, label=label)

    xlim = [plot.xlim[0],plot.xlim[1]]
    ylim = [plot.ylim[0],plot.ylim[1]]
    plot.add_line(xlim,[threshold,threshold],label='threshold')

    #plot.epoch = epoch
    plot.ylabel = 'Velocity [log10(m/s)]'
    plot.add_legend(loc=1,prop={'size':10})

    plot.save(plotName,dpi=200)
    plot.close()

def efficiency(data,plotName):
    """@efficiency plot

    @param data
        list of data structures
    @param plotName
        name of plot
    """

    data = np.array(data)
    t = data[:,0] - data[0,0]

    plt.figure()
    plt.plot(t,np.log10(data[:,2]),marker='*',label="Data")
    plt.plot(t,np.log10(data[:,3]),marker='*',label="Predicted")
    plt.legend(loc=3)
    plt.xlabel('Time [s] [%d]'%data[0,0])
    plt.ylabel('Amplitude')
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def efficiency_limits(data,plotName):
    """@efficiency limits plot

    @param data
        list of data structures
    @param plotName
        name of plot
    """

    data = np.array(data)
    t = data[:,0] - data[0,0]

    plt.figure()
    plt.plot(t,np.log10(data[:,2]),marker='*',label="Data")
    plt.plot(t,np.log10(data[:,3]),marker='*',label="Predicted")
    plt.legend(loc=3)
    plt.ylim([-10,-2])
    plt.xlabel('Time [s] [%d]'%data[0,0])
    plt.ylabel('Amplitude')
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def latencies_sent(params,attributeDics,plotName):
    """@latencies sent plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param plotName
        name of plot
    """

    latencies = []
    for attributeDic in attributeDics:
        latencies.append(attributeDic["SentGPS"]-attributeDic["GPS"])

    if latencies == []:
        return

    plt.figure()
    bins=np.logspace(1,5,15)
    plt.hist(latencies, bins=bins, rwidth=1)
    plt.gca().set_xscale("log")
    plt.gca().set_xlim([10**1,10**5])
    plt.xlabel('Latencies [s]')
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def latencies_written(params,attributeDics,plotName):
    """@latencies written plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param plotName
        name of plot
    """

    latencies = []
    for attributeDic in attributeDics:
        latencies.append(attributeDic["WrittenGPS"]-attributeDic["SentGPS"])

    if latencies == []:
        return

    plt.figure()
    bins=np.linspace(0,100,100)
    plt.hist(latencies, bins=bins, rwidth=1)
    plt.gca().set_xscale("linear")
    plt.gca().set_xlim([0,25])
    plt.xlabel('Latencies [s]')
    #title("Latencies Written")
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def magnitudes(params,attributeDics,plotName):
    """@magnitudes plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param plotName
        name of plot
    """

    gps = []
    magnitudes = []
    for attributeDic in attributeDics:
        gps.append(attributeDic["GPS"])
        magnitudes.append(attributeDic["Magnitude"])

    if magnitudes == []:
        return

    gps = np.array(gps)
    magnitudes = np.array(magnitudes)

    startTime = min(gps)
    #endTime = max(gps)
    endTime = params["gpsEnd"]
    gps = (gps - endTime)/(60)

    plt.figure()
    plt.plot(gps,magnitudes, 'k*')
    plt.ylim([min(magnitudes)-0.5, max(magnitudes)+0.5])
    plt.xlabel('Time [Minutes]')
    plt.ylabel("%.0f - %.0f"%(startTime,endTime))
    plt.xlim([-60, 0])
    plt.title("Magnitude vs. Time")
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def magnitudes_latencies(params,attributeDics,plotName):
    """@magnitudes latencies plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param plotName
        name of plot
    """

    latencies = []
    magnitudes = []
    for attributeDic in attributeDics:
        latencies.append(attributeDic["SentGPS"]-attributeDic["GPS"])
        magnitudes.append(attributeDic["Magnitude"])

    if latencies == []:
        return

    plt.figure()
    plt.plot(latencies, magnitudes, '*')
    plt.gca().set_xscale("log")
    plt.gca().set_xlim([10**1,10**5])
    plt.xlabel('Latencies [s]')
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def variable_magnitudes(attributeDicsDiff,variable,plotName):
    """@variable magnitudes plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param plotName
        name of plot
    """

    variables = []
    magnitudes = []
    for attributeDicDiff in attributeDicsDiff:
        variables.append(attributeDicDiff[variable])
        magnitudes.append(attributeDicDiff["attributeDic2"]["Magnitude"])

    if variables == []:
        return

    plt.figure()
    plt.plot(magnitudes, variables, '*')
    plt.xlabel('Magnitudes')
    plt.xlim([min(magnitudes)-0.5,max(magnitudes)+0.5])
    plt.ylim([min(variables)-0.5,max(variables)+0.5])
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def traveltimes(params,attributeDics,ifo,currentGPS,plotName):
    """@latencies sent plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param ifo
        ifo
    @param currentGPS
        current gps time
    @param plotName
        name of plot
    """

    traveltimes = []

    for attributeDic in attributeDics:

        if not ifo in attributeDic["traveltimes"]:
            continue

        if traveltimes == []:
            arrivalTimes = [max(attributeDic["traveltimes"][ifo]["RthreePointFivetimes"]),max(attributeDic["traveltimes"][ifo]["Stimes"]),max(attributeDic["traveltimes"][ifo]["Ptimes"])]
            traveltimes = np.array(arrivalTimes)
        else:
            arrivalTimes = [max(attributeDic["traveltimes"][ifo]["RthreePointFivetimes"]),max(attributeDic["traveltimes"][ifo]["Stimes"]),max(attributeDic["traveltimes"][ifo]["Ptimes"])]            
            traveltimes = np.vstack([traveltimes,arrivalTimes])

    if traveltimes == []:
        return

    traveltimes = currentGPS-traveltimes

    plotNameSplit = plotName.split("/")
    plotTitle = plotNameSplit[-1].replace(".png","").replace("traveltimes","")

    startTime = np.min(traveltimes)
    endTime = np.max(traveltimes)

    ax = plt.subplot(1,1,1)

    if len(traveltimes.shape) == 1:
        plt.plot(traveltimes[0],1.5 * np.ones(1), 'r*', label='P', markersize=10.0)
        plt.plot(traveltimes[1],2.0 * np.ones(1), 'g*', label='S', markersize=10.0)
        plt.plot(traveltimes[2],2.5 * np.ones(1), 'b*', label='R', markersize=10.0)
        plt.vlines(traveltimes[0], 0, 1.5)
        plt.vlines(traveltimes[1], 0, 2.0)
        plt.vlines(traveltimes[2], 0, 2.5)
    else:
        plt.plot(traveltimes[:,0],1.5 * np.ones(len(traveltimes[:,0])), 'r*', label='P', markersize=10.0)
        plt.plot(traveltimes[:,1],2.0 * np.ones(len(traveltimes[:,1])), 'g*', label='S', markersize=10.0)
        plt.plot(traveltimes[:,2],2.5 * np.ones(len(traveltimes[:,2])), 'b*', label='R', markersize=10.0)
        plt.vlines(traveltimes[:,0], 0, 1.5)
        plt.vlines(traveltimes[:,1], 0, 2.0)
        plt.vlines(traveltimes[:,2], 0, 2.5)
    plt.xlim([startTime-1000, 1000])
    plt.ylim([1, 3])
    plt.xlabel('Countdown [s]')
    plt.title(plotTitle)

    handles, labels = ax.get_legend_handles_labels()
    plt.legend(handles[0:3], labels[0:3])
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def find_nearest(array,value):
    """@find nearest value

    @param array
        array of values
    @param value
        value to compare array to
    """

    array = np.array(array)
    index=(np.abs(array-value)).argmin()
    return array[index], index

def worldmap_plot(params,attributeDics,type,plotName):
    """@worldmap plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param type
        type of worldmap plot
    @param plotName
        name of plot
    """

    ifo = pylal.pylal_seismon_utils.getIfo(params)

    plt.figure(figsize=(10,5))
    plt.axes([0,0,1,1])

    # lon_0 is central longitude of robinson projection.
    # resolution = 'c' means use crude resolution coastlines.
    m = Basemap(projection='robin',lon_0=0,resolution='c')
    #set a background colour
    m.drawmapboundary(fill_color='#85A6D9')

    # draw coastlines, country boundaries, fill continents.
    m.fillcontinents(color='white',lake_color='#85A6D9')
    m.drawcoastlines(color='#6D5F47', linewidth=.4)
    m.drawcountries(color='#6D5F47', linewidth=.4)

    # draw lat/lon grid lines every 30 degrees.
    m.drawmeridians(np.arange(-180, 180, 30), color='#bbbbbb')
    m.drawparallels(np.arange(-90, 90, 30), color='#bbbbbb')

    if not attributeDics == []:
        traveltimes = attributeDics[0]["traveltimes"][ifo]
        ifolat = traveltimes["Latitudes"][-1]
        ifolng = traveltimes["Longitudes"][-1]
        # compute the native map projection coordinates for cities
        ifox,ifoy = m(ifolng,ifolat)

        m.scatter(
            ifox,
            ifoy,
            s=10, #size
            c='black', #color
            marker='x', #symbol
            alpha=0.5, #transparency
            zorder = 1, #plotting order
            )
        plt.text(
            ifox+50000,
            ifoy+50000,
            ifo,
            color = 'black',
            size='small',
            horizontalalignment='center',
            verticalalignment='center',
            zorder = 2,
            )

    for attributeDic in attributeDics:

        if type == "Restimates" and "Restimate" not in attributeDic["traveltimes"][ifo]:
            continue

        x,y = m(attributeDic["Longitude"], attributeDic["Latitude"])
        if type == "Magnitude":
            color = attributeDic["Magnitude"]
            colorbar_label = "Magnitude"
            vmin = 0
            vmax = 7
        elif type == "Traveltimes":
            travel_time = attributeDic["traveltimes"][ifo]["RthreePointFivetimes"][-1] - attributeDic["traveltimes"][ifo]["RthreePointFivetimes"][0]
            travel_time = travel_time / 60
            color = travel_time
            colorbar_label = "Travel times [minutes]"
            vmin = 0
            vmax = 60
        elif type == "Restimates":
            
            travel_time = attributeDic["traveltimes"][ifo]["Restimate"] - attributeDic["traveltimes"][ifo]["RthreePointFivetimes"][0]
            travel_time = travel_time / 60
            color = travel_time
            colorbar_label = "Travel times [minutes]"
            vmin = 0
            vmax = 60
        m.scatter(
                x,
                y,
                s=10, #size
                marker='o', #symbol
                alpha=0.5, #transparency
                zorder = 3, #plotting order
                c=color, 
                vmin=vmin, 
                vmax=vmax
        )

    try:
       cbar=plt.colorbar()
       cbar.set_label(colorbar_label)
       cbar.set_clim(vmin=vmin,vmax=vmax)
    except:
       pass
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def worldmap_station_plot(params,attributeDics,data,type,plotName):
    """@worldmap plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param data
        channel data dictionary
    @param type
        type of worldmap plot
    @param plotName
        name of plot
    """

    ifo = pylal.pylal_seismon_utils.getIfo(params)

    plt.figure(figsize=(10,5))
    plt.axes([0,0,1,1])

    # lon_0 is central longitude of robinson projection.
    # resolution = 'c' means use crude resolution coastlines.
    m = Basemap(projection='robin',lon_0=0,resolution='c')
    #set a background colour
    m.drawmapboundary(fill_color='#85A6D9')

    # draw coastlines, country boundaries, fill continents.
    m.fillcontinents(color='white',lake_color='#85A6D9')
    m.drawcoastlines(color='#6D5F47', linewidth=.4)
    m.drawcountries(color='#6D5F47', linewidth=.4)

    # draw lat/lon grid lines every 30 degrees.
    m.drawmeridians(np.arange(-180, 180, 30), color='#bbbbbb')
    m.drawparallels(np.arange(-90, 90, 30), color='#bbbbbb')

    for attributeDic in attributeDics:
        x,y = m(attributeDic["Longitude"], attributeDic["Latitude"])
        m.scatter(
                x,
                y,
                s=20, #size
                marker='x', #symbol
                alpha=0.5, #transparency
                zorder = 3, #plotting order
        )
        plt.text(
                x,
                y+5,
                attributeDic["eventName"],
                color = 'black',
                size='small',
                horizontalalignment='center',
                verticalalignment='center',
                zorder = 3,
        )


    xs = []
    ys = []
    zs = []
    for channel in params["channels"]:
        channel_data = data["channels"][channel.station_underscore]

        if len(channel_data["timeseries"]["data"]) == 0:
            continue

        x,y = m(channel_data["info"].longitude,channel_data["info"].latitude)
        if type == "amplitude":
            z = channel_data["timeseries"]["data"][0] * 1e6
            xs.append(x)
            ys.append(y)
            zs.append(z)
        elif type == "time":
            z = channel_data["timeseries"]["ttMax"][0]
            xs.append(x)
            ys.append(y)
            zs.append(z)

    if xs == []:
        return

    zs = np.array(zs)
    if type == "time":
        minTime = attributeDics[0]["GPS"]
        zs = zs - minTime
        colorbar_label = "dt [s] [%d]"%minTime
        vmin = np.min(zs)
        vmax = np.max(zs)
    elif type == "amplitude":
        #vmin = np.mean(zs) - np.std(zs)
        #vmax = np.mean(zs) + np.std(zs)
        colorbar_label = "Velocity [$\mu$m/s]"
        vmin = np.min(zs)
        vmax = np.max(zs)

    im = m.scatter(
                xs,
                ys,
                s=10, #size
                marker='o', #symbol
                alpha=0.5, #transparency
                zorder = 3, #plotting order
                c=zs
    )

    #try:
    cbar = plt.colorbar(im)
    cbar.set_label(colorbar_label)
    cbar.set_clim(vmin=vmin,vmax=vmax)
    
    #except:
    #   pass
    plt.show()
    plt.savefig(plotName,dpi=200)
    plt.close('all')

def worldmap_wavefronts(params,attributeDics,currentGPS,plotName):
    """@worldmap wavefronts plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param currentGPS
        current gps
    @param plotName
        name of plot
    """

    plt.figure(figsize=(10,5))
    plt.axes([0,0,1,1])

    # lon_0 is central longitude of robinson projection.
    # resolution = 'c' means use crude resolution coastlines.
    m = Basemap(projection='robin',lon_0=0,resolution='c')
    #set a background colour
    m.drawmapboundary(fill_color='#85A6D9')

    # draw coastlines, country boundaries, fill continents.
    m.fillcontinents(color='white',lake_color='#85A6D9')
    m.drawcoastlines(color='#6D5F47', linewidth=.4)
    m.drawcountries(color='#6D5F47', linewidth=.4)

    # draw lat/lon grid lines every 30 degrees.
    m.drawmeridians(np.arange(-180, 180, 30), color='#bbbbbb')
    m.drawparallels(np.arange(-90, 90, 30), color='#bbbbbb')

    if not attributeDics == []:
     for ifoName, traveltimes in attributeDics[0]["traveltimes"].items():
        ifolat = traveltimes["Latitudes"][-1]
        ifolng = traveltimes["Longitudes"][-1]
        # compute the native map projection coordinates for cities
        ifox,ifoy = m(ifolng,ifolat)

        m.scatter(
            ifox,
            ifoy,
            s=10, #size
            c='blue', #color
            marker='o', #symbol
            alpha=0.5, #transparency
            zorder = 2, #plotting order
            )
        plt.text(
            ifox+50000,
            ifoy+50000,
            ifoName,
            color = 'black',
            size='small',
            horizontalalignment='center',
            verticalalignment='center',
            zorder = 3,
            )


    for attributeDic in attributeDics:

        if attributeDic["traveltimes"] == {}:
            continue

        ifoNames = []
        ifoDist = []
        for ifoName, traveltimes in attributeDic["traveltimes"].items():
            ifoDist.append(traveltimes["Distances"][-1])
            ifoNames.append(ifoName)
        ifoIndex = np.array(ifoDist).argmax()
        ifo = ifoNames[ifoIndex]

        nearestGPS, Pindex = find_nearest(attributeDic["traveltimes"][ifo]["Ptimes"],currentGPS)
        Pdist = attributeDic["traveltimes"][ifo]["Distances"][Pindex]/1000
        nearestGPS, Sindex = find_nearest(attributeDic["traveltimes"][ifo]["Stimes"],currentGPS)
        Sdist = attributeDic["traveltimes"][ifo]["Distances"][Sindex]/1000
        nearestGPS, Rindex = find_nearest(attributeDic["traveltimes"][ifo]["Ptimes"],currentGPS)
        Rdist = attributeDic["traveltimes"][ifo]["Distances"][Rindex]/1000

        if currentGPS > max([attributeDic["traveltimes"][ifo]["Ptimes"][-1],attributeDic["traveltimes"][ifo]["Stimes"][-1],attributeDic["traveltimes"][ifo]["RthreePointFivetimes"][-1]]):
            continue

        x,y = m(attributeDic["Longitude"], attributeDic["Latitude"])
        m.scatter(
                x,
                y,
                s=10, #size
                marker='o', #symbol
                alpha=0.5, #transparency
                zorder = 2, #plotting order
        )
        plt.text(
                x,
                y,
                attributeDic["eventName"],
                color = 'black',
                size='small',
                horizontalalignment='center',
                verticalalignment='center',
                zorder = 3,
        )

        X,Y = pylal.pylal_seismon_eqmon.equi(m, attributeDic["Longitude"], attributeDic["Latitude"], Pdist)
        m.plot(
                X,
                Y,
                linewidth = attributeDic["Magnitude"] / 2,
                zorder = 3, #plotting order
                color = 'b'
        )
        X,Y = pylal.pylal_seismon_eqmon.equi(m, attributeDic["Longitude"], attributeDic["Latitude"], Sdist)
        m.plot(
                X,
                Y,
                linewidth = attributeDic["Magnitude"] / 2,
                zorder = 3, #plotting order
                color = 'r'
        )
        X,Y = pylal.pylal_seismon_eqmon.equi(m, attributeDic["Longitude"], attributeDic["Latitude"], Rdist)
        m.plot(
                X,
                Y,
                linewidth = attributeDic["Magnitude"] / 2,
                zorder = 3, #plotting order
                color = 'y'
        )

    plt.show()
    plt.savefig(plotName,dpi=200)
    #savefig(plotNameCounter,dpi=200)
    plt.close('all')

def station_plot(params,attributeDics,data,type,plotName):
    """@worldmap plot

    @param params
        seismon params dictionary
    @param attributeDics
        list of eqmon structures
    @param data
        channel data dictionary
    @param type
        type of worldmap plot
    @param plotName
        name of plot
    """

    ifo = pylal.pylal_seismon_utils.getIfo(params)

    try:
        from obspy.taup.taup import getTravelTimes
        from obspy.core.util.geodetics import gps2DistAzimuth
    except:
        print "Enable ObsPy if updated earthquake estimates desired...\n"
        return attributeDic

    plot = gwpy.plotter.Plot(auto_refresh=True,figsize=[14,8])

    colors = cm.rainbow(np.linspace(0, 1, len(data["channels"])))
    for attributeDic in attributeDics:
        xs = []
        ys = []

        count=0
        for channel in params["channels"]:
            channel_data = data["channels"][channel.station_underscore]

            if len(channel_data["timeseries"]["data"]) == 0:
                continue

            distance,fwd,back = gps2DistAzimuth(attributeDic["Latitude"],attributeDic["Longitude"],channel_data["info"].latitude,channel_data["info"].longitude)

            xs.append(distance)
            if type == "amplitude":
                y = channel_data["timeseries"]["data"][0] * 1e6
                ys.append(y)
            elif type == "time":
                y = channel_data["timeseries"]["ttMax"][0] - attributeDic["GPS"]
                ys.append(y)

        if xs == []:
            continue

        label = attributeDic["eventName"]

        xs, ys = zip(*sorted(zip(xs, ys)))

        color = colors[count]
        plot.add_scatter(xs,ys,marker='*', zorder=1000, label=label, color=color)
        count=count+1

        z = np.polyfit(xs, ys, 1)
        p = np.poly1d(z)
        xp = np.linspace(np.min(xs),np.max(xs),100)

        label = "%s fit"%attributeDic["eventName"]
        plot.add_line(xp,p(xp),label=label)

        if type == "amplitude":
            c = 18
            fc = 10**(2.3-(attributeDic["Magnitude"]/2.))
            Q = np.max([500,80/np.sqrt(fc)])

            Rfamp = ((attributeDic["Magnitude"]/fc)*0.0035) * np.exp(-2*math.pi*attributeDic["Depth"]*fc/c) * np.exp(-2*math.pi*(xp/1000.0)*(fc/c)*1/Q)/(xp/1000.0)
            Rfamp = Rfamp * 1e6
            label = "%s prediction"%attributeDic["eventName"]
            plot.add_line(xp,Rfamp,label=label)

            Rfamp = 100 + xp * -1e-7*(attributeDic["Magnitude"]/fc) * np.exp(-2*math.pi*attributeDic["Depth"]*fc/c)
            label = "%s linear prediction"%attributeDic["eventName"]
            plot.add_line(xp,Rfamp,label=label)

        elif type == "time":
            p = np.poly1d([1.0/2000,0])
            label = "%s prediction [2 km/s]"%attributeDic["eventName"]
            plot.add_line(xp,p(xp),label=label)
            p = np.poly1d([1.0/3500,0])
            label = "%s prediction [3.5 km/s]"%attributeDic["eventName"]
            plot.add_line(xp,p(xp),label=label)
            p = np.poly1d([1.0/5000,0])
            label = "%s prediction [5 km/s]"%attributeDic["eventName"]
            plot.add_line(xp,p(xp),label=label)

    if count == 0:
        return

    if type == "time":
        ylabel = "dt [s]"
    elif type == "amplitude":
        ylabel = "Velocity [$\mu$m/s]"
        plot.axes.set_yscale("log")
        plot.ylim = [1,200]

    plot.xlabel = 'Distance [m]'
    plot.ylabel = ylabel
    plot.add_legend(loc=1,prop={'size':10})
    plot.axes.set_xscale("log")

    plot.save(plotName,dpi=200)
    plot.close()

