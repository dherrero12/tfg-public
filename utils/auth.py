import os
import time
import requests
from dotenv import load_dotenv

def retry(function):
	def wrapper(*args, **kwargs):
		while True:
			try:
				return function(*args, **kwargs)
			except Exception as error:
				print(error)
				return
	return wrapper

@retry
def generate_token():
	headers = {'Content-Type': 'application/x-www-form-urlencoded'}
	data = f'grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={IAM_API_KEY}'
	response = requests.post(IAM_AUTH_ENDPOINT, headers=headers, data=data)
	return response.json()

def refresh_token(token):
	if token['expiration'] < time.time():
		token = generate_token()
	return token

load_dotenv(dotenv_path='../.env')
IAM_API_KEY = os.getenv('IAM_API_KEY')
IAM_AUTH_ENDPOINT = os.getenv('IAM_AUTH_ENDPOINT')
