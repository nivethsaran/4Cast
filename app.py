import re
from urllib3.exceptions import InsecureRequestWarning
import warnings
from datetime import datetime, timedelta, timezone, date
import datetime
import time
import urllib3
import os
from flask import *
app = Flask(__name__)
import sqlite3,json
from secret import *
from tempjson import *
warnings.simplefilter('ignore', InsecureRequestWarning)
ROOT_FOLDER= os.path.dirname(os.path.abspath(__file__))
today = date.today()
app.config['SECRET_KEY'] = 'RailwayManagement'
@app.route('/')
def startup():
   message=''
   if 'username' in session:
      message='Working'
   return render_template('startup.html',message=message)

#Login Route 
@app.route('/login', methods=('GET', 'POST'))
def login():
      error=''
      if request.method == 'POST':
         try:
            username = request.form['username']
            password = request.form['password']
            if len(username) == 0 or len(password) == 0:
               flash('Please fill both fields to login')
            else:
               conn = None
               try:
                  railway = os.path.join(ROOT_FOLDER,'weather.db')
                  conn = sqlite3.connect(railway)
                  dbURL = "SELECT username,password,fname,lname,email,mobile,city FROM user where username=?"
                  cursor = conn.cursor()
                  cursor.execute(dbURL,(username,))
                  rows=cursor.fetchall()
                  clen=int(len(rows))
                  if clen==0:
                     flash('Account does not exist')
                  else:
                     for row in rows:
                        if row[0]==username and row[1]==password:
                           fullname=row[2]+' '+row[3]
                           citytocookie=row[6]
                           # resp.set_cookie('city',citytocookie)
                           session['fullname']=fullname
                           session['username']=username
                           session['mobile']=row[5]
                           session['email']=row[4]
                           resp=make_response(redirect(url_for('home')))
                           resp.set_cookie('city',citytocookie)
                           return resp
                        else:
                           flash('Wrong passwords')
                  
               except Exception as e:
                  flash('Some unexpected error occured, so please try again')
               finally:
                  if conn:
                     conn.close()   
         except Exception as e:
            flash('Some unexpected error occured, so please try again')
      return render_template('login.html')
      
#Function to check is mobile number is valid
def isValidNumber(number):
    Pattern = re.compile("(0/91)?[5-9][0-9]{9}")
    return Pattern.match(number)

#Function to check if password is valid
def validPassword(password):
   flag = 0
   while True:
       if (len(password) < 8):
           flag = -1
           break
       elif not re.search("[a-z]", password):
           flag = -1
           break
       elif not re.search("[A-Z]", password):
           flag = -1
           break
       elif not re.search("[0-9]", password):
           flag = -1
           break
       elif not re.search("[_@$#]", password):
           flag = -1
           break
       elif re.search("\s", password):
           flag = -1
           break
       else:
           flag = 0
           return 'valid'

   if flag == -1:
       return 'invalid'

#Signup Route
@app.route('/signup',methods=['GET','POST'])
def signup():
   city=''
   if request.method=='POST':
      fname=request.form['fname']
      lname=request.form['lname']
      username=request.form['username']
      password=request.form['password']
      email=request.form['email']
      mobile=request.form['mobile']
      city=request.form['city']
      regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
      if fname == '' or lname == '' or username == '' or password == '' or email == '' or mobile == '':
         flash('All fields are mandatory')
      elif not re.search(regex,email):
            flash('Enter Valid email')
      elif validPassword(password)=='invalid':
         flash('Weak Password')
      elif city == 'EMPTY':
         flash('Choose a City')
      elif not isValidNumber(mobile):
         flash('Invalid Mobile Number')
      else:
         conn = None
         try:

            railway = os.path.join(ROOT_FOLDER, 'weather.db')
            conn = sqlite3.connect(railway)
            dbURL = "INSERT INTO user values(?,?,?,?,?,?)"
            cursor = conn.cursor()
            cursor.execute(dbURL,(fname,lname,username,password,email,mobile))
            conn.commit()
            resp=make_response(redirect(url_for('login')))
            resp.set_cookie('city',city)
            return resp
         except Exception as e:
            flash('Duplicate username')
         finally:
            if conn:
               conn.close()

   resp = make_response(render_template('signup.html', list=sorted(citylist)))
   resp.set_cookie('city', city)
   return resp


#Home Route 
@app.route('/home',methods=["GET","POST"])
def home():
   listbm = []
   if request.method=='POST' and 'username' in session:
      conn = None
      try:
         railway = os.path.join(ROOT_FOLDER, 'weather.db')
         conn = sqlite3.connect(railway)
         dbURL = "SELECT trainnumber,station FROM trainbookmark where username=?"
         cursor = conn.cursor()
         cursor.execute(dbURL, (session['username'],))
         for row in cursor:
            listbm.append(row)
      except Exception as e:
         print(e)
      return render_template('home.html', listbm=listbm)
   else:
      return render_template('home.html')


@app.route('/timemachine',methods=["GET","POST"])
def timemachine():
   selected = ''
   data = {'currently': None}
   if request.method == "POST":
      city = request.form['city']
      datech=request.form['date']
      print(datech)
      if not city == 'EMPTY':
         citylat = citydict[city]['lat']
         citylng = citydict[city]['lng']
      if datech=='':
         flash("Enter Date")
      else:
         timestamp=int(time.mktime(datetime.datetime.strptime(datech, "%Y-%m-%d").timetuple()))
         try:
            queryURL = 'https://api.darksky.net/forecast/'+apikey+'/'+citylat+','+citylng+','+str(timestamp)+"?units=si"
            print(queryURL)
            http = urllib3.PoolManager()
            r = http.request('GET', queryURL)
            data = json.loads(r.data)
         except Exception as e:
             print(e)
             flash('Unexpected Error Occured, Check your Internet Connection')
   return render_template('timemachine.html', list=sorted(citylist), selected=selected,currently=data['currently'])


@app.route('/weekly',methods=["GET","POST"])
def weekly():
   selected=''
   trainlist = []
   weeklylist=[]
   data={'currently':None}
   if request.method=="POST":
      city=request.form['city']
      if not city == 'EMPTY':
         citylat=citydict[city]['lat']
         citylng=citydict[city]['lng']
         try:
            queryURL = 'https://api.darksky.net/forecast/'+apikey+'/'+citylat+','+citylng
            http = urllib3.PoolManager()
            r = http.request('GET', queryURL)
            data=json.loads(r.data);
            weeklydata=data['daily']['data']
            # print(weeklydata)
            # print(data['daily']['data'])
            for dailydata in weeklydata:
               temptime = dailydata['time']
               timestamp = datetime.datetime.fromtimestamp(temptime)
               datefinal=(timestamp.strftime('%d-%m-%Y'))
               
               tempicon=dailydata['icon']
               icon=''
               if tempicon=='clear-day':
                  icon='🌞'
               elif tempicon == 'clear-night':
                  icon='🌙'
               elif tempicon=='rain':
                  icon='🌧'
               elif tempicon=='snow':
                  icon='❄'
               elif tempicon=='wind':
                  icon='🍃'
               elif tempicon=='fog':
                  icon='🌁'
               elif tempicon == 'cloudy':
                  icon='☁'
               elif tempicon == 'partly-cloudy-day':
                  icon='⛅'
               elif tempicon == 'partly-cloudy-night':
                  icon='🌥'
               weeklylist.append({'time':datefinal,'summary':dailydata['summary'],'icon':icon})
            print(weeklylist)
         except Exception as e:
               print(e) 
               flash('Unexpected Error Occured, Check your Internet Connection')
         # print(data['currently'])
         
         # data = json.loads(livestationdata);
         #trainlist=data['trains']

         selected=request.form['city']
      else:
         flash('Choose a city to continue')
   return render_template('weekly.html',list=sorted(citylist),selected=selected,weeklylist=weeklylist)


@app.route('/raincoat',methods=["GET", "POST"])
def raincoat():
   selected=''
   weeklylist=[]
   data={'currently':None}

   if (request.method == 'GET'):
      city = request.cookies.get('city')
      if(city):
         citylat=citydict[city]['lat']
         citylng=citydict[city]['lng']
         try:
            queryURL = 'https://api.darksky.net/forecast/'+apikey+'/'+citylat+','+citylng
            http = urllib3.PoolManager()
            r = http.request('GET', queryURL)
            data=json.loads(r.data);
         except Exception as e:
            print(e) 
            flash('Unexpected Error Occured, Check your Internet Connection')

   if request.method=="POST":
      city=request.form['city']
      if not city == 'EMPTY':
         citylat=citydict[city]['lat']
         citylng=citydict[city]['lng']
         try:
            queryURL = 'https://api.darksky.net/forecast/'+apikey+'/'+citylat+','+citylng
            http = urllib3.PoolManager()
            r = http.request('GET', queryURL)
            data=json.loads(r.data);
         except Exception as e:
            print(e) 
            flash('Unexpected Error Occured, Check your Internet Connection')
         selected=request.form['city']
      else:
         flash('Choose a city to continue')

   return render_template('raincoat.html',list=sorted(citylist),selected=selected,currently=data['currently'])



@app.route('/about')
def about():
   return render_template('about.html')


@app.route('/logout')
def logout():
   session.pop('username',None)
   session.pop('fullname',None)
   session.pop('mobile',None)
   session.pop('email',None)
   return render_template('login.html')




if __name__=='__main__':
    app.run()
