import requests
import logging
import sys
from threading import Thread
import time
import pandas as pd
from newsapp.endpoints import INDIA_STATE_WISE_URL,API_KEY_HEADERS,INDIA_COVID_HISTORY_URL, STATE_URL, COUNTRIES_URL
import re
from covid import Covid

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
CACHE_STATE_DATA = []
CACHE_COUNTRY_DATA = []
covid = Covid(source="worldometers")

def clear_cache_thread():
    global CACHE_STATE_DATA, CACHE_COUNTRY_DATA
    reset_cache_timer = 0
    logging.info("CACHING DATA INITIALLY") 
    CACHE_STATE_DATA = get_state_wise_data_wiki()
    CACHE_COUNTRY_DATA = get_country_wise_data_wiki()
    while True:
        if reset_cache_timer < 1800: # refresh every one hour, todo: add hardcoded data to config files
            reset_cache_timer += 1
            time.sleep(1)
        elif reset_cache_timer == 1800:
            logging.info("REFRESHING CACHE")
            reset_cache_timer = 0
            CACHE_STATE_DATA = []
            CACHE_COUNTRY_DATA = []
            CACHE_STATE_DATA = get_state_wise_data_wiki()
            CACHE_COUNTRY_DATA = get_country_wise_data_wiki()

def get_data():
    try:
        response = requests.get(INDIA_STATE_WISE_URL,headers = API_KEY_HEADERS)
        response = response.json()
        
        if response["statusCode"] == "200":
            data = response["response"]
            data = data[0:len(data)-1]
            return data

    except requests.RequestException as E:
        logging.log(str(E))
        return {"ERROR": "Problem with API"}

def get_corona_history():
    try:
        response = requests.get(INDIA_COVID_HISTORY_URL)
        return response.json()

    except requests.RequestException as E:
        logging.log(str(E))
        return {"ERROR": "Problem with API"}

def get_state_wise_data_wiki():
    global CACHE_STATE_DATA
    try:
        if CACHE_STATE_DATA:
            logging.info("FETCHING FROM CACHED DATA")
            return CACHE_STATE_DATA
        table = pd.read_html(STATE_URL)
        for idx in range(20):
            real_table = table[idx].columns[0:1][0:1]
            if len(real_table) > 0 and "vte COVID-19 pandemic in India by state and union territory" in real_table:  # finding the  statwise table
                table = table[idx][0:37]
                table.columns = ["S.No","location", "cases", "deaths", "recovered", "active"]
                state_data = table.to_dict('records')
                logging.info(f" India Example - {state_data[0]}")
                state_data = clean_json_data(state_data)
                CACHE_STATE_DATA = state_data
                return state_data
        return {"ERROR": "Couldn't find data in Wiki Tables"}
        # {'location': 'Andaman and Nicobar Islands', 'cases': '33', 'deaths': '0', 'recovered': '33', 'active': '0'}
    except Exception as ex:
        logging.error("Exception in State Wise Wiki API--->",ex)
        return {"ERROR": "Problem with API"}

def get_country_wise_data_wiki_archived():
    global CACHE_COUNTRY_DATA
    try:
        if CACHE_COUNTRY_DATA:
            logging.info("FETCHING FROM CACHED DATA")
            return CACHE_COUNTRY_DATA
        world_table = pd.read_html(COUNTRIES_URL)[4][0:228]
        world_table.drop([('Locations[e]', '229'), 'Ref.'], axis = 1, inplace=True)
        world_table.columns = ["location", "cases", "deaths", "recovered"]
        world_table_data =  world_table.to_dict(orient = 'records')
        logging.info(f"Countries Example - {world_table_data[0]}")
        world_table_data = clean_json_data(world_table_data)
        CACHE_COUNTRY_DATA = world_table_data
        return world_table_data
    except Exception as ex:
        logging.error("Exception in Country Wise Wiki API--->",ex)
        return {"ERROR": "Problem with Country Wise Wiki API"}

def get_country_wise_data_wiki():
    global CACHE_COUNTRY_DATA
    try:
        if CACHE_COUNTRY_DATA:
            logging.info("FETCHING FROM CACHED DATA")
            return CACHE_COUNTRY_DATA
        country_data = []
        data = covid.get_data() # Decimal values causing issues, taking only required data
        for country in data:
            if not country['country'].isdigit():
                country_data.append({"location":country["country"],"cases":country["confirmed"],"recovered":country["recovered"],"deaths":country["deaths"]})
        CACHE_COUNTRY_DATA = country_data
        return country_data
        # ["country", "confirmed", "deaths", "recovered", "active"]
    except Exception as ex:
        logging.error("Exception in Country Wise Wiki API--->",ex)
        return {"ERROR": "Problem with Country Wise Wiki API"}

def clean_json_data(data):
    """Removes Special Characters and Ablphabets from numbers"""
    for entry in data:
        entry['cases'] = re.sub('[^0-9]+', '',entry['cases'])
        entry['deaths'] = re.sub('[^0-9]+', '',entry['deaths'])
        entry['recovered'] = re.sub('[^0-9]+', '',entry['recovered'])
        if entry.get("active", None):  # Active not in Global
            entry["active"] = re.sub('[^0-9]+', '',entry.get("active", ""))
    return data

# to do, place this at apt place
t1 = Thread(target = clear_cache_thread)
logging.info("STARTING THREAD") 
t1.start()
