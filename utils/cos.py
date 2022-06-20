import os
import sys
import requests
from dotenv import load_dotenv
sys.path.insert(0, '.')
from utils.hash import hash_md5
from utils.auth import refresh_token, retry

@retry
def upload_file(item_name, iam_token, proxy=False):
	iam_token = refresh_token(iam_token)
	data = open(item_name).read()
	if item_name.endswith('.sml'):	
		uid = hash_md5(os.path.abspath(item_name).split('\\')[-2])
		lid = hash_md5(data)
		item_name = f'{uid}-{lid}.xml' 
	if item_name.endswith('.csv'):
		path, item_name = os.path.split(item_name)
	print(item_name)
	url = f'https://{COS_DIRECT_ENDPOINT}/{COS_BUCKET}/{item_name}'	
	headers = {'Authorization': f'bearer {iam_token["access_token"]}', 'Content-Type': 'text/plain'}
	if proxy:
		proxies = {'http': 'socks5://localhost:8443', 'https': 'socks5://localhost:8443'}
		response = requests.put(url, headers=headers, proxies=proxies, data=data)
	else:
		response = requests.put(url, headers=headers, data=data)
	return response

@retry
def retrieve_file(item_name, iam_token):
	iam_token = refresh_token(iam_token)
	url = f'https://{COS_DIRECT_ENDPOINT}/{COS_BUCKET}/{item_name}' 
	headers = {'Authorization': f'bearer {iam_token["access_token"]}'} 
	response = requests.get(url, headers=headers)
	return response.content

load_dotenv(dotenv_path=os.path.join('..', '.env'))
COS_DIRECT_ENDPOINT = os.getenv('COS_DIRECT_ENDPOINT')
COS_BUCKET = os.getenv('COS_BUCKET')
