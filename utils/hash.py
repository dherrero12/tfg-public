import hashlib

def hash_md5(data):
	data = data.encode('utf-8')
	digest = hashlib.md5(data).hexdigest()
	return int(digest, 16) // 10**30
