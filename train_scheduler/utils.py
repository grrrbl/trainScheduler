import datetime
from dateutil.parser import isoparse
from itertools import tee, chain

d_ofst='19000101T'
def time_parser(time):
    d_ofst='19000101T'
    if type(time) is int:
        if 0 <= time <= 2359:
            time= '{:04d}'.format(time)
            return isoparse(d_ofst+time)
        elif time == -1:
            return None
        else:
            print('Ungültige Zeitangabe in _time_pares')
            return None
    elif type(time) is datetime.datetime:
        return time
    else:
        return None

def get_item_nummer(name,fpl):
    if name == None or name == '':
        raise LookupError('Keine Station gegeben')
    station_lst = [i['name'] for i in fpl._sched]
    station=[i for i in station_lst if name in i]
    if len(station) == 0:
        print('Station nicht gefunden')
        raise LookupError('Station nicht gefunden')
        return
    if len(station) > 1:
        print('Station nicht eindeutig')
        raise LookupError('Station nicht gefunden')
        return
    else:
        return next(i for i,x in enumerate(fpl._sched) if x['name']==station[0])


def name_completion(name,station_lst):
# einfach name completion
    station=[i for i in station_lst if name in i]
    if len(station) == 0:
        print('Station nicht gefunden')
        return None
    if len(station) > 1:
        print('Station nicht eindeutig')
        return None
    else:
        station = station[0]   
    return station

def number_lookup(name,route):
    if name == None or name=='':
        raise LookupError('Keine Station angegeben')
        return
    station_lst = [getattr(i,'name') for i in route]
    station=[i for i in station_lst if name in i]
    if len(station) == 0:
        raise LookupError('Station nicht gefunden')
        #return
    if len(station) > 1:
        #print('Station nicht eindeutig')
        raise LookupError('Station nicht eindeutig')
        #return
    else:
        return next(i for i,x in enumerate(route) if x.name==station[0])



def pc_iter(i):
    prevs, items = tee(i, 2)
    prevs = chain([None], prevs)
    #nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items)

def pcn_iter(i):
    prevs, items = tee(i, 2)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)


