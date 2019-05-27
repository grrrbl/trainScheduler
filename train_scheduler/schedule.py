import json
import sys
import time
import datetime
import train_scheduler.route as route
import train_scheduler.plot as plot
import train_scheduler.physik as physik
import train_scheduler.utils as utils

class _zug_item():
    _attr_zug = ['nummer', 'gattung','vref','folgezug','folgt','start','ende']
    _attr_fpl = ['name', 'abfahrt', 'ankunft', 'gleis', 'kreuzt', 'überholt']

    def __init__(self,nummer, **args):
        self._attr = {}
        self._attr['nummer'] = nummer
        self._ax_labels = None
        self._ax_lines = None
        self._sched = []
        for arg in self._attr_zug[1:]:
            try:
                self._attr[arg] = args[arg]
            except KeyError:
                self._attr[arg] = None

    def __repr__(self):
        return repr((self._attr))

    def __getitem__(self, attr):
        return self._attr[attr]

    def _print_station(self,station):
        if station['gleis'] == None:
            station['gleis'] = ''
        print_format = "{:.<20} {:5} {:5}   {:1}"
        if station['abfahrt'] == None and station['ankunft'] != None:
            print(print_format.format(station['name'],station['ankunft'].strftime('%H:%M'),'',station['gleis']))
        elif station['abfahrt'] != None and station['ankunft'] == None:
            print(print_format.format(station['name'],'',station['abfahrt'].strftime('%H:%M'),station['gleis']))
        elif station['abfahrt'] != None and station['ankunft'] != None:
            print(print_format.format(station['name'],station['ankunft'].strftime('%H:%M'), \
                                      station['abfahrt'].strftime('%H:%M'),station['gleis']))
        else:
            print('Fehler im Format!')

    def shift(self,h=0,min=0,start=None, end=None):
        """
        Verschiebe Ankunft-/Abfahrtzeiten.
        
        Args:
            h:      Zeit in Stunden
            min:    Zeit in Minuten
            start:  Verschiebe ab Bahnhof
            en:     Verschiebe bis Bahnhof
        """
        item_start = 0
        item_end = -1

        try:
            shift = datetime.timedelta(minutes=min, hours=h)
        except TypeError:
            print('Ungültiges Format')
            return

        try:
            item_start = utils.get_item_nummer(start,self)
        except LookupError:
            item_start = 0
        try:
            item_end = utils.get_item_nummer(end,self)
        except LookupError:
            item_end = -1
        print(item_start,item_end)    
        if self._sched[item_start]['abfahrt'] != None:
            self._sched[item_start]['abfahrt'] += shift
            self._print_station(self._sched[item_start])

        for i in self._sched[item_start+1:item_end]:
            if i['abfahrt'] != None:
                i['abfahrt'] += shift
            if i['ankunft'] != None :
                i['ankunft'] += shift
            self._print_station(i)

        if self._sched[item_end]['ankunft'] != None:
            self._sched[item_end]['ankunft'] += shift
            self._print_station(self._sched[item_end])

    def fill(self,route,start_time,vref,**args):

        def get_train_direction(route):
            if (route.station(1).km - route.station(0).km) > 0:
                return 1
            else:
                return -1

        def get_vmax(route, prev, cur, vref, vcur):
            # takes a station item as arg   
            if get_train_direction(route) > 0:
                try:
                    vmax = prev.vmax
                except TypeError:
                    vmax = None
            else:
                try:
                    pos_in_list = next(route._stations.index(i) for i in route if i.name==cur.name) 
                    vmax = next(i.vmax for i in route._stations[pos_in_list:] if i.vmax != None) 
                except StopIteration:
                    vmax =  None

            if vmax == None:
                return vcur
            elif vref >= vmax:
                return vmax * 0.9
            else:   
                return vref
                        
        def add_to_sched(station_item,route,ankunft,abfahrt):
            if get_train_direction(route) > 0:
                self._sched.append({'name':station_item.name,'abfahrt':abfahrt,'ankunft':ankunft, \
                                    'gleis':station_item.gleis_rauf})
            else:
                self._sched.append({'name':station_item.name,'abfahrt':abfahrt,'ankunft':ankunft, \
                                    'gleis':station_item.gleis_runter})
            self._print_station(next(i for i in self._sched if i['name'] == station_item.name))

        abfahrt = utils.time_parser(start_time)
        ankunft = None

        # falls start und/oder stop station gegeebn wurden, sonst default
        try:
            start_pos = utils.number_lookup(args['startet'],route)
        except KeyError:
            start_pos = 0
        try:
            end_pos = utils.number_lookup(args['endet'],route)
        except KeyError:
            end_pos = -1
            
        vcur = vref
        for prev, cur in utils.pc_iter(route[start_pos:end_pos]):
            if prev != None:
                vcur = get_vmax(route,prev,cur,vref,vcur)
                try:
                    if args['gattung'] in cur.halt_fuer:
                        ankunft = abfahrt + datetime.timedelta( \
                            seconds=physik.fahrtzeit(abs(cur.km - prev.km),vcur,140,120e3,650e3,gattung=args['gattung']))
                        try:
                            abfahrt = ankunft + cur.aufenthalt
                        except TypeError:
                            abfahrt = ankunft
                    else:
                        ankunft = None
                        abfahrt += datetime.timedelta( \
                            seconds=physik.fahrtzeit(abs(cur.km - prev.km),vcur,140,120e3,650e3,gattung=args['gattung']))
                        
                except (KeyError, TypeError):
                    ankunft = None
                    abfahrt += datetime.timedelta( \
                            seconds=physik.fahrtzeit(abs(cur.km - prev.km),vcur,140,120e3,650e3))
            add_to_sched(cur, route, ankunft, abfahrt)

        # letzter halt, nur ankunft
        vcur = get_vmax(route,route[end_pos-1],route[end_pos],vref,vcur)
        ankunft = abfahrt + datetime.timedelta( seconds=physik.fahrtzeit(abs(route[end_pos].km - route[end_pos-1].km), \
                                                vcur,140,120e3,650e3,gattung=args['gattung']))
        add_to_sched(route[end_pos], route, ankunft, None)

    def add(self,route,name,*arg,**args):
        """
        Add Station to schedule.
        
        Args:
            Route
            Name
            Ankunft / Abfart
            abfahrt=,ankunft=None,gleis=None,start=None,ende=None,kreuzt=None
        """
        station_lst = [getattr(i,'name') for i in route]
        args['name'] = utils.name_completion(name, station_lst)
        if args['name'] == None:
            return

        time = []
        for i,val in enumerate(arg[:2]):
            time.append(val)

        if len(time) == 1:
            args['abfahrt'] = utils.time_parser(time[0])
            args['ankunft'] = None

        if len(time) == 2:
            args['abfahrt'] = utils.time_parser(max(time))
            args['ankunft'] = utils.time_parser(min(time))

        for attr in self._attr_fpl[1:3]:
            try:
                args[attr] = utils.time_parser(args[attr])
            except KeyError:
                pass       

        lst = [i['name'] for i in self._sched]
        if not name in lst:
            station_item = {}
            for attr in self._attr_fpl:
                try:
                    station_item[attr] = args[attr]
                except KeyError:
                    station_item[attr] = None
            self._sched.append(station_item)
            stations_fahrplan  = [i['name'] for i in self._sched]
            new_index =  [stations_fahrplan.index(i) for i in station_lst if i in stations_fahrplan]
            self._sched=[self._sched[i] for i in new_index]
        else:
            print('Station schon vorhanden')
            return            

        # print result
        self._print_station(next(i for i in self._sched if i['name'] == args['name']))

    def edit(self,name,*arg,**args):
        """
        Add Station to schedule.
        
        Args:
            Name
            Ankunft / Abfart
            abfahrt=,ankunft=None,gleis=None,start=None,ende=None,kreuzt=None
        """
        station_lst = [i['name'] for i in self._sched]
        args['name'] = utils.name_completion(name, station_lst)
        if args['name'] == None:
            return

        time = []
        for i,val in enumerate(arg[:2]):
            time.append(val)

        if len(time) == 1:
            print(len(time))
            args['abfahrt'] = utils.time_parser(time[0])
            args['ankunft'] = None

        if len(time) == 2:
            args['abfahrt'] = utils.time_parser(max(time))
            args['ankunft'] = utils.time_parser(min(time))

        for attr in self._attr_fpl[1:3]:
            try:
                args[attr] = utils.time_parser(args[attr])
            except KeyError:
                pass       

        for attr in self._attr_fpl[-2:]:
            try:
                args[attr] = utils.time_parser(args[attr])
            except KeyError:
                pass       

        nmr = next(station_lst.index(i) for i in station_lst if i==args['name'])
        for attr in self._attr_fpl:
            try:
                self._sched[nmr][attr] = args[attr]
            except KeyError:
                pass
        # print result
        self._print_station(next(i for i in self._sched if i['name'] == args['name']))

    def rm(self,station):
        lst = [i['name'] for i in self._sched]
        if station in lst:
            del self._sched[lst.index(station)]

    def ls(self):
        frmt_lst = ['Zug Nummer: {}','Folgt auf: {}','Geht über: {}']
        attr_lst =['nummer','folgt','folgezug']
        #frmt_lst = ['Zug Nummer: {}','Bereitstellung: {}','Auflösung: {}','Folgt auf: {}','Geht über: {}']
        #attr_lst =['nummer','start','end','folgt','folgezug']
        for attr,frmt in zip(attr_lst,frmt_lst):
            if self._attr[attr] != None:
                print(frmt.format(self._attr[attr]))

        print("{:20} {:6} {:6} {:6}".format('Station','Ank.', 'Abf.','Gleis'))
        for i in self._sched:
            self._print_station(i)

class schedule():
    _fig = None
    _ax = None

    def __init__(self):
        self._zug_lst = {}        

    def __repr__(self):
        return repr((self._zug_lst))

    def __getitem__(self, attr):
        return self._zug_lst[attr]

    def add_fill(self,nummer,strecke, start_time, vref, **args):
        if self._zug_lst.get(nummer,False) == False:
            self._zug_lst[nummer] = _zug_item(nummer,**args)
            self._zug_lst[nummer].fill(strecke,start_time,vref,**args)
        else:
            print('Zugnummer {} schon vergeben!'.format(nummer))
            return

    def add(self, nummer, **args):
        """ Fügt einen Zug hinzu.

        add(zugnummer, gattung=gattung, vref=vref)
        """        
        if self._zug_lst.get(nummer,False) == False:
            self._zug_lst[nummer] = _zug_item(nummer,**args)
        else:
            print('Zugnummer {} schon vergeben!'.format(nummer))
            return
            
    def edit(self, nummer, **args):
        if self._zug_lst.get(nummer,False) != False:
            for attr in ['gattung','vref','folgezug','folgt']:
                try:
                    self._zug_lst[nummer]._attr[attr] = args[attr]
                except KeyError:
                    pass
            for attr in _zug_item._attr_zug[-2:]:
                try:
                    self._zug_lst[nummer]._attr[attr] = utils.time_parser(args[attr])
                except KeyError:
                    pass       
        else:
            print('Zugnummer {} nicht vergeben!'.format(nummer))
            return
        
    def rename(self, nummer, nummer_neu):
        if self._zug_lst.get(nummer,False) != False:
            if self._zug_lst.get(nummer_neu,False) == False:
                self._zug_lst[nummer]._attr['nummer'] = nummer_neu
                self._zug_lst[nummer_neu] = self._zug_lst[nummer]
                del self._zug_lst[nummer]
            else:
                print('Neue Zugnummer {} ist schon vergeben!'.format(nummer))
        else:
            print('Zugnummer {} nicht vergeben!'.format(nummer))
            return
        
    def ls(self):
        return list(self._zug_lst)


    def cp(self, nummer_neu, nummer,h=0,min=0):
        if self._zug_lst.get(nummer,False) == False:
            print('Zugnummer {} nicht vergeben!'.format(nummer))
            return
        elif self._zug_lst.get(nummer_neu,False) != False:
            print('Neue Zugnummer {} ist schon vergeben!'.format(nummer_neu))
            return
        else:
            self.add(nummer_neu)
            # wenn ich die attribute nicht itemweise zuordne werden sie verlinkt (pointer like)
            for attr in self._zug_lst[nummer_neu]._attr_zug[1:]:
                self._zug_lst[nummer_neu]._attr[attr] = self._zug_lst[nummer]._attr[attr]
            for i in self._zug_lst[nummer]._sched:
                station_item={}
                for j in list(i.keys()):
                    station_item[j] = i[j]
                self._zug_lst[nummer_neu]._sched.append(station_item)
            self._zug_lst[nummer_neu].shift(h=h,min=min)

        
    def ls(self):
        return list(self._zug_lst)


    def rm(self,*args):
        for item in args:
            try:
                del(self._zug_lst[item])
            except KeyError:
                pass
            except StopIteration:
                print('No argument given')
                return

    def plot(self,strecke,size=(14,20),redraw=False,reopen_fig=False):
        if reopen_fig:
            self._fig  = None
            self._ax = None
            redraw=True
        self._fig, self._ax = plot.plot_schedule(self,strecke,size=size,fig=self._fig,ax=self._ax,redraw=redraw)
    
    def save(self,filename):
        def converter(o): 
           if isinstance(o, datetime.datetime): 
              return o.isoformat()

        data = {}
        for i in self._zug_lst:
            out = {'zug':{},'fpl':None}
            for j in ['nummer', 'gattung','vref','folgezug','folgt','start','ende']:
                out['zug'][j] = self._zug_lst[i]._attr[j]
            out['fpl'] = self._zug_lst[i]._sched
            data[i] = out
        
        with open(filename, 'w') as file:
            json.dump(data,file,default=converter)
    
    def load(self,filename):
        with open(filename, 'r') as file:
            data = json.load(file)

        for i in data:
            self.add(i)
            for j in ['nummer', 'gattung','vref','folgezug','folgt','start','ende']:
                try:
                    self._zug_lst[i]._attr[j] = data[i]['zug'][j]
                except KeyError:
                    self._zug_lst[i]._attr[j] = None
            for j in ['start','ende']:
                try:
                    self._zug_lst[i]._attr[j] = datetime.datetime.fromisoformat(self._zug_lst[i]._attr[j])
                except (AttributeError,TypeError,KeyError):
                    pass

            self._zug_lst[i]._sched = data[i]['fpl'] 
            for station in self._zug_lst[i]._sched:
                for time in ['ankunft','abfahrt']:
                    try:
                        station[time] = datetime.datetime.fromisoformat(station[time])
                    except (AttributeError,TypeError,KeyError):
                        pass
  
