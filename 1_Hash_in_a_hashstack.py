import hashlib

hash_with_flag = "790d88483531ac32a12a57b233818ff698fb4ed7011f5c749f3b7493ba1ac5e1"
block_size = 512
filename = "hashstack.bin"

#Looking for a flag to be decoded
try:
    with open(filename, "rb") as f:
        while True:
            block_to_read = f.read(block_size)
            if not block_to_read:
                break
            if hashlib.sha256(block_to_read).hexdigest() == hash_with_flag:
                print("Block with flag found")
                print(f"Decoded block: {block_to_read.decode()}")
                break
except FileNotFoundError:
    print("File not found.")

#Decoding flag:

flag_found = "} k C a 4 S h s 4 H - e h T - n I - e L d 3 3 N { A x e H"
cleaned_flag = ''.join(flag_found.split())[::-1]
print(cleaned_flag)