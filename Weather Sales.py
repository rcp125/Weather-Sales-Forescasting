import pandas as pd
from fbprophet import Prophet
from os import walk


####### ENTER INPUTS HERE #######

zipcode = '90210'
event_type = 'Thunderstorm Wind'
path = 'ENTER PATH HERE'

################################

dataframe = []

### traverses through csv files for each year and stores dir in an array
f = []
for (dirpath, dirnames, filenames) in walk(path + "//WeatherEvents"):
    f.extend(filenames)
    break

### remove leading zeros from zip to match columns in excel
def formatZip(zipcode):
    zipcode = str(zipcode).lstrip('0')
    return zipcode

### use modified zip to find fip. implement function to find zip and then return fip in the same row
modzip = int(formatZip(zipcode))
df = pd.read_csv(path + "//ZipToFip.csv")

ziploc = df.loc[df['ZIP']==modzip].index.values  ### returns array of indices where zipcode is found
# print(ziploc)

fipcol = df['STCOUNTYFP']
fiparray = []
for i in ziploc: ### traverses through array of zipcodes and finds corresponding FIP
    temp = fipcol[i]
    fiparray.append(temp)
# print(fiparray)

### parse fip to match format in excel
def parsefip(fip):
    if(len(fip) == 4):
        state = fip[:1]
        county = fip[1:]
    if(len(fip) == 5):
        state = fip[:2]
        county = fip[2:]

    return (state, county)

def read(filename):
    df = pd.read_csv(path + "//WeatherEvents" + filename)
    return df 

### using state fip, county fip and event input; search excel and return all corresponding dates
def find_intersect(county, state, df):
    eventloc = df.loc[df['EVENT_TYPE']==event_type].index.values
    cfiploc = df.loc[df['CZ_FIPS']==county].index.values
    sfiploc = df.loc[df['STATE_FIPS']==state].index.values
    intersect = list(set(eventloc).intersection(cfiploc, sfiploc))
    return intersect

def formatDate(y, m, d):
    if(len(d) == 1):
        d = "0" + d
    month = {
        'January': '01',
        'February': '02',
        'March': '03',
        'April': '04',
        'May': '05',
        'June': '06',
        'July': '07',
        'August': '08',
        'September': '09',
        'October': '10',
        'November': '11',
        'December': '12'
    }
    date = y + "-" + month[m] + "-" + d
    return date

# print(intersect[0])
def print_result(intersect, df):
    months = df['MONTH_NAME']
    years = df['YEAR']
    days = df['BEGIN_DAY']
    marray = []
    yarray = []
    darray = []

    for i in intersect: ### traverses through array of zipcodes and finds corresponding FIP
        temp_month = months[i]
        temp_year = years[i]
        temp_day = days[i]

        marray.append(temp_month)
        yarray.append(temp_year)
        darray.append(temp_day)

    for i in range(len(marray)):
        date = formatDate(str(yarray[i]), str(marray[i]), str(darray[i]))
        dataframe.append(date)

# executes for one occurrence
def execute_once(fip, filename):
    df = read(filename)
    state = int(parsefip(fip)[0])
    county = int(parsefip(fip)[1])
    intersect = find_intersect(county, state, df)
    print_result(intersect, df)

# executes for all occurrences in a particular year
def loop_dates(filename):
    for i in range(len(fiparray)):
        execute_once(str(fiparray[i]), filename)

# executes for all dates & years
def execute():
    for i in f:
        loop_dates(i)

execute()
print(dataframe)

### Forecasting

salesdf = pd.read_csv(path + "sales.csv")
df = salesdf[(salesdf['pstlcd']==str(modzip))][['ds','y']]
df = df[['ds','y']]
df['y'] = df['y'].rolling(7,center=False).sum()
df = df.dropna()

m = Prophet(daily_seasonality=False).add_seasonality(
    name='monthly', period=30.5, fourier_order=15).add_seasonality(
    name='quarterly', period=365.25/4, fourier_order=5)

m.fit(df)

future = m.make_future_dataframe(periods=365)
# future.tail()

# forecast = m.predict(future)
# forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()


### Create holiday
occurrences = pd.DataFrame({
  'holiday': 'occurrences',
  'ds': pd.to_datetime(dataframe),
  'lower_window': -7,
  'upper_window': 7,
})

holidays = occurrences

m = Prophet(holidays=holidays)
forecast = m.fit(df).predict(future)

forecast[(forecast['occurrences']).abs() > 0][
        ['ds', 'occurrences']][-10:]

fig1 = m.plot(forecast)
fig2 = m.plot_components(forecast)
