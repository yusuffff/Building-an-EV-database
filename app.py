import datetime
import random

from flask import Flask, render_template, request,redirect,flash
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token

app = Flask(__name__)
app.secret_key = 'kiwi'
datastore_client = datastore.Client()


def createEv(claims, manufacturer_name, vehicle_name, vehicle_battery, vehicle_power, vehicle_year, vehicle_range, vehicle_cost, date):
 # 63 bit random number that will serve as the key for this address object. not sure why the data store doesn't like 64 bit numbers
    id = random.getrandbits(63)
    entity_key = datastore_client.key('ElectricVehicle', id)
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'manufacturer_name': manufacturer_name.lower(),
        'vehicle_name': vehicle_name.lower(),
        'vehicle_battery': float(vehicle_battery),
        'vehicle_power': float(vehicle_power),
        'vehicle_year': int(vehicle_year),
        'vehicle_range': float(vehicle_range),
        'vehicle_cost':  float(vehicle_cost),
        'date': datetime.datetime.now(),
        'evid': id
    })
    datastore_client.put(entity)
    return id

def getAll_Ev():
    query = datastore_client.query(kind='ElectricVehicle')
    query.order = ['-date']
    data = query.fetch()
    return data

def fetch_ev_details(id):
    fetchRetrieval_key = datastore_client.key('ElectricVehicle', int(id))
    retrieve_key = datastore_client.get(fetchRetrieval_key)
    print('****Show items pls ***')
    print(retrieve_key)
    return retrieve_key

@app.route('/filter', methods=['POST'])
def filter():
    result = []
    list_of_ids = []
    set_of_ids = set()

    manufacturer = request.form.get('manufacturer')
    evname=request.form.get('vehicle_name')
    batterymin=request.form.get('vehicle_battery_min')
    batterymax=request.form.get('vehicle_battery_max')
    powermin=request.form.get('vehicle_power_min')
    powermax=request.form.get('vehicle_power_max')
    wltpmin=request.form.get('vehicle_range_min')
    wltpmax=request.form.get('vehicle_range_max')
    costmin=request.form.get('vehicle_cost_min')
    costmax=request.form.get('vehicle_cost_max')
    yearmin=request.form.get('vehicle_year_min')
    yearmax=request.form.get('vehicle_year_max')

    # get data id from store
    if manufacturer:
        list_of_ids.append(filter_by_name("manufacturer_name",manufacturer.lower()))

    if evname:
        list_of_ids.append(filter_by_name("vehicle_name",evname.lower()))

    if batterymin:
        list_of_ids.append(filter_by_range("vehicle_battery",{'min':float(batterymin), 'max':float(batterymax)}))

    if powermin:
        list_of_ids.append(filter_by_range("vehicle_power",{'min':float(powermin), 'max':float(powermax)}))

    if costmin:
        list_of_ids.append(filter_by_range("vehicle_cost",{'min':float(costmin), 'max':float(costmax)}))

    if yearmin:
        list_of_ids.append(filter_by_range("vehicle_year",{'min':int(yearmin), 'max':int(yearmax)}))

    if wltpmin:
        list_of_ids.append(filter_by_range("vehicle_range",{'min':float(wltpmin), 'max':float(wltpmax)}))


    # join all the id data with interception
    x = 0
    for lst in list_of_ids:
        if x == 0:
            set_of_ids = lst
        else:
            set_of_ids = set_of_ids.intersection(lst)
        x = x + 1


    # loop through the id data and get details. Save the result in a list and send it to the view
    for id in set_of_ids:
        print("id values are ")
        print(id)
        result.append(fetch_ev_details(id))

    if (not manufacturer and not evname and not batterymin and not powermin and not
    costmin and not yearmin and not wltpmin):
        result= getAll_Ev()

    return render_template('filter.html' ,data= result)

def filter_by_name(col,x):
    data = set()
    query = datastore_client.query(kind='ElectricVehicle')
    query.add_filter(col, '=', x)
    results = query.fetch()
    for result in results:
        data.add(result['evid'])
    return data

def filter_by_range(col, value):
    data = set()
    query = datastore_client.query(kind='ElectricVehicle')
    query.add_filter(col, '>=',value['min'])
    query.add_filter(col, '<=',value['max'])
    results = query.fetch()
    for result in results:
        data.add(result['evid'])
    return data

@app.route('/add', methods=['POST'])
def addEv():
    id_token = request.cookies.get("token")
    claims = None
    user_info = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
            firebase_request_adapter)
            id = createEv(claims, request.form[ 'manufacturer_name'], request.form['vehicle_name'], request.form['vehicle_battery'], request.form['vehicle_power'],
            request.form['vehicle_year'], request.form['vehicle_range'], request.form['vehicle_cost'], datetime.datetime.now())
        except ValueError as exc:
             error_message = str(exc)
    return redirect('/')

def createReviews(claims, ev_id, rating_name, comment_name, date):
 # 63 bit random number that will serve as the key for this address object. not sure why the data store doesn't like 64 bit numbers
    id = random.getrandbits(63)
    entity_key = datastore_client.key('Reviews', id)
    entity = datastore.Entity(key = entity_key)
    entity.update({
        'ev_id': ev_id,
        'rating_name':rating_name,
        'comment_name':comment_name,
        'date': datetime.datetime.now()
    })
    datastore_client.put(entity)
    return id


@app.route('/addReview', methods=['POST'])
def addReviews():
    claims = None
    id_token = request.cookies.get("token")

    if id_token:
        try:
            createReviews(claims, request.form['ev_id'], request.form['rating_name'], request.form['comment_name'], datetime.datetime.now())
        except ValueError as exc:
             error_message = str(exc)
    return redirect('/fetch_details/'+request.form['ev_id'])

@app.route('/evcomparison', methods=['POST', 'GET'])
def evcomparison():
    ev_vehicle_dictionary = {}
    get_ev_list = []


    if request.form.get('button') == "Ev_Comparsion":
        ev_get_checked = request.form.getlist('checkedEv')


        if(len(ev_get_checked) >= 2):
            get_ev_list = []

            get_ev_year_list = []
            get_ev_battery_list = []
            get_ev_wltp_list = []
            get_ev_cost_list = []
            get_ev_power_list = []
            get_ev_rating_list = []

            get_ev_maximum_year = []
            get_ev_maximum_battery = []
            get_ev_maximum_wltp = []
            get_ev_maximum_cost = []
            get_ev_maximum_power = []
            get_ev_maximum_rating = []


            maximum_year_ = 0.0
            minimum_year_ = 0.0

            maximum_rating_ = 0
            minimum_rating_ = 0

            maximum_battery_ = 0.0
            minimum_battery_ = 0.0

            maximum_wltp_ = 0.0
            minimum_wltp_ = 0.0

            maximum_cost_ = 0.0
            minimum_cost_ = 0.0

            maximum_power_ = 0.0
            minimum_power_ = 0.0

            for item in ev_get_checked:
                list = fetch_ev_details(item)
                get_ev_list.append(list)
                arg = comment_retrieve(item)


                total = 0
                count = 0
                average = 0
                comments = []
                result = {}
                for x in arg:
                    comments.append(x)
                    total = total +int(x['rating_name'])
                    count = count + 1
                if total > 0 :
                    average = total /count
                result = {'average': average, 'comments':comments}

                list['rating'] = average

                get_ev_year_list.append(list['vehicle_year'])
                get_ev_battery_list.append(list['vehicle_battery'])
                get_ev_wltp_list.append(list['vehicle_range'])
                get_ev_cost_list.append(list['vehicle_cost'])
                get_ev_power_list.append(list['vehicle_power'])
                # get_ev_rating_list.append(list['rating_name'])

                get_ev_maximum_year.append(list['vehicle_year'])
                get_ev_maximum_battery.append(list['vehicle_battery'])
                get_ev_maximum_wltp.append(list['vehicle_range'])
                get_ev_maximum_cost.append(list['vehicle_cost'])
                get_ev_maximum_power.append(list['vehicle_power'])
                # get_ev_maximum_rating.append(list['rating_name'])

                if int(minimum_year_) > list['vehicle_year'] or not minimum_year_:
                    minimum_year_ = list['vehicle_year']

                if float(minimum_battery_) > list['vehicle_battery'] or not minimum_battery_:
                    minimum_battery_ = list['vehicle_battery']

                if float(minimum_wltp_) > list['vehicle_range'] or not minimum_wltp_ :
                    minimum_wltp_ = list['vehicle_range']

                if float(minimum_cost_) > list['vehicle_cost'] or not minimum_cost_:
                    minimum_cost_ = list['vehicle_cost']

                if float(minimum_power_) > list['vehicle_power'] or not minimum_power_:
                    minimum_power_ = list['vehicle_power']

                if float(minimum_rating_) > average or not minimum_rating_:
                    minimum_rating_ = average



                if int(maximum_year_) < list['vehicle_year']:
                    maximum_year_ = list['vehicle_year']

                if float(maximum_battery_) < list['vehicle_battery']:
                    maximum_battery_ = list['vehicle_battery']

                if float(maximum_wltp_) < list['vehicle_range']:
                    maximum_wltp_ = list['vehicle_range']

                if float(maximum_cost_) < list['vehicle_cost']:
                    maximum_cost_ = list['vehicle_cost']

                if float(maximum_power_) < list['vehicle_power']:
                    maximum_power_ =  list['vehicle_power']

                if float(maximum_rating_) < average:
                    maximum_rating_ = average


                ev_vehicle_dictionary['minimum_year'] = minimum_year_
                ev_vehicle_dictionary['minimum_battery'] = minimum_battery_
                ev_vehicle_dictionary['minimum_wltp'] = minimum_wltp_
                ev_vehicle_dictionary['minimum_cost'] = minimum_cost_
                ev_vehicle_dictionary['minimum_power'] = minimum_power_
                ev_vehicle_dictionary['minimum_rating'] = minimum_rating_


                ev_vehicle_dictionary ['maximum_year'] = maximum_year_
                ev_vehicle_dictionary ['maximum_battery'] = maximum_battery_
                ev_vehicle_dictionary ['maximum_wltp'] = maximum_wltp_
                ev_vehicle_dictionary ['maximum_cost'] = maximum_cost_
                ev_vehicle_dictionary ['maximum_power'] = maximum_power_
                ev_vehicle_dictionary ['maximum_rating'] = maximum_rating_



    return render_template('evcomparison.html', data = getAll_Ev(), values = ev_vehicle_dictionary, result = get_ev_list)


def comment_retrieve(id):
    _retrieve = datastore_client.query(kind = 'Reviews')
    _retrieve.add_filter("ev_id", "=", id)
    _retrieve.order = ['-date']
    _fetch = _retrieve.fetch()
    return _fetch

firebase_request_adapter = requests.Request()

@app.route('/add')
def add_Evehicle():
    return render_template('add.html')

@app.route('/listing')
def detail():
    return render_template('listing.html')

@app.route('/fetch_details/<id>')
def fetch_details(id):
    ll = None
    review = None
    data = {}
    try:
        ll = fetch_ev_details(id)
        review = comment_retrieve(id)
        result = get_avg_rating(review)
        data['list'] = ll
        data['rating'] ="{:.1f}".format(float(result['avg']))
        data['review'] = result['comments']
        print("**************** print something  ********************")
        print(list(review))
    except ValueError as exec:
        error_message = str(exec)

    return render_template('fetch_details.html', data = data )

def get_avg_rating(arg):
    total = 0
    count = 0
    avg = 0
    comments = []
    result = {}
    for x in arg:
        comments.append(x)
        total = total +int(x['rating_name'])
        count = count + 1
    if total > 0 :
        avg = total /count
    result = {'avg': avg, 'comments':comments}
    return result

@app.route('/edit_vehicle_data', methods=['POST'])
def editVehicleData():
    id_token = request.cookies.get("token")
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            if claims:
                edit_manufacturer = request.form['manufacturer_name']
                edit_vehicle= request.form['vehicle_name']
                edit_year = request.form['vehicle_year']
                edit_battery = request.form['vehicle_battery']
                edit_range = request.form['vehicle_range']
                edit_cost = request.form['vehicle_cost']
                edit_power = request.form['vehicle_power']
                id = request.form['evid']
                updateEVInfo(edit_manufacturer, edit_vehicle, edit_year, edit_battery, edit_range, edit_cost, edit_power,id)
            else:
                flash('Login required')
                print("Login required")
        except ValueError as exc:
            error_message = str(exc)
    return redirect("/")


def updateEVInfo(edit_manufacturer, edit_vehicle, edit_year, edit_battery, edit_range, edit_cost, edit_power, id):
    Vehicle_key = datastore_client.key('ElectricVehicle', int(id))
    Vehicle_entity = datastore.Entity(key = Vehicle_key)
    Vehicle_entity.update({
        'vehicle_name': edit_vehicle.lower(),
        'manufacturer_name': edit_manufacturer.lower(),
        'vehicle_year': int(edit_year),
        'vehicle_battery': float(edit_battery),
        'vehicle_range': float(edit_range),
        'vehicle_cost': float(edit_cost),
        'vehicle_power': float(edit_power),
        'date': datetime.datetime.now(),
        'evid':id
        })
    datastore_client.put(Vehicle_entity)

@app.route('/delete_address/<id>')
def deleteEVData(id):
    id_token = request.cookies.get("token")
    error_message = None
    if id_token:
        try:
            claims = google.oauth2.id_token.verify_firebase_token(id_token,
            firebase_request_adapter)
            deleteEV(claims, id)
        except ValueError as exc:
            error_message = str(exc)
    return redirect('/')

def deleteEV(claims,id):
    deletekey = datastore_client.key('ElectricVehicle', int(id))
    datastore_client.delete(deletekey)


@app.route('/')
def root():
    return render_template('index.html', data=getAll_Ev())


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
