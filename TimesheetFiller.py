import requests
import csv
import json
from datetime import datetime

### Globals ###
config_file = "config.json"
config = {}

session  = requests.Session()
timesheets = []
dateEntries = []


### Functions ###

def main():
    init_config()
    login()
    read_csv()
    get_timesheets()
    add_entries()

def login():
    data = {
        'username' : config["username"],
        'password' : config["password"]
    }

    headers = {
        'Accept': '*/*',
        'Accept-Encoding':'gzip, deflate, br',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'Referer':'https://ice.devalore.com/app/login.php',
        'Connection': 'keep-alive'
    }

    session.post(url = config["url"] + config["login_url"], data = data)

def get_timesheets():
    timesheets.clear()

    # get earliest date
    earliestDate = datetime.strptime('01/01/3000','%d/%m/%Y')
    for dateEntry in dateEntries:
        if dateEntry.dateStart < earliestDate:
            earliestDate = dateEntry.dateStart

    # get timesheets and save only ones that end after earliest date
    r = session.get(url = config["url"] + config["timesheets_url"])
    aadata = json.loads(r.text)['aaData']
    for dat in aadata:
        dat_org = dat['_org']
        tempTimesheet = Timesheet(dat_org['id'],
            datetime.strptime(dat_org['date_start']+' 00:00','%Y-%m-%d %H:%M'),
            datetime.strptime(dat_org['date_end']+' 23:59','%Y-%m-%d %H:%M'),
            dat_org['status']
            )
        if earliestDate < tempTimesheet.dateend:
            timesheets.append(
                tempTimesheet
            )

def read_csv():
    with open(config["csv_path"]) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter = ',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                try:
                    dateEntries.append(
                        DayEntry(
                            datetime.strptime(row[0] + ' ' + row[1],'%d/%m/%Y %H:%M'),
                            datetime.strptime(row[0] + ' ' + row[2],'%d/%m/%Y %H:%M')
                            )
                        )
                except:
                    print ('err in line ' + str(line_count)+ ' ' + str(row))
            line_count += 1

def add_entry(dateEntry, timesheetId):
    data = {
        'project':'NULL',
        'date_select': dateEntry.dateStart.strftime('%Y-%m-%d'), 
        'date_start': dateEntry.dateStart.strftime('%Y-%m-%d %H:%M:%S'), 
        'date_end': dateEntry.dateEnd.strftime('%Y-%m-%d %H:%M:%S'),
        'details':'',
        'a':'add',
        'timesheet': timesheetId,
        't':'EmployeeTimeEntry',
        'time_start': dateEntry.dateStart.strftime('%H:%M:%S'),
        'time_end': dateEntry.dateEnd.strftime('%H:%M:%S'), 
        } 

    session.post(url = config["url"] + config["add_entry_url"], data = data)

def add_timesheet(date):
    # get closest timesheet
    closest_timesheet = Timesheet("0", datetime(3000,1,1,00,00),datetime(3000,1,1,23,59),"")
    for timesheet in timesheets:
        if timesheet.datestart <= date.dateStart and date.dateStart <= timesheet.dateend:
            return timesheet.id # relevent timesheet exist

        if timesheet.datestart > date.dateStart and timesheet.datestart < closest_timesheet.datestart:
            closest_timesheet = timesheet

    # send request to add prevous timesheet
    session.get(url = config["url"] + config["add_prev_timesheet_url"] + closest_timesheet.id + config["add_prev_timesheet_url_sfx"])
    get_timesheets() # update timesheets
    return add_timesheet(date) # try again

def add_entries():
    for dateEntry in dateEntries:
        timesheetId = add_timesheet(dateEntry)
        add_entry(dateEntry, timesheetId)

def init_config():
    global config
    with open(config_file) as config_file_data:
        config = json.load(config_file_data)

### Classes ###

class Timesheet():
    def __init__(self, id, datestart, dateend, status):
        self.id = id
        self.datestart = datestart
        self.dateend = dateend
        self.status = status

class DayEntry():
    def __init__(self,dateStart,dateEnd):
        self.dateStart = dateStart
        self.dateEnd = dateEnd

if __name__ == "__main__":
    main() 