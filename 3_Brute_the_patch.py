import hashlib
import json
block_size = 32
file_to_repair = "broken.zip.bin"
benchmark_file = "hashes.json"
output_file = "repaired.zip"
repaired_data = bytearray()

#Get correct hashes
with open(benchmark_file, "r") as b:
    correct_hashes = json.load(b)
    print(f"List of correct hashes created with {len(correct_hashes)} records. ")

#Work on broken file
with open(file_to_repair,"rb") as f:
    block_index = 0
    while True:
        block_to_read = f.read(block_size)  # Read the next block
        if not block_to_read:
            break

        #Calculating current and target hash
        current_hash = hashlib.sha256(block_to_read).hexdigest()
        target_hash = correct_hashes[block_index]

        #Comparing hashes
        if current_hash == target_hash:
            repaired_data.extend(block_to_read)
        else:
            print(f"Block {block_index} is broken - repairing...")
            block_to_repair = bytearray(block_to_read)
            repaired = False

            for i in range(block_size):
                original_byte = block_to_repair[i]
                for bi in range(256):
                    block_to_repair[i] = bi
                    if hashlib.sha256(block_to_repair).hexdigest() == target_hash:
                        print(f"Block {block_index} has been repaired")
                        repaired_data.extend(block_to_repair)
                        repaired = True
                        break
                if repaired:
                    break
                else:
                    block_to_repair[i] = original_byte

        block_index += 1

#New file creation
with open(output_file,"wb") as f_repaired:
    f_repaired.write(repaired_data)






