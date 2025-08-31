block_size = 8192
filename = "shuffled.png.bin"
num_blocks = 10

#how to sort blocks
new_order = [9,2,1,4,5,0,8,7,3,6]

#final, sorted file
blocks = [None] * num_blocks

with open(filename,"rb") as f:
    for i in range(num_blocks):
        block = f.read(block_size)
        blocks[new_order[i]] = block

correct_order_data = b"".join(blocks)


#Save file with corrected blocks order
with open("correct.png","wb") as c:
   c.write(correct_order_data)

