# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 10:17:15 2016

Get operational stations from the Global Runoff Data Centre (GRDC)
per year and their distribution

@author: Marc.Girons
"""

import os
import glob
import shutil
import numpy as np
import pandas as pd
from io import BytesIO
from zipfile import ZipFile
import matplotlib.pyplot as plt
from matplotlib import animation
from urllib.request import urlopen
from matplotlib.lines import Line2D
from mpl_toolkits.basemap import Basemap

# %%


def extract_from_url(zipurl, path):
    """extract a zip file to the cwd given its url address
    """

    print('Fetching and unzipping file...')

    if not os.path.exists(path):
        os.makedirs(path)

    with urlopen(zipurl) as zipresp:
        with ZipFile(BytesIO(zipresp.read())) as zfile:
            zfile.extractall(path)


def parse_grdc_file(path):
    """import the grdc stations excel file to a pandas dataframe and
    convert a number of columns to the suitable data type
    """

    print('Parsing file...')

    filename = glob.glob(path + '*GRDC_Stations.xlsx')[0]

    with open(filename, 'rb') as excelfile:
        data = pd.read_excel(excelfile, sheetname='grdc_metadata', index_col=0)

    num_cols = ['d_start', 'd_end', 'd_yrs', 'd_miss',
                'm_start', 'm_end', 'm_yrs', 'm_miss']

    dt_cols = ['f_import', 'l_import']

    for column in num_cols:
        data[column] = pd.to_numeric(data[column], errors='coerce')

    for column in dt_cols:
        data[column] = pd.to_datetime(data[column], format='%d.%m.%Y')

    return data


def get_data_period(data):
    """return the measurement start and end years as well as the
    associated period
    """

    print('Establishing data period...')

    m_start = np.min(data['m_start'])
    m_end = np.max(data['m_end'])

    period = np.arange(m_start, m_end).astype(int)

    return m_start, m_end, period


def count_stations(data, period):
    """count the available grdc stations for a given year
    """

    print('Calculating yearly available stations...')

    stations = np.zeros_like(period)

    for index_p, year in enumerate(period):
        for index_s, station in enumerate(data.index):
            if (year >= data['m_start'].iloc[index_s] and
                    year <= data['m_end'].iloc[index_s]):
                stations[index_p] += 1

    return stations


def get_station_locations(data, period):
    """get the coordinates of the grdc stations operational in
    a given year
    """

    print('Processing available stations locations...')

    locations = {}

    for year in period:
        ls = []
        for index_s, station in enumerate(data.index):
            if (year >= data['m_start'].iloc[index_s] and
                    year <= data['m_end'].iloc[index_s]):
                lat = data['lat'].iloc[index_s]
                lon = data['long'].iloc[index_s]
                coors = (lon, lat)
                ls.append(coors)
        locations[year] = np.array(ls)

    return locations


class SubplotAnimation(animation.TimedAnimation):

    def __init__(self, stations, locations, period):

        print('Plotting figure...')

        fig = plt.figure(figsize=(12, 4))
        ax1 = plt.subplot2grid((1, 3), (0, 0))
        ax2 = plt.subplot2grid((1, 3), (0, 1), colspan=2)

        self.stations = stations
        self.locations = locations
        self.period = period

        ax1.set_xlabel('Time (year)')
        ax1.set_ylabel('GRDC stations')
        self.time = Line2D([], [], color='#FF8000', linewidth=3)
        ax1.add_line(self.time)
        ax1.set_xlim(m_start, m_end)
        ax1.set_ylim(0, 5000)

        m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=90,
                    llcrnrlon=-180, urcrnrlon=180, resolution='l')
        m.fillcontinents(color='0.8')
        # m.drawmapboundary(linewidth=1)
        m.drawrivers(linewidth=0.2, color='C0')
        m.drawcountries(linewidth=0.4, color='w')
        self.space = m.plot([], [], markersize=3, linestyle='None',
                            marker='o', color='#FF8000',
                            markeredgecolor='none')[0]
        ax2.add_line(self.space)
        ax2.set_xlabel('GRDC stations')
        self.text = ax2.text(150, 75, '', fontsize=12)

        fig.tight_layout()

        animation.TimedAnimation.__init__(self, fig, interval=100, blit=True)

    def _draw_frame(self, framedata):

        i = framedata
        self.time.set_data(self.period[:i], self.stations[:i])

        year = self.period[i]
        lons = self.locations[year][:, 0]
        lats = self.locations[year][:, 1]
        self.space.set_data(lons, lats)

        self.text.set_text(str(year))

        self._drawn_artists = [self.time, self.space, self.text]

    def new_frame_seq(self):
        return iter(range(self.period.size))

    def _init_draw(self):
        self.time.set_data([], [])
        self.space.set_data([], [])
        self.text.set_text('')

# %%

if __name__ == '__main__':

    zipurl = ('http://www.bafg.de/GRDC/EN/02_srvcs/21_tmsrs/211_ctlgs/' +
              'GRDC_Stations.zip?__blob=publicationFile')

    path = os.getcwd() + '\\..\\tmp\\'

    extract_from_url(zipurl, path)
    data = parse_grdc_file(path)
    m_start, m_end, period = get_data_period(data)
    stations = count_stations(data, period)
    locations = get_station_locations(data, period)

    ani = SubplotAnimation(stations, locations, period)

    ani.save(os.getcwd() + '\\..\\GRDC_time_lapse.mp4', dpi=300)

    shutil.rmtree(path)

    plt.show()
