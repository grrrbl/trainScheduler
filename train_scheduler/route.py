import pickle
import json
import datetime
import train_scheduler.utils as utils

_attr = ['km','name', 'gleise','gleis_rauf','gleis_runter','vmax','halt_fuer','art','ladestellen','steigung','aufenthalt']

class _station_item():
    def __init__(self, name, km, **kwargs):
        self.name = name
        self.km = km
        # handle gleise, wenn kein attribute vergeben wird ist gleis = 1
        # gleis ist damit immer feniniert und wirft keine exceptions in zuege
        for i in _attr[2:5]:
            try:
                setattr(self, i, kwargs[i])
            except KeyError:
                setattr(self, i, 1)

        # handle other
        for i in _attr[5:-1]:
            try:
                setattr(self, i, kwargs[i])
            except KeyError:
                setattr(self, i, None)

        # handle time
        try:
            setattr(self, _attr[-1], datetime.timedelta(minutes=kwargs[kwargs['aufenthalt']]))
        except KeyError:
            setattr(self, _attr[-1], datetime.timedelta(0))

    def edit(self, **kwargs):
        for i in _attr:
            try:
                setattr(self, i, kwargs[i])
            except KeyError:
                pass

    def __repr__(self):
        return repr({i : getattr(self,i) for i in _attr})

    def __getitem__(self):
        return {i : getattr(self,i) for i in _attr}

class route():
    def __init__(self):
        self._stations=[]
    
    def __getitem__(self, item):
        #out = strecke()
        #out.stations=self.stations[item]
        #return out
        return self._stations[item]
    
    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(self._stations):
            self.n += 1
            return(self._stations[self.n-1])
        else:
            raise StopIteration    
    
    def __repr__(self):
        return repr(self._stations)
    
    def __len__(self):
        return len(self._stations)

    def add(self,name,km,**kwargs):
        self._stations.append(_station_item(name,km,**kwargs))
        self._stations = sorted(self._stations, key=lambda k: getattr(k,'km'))
        
       
    def reversed(self):
        out = route()
        out._stations=self._stations[::-1]
        return out

    def ls(self):
        chars_gl = str(len(str(self._stations[-1].km))+2)
        print(("{:"+chars_gl+"} {:20} {:6}").format('km','Station','Gleise'))
        print_format = "{:"+chars_gl+".1f} {:.20} {:6}"
        for i in self._stations:
            if getattr(i,'gleise') < 2:
                print(print_format.format(getattr(i,'km'),getattr(i,'name'),''))
            else:
                print(print_format.format(getattr(i,'km'),getattr(i,'name'),getattr(i,'gleise')))

    def la(self):
        chars_gl = str(len(str(self._stations[-1].km))+2)
        print(("{:"+chars_gl+"} {:20} {:8} {:4} {:9} {:15} {:10}").format(\
                    'km','Station','Gleise','Vmax','Halt für','Betriebsstelle','Aufenthalt'))
        #print(("{:"+chars_gl+"} {:24} {:2} {:2}").format('','','+','-'))
        frmt_lst = ["{:"+chars_gl+".1f} ", "{:20} ", "{:<2d} ", "{:<2d} ", "{:<2d} ", '{:3d}  ']
        frmt_fallback = ["{:"+chars_gl+".1f} ", "{:20} ", "{:2} ", "{:2} ", "{:2} ",'{:4} ']
        for station_item in self._stations:
            for attr,frmt, frmt_fb in zip(_attr[:7], frmt_lst, frmt_fallback):
                try:
                    print(frmt.format(getattr(station_item,attr)), end='')
                except (TypeError, ValueError):
                    print(frmt_fb.format(' '), end='')
            try:
                if type(getattr(station_item,'halt_fuer')) is str:
                    print('{:10}'.format(*getattr(station_item,'halt_fuer')), end='')
                    pass
                elif type(getattr(station_item,'halt_fuer')) is list:
                    frmt_halt_fuer = '{:2}' * len(getattr(station_item,'halt_fuer'))
                    print(frmt_halt_fuer.format(*getattr(station_item,'halt_fuer')), end='')
                    print('  ' * (5 - len(getattr(station_item,'halt_fuer'))), end='')
                else:
                    print('{:10}'.format(' '), end='')
            except (TypeError, ValueError):
                print('{:12}'.format(' '), end='')

            try:
                print('{:14}'.format(getattr(station_item,'art')), end='')
            except (TypeError, ValueError):
                print(' '*15,end='')

            try:
                time = int(round(getattr(station_item,'aufenthalt').total_seconds()/60))
                print("{:3d} {}".format(time, 'min'), end=" ")
            except (TypeError,AttributeError):
                print(" ",end=" ")
            print(' ')

    def ed(self, name_in, **kwargs):
        name = utils.name_completion(name_in,[i.name for i in self])

        if name == None:
            return

        pos_in_list = next(self._stations.index(i) for i in self if i.name==name)

        for i in _attr[:1] + _attr[2:-1]:
            try:
                setattr(self._stations[pos_in_list], i, kwargs[i])
                print("{}[{}] = {}".format(name, i, kwargs[i]))
            except KeyError:
                pass
        try:
            if kwargs['aufenthalt'] != None:
                setattr(self._stations[pos_in_list], _attr[-1], datetime.timedelta(minutes=kwargs['aufenthalt']))
                print("{}[{}] = {}".format(name, 'aufenthalt', kwargs['aufenthalt']))
            else:
                setattr(self._stations[pos_in_list], _attr[-1], None)
                print("{} - {}: {} ".format(name, 'aufenthalt', kwargs['aufenthalt']))
                
        except (KeyError,TypeError):
            pass

    def station(self, arg):
        if type(arg) is int:
            return self._stations[arg]
        elif type(arg) is str:    
            name = utils.name_completion(arg,[i.name for i in self])
            if name == None:
                return
            pos_in_list = next(self._stations.index(i) for i in self if i.name==name)
            return self._stations[pos_in_list]
        else:
            print('Unknown argument')
            return
            
        
    def rm(self,arg):
        if type(arg) is str:
            name = utils.name_completion(arg,[i.name for i in self])
            if arg == None:
                print('Station not found')
                return
            # get number
            pos_in_list = next(self._stations.index(i) for i in self if i.name==name)
            del self._stations[pos_in_list]

        elif type(arg) is int or type(arg) is float:
            pos_in_list = next(self._stations.index(i) for i in self if i.km==arg)
            del self._stations[pos_in_list]
        else:
            print('Unknown argument')
            return

    def save(self,filename):
        station_as_dict_lst = []
        for item in self._stations:
            station_dict = {}
            for attr in _attr[:-1]:
                try:
                    station_dict[attr] = getattr(item,attr)
                except KeyError:
                    station_dict[attr] = None
            # handle aufenthalt datetime
            try:
                station_dict['aufenthalt'] = int(getattr(item,'aufenthalt').total_seconds())
            except (KeyError,AttributeError):
                station_dict['aufenthalt'] = None
            station_as_dict_lst.append(station_dict)
        
        with open(filename, 'w') as file:
            json.dump(station_as_dict_lst,file,indent=3)

    def load(self,filename):
        with open(filename, 'r') as file:
            station_as_dict_lst = json.load(file)

        for item in station_as_dict_lst:
            station_item = _station_item(item['name'],item['km'])            
            for attr in _attr[2:-1]:
                try:
                    setattr(station_item,attr,item[attr])
                except KeyError:
                    setattr(station_item,attr,None)
            # handle aufenthalt datetime
                try:
                    setattr(station_item,'aufenthalt',datetime.timedelta(seconds=item['aufenthalt']))
                except (KeyError, TypeError,AttributeError):
                    setattr(station_item,'aufenthalt',None)
            self._stations.append(station_item)
        
