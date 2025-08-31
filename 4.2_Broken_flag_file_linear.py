"""This is the linear approach to fix the file. With slow server response, it could take even up to few days"""

import hashlib
import time
import requests

SERVER_URL = "https://py10-day4-577570284557.europe-west1.run.app"
BLOCK_SIZE = 64
BROKEN_FILE = "brokenflag.png"
REPAIRED_FILE = "repairedflag.png"

#Get Proof of Work token
def get_pow_token():
    try:
        resp = requests.get(SERVER_URL + "/ex4/get-pow")
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error in connection with server: {e}")
        return None

    #Getting challenge string
    challenge_hex = resp.json()["challenge"]
    challenge_bytes = bytes.fromhex(challenge_hex)

    #Start proof of work
    print("Proof of work starts...")
    addition = 0
    start_time = time.time()

    while True:
        token = challenge_bytes + addition.to_bytes(8,"big")
        hash_result = hashlib.sha256(token).hexdigest()

        if hash_result.startswith('ffffff'):
            end_time = time.time()
            expire_time = time.time() + 120
            print(f"Token found in {end_time - start_time:.2f} sec")
            print(f"Token to be sent: {token.hex()}. Token valid till {expire_time}")
            return token.hex(), expire_time
        addition += 1

def is_token_valid(expire_time):
    return time.time() < expire_time - 10

def request_with_token(endpoint, params, token_info):
    token, expiration = token_info
    if not is_token_valid(expiration):
        print("Token close to expire, generating new one...")
        token_info = get_pow_token()
        token, expiration = token_info
    params["pow"] = token
    r = requests.get(endpoint,params=params)
    r.raise_for_status()
    return r, token_info

def fix_file():
    token_info = get_pow_token()
    with open(BROKEN_FILE, "rb") as f_in:
        broken = bytearray(f_in.read())
    file_size = len(broken)
    repaired = bytearray(broken)
    total_blocks = file_size//BLOCK_SIZE
    print(f"Total amount of blocks in broken file: {total_blocks}")

    for i in range(total_blocks):
        offset = i * BLOCK_SIZE
        data_block = broken[offset:offset+BLOCK_SIZE]

        #Get hash from the server
        r, token_info = request_with_token(SERVER_URL+"/ex4/get-hash",{"offset":offset,"size":BLOCK_SIZE},token_info)
        correct_hash = r.text.strip()

        #Compare downloaded hash with local one
        local_hash = hashlib.sha256(data_block).hexdigest()
        if local_hash != correct_hash:
            print(f"Block no. {i} is broken. Downloading correct block")
            r, token_info = request_with_token(SERVER_URL+"/ex4/get-data",{"offset":offset},token_info)
            repaired[offset:offset+BLOCK_SIZE]=r.content
        else:
            print(f"Block no.{i} status: OK")

    #Create fixed file
    with open(REPAIRED_FILE, 'wb') as f_out:
        f_out.write(repaired)
    print(f"File fixed and saved as {REPAIRED_FILE}")

if __name__=="__main__":
    fix_file()