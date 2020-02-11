from zipfile import ZipFile
from xml.etree import ElementTree
from shapely.geometry import Point
import geopandas as gpd
import pandas as pd
import glob
from itertools import groupby

#dto_path = r"D:\BARATA\6.dto\cosmo_skymed\201907\20190704\psdkp_singkep_20190704_102120_dto.kml"
                
class DTO:
    def __init__(self, dto_path, i):
        with open(dto_path) as dto:
            self.dto_content = dto.read()
            self.tree = ElementTree.fromstring(self.dto_content)
            self.kmlns = self.tree.tag.split('}')[0][1:]
            self.name_elems = self.tree.findall(".//{%s}name" % self.kmlns)

            if self.name_elems[0].text[:10] == 'RADARSAT-2':
                self.desc_elems = self.tree.findall(".//{%s}description" % self.kmlns)
                
                self.info_list = []
                for desc_elem in self.desc_elems:
                    desc = desc_elem.text.split('\n')[1:-1]
                    
                    desc_dict = {}
                    for d in desc:
                        x = d.split(': ')
                        desc_dict[x[0]] = x[1]
                    self.info_list.append(desc_dict)

                self.dto_dict = self.info_list[1:][i-1]

            else:
                self.b_elems = self.tree.findall(".//{%s}b" % self.kmlns)
                self.desc = [b.text for b in self.b_elems]
                self.info_list = self.desc[2:]
                
                def split_condition(x):
                    return x in {' '}
                
                self.grouper = groupby(self.info_list, key=split_condition)
                self.info_grouped = dict(enumerate((list(j) for i, j in self.grouper if not i), 1))

                self.info = self.info_grouped[i]
                
                self.pr_id = self.info[0]
                self.ar_counter = self.info[1]
                self.sensing_start = self.info[2]
                self.sensing_stop = self.info[3]
                self.sensor_mode = self.info[4]
                self.satellite = self.info[5]
                self.orbit_direction = self.info[6]
                self.look_side = self.info[7]
                self.look_angle = self.info[8]
                self.beam = self.info[9]
                
                self.dto_dict = {'PR ID':self.pr_id,
                            'AR Counter':self.ar_counter,
                            'Sensing Start':self.sensing_start,
                            'Sensing Stop':self.sensing_stop,
                            'Sensor Mode':self.sensor_mode,
                            'Satellite':self.satellite,
                            'Orbit Direction':self.orbit_direction,
                            'Look Side':self.look_side,
                            'Look Angle':self.look_angle,
                            'Beam':self.beam}

    def to_dict(self):
        return self.dto_dict

#data_path = r"X:\2.seonse_outputs\cosmo_skymed\201812\kepri_20181207_23*"
    
class AIS:
    def __init__(self, data_path):
        self.longitude = []
        self.latitude = []
        self.shipnumber = []
        self.targetlength = []
        self.ais_mmsi = []
        self.geometry = []

        self.zipfilelist = glob.glob(f'{data_path}\\*SHIPKML.zip')
        if len(self.zipfilelist) > 0:
            self.zipfilepath = self.zipfilelist[0]
            self.shipfilepath = glob.glob(f'{data_path}\\*SHIP.shp')[0]

            with ZipFile(self.zipfilepath) as theZip:
                self.fileNames = theZip.namelist()
                for fileName in self.fileNames:
                    if fileName.endswith('kml'):
                        self.content = theZip.open(fileName).read()
                        self.tree = ElementTree.fromstring(self.content)
                        self.kmlns = self.tree.tag.split('}')[0][1:]
                        self.data_elems = self.tree.findall(".//{%s}Data" % self.kmlns)
                        self.point_elems = self.tree.findall(".//{%s}Point" % self.kmlns)
                        for child in self.point_elems:
                            for subchild in child:
                                self.coords = (subchild.text).split(' ')
                                self.x_coord = float(self.coords[0])
                                self.y_coord = float(self.coords[1])
                                self.geom = Point(self.x_coord, self.y_coord)
                                self.longitude.append(self.x_coord)
                                self.latitude.append(self.y_coord)
                                self.geometry.append(self.geom)
                        for data in self.data_elems:
                            self.name = data.get('name')
                            if self.name == 'AIS MMSI':
                                self.mmsi = data.find(".//{%s}value" % self.kmlns).text
                                if self.mmsi != 'N/A':
                                    self.aismmsi = int(self.mmsi)
                                else:
                                    self.aismmsi = None
                                self.ais_mmsi.append(self.aismmsi)
                            if self.name == 'Ship Number':
                                self.number = data.find(".//{%s}value" % self.kmlns).text
                                self.shipnumber.append(int(self.number))
                            if self.name == 'Target Length':
                                self.length =  data.find(".//{%s}value" % self.kmlns).text
                                self.targetlength.append(float(self.length))
                                
            self.aisdf = pd.DataFrame({'LON_CENTRE':self.longitude, 'LAT_CENTRE':self.latitude, 'SHIP_ID':self.shipnumber, 'LENGTH':self.targetlength, 'AIS_MMSI':self.ais_mmsi})
            self.aisdf['AIS_MMSI'] = self.aisdf['AIS_MMSI'].where(pd.notnull(self.aisdf['AIS_MMSI']), None)
            self.shipgdf = gpd.read_file(self.shipfilepath)
            self.shipgdf['AIS_MMSI'] =  self.aisdf['AIS_MMSI']
            self.shipgdf.to_file(self.shipfilepath)

    def to_gdf(self):
        return self.shipgdf
