import train_scheduler.route
import train_scheduler.schedule
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.transforms
import datetime
import train_scheduler.utils

# for label lines
from math import atan2,degrees
import numpy as np
import datetime
import matplotlib.dates as md

def labelLine(line,x,label=None,align=True,**kwargs):

    ax = line.axes
    xdata = line.get_xdata()
    ydata = line.get_ydata()
    ydata_m = md.date2num(ydata)
    x=min(xdata) + (max(xdata) - min(xdata))/2
    y=min(ydata) + (max(ydata) - min(ydata))/2
    y=md.date2num(y)+0.01
    if (max(xdata) - min(xdata))/2 < 1:
        return

    if not label:
        label = line.get_label()

    if align:
        #Compute the slope
        dx = xdata[0] - xdata[1]
        dy = md.date2num(ydata[0]) - md.date2num(ydata[1])
        ang = degrees(atan2(dy,dx))
        if abs(ang) > 90:
            ang += 180 
        print('dx,dy,a',dx,dy,ang)

        #Transform to screen co-ordinates
        pt = np.array([x,1]).reshape((1,2))
        pt = np.array([x,y]).reshape((1,2))
        #pt = np.array([x,y.minute]).reshape((1,2))
        trans_angle = ax.transData.transform_angles(np.array((ang,)),pt)[0] 

    else:
        trans_angle = 70

    #Set a bunch of keyword arguments
    if 'color' not in kwargs:
        kwargs['color'] = line.get_color()

    if ('horizontalalignment' not in kwargs) and ('ha' not in kwargs):
        kwargs['ha'] = 'center'

    if ('verticalalignment' not in kwargs) and ('va' not in kwargs):
        kwargs['va'] = 'center'

    #if 'backgroundcolor' not in kwargs:
    #    kwargs['backgroundcolor'] = ax.get_facecolor()

    if 'clip_on' not in kwargs:
        kwargs['clip_on'] = True

    if 'zorder' not in kwargs:
        kwargs['zorder'] = 2.5

    ax.text(x,y,label,rotation=trans_angle,backgroundcolor=(1,1,1,0),**kwargs)

def labelLines(lines,align=True,xvals=None,**kwargs):

    ax = lines[0].axes
    labLines = []
    labels = []

    #Take only the lines which have labels other than the default ones
    for line in lines:
        label = line.get_label()
        if "_line" not in label:
            labLines.append(line)
            labels.append(label)

    if xvals is None:
        xmin,xmax = ax.get_xlim()
        xvals = np.linspace(xmin,xmax,len(labLines)+2)[1:-1]

    for line,x,label in zip(labLines,xvals,labels):
        labelLine(line,x,label,align,**kwargs)


def gleis_linien(station_item):
    gleis_linie_distance = .3
    gleis_linie_distance_ba = .3
    if station_item.gleise > 1 and station_item.gleise % 2 == 0:
        gleise = list(range(station_item.gleise))
        gleise =[(i+0.5-station_item.gleise/2)*gleis_linie_distance for i in gleise]
        gleise = [min(gleise)-gleis_linie_distance_ba] + gleise + [max(gleise)+gleis_linie_distance_ba]
    elif station_item.gleise > 1 and station_item.gleise % 2 == 1:
        gleise = list(range(station_item.gleise))
        gleise =[(i-int((station_item.gleise)/2))*gleis_linie_distance for i in gleise]
        gleise = [min(gleise)-gleis_linie_distance_ba] + gleise + [max(gleise)+gleis_linie_distance_ba]
    else:
        gleise = [0]
    return gleise

def x_minor_ticks(loc_strecke):
    ticks = []
    for station_item in loc_strecke:
        if  len(gleis_linien(station_item)) <= 1:
            continue
        for gleis in gleis_linien(station_item):
            ticks.append(station_item.km+gleis)
    return ticks
    
def x_tick_labels(loc_strecke):
    tick_labels = []
    for i in loc_strecke:
        tick_labels.append(i.name+', '+str(i.km))
        if i.gleise != None or i.gleise > 1:
            tick_labels.append(' ')
    return tick_labels

def x_major_ticks(loc_strecke):
    ticks = []
    for station_item in loc_strecke:
        ticks.append(station_item.km+max(gleis_linien(station_item)))
        if station_item.gleise != None or station_item.gleise > 1:
            ticks.append(station_item.km+min(gleis_linien(station_item)))
    return ticks

def plot_zug(zug_lst,i,cur_strecke,ax):

    zug=zug_lst[i] 
    lines=[]

    def plot_item_line(prev,cur,lines):
        km = []
        if prev['station'].km < cur['station'].km:
            km.append(prev['station'].km+max(gleis_linien(prev['station'])))
            km.append(cur['station'].km+min(gleis_linien(cur['station'])))
        else:
            km.append(prev['station'].km+min(gleis_linien(prev['station'])))
            km.append(cur['station'].km+max(gleis_linien(cur['station'])))


        if cur['fpl']['ankunft'] != None:
            time = [prev['fpl']['abfahrt'],cur['fpl']['ankunft']]
        else:
            time = [prev['fpl']['abfahrt'],cur['fpl']['abfahrt']]

        if zug['gattung'] == 'G':
            line_color = 'g'
        elif zug['gattung'] == 'E':
            line_color = 'b'
        else:
            line_color = 'k'

        if type(time[0]) is datetime.datetime and type(time[1]) is datetime.datetime:         
            lines += ax.plot(km,time,color=line_color,linewidth=1,label=zug['nummer'])
            labelLines([lines[-1]]) 
            #labelLines([ax.get_lines()[-1]]) 
            #labelLines([lines[-1]],label=zug['nummer'])
        else:
            return

    def plot_item_station(station_item, fpl_item, marker=None,lines=[]):
        try:
            gleis_plt = gleis_linien(station_item)[fpl_item['gleis']]
        except IndexError:
            gleis_plt = 0
            
        if fpl_item['ankunft'] != None:
            time = [fpl_item['ankunft'],fpl_item['abfahrt']]
        else:
            time = [fpl_item['abfahrt'],fpl_item['abfahrt']]
        gleis_station = 2*[station_item.km + gleis_plt]

        if marker == 's':
            my_markersize = 3
        else:
            my_markersize = 3

        if zug['gattung'] == 'G':
            line_color = 'g'
        elif zug['gattung'] == 'E':
            line_color = 'b'
        else:
            line_color = 'k'

        if type(time[0]) is datetime.datetime and type(time[1]) is datetime.datetime:         
            lines += ax.plot(gleis_station,time,line_color, marker=marker, markersize=my_markersize,linewidth=3)
        else:
            return
        
        
    #plotte jeweils streckenweise zwischen bahnhöfen
    #station_items = 
    iter = []
    # plot line station start
    if type(zug['start']) is datetime.datetime:
            station_item = next(j for j in cur_strecke if j.name in zug._sched[0]['name'])
            plot_item_station(station_item, \
                              {'ankunft':zug['start'],'abfahrt':zug._sched[0]['abfahrt'],'gleis':zug._sched[0]['gleis']} , \
                              marker='', lines=lines)

    if type(zug['start']) is datetime.datetime:
            station_item = next(j for j in cur_strecke if j.name in zug._sched[0]['name'])
            plot_item_station(station_item, \
                              {'ankunft':zug['start'],'abfahrt':zug._sched[0]['abfahrt'],'gleis':zug._sched[0]['gleis']} , \
                              marker='', lines=lines)
    # plot erste
    station_item = next(j for j in cur_strecke if j.name in zug._sched[0]['name'])
    if type(zug['start']) is datetime.datetime:
        plot_item_station(station_item, \
                          {'abfahrt':zug._sched[0]['abfahrt'],'ankunft':zug['start'],'gleis':zug._sched[0]['gleis']} , \
                          marker='', lines=lines)
    else:
        plot_item_station(station_item, \
                          {'abfahrt':zug._sched[0]['abfahrt'],'ankunft':None,'gleis':zug._sched[0]['gleis']} , \
                          marker='s', lines=lines)
    # plot lines route
    station_items = []
    for i in zug._sched:
        station_items.append(next( j for j in cur_strecke if j.name==i['name']))
    for i,j in zip(zug._sched,station_items):
        iter.append({'fpl':i,'station':j})
    for prev, cur in utils.pc_iter(iter):
        if prev != None:
            # plot aufenthalt im bahnhof
            if cur['fpl']['ankunft'] == cur['fpl']['abfahrt']:
                plot_item_station(cur['station'], cur['fpl'], marker="s",lines=lines)
            if cur['fpl']['abfahrt'] != None:
                if cur['fpl']['ankunft'] != None:
                    plot_item_station(cur['station'], cur['fpl'], lines=lines)
                else:
                    plot_item_station(cur['station'], cur['fpl'], marker="o",lines=lines)
            
            # plot fahrstrecke
            plot_item_line(prev,cur,lines=lines)

    # plot letzte
    station_item = next(j for j in cur_strecke if j.name in zug._sched[-1]['name'])
    if type(zug['ende']) is datetime.datetime:
        plot_item_station(station_item, \
                          {'ankunft':zug._sched[-1]['ankunft'],'abfahrt':zug['ende'],'gleis':zug._sched[-1]['gleis']} , \
                          marker='', lines=lines)
    else:
        plot_item_station(station_item, \
                          {'abfahrt':zug._sched[-1]['ankunft'],'ankunft':None,'gleis':zug._sched[-1]['gleis']} , \
                          marker='s', lines=lines)
    return lines

def plot_schedule(zug,my_strecke,size=(14,20),fig=None,ax=None,redraw=False):

    # plots erstellen
    if fig == None:
        fig = plt.figure(figsize=size,dpi=100)  # an empty figure with no axes

    if redraw:
        fig.delaxes(ax)

    if ax == None or redraw:
        ax = fig.add_subplot(111)
        ax.set_xticks(x_major_ticks(my_strecke))
        ax.set_xticks(x_minor_ticks(my_strecke),minor=True)

        ax.set_xticklabels(x_tick_labels(my_strecke))
        ax.tick_params(labelrotation=40,axis='x')
        ax.invert_yaxis()
        hours = mdates.HourLocator()
        mins = mdates.MinuteLocator(byminute=[15,30,45])
        yearsFmt = mdates.DateFormatter('%H:%M')
        ax.yaxis.set_major_locator(hours)
        ax.yaxis.set_major_formatter(yearsFmt)
        ax.yaxis.set_minor_locator(mins)
        ax.grid(which='major', axis='x', linewidth=1.6)
        ax.grid(which='major', axis='y')
        ax.grid(which='minor', axis='y', linestyle=':')
        ax.grid(which='minor', axis='x')
        ax.autoscale_view(tight=None, scalex=False)
        ax.set_ylim(top=datetime.datetime(1900,1,1,5),bottom=datetime.datetime(1900,1,1,20))
        ax.set_xlim(left=my_strecke[0].km-1, right=my_strecke[-1].km+1)

        dx = -4/72.; dy = 9/72. 
        offset = matplotlib.transforms.ScaledTranslation(dx, dy, fig.dpi_scale_trans)
        for label in ax.xaxis.get_majorticklabels():
            label.set_rotation_mode('anchor')
            label.set_ha('right')
            label.set_va('center_baseline')
            label.set_transform(label.get_transform() - offset)

        if not redraw:
            fig.tight_layout()

    #plot_zug(zug[1642],my_strecke,ax)
    for i in zug.ls():
        plot_zug(zug,i,my_strecke,ax)
        #labelLines(fig.gca().get_lines())
        #print(fig.gca().get_lines()[0])





    fig.savefig('res1.png')
    plt.show()
    #plt.close(fig)
    
    return fig,ax

