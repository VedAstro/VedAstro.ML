import time
from datetime import datetime
import swisseph as swe
import collections
from pyswisseph_constants import *
import csv
import os

class Kundali(object):
    
    def __init__(self):
        self.data = []
        self.details = [] # [row['number'], row['prsName'], row['dobStr']+" "+row['dobTz']])
        self.BhavaNumList = []
        self.dob_jul = 0
        self.lat = 0
        self.lon = 0
        self.BhavaMap = collections.OrderedDict()
        self.RashiToHouseMap = {}
        self.Grahas = {}
        self.Rashis = {}
        self.lagnaDec = 0
        self.PandasRow = {}
        swe.set_ephe_path(os.path.dirname(os.path.abspath(__file__))+"/jhcore/ephe") # set path to ephemeris files (used from datafiles of jhora)
        # swe.set_sid_mode(AYANAMSHA_RAMAN)
        swe.set_sid_mode(AYANAMSHA_LAHIRI)

    def Header(self):
        print("")
        print("####### VedAstro <> Swisseph : Degree Test#######")
        print("")

    def Setup_eph(self, lat, long):
        self.lat = lat
        self.lon = long
        swe.set_topo(lat,long)

    def decdeg2dms(self, dd):
       is_positive = dd >= 0
       dd = abs(dd)
       minutes,seconds = divmod(dd*3600,60)
       degrees,minutes = divmod(minutes,60)
       degrees = degrees if is_positive else -degrees
       return (int(degrees),int(minutes),round(seconds, 3))
   
    def hrtodec(self, hr, min, sec):
        return(hr + (min/60) + (sec/3600))

    def getRashiNum(self, degree):
        return(int(degree/30))
    
    def getDegreeStr(self, degree):
        return str(self.getRashiNum(degree)+1)+'.'+self.prnt(self.decdeg2dms((degree % 30)))
        
    def prnt(self, var):
        return(str(var[0])+'.'+str(var[1])+"."+str(var[2]))

    def getHouse(self, PlanetDegree):
        BhavaNumList = self.BhavaNumList
        if PlanetDegree<BhavaNumList[0]:
            # return last index
            return BhavaNumList[len(BhavaNumList)-2]

        for a in range(1,14):
             if PlanetDegree<=BhavaNumList[a]:
                 return BhavaNumList[a-1]
                 break


    def CaclHouses(self):
        # Vehlow = V - scroll down from :  https://www.astro.com/swisseph/swephprg.htm#_Toc112949026
        # house_loc = swe.houses_ex2(self.dob_jul, self.lat, self.lon, str.encode('V'), FLG_SIDEREAL)
        house_loc = swe.houses_ex2(self.dob_jul, self.lat, self.lon, str.encode('V'), FLG_SIDEREAL)
        Cusps = house_loc[0]
        Asc = house_loc[1]
        # print("Asc ", Asc)
        self.lagnaDec = Asc[0]
        for j in House_list:
            self.BhavaMap[Cusps[j - 1]] = str(j)
            self.RashiToHouseMap[Zodiac_sign[self.getRashiNum(Cusps[j - 1])]] = str(j)
        self.BhavaNumList = sorted(self.BhavaMap.keys())
        self.BhavaNumList.insert(13, 360)
        self.BhavaMap = self.BhavaMap 
        # print("self.BhavaMapt", selfBhavaMapHouseDict)
        # print("self.BhavaNumList", self.BhavaNumList)
        # print("self.RashiToHouseMap", self.RashiToHouseMap)
    

    def getASC(self):
        self.Grahas["LG"] = self.createGrahaJson2("LG", "")

    def createGrahaJson2(self, planet, planetPosition):
        graha_degree = 0
        lordOf = ''
        if planet in ["KE", "LG"]:
            if planet == "LG":
                graha_degree = self.lagnaDec
            elif planet == "KE":
                # print(self.Grahas)
                graha_degree =  round((self.Grahas["RA"]["degreeDecimal"] + 180) % 360, 5)
            name = planet
        else:            
            graha_degree = planetPosition[0][0]
            name = Planet_List[planet]
        house = self.BhavaMap[self.getHouse(graha_degree)]
        rashi = Zodiac_sign[self.getRashiNum(graha_degree)]
        # print(f"{planetPosition}")
        # print(f"{name} {graha_degree} {house} {rashi}")
        if(planet == "KE"):
            ke_house_calc = (int(self.Grahas["RA"]['bhava']) + 6) %12
            if( ke_house_calc != int(house) and ke_house_calc+12 != int(house)):
                print(f"{self.details[0]} -- {(int(self.Grahas['RA']['bhava']) + 6) %12} -- Error: RA -{self.Grahas['RA']['bhava']}-{self.Grahas['RA']['degreeDecimal']} and KE-{house}-{graha_degree} are not in opposite houses")
                
        lordOf = ""
        if planet != "LG":
            lordOf = []
            [lordOf.append(self.RashiToHouseMap[x]) for x in Lord_of_rashi[name]]
            # [print(x) for x in Lord_of_rashi[name]]
        
        return {
                "name": name,
                "degree": self.getDegreeStr(graha_degree),
                "degreeDecimal": graha_degree,
                "bhava": house,
                "rashi": rashi,
                "lordOf" : lordOf
            }

    def CalcPlanets(self):
        for i in Planet_List:
            # response xx = array of 6 doubles for longitude, latitude, distance, speed in long., speed in lat., and speed in dist.
            planet_pos = swe.calc(self.dob_jul, i, FLG_SIDEREAL + FLG_SWIEPH)
            self.Grahas[Planet_List[i]] = self.createGrahaJson2(i, planet_pos)

        # keDec =  round((Grahas["RA"]["degreeDecimal"] + 180) % 360, 5)
        self.Grahas["KE"] = self.createGrahaJson2("KE", "")
    
    def caclRashi(self):
        Rashis = {}
        Grahas = self.Grahas
        for key in Grahas:
            thisRashi = Grahas[key]["rashi"]
            # print(Grahas[key])
            if thisRashi not in Rashis:                                                                  
                Rashis[thisRashi] = []
            Rashis[thisRashi].append(Grahas[key])
        self.Rashis = Rashis

    def GetAyanamsa(self):
        ayan = swe.get_ayanamsa_ut(self.dob_jul)
        print("Ayanamsa = ", self.prnt(self.decdeg2dms(ayan)))


    def ReadingSetup(self,prntArr):
        strToPrnt = ""
        self.details = prntArr
        for x in prntArr:
            strToPrnt += str(x) + " --> "
        print(strToPrnt)
        
    def GetHourStrToDecimal(self, hour):
        hr = hour.split(":")
        hr_dec = float(hr[0])
        if len(hr) > 1:
            hr_dec += (float(hr[1]) / 60.0)
        if len(hr) > 2:
            hr_dec += (float(hr[2]) / 3600.0)
        return hr_dec

    def DateTime(self,year,month,date,hr,min,sec,tz):
        time = self.hrtodec(hr,min,sec)
        if tz is not None:
            tzDec = self.GetHourStrToDecimal(tz)
            time = time - tzDec
        self.dob_jul = swe.julday(year,month,date,time,GREG_CAL)
        
    def getJulByTimeDec(self,year,month,date,time,tz):
        timeDec = self.GetHourStrToDecimal(time)
        if tz is not None:
            tzDec = self.GetHourStrToDecimal(tz)
            timeDec = timeDec - tzDec
        self.dob_jul = swe.julday(year,month,date,timeDec,GREG_CAL)

    def executeSampleChartJson(self, chartjson):
        sampleChart = Kundali()
        # sampleChart.printPaths()
        sampleChart.Header()
        sampleChart.ReadingSetup([chartjson["number"], chartjson["prsName"], chartjson['place']])
        sampleChart.Setup_eph(chartjson['latitude'], chartjson['longitude'])
        # sampleChart.DateTime(1863, 1, 12, 6, 33, 0, "+05:53") # swami vivekananda
        dob = chartjson['dob'].split(" ")
        dob_date = dob[0].split("/")
        dob_time = dob[1]
        dob_tz = chartjson['dob_tz']
        sampleChart.getJulByTimeDec(int(dob_date[2]), int(dob_date[0]), int(dob_date[1]), dob_time, dob_tz)

        sampleChart.GetAyanamsa()
        sampleChart.CaclHouses()
        sampleChart.CalcPlanets()
        sampleChart.getASC()
        sampleChart.caclRashi()
        print("[")
        for key in sampleChart.Rashis:
            print(key,":", sampleChart.Rashis[key], ",")
        print("]")

    def printPaths(self):
        current_path = os.path.abspath(__file__)
        print("current_path:", current_path)

        # Get the directory of the script
        script_directory = os.path.dirname(current_path)
        print("script_directory:", script_directory)

        # Get the relative path from the script directory
        relative_path = os.path.relpath(".", script_directory)
        contents = os.listdir(relative_path)
        print("relative_path:", relative_path)
        print("relative_path contents:", contents)

#Change the input below for the chart you want to generate
start = time.time()
chart = Kundali()

zuk_chart = { # mark zuckerberg
    "number": "73618",
    "prsName": "Zuckerberg, Mark",
    "dob": "05/14/1984 00:00:00",
    "dob_tz": "-04:00",
    "place": "White Plains, New York",
    "latitude": 41.03333333333333,
    "longitude": -73.76666666666667
}

# vivekananda_chart = {
#     "number": "70141",
#     "prsName": "Vivekananda, Swami",
#     "dob": "01/12/1863 06:33:00",
#     "dob_tz": "+05:53",
#     "place": "Kolkata, India",
#     "latitude": 22.53,
#     "longitude": 88.36
# }
# chart.executeSampleChartJson(vivekananda_chart)

eclipse_chart_oct_2023 = {
    "number": "007",
    "prsName": "Rahu eclipse",
    "dob": "10/31/2023 00:00:00",
    "dob_tz": "+05:30",
    "place": "Kolkata, India",
    "latitude": 22.53,
    "longitude": 88.36
}
chart.executeSampleChartJson(eclipse_chart_oct_2023)


end = time.time()
print(datetime.now(), "- Time taken: ", end - start)