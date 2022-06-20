import os
import sys
import psycopg2
import pandas as pd
import xml.etree.ElementTree as ET	
from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, String, Integer, BigInteger, Float
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
sys.path.insert(0, '..')
from utils.hash import hash_md5
from utils.cos import retrieve_file
from utils.auth import generate_token

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'

	id = Column(BigInteger, primary_key=True, autoincrement=False)
	fn = Column(String)
	gender = Column(Integer) 
	logs = relationship('Log', backref='user', cascade='all,delete')   
	tests = relationship('Test', backref='user', cascade='all,delete')

class Log(Base):
	__tablename__ = 'log'
	
	id = Column(BigInteger, primary_key=True, autoincrement=False)
	msgname = Column(String)
	wristopid = Column(Integer)
	logtitle = Column(String)
	lognotes = Column(String)
	starttime = Column(String)
	sampleinterval = Column(Integer)
	duration = Column(Integer)
	minalt = Column(Integer)
	maxalt = Column(Integer)
	minhr = Column(Integer)
	maxhr = Column(Integer)
	maxspeed = Column(Integer)
	avgspeed = Column(Integer)
	avgcadence = Column(Integer)
	avghr = Column(Integer)
	mintemp = Column(Integer)
	maxtemp = Column(Integer)
	totasc = Column(Integer)
	totdesc = Column(Integer)
	distance = Column(Integer)
	trainingeffect = Column(Float)
	totenergyconsumption = Column(Integer)
	totfatconsumption = Column(Integer)
	asctime = Column(Integer)
	dsctime = Column(Integer)
	hrabovetime = Column(Integer)
	hrbelowtime = Column(Integer)
	hrintime = Column(Integer)
	maxventilation = Column(Integer)
	maxoxygenconsumption = Column(Integer)
	maxbreathingfrequency = Column(Integer)
	activityid = Column(Integer)
	hrzone1 = Column(Integer)
	hrzone2 = Column(Integer)
	hrzone3 = Column(Integer)
	hrzone4 = Column(Integer)
	hrzone5 = Column(Integer)
	personal_length = Column(Integer)
	personal_weight = Column(Integer)
	personal_smoking = Column(Integer)
	personal_restinghr = Column(Integer)
	personal_maxhr = Column(Integer)
	personal_activityclass = Column(Integer)
	personal_maxbreathfrequency = Column(Integer)
	personal_lungvolume = Column(Integer)
	personal_maxventilation = Column(Integer)
	personal_epoclevel1 = Column(Integer)
	personal_epoclevel2 = Column(Integer)
	personal_epoclevel3 = Column(Integer)
	personal_epoclevel4 = Column(Integer)
	personal_maxmet = Column(Float)
	peakepoc = Column(Integer)
	hrlimithigh = Column(Integer)
	hrlimitlow = Column(Integer)
	feeling = Column(Integer)
	mod_resthr = Column(Integer)
	mod_weight = Column(Integer)
	logtype = Column(Integer)
	user_id = Column(Integer, ForeignKey('user.id')) 
	samples = relationship('Sample', backref='log', cascade='all,delete')   

class Sample(Base):
	__tablename__ = 'sample'
	
	id = Column(BigInteger, primary_key=True) 
	tm = Column(String)
	hr = Column(Integer)
	vent = Column(Integer)
	nrg = Column(Float)
	ef = Column(Float)
	vo2 = Column(Integer)	
	st = Column(Integer)
	fom = Column(Integer)
	ibi = Column(Integer)
	corrected = Column(Float)
	log_id = Column(Integer, ForeignKey('log.id')) 

class Test(Base):
	__tablename__ = 'test'

	id = Column(BigInteger, primary_key=True)
	fergo = Column(String)
	ergon = Column(Integer)
	edad = Column(Integer)
	cancer = Column(String)	
	peso = Column(Float)
	talla = Column(Float)	
	imc = Column(Integer)
	fco = Column(Integer)
	fcpico = Column(Integer)
	vo2pico = Column(Float)
	wattpico = Column(Integer)
	wattpico_peso = Column(Float)
	vepico = Column(Integer)
	eqo2pico = Column(Float)	
	eqco2pico = Column(Float)
	crpico = Column(Float)
	fcuv = Column(Integer)
	fcuvp = Column(Integer)
	vo2uv = Column(Float)
	vo2uvp = Column(Integer)
	wattuv = Column(Integer)
	wattuvp = Column(Integer)
	wattuv_peso = Column(Float)
	veuv = Column(Integer)
	veuvp = Column(Integer)
	eqo2uv = Column(Float)
	eqco2uv = Column(Float)
	cruv = Column(Float)
	fcucr = Column(Integer)
	fcucrp = Column(Integer)
	vo2ucr = Column(Float)
	vo2ucrp = Column(Integer)
	wattucr = Column(Integer)
	wattucrp = Column(Integer)
	wattucr_peso = Column(Float)
	veucr = Column(Integer)
	veucrp = Column(Integer)
	eqo2ucr = Column(Float)
	eqco2ucr = Column(Float)
	crucr = Column(Float)
	user_id = Column(Integer, ForeignKey('user.id')) 

def parse_log(data, lid):
	root = ET.fromstring(data)
	elements = [root[0][0]] + root[1][:-2]
	samples = list()
	correction_fields = ['corrected', 'ibi']
	corrections = {field: root[1][-(index+1)][0].text.split(';') for index, field in enumerate(correction_fields)}
	log_values = dict()
	index = 0
	for element in elements:
		tag = element.tag	
		value = element.text 
		if tag in {'PERSONAL_GENDER', 'PERSONAL_YEAROFBIRTH'}: continue
		if tag not in {'SAMPLE', 'IBI', 'CORRECTED'}:
			log_values[tag.lower()] = value
		elif tag == 'SAMPLE':
			sample_values = dict()
			items = element[:] + [{'tag': field, 'text': corrections[field][index]} for field in correction_fields]
			for item in items:
				if isinstance(item, dict):
					tag = item['tag']
					value = item['text']
				else:
					tag = item.tag
					value = item.text
				sample_values[tag.lower()] = value
			sample = Sample(**sample_values)	
			samples.append(sample)
	return Log(id=lid, samples=samples, **log_values) 

def parse_test(data, tid):
	data.drop(['Sexo', 'FN', 'ID'], inplace=True)
	test_values = {key.lower().strip().replace('/', '_'): value for key, value in data.to_dict().items()}
	return Test(id=tid, **test_values)
		
def update_database(iam_token, session):
	if COS_OBJECT.endswith('.xml'):
		uid, lid = COS_OBJECT[:-4].split('-')	
		log = session.query(Log).filter_by(id=lid).first()
		if log: return
		user = session.query(User).filter_by(id=uid).first()
		if not user:
			user = User(id=uid)
			session.add(user)
		data = retrieve_file(COS_OBJECT, iam_token)
		log = parse_log(data, lid)
		user.logs.append(log)
	if COS_OBJECT.endswith('tests.csv'):
		data = retrieve_file(COS_OBJECT, iam_token)
		with open(COS_OBJECT, mode='wb') as file:
			file.write(data)
		tests = pd.read_csv(COS_OBJECT)
		for index, data in tests.iterrows():
			uid = data["ID"]
			tid = hash_md5(f'{uid}{data["ErgoN"]}')
			test = session.query(Test).filter_by(id=tid).first()
			if test: continue 
			user = session.query(User).filter_by(id=uid).first()
			if not user:
				user = User(id=uid)
				session.add(user)
			user.gender = data['Sexo']
			user.fn = data['FN']
			test = parse_test(data, tid)
			user.tests.append(test)	
	session.commit()

PG_HOSTNAME = os.getenv('PG_HOSTNAME')
PG_PORT = os.getenv('PG_PORT')
PG_USER	= os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_SSL_MODE = os.getenv('PG_SSL_MODE')
PG_SSL_ROOT_CERT = os.getenv('PG_SSL_ROOT_CERT')
PG_DATABASE = os.getenv('PG_DATABASE')
PG_ENDPOINT = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOSTNAME}:{PG_PORT}/{PG_DATABASE}?sslmode={PG_SSL_MODE}'

COS_OBJECT = eval(os.getenv('CE_DATA'))['key']

if __name__ == '__main__':
	pg_path = os.path.join(os.path.expanduser('~'), '.postgresql')
	if not os.path.exists(pg_path):
		os.mkdir(pg_path)
	with open(os.path.join(pg_path, 'root.crt'), mode='w') as file:
		file.writelines([f'{line}\n' for line in PG_SSL_ROOT_CERT.split('\\n')])

	database = create_engine(PG_ENDPOINT)
	Session = sessionmaker(database)
	session = Session()
	Base.metadata.create_all(database)

	iam_token = generate_token() 
	update_database(iam_token, session)
