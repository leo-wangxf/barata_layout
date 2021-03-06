import sys, os, glob
import pandas as pd
from datetime import datetime
#from tkinter import Tk, filedialog
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm

# source paths
QGIS_PATH = 'C:/OSGeo4W64/apps/qgis'
SCRIPT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PATH = os.path.dirname(SCRIPT_PATH)
TEMPLATE_BASEPATH = f'{SCRIPT_PATH}/templates/tb'
TBOUTPUT_BASEPATH = f'{BASE_PATH}/8.technical_brief'

sys.path.append(SCRIPT_PATH)

from barata.barata_layout import QgsApp, FileDialog
from info.radar_info import RadarInfo

qgs = QgsApp(QGIS_PATH)
qgs.start()

# define project type
project_type = sys.argv[-2]

# define method
method = sys.argv[-1]

# input directory path
data_folder = FileDialog(BASE_PATH, method=method).open()

qgs.quit()

print('Sumber data:')
print(data_folder)
print('\n')

print('Ketersediaan data:')

# define list of data based on data folder
raster_list = glob.glob(f'{data_folder}/*.tif')

if len(raster_list) > 0:
    print('- Ada data raster')
    raster_path = raster_list[-1]
    raster_basename = os.path.basename(raster_path)

    # get radar info from raster filename
    bulan_dict = {
        '01': 'JANUARI',
        '02': 'FEBRUARI',
        '03': 'MARET',
        '04': 'APRIL',
        '05': 'MEI',
        '06': 'JUNI',
        '07': 'JULI',
        '08': 'AGUSTUS',
        '09': 'SEPTEMBER',
        '10': 'OKTOBER',
        '11': 'NOVEMBER',
        '12': 'DESEMBER',
    }

    wil = os.path.basename(os.path.dirname(raster_path))[:-16]
    radar_info = RadarInfo(raster_basename)
    rdr_name = radar_info.rdr_name
    local = radar_info.local
    tgl_local = radar_info.tgl_local
    bln_local = radar_info.bln_local
    thn_local = radar_info.thn_local
    jam_local = radar_info.jam_local
    thn = radar_info.thn
    bln = radar_info.bln
    tgl = radar_info.tgl
    j = radar_info.j
    m = radar_info.m
    d = radar_info.d

else:
    print('- Tidak ada data raster')

if len(raster_list) > 1:
    method = 'gabungan'
else:
    method = 'satu'

if method == 'gabungan':
    local_datetime = local[:-2]
    date_time = datetime.strptime(local_datetime, '%Y%m%d_%H%M')
    time = f'{jam_local}:{m}'
else:
    local_datetime = local
    date_time = datetime.strptime(local_datetime, '%Y%m%d_%H%M%S')
    time = f'{jam_local}:{m}:{d}'

location = wil.capitalize()
if location == 'Kepri':
    location = 'Kepulauan Riau'
elif location == 'Seribu':
    location == 'Kepulauan Seribu'

radar = rdr_name
date = f'{tgl_local} {(bulan_dict[bln_local]).capitalize()} {thn_local}'

layout_basepath = f'{os.path.dirname(data_folder).replace("2.seonse_outputs","3.layouts")}/{local[:8]}'

if project_type == 'ship':
    TBOUTPUT_NAME = f'TB IUU_{local_datetime} {wil.upper()}.docx'

    ship_list = glob.glob(f'{data_folder}/*{local_datetime}_ship*.csv')
    layout_list = glob.glob(f'{layout_basepath}/*{local_datetime}_ship*.png')

    if len(ship_list) > 0:
        print('- Ada data kapal')
        ship_path = ship_list[0]
        ship_df = pd.read_csv(ship_path)

        ship_df[['Longitude', 'Latitude']] = ship_df[['Longitude', 'Latitude']].applymap('{:,.6f}'.format)
        ship_df[['Heading (deg)', 'MMSI']] = ship_df[['Heading (deg)', 'MMSI']].astype('Int64')

        ship_columns = ship_df.columns.tolist()
        ship_rows = [{'label': row.tolist()[0], 'cols': row.fillna('-').tolist()[1:]} for i, row in ship_df.iterrows()]

        echo_len = len(ship_df)

        ais_len = len(ship_df[ship_df['Asosiasi (AIS/VMS)'] == 'AIS'])
        vms_len = len(ship_df[ship_df['Asosiasi (AIS/VMS)'] == 'VMS'])

        echo_text = str(echo_len)
        non_text = str(echo_len - (ais_len+vms_len))

        ais_list = glob.glob(f'{os.path.dirname(raster_path)}/*{local_datetime}_ais.csv')
        vms_list = glob.glob(f'{os.path.dirname(raster_path)}/**{local_datetime}_vms.csv')

        if len(ais_list) > 0:
            print('- Ada data AIS')
            ais_path = ais_list[0]
            ais_df = pd.read_csv(ais_path)
            ais_df[['Longitude', 'Latitude']] = ais_df[['Longitude', 'Latitude']].applymap('{:,.6f}'.format)

            ais_columns = ais_df.columns.tolist()
            ais_rows = [{'label': row.tolist()[0], 'cols': row.fillna('-').tolist()[1:]} for i, row in ais_df.iterrows()]
            ais_text = f"{ais_len}"

        else:
            print('- Tidak ada data AIS')
            ais_columns = []
            ais_rows = []
            ais_text = "0"

        if len(vms_list) > 0:
            print('- Ada data VMS')
            vms_path = vms_list[0]
            vms_df = pd.read_csv(vms_path)
            vms_df[['Longitude', 'Latitude']] = vms_df[['Longitude', 'Latitude']].applymap('{:,.6f}'.format)
            vms_df['Heading (deg)'] = vms_df['Heading (deg)'].astype('Int64')

            vms_columns = vms_df.columns.tolist()
            vms_rows = [{'label': row.tolist()[0], 'cols': row.fillna('-').tolist()[1:]} for i, row in vms_df.iterrows()]
            vms_text = f"{vms_len}"

        else:
            print('- Tidak data VMS')
            vms_columns = []
            vms_rows = []
            vms_text = "0"

        if ais_len > 0 and vms_len > 0:
            TEMPLATE_PATH = f'{TEMPLATE_BASEPATH}/TB IUU TEMPLATE (AIS and VMS).docx'
        elif ais_len > 0 or vms_len > 0:
            if ais_len > 0 and vms_len == 0:
                TEMPLATE_PATH = f'{TEMPLATE_BASEPATH}/TB IUU TEMPLATE (AIS).docx'
            elif ais_len == 0 and vms_len > 0:
                TEMPLATE_PATH = f'{TEMPLATE_BASEPATH}/TB IUU TEMPLATE (VMS).docx'
        else:
            TEMPLATE_PATH = f'{TEMPLATE_BASEPATH}/TB IUU TEMPLATE (No AIS and VMS).docx'

    else:
        print('- Tidak ada data kapal')

        echo_text = '0'
        ais_text = '0'
        vms_text = '0'
        non_text = '0'
        ship_columns = []
        ship_rows = []
        ais_columns = []
        ais_rows = []
        vms_columns = []
        vms_rows = []

        TEMPLATE_PATH = f'{TEMPLATE_BASEPATH}/TB IUU TEMPLATE (No Ship).docx'

    tpl = DocxTemplate(TEMPLATE_PATH)

    if len(layout_list) > 0:
        print('- Ada layout')
        image = InlineImage(tpl, layout_list[0], width=Mm(163.5), height=Mm(115.6))
    else:
        print('- Tidak ada layout')
        image = 'Tidak ada layout peta'

    context = {
        'image': image,
        'location': location,
        'radar': radar,
        'date': date,
        'time': time,
        'echo': echo_text,
        'ais': ais_text,
        'vms': vms_text,
        'non': non_text,
        'ship_labels': ship_columns,
        'ship_contents': ship_rows,
        'ais_labels': ais_columns,
        'ais_contents': ais_rows,
        'vms_labels': vms_columns,
        'vms_contents': vms_rows, 
    }

else:
    TBOUTPUT_NAME = f"TB OILSPILL_{local_datetime} {wil.upper()}.docx"

    oil_list = glob.glob(f'{data_folder}/*{local_datetime}_oils.csv')
    layout_list = glob.glob(f'{layout_basepath}/*{local_datetime}_oils*.png')

    if len(oil_list) > 0:
        print('- Ada data tumpahan minyak')

        oil_path = oil_list[0]
        oil_df = pd.read_csv(oil_path)
        oil_df[['Longitude', 'Latitude', 'Luas (km2)']] = oil_df[['Longitude', 'Latitude', 'Luas (km2)']].applymap('{:,.2f}'.format)
        oil_df['Luas (km2)'] = oil_df['Luas (km2)'].astype(float)

        oil_count = len(oil_df)
        total_area = oil_df['Luas (km2)'].sum()
        max_area = oil_df['Luas (km2)'].max()
        number = oil_df[oil_df['Luas (km2)'] == max_area]['No.'].array[0]
        longitude = oil_df[oil_df['Luas (km2)'] == max_area]['Longitude'].array[0]
        latitude = oil_df[oil_df['Luas (km2)'] == max_area]['Latitude'].array[0]

        if oil_count > 1:
            TEMPLATE_PATH = f'{TEMPLATE_BASEPATH}/TB OILSPILL TEMPLATE (More Oils).docx'
        elif oil_count == 1:
            TEMPLATE_PATH = f'{TEMPLATE_BASEPATH}/TB OILSPILL TEMPLATE (One Oil).docx'

    else:
        print('- Tidak ada data tumpahan minyak')

        oil_count = 0
        total_area = 0
        max_area = 0
        number = '-'
        longitude = '-'
        latitude = '-'

        TEMPLATE_PATH = f'{TEMPLATE_BASEPATH}/TB OILSPILL TEMPLATE (No Oil).docx'

    tpl = DocxTemplate(TEMPLATE_PATH)

    if len(layout_list) > 0:
        print('- Ada layout')
        if oil_count > 1:
            layout1 = [layout for layout in layout_list if "oils.png" in layout][0]
            layout2 = [layout for layout in layout_list if f"oils_{number}.png" in layout][0]
            image1 = InlineImage(tpl, layout1, width=Mm(163.5), height=Mm(115.6))
            image2 = InlineImage(tpl, layout2, width=Mm(163.5), height=Mm(115.6))
        else:
            layout1 = [layout for layout in layout_list if "oils.png" in layout][0]
            image1 = InlineImage(tpl, layout1, width=Mm(163.5), height=Mm(115.6))
            image2 = 'Tidak ada layout peta'
    else:
        print('- Tidak ada layout')
        image1 = 'Tidak ada layout peta'
        image2 = 'Tidak ada layout peta'

    context = {
        'image1': image1,
        'image2': image2,
        'location': location,
        'radar': radar,
        'date': date,
        'time': time,
        'oil_count': oil_count,
        'total_area': total_area,
        'longitude': longitude,
        'latitude': latitude,
        'number': number,
        'area': max_area,
    }

tpl.render(context)
tboutput_path = f'{TBOUTPUT_BASEPATH}/{local_datetime[:4]}/{local_datetime[:6]}'

if not os.path.exists(tboutput_path):
    os.makedirs(tboutput_path)
else:
    pass

tpl.save(f'{tboutput_path}/{TBOUTPUT_NAME}')
print('\nTB telah dibuat\n')

print('Membuka TB...')
os.startfile(f'{tboutput_path}/{TBOUTPUT_NAME}')