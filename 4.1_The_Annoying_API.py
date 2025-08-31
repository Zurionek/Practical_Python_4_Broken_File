import hashlib
import json
import requests
import time

def get_challenge(url):
    #Connection establish and get json from link
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error in connection with server: {e}")
        return None

    #Getting challenge string
    challenge_hex = data["challenge"]
    challenge_hex_in_bytes = bytes.fromhex(challenge_hex)
    print(f"Received challenge in hex: {challenge_hex}")

    #Proof of work stage
    print("Proof of work begins...")
    addition = 0
    start_time = time.time()

    while True:
        additional_bytes = addition.to_bytes(8,"big")
        new_token = challenge_hex_in_bytes + additional_bytes

        #Counting hash of new_token in bytes
        hash_result = hashlib.sha256(new_token).hexdigest()

        #Check if hash result starts with 0xFFFFFF
        if hash_result.startswith('ffffff'):
            end_time = time.time()
            print(f"Solution found in {end_time-start_time:.2f} sec")
            print(f"Addition found is: {addition}")
            print(f"Final hash in hex: {hash_result}")
            print(f"Token to be sent: {new_token.hex()}")
            return new_token

        addition += 1

if __name__=="__main__":
    base_url = "https://py10-day4-577570284557.europe-west1.run.app/ex4/get-pow"
    get_flag_url = "https://py10-day4-577570284557.europe-west1.run.app/ex4/get-flag"
    final_result = get_challenge(base_url).hex()

    if final_result:
        params = {"pow":final_result}
        the_flag = requests.get(get_flag_url, params=params)
        the_flag.raise_for_status()
        print(f"Received flag: {the_flag.text}")


