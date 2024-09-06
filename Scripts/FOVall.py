""" Create FOV Slice map (KML files) for all GMN cameras at all FLs """


import os
import sys
import shutil
import zipfile
from datetime import datetime
from dateutil.relativedelta import relativedelta

try:
    from RMS.Formats.Platepar import Platepar
    from RMS.Routines.MaskImage import loadMask
    from Utils.FOVKML import fovKML

except ModuleNotFoundError as m:
    print(f"{m}\nExiting...")
    sys.exit()


DATA_PATH = "/srv/meteor/rms/gmn/extracted_data/"
OUTPUT = os.path.join(os.getcwd(), "FOVall")
LOG_FILE = os.path.join(os.getcwd(), "FOVall.log")

# Flight levels: { (Flight level) : (Height in meters) }
FLIGHT_LEVELS = {
    "FL280": 8534,
    "FL290": 8839,
    "FL300": 9144,
    "FL310": 9449,
    "FL320": 9754,
    "FL330": 10058,
    "FL340": 10363,
    "FL350": 10668,
    "FL360": 10973,
    "FL370": 11278,
    "FL380": 11582,
    "FL390": 11887,
    "FL400": 12192,
    "FL410": 12497,
    "FL420": 12802,
    "FL430": 13106,
    "FL440": 13411,
    "FL450": 13716
}


def FOVall():
    """ Create FOV Slice map (KML files) for all GMN cameras at all FLs listed in FLIGHT_LEVELS

    Returns
    -------
        Creates an output folder in working directory with subdirectories for each station, containing the
        KML files
    """

    # Setup logging
    print(f"Logging to {LOG_FILE}\n")
    log = open(LOG_FILE, "w")
    print('''The below listed stations don't have data in the past month and so are not processed.
          \nOther errors will be explicitly logged.\n''', file = log)

    # Produces output directory "FOVall" in current directory if not already present
    if not os.path.exists(OUTPUT):
        os.makedirs(OUTPUT)
    os.chdir(OUTPUT)

    # Extract station names from server mount.
    # Assumes that station directories will have length 6 and
    # uppercase country code as first two characters.
    try:
        stations = [d for d in os.listdir(DATA_PATH) if (os.path.isdir(DATA_PATH + d)
                                                         and (d[:2].isupper())
                                                         and (len(d) == 6))]

    except Exception as e:
        print(f"{e}\nMake sure the GMN server is mounted at above path\nExiting...")
        sys.exit()

    # Process for each station
    for station in stations:

        # Find latest data in the station.
        station_path = os.path.join(DATA_PATH, station)
        latest_path = os.path.join(station_path, sorted([d for d in os.listdir(station_path)])[-1])

        # Station must have been active in the last month.
        # Station data directories are of the format (stationcode)_(yyyymmdd)_(hhmmss)_(ms)_detected.
        latest_date = datetime.strptime(latest_path.split('_')[2], "%Y%m%d")
        today = datetime.today()
        if latest_date <= (today - relativedelta(months = 1)):
            print(f"{station}", file = log)
            continue

        try:

            # Extract files needed for FOVKML utility.
            if not os.path.exists(os.path.join(OUTPUT, station)):
                os.makedirs(station)
            os.chdir(station)
            cwd = os.getcwd()

            shutil.copy(os.path.join(latest_path, "platepar_cmn2010.cal"), cwd)
            shutil.copy(os.path.join(latest_path, ".config"), cwd)
            with zipfile.ZipFile(os.path.join(latest_path, "mask.zip"), 'r') as z:
                z.extractall(cwd)

            # Run FOVKML for all flight levels.
            for fl in FLIGHT_LEVELS:

                pp = Platepar()
                pp.read(os.path.join(cwd, "platepar_cmn2010.cal"))
                mask = loadMask(os.path.join(cwd, "mask.bmp"))
                kml_path = fovKML(cwd, pp, mask, area_ht = FLIGHT_LEVELS[fl],
                                  side_points = 50, plot_station = False, decimal_height=True)

                # rename file to reflect flight level rather than distance in km
                os.rename(kml_path, kml_path.replace(str(FLIGHT_LEVELS[fl]/1000) + 'km', fl))

            os.chdir(OUTPUT)

        except Exception as e:

            print(f"Exception {station}: {e}", file = log)
            os.chdir(OUTPUT)
            os.rmdir(station)

    log.close()


if __name__ == "__main__":
    FOVall()
