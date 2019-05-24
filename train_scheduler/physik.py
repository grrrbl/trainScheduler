import math

#Beschleunigung: (abhängig von Länge/Gewicht und Lokomotive) 
#Reisezüge 0,2 ... 0,5 m/s² 
#Güterzug 0,05... 0,2 m/s²
#Stadtbahnen 1,0 ... 1,2 m/s²
#Straßenbahnen 1,2 ... 1,4 m/s²

#Bremsen: (abhängig von Länge/Gewicht und Lokomotivleistung) 
#Reisezüge 0,6 ... 1,0 m/s² 
#Güterzug 0,2 ... 0,5 m/s²
#Stadtbahnen 0,9 ... 1,5 m/s² 
#Straßenbahnen 0,9 ... 1,5 m/s² (Magnetschienenbremse 2,75 m/s² )<hr></blockquote></p>

def luftwiderstand(m,cw,v):
    """
    Berechne Luftwiderstand.

    Args:
        m:          Masse in tonnen
        cw:         Widerstandsbeiwert
        v:          Geschwindigkeit

        A:          Normierte  Fläche, 10m^2
        phi:        Dichte Luft
    """
    
    A = 10
    phi = 1.4
    return (cw*A*phi*v)/(2*m*9.81)
    

def lok_kn_max(lok_m,steigung=0,mu=0.25):
    """
    Berechne maximale Zugkraft in abhängigkeit vin Steigung und Reibungszahl.

    Args:
        lok_m:      Masse in tonnen
        steigung:   Steigung in promille
        mu:         Reibungszahl
    """
    return lok_m * 9810 * math.cos(steigung/1000) * mu

def fz(lok_m,wagen_m,wagen_n,a,v,steigung=0):
    # m*g*dv/dt = -W(s,v) + F_zugkraft - F_bremskraft 
    """
    lok_m:      Masse Lok
    wagen_m:    Masse Wagen
    wagen_n:    Anzahl Wägen
    a:          Beschleunigung
    v:          Geschwindigkeit
    """

    rollwiderstand              = 2e-3
    steigungswiderstand         = math.sin(math.tan(steigung/1000))
    beschleunigungswiderstand   = a*1.2/9.81

    def luftwiderstand(m,cw,v):
        """
            m:          Masse in tonnen
            cw:         Widerstandsbeiwert
            v:          Geschwindigkeit
            A:          Normierte  Fläche, 10m^2
            phi:        Dichte Luft
        """
        A = 10
        phi = 1.4
        return (cw*A*phi*v**2)/(2*m*9.81)

    if wagen_n > 2:
        cw = 0.4 + 0.35 + (wagen_n-2)*0.12 + 0.25
    elif wagen_n > 1:
        cw = 0.4 + 0.7
    else:
        cw = 0.8

    m_zug = lok_m + wagen_m * wagen_n
    return round(m_zug* 9.81 * (luftwiderstand(m_zug,cw,v) + rollwiderstand + steigungswiderstand+beschleunigungswiderstand))

def kn(zug_w,fz_max,v):
    v /= 3.6 #v normieren in m/s
    if v == 0:
        return fz_max
    elif 0.7*(zug_w / v) > fz_max:
        return fz_max 
    else:
        return (0.7 * zug_w)/v

def kn_dd1100(fz_max,v):
    v /= 3.6 #v normieren in m/s
    if v < 2.8:
        return fz_max
    elif v < 8.4:
        return 1.3*fz_max - (.6*fz_max/8.3) *v
    else:
        return 0.7*fz_max - (.5*fz_max/18.8) *v

def fahrtzeit(strecke,vmax,zug_m,lok_kn_max,lok_w,a_brems = 0, stepsize=0.1,gattung=None):
    """
    Berechne fahrtzeit in Sekunden in abhängigkeit von Strecke und Zug.

    Args:
        strecke:  Strecke in km
        vmax:     Maximale geschwindigkeit
        zug_m:    Masse zug in t
        lok_kn:   Maximale Zugkraft Lok
        lok_w:    Leistung Lok

        stepsize: Iterationsschritt (eIn Wert 0.1 ist sinnvoll)
        
    """

    if gattung in ['P','E']:
        a_brems = .3
    if gattung in ['G','N','Ng']:
        a_brems = .1

    def bremsweg(v,a):
        return v**2/(2*a)

    s,v,t = 0,0,0
    while t <= 1e9: 
        a = kn(lok_w,lok_kn_max,v*3.6)/(zug_m*1000)
        if v < vmax/3.6:
            v += a*stepsize
            s += v*stepsize
            t += stepsize
            #if t%1.0 > .99:
            #    print("a: {:4.1f}, v: {:5.1f}, strecke [m]:{:5.1f}, zeit [s]:{:5.0f}".format(a,v*3.6,s/1000,t))
        else:
            t += (strecke*1000 - s)/v
            s = strecke
            break

        if  s >= strecke*1000:
            break
    
    if a_brems != 0:
        t -= bremsweg(v,a_brems) / v
        t += v / a_brems
    
    #print("{:8} v: {:5.1f}, strecke [m]:{:5.0f}, zeit [s]:{:5.0f}".format('',v*3.6,s,t))
    return int(round(t))
    
def fahrtzeit_neu(strecke,vmax,lok_m, wagen_m, wagen_n, lok_kn_max, a_brems = 0, stepsize=0.1, gattung=None,steigung=0):
    """
    Berechne fahrtzeit in Sekunden in abhängigkeit von Strecke und Zug.

    Args:
        strecke:  Strecke in km
        vmax:     Maximale geschwindigkeit
        zug_m:    Masse zug in t
        lok_kn:   Maximale Zugkraft Lok
        lok_w:    Leistung Lok

        stepsize: Iterationsschritt (eIn Wert 0.1 ist sinnvoll)
        
    """

    if gattung in ['P','E']:
        a_brems = .3
    if gattung in ['G','N','Ng']:
        a_brems = .1

    def bremsweg(v,a):
        return v**2/(2*a)

    a,s,v,t = 0,0,0,0
    while t <= 1e9: 
        a_cur = (kn_dd1100(lok_kn_max,v) - fz(lok_m,wagen_m, wagen_n, a,v,steigung=steigung) ) / (lok_m+wagen_m*wagen_n)
        if a_cur >= 0:
            if a_cur > 0.3:
                a = 0.3
            else:
                a = a_cur        

        if v < vmax/3.6:
            v += a*stepsize
            s += v*stepsize
            t += stepsize
            #if t%1.0 > .99:
            print("a: {:4.1f}, v: {:5.1f}, strecke [m]:{:5.1f}, zeit [s]:{:5.0f}".format(a,v*3.6,s/1000,t))
        else:
            t += (strecke*1000 - s)/v
            s = strecke
            break

        if  s >= strecke*1000:
            break
    
    if a_brems != 0:
        t -= bremsweg(v,a_brems) / v
        t += v / a_brems
    
    #print("{:8} v: {:5.1f}, strecke [m]:{:5.0f}, zeit [s]:{:5.0f}".format('',v*3.6,s,t))
    return int(round(t))
    
