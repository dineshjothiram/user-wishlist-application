from flask import Flask, render_template,request
import redis

app = Flask(__name__)

#postgresql://username:password@host:port/database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev'

from models import db, UserFavs

db.init_app(app)
with app.app_context():
	db.create_all()
	db.session.commit()

red = redis.Redis(host='redis',port=6379)
@app.route("/")
def main():
	return render_template("index.html")

@app.route("/save",methods=['POST'])
def save():
	username = request.form['username']
	place    = request.form["place"]
	food     = request.form["food"] 

	print("Username:",username)
	print("Place:",place)
	print("Food",food)


	#check if username exists in redis
	if red.hgetall(username).keys():
		print("hget username:", red.hgetall(username))
		return render_template('index.html', user_exists = 1,msg='(From Redis)',username=username,place=red.hget(username,"place").decode('utf-8'), food=red.hget(username,"food").decode('utf-8'))
	# if not in redis, then check in db
	elif len(list(red.hgetall(username).keys()))==0:
		record = UserFavs.query.filter_by(username=username).first()
		print("Records fetched from DB is :", record)
	
		if record:
			red.hset(username,"place",record.place)
			red.hset(username,"food",record.food)

			return render_template('index.html', get=1, msg='(From DataBase)',username=username, place=record.place, food=record.food)
	
	# if data of the username doesnot exist either in redis or in db
	# create a new record in db and store the data in redis as well

	new_record  = UserFavs(username=username,place=place,food=food)
	db.session.add(new_record)
	db.session.commit()
	
	#store in redis
	red.hset(username,"place",place)
	red.hset(username,"food",food)

	record = UserFavs.query.filter_by(username=username).first()
	print("Records fetched from DB after insert is :", record)

	#check insert operation in redis
	print("Username from redis after insert", red.hgetall(username))

	return render_template("index.html",saved=1,username=username, place=red.hget(username,"place").decode('utf-8'), food=red.hget(username,"food").decode('utf-8'))
	#return "Entered Save"

@app.route("/keys", methods=['GET'])
def keys():
	records = UserFavs.query.all()
	names = []
	for record in records:
		names.append(record.username)
	return render_template('index.html', keys=1, usernames=names)

@app.route("/get",methods=['POST'])
def get():
	username = request.form['username']
	print("Username",username)
	user_data = red.hgetall(username)

	if not user_data:
		record = UserFavs.query.filter_by(username=username).first()
		if not record:
			return render_template('index.html',no_record=1,msg=f"Record not yet defined for {username}")
		red.hset(username,"place",record.place)
		red.hset(username,"food",record.food)
		return render_template('index.html',get=1,msg="(From Database)",username=username, place=record.place, food=record.food)
	return render_template('index.html',get=1, msg="(From Redis)", username=username, place=user_data[b'place'].decode('utf-8'), food=user_data[b'food'].decode('utf-8'))