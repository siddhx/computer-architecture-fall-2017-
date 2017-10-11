#! python

import sys, string
wordsize 		= 24
numregbits 		= 3
opcodesize		= 5
memloadsize 	= 1024
numregs 		= 2**numregbits
opcodeposition	= wordsize - (opcodesize + 1)
reg1position	= opcodeposition - (numregbits + 1)
reg2position	= reg1position - (numregbits + 1)

memaddrimmedposition	= reg2position
startexecptr 	= 0;
def regval(rstr):
	if rstr.isdigit():
		return (int(rstr))
	elif rstr[0] == '*':
		return ( int(rstr[1:]) + ( 1 << numregbits))
	else:
		return 0
mem = [0] * memloadsize
# instruction mnemonic, type: (1 reg, 2 reg, reg + reg, reg + addr, immed, pseudoop), opcode
opcodes = { 'add':(2,1), 'sub':(2,2),
			'dec':(1,3), 'inc':(1,4),
			'ld':(3,7), 'st':(3,8), 'ldi':(3,9),
			'bnz':(3,12), 'brl':(3,13),
			'ret':(1,14), 
			'int':(3, 16), 'sys':(3,16),
			'dw':(4, 0), 'go':(3, 0), 'end':(0, 0) }

curaddr = 0
# for line in open(sys.argv[1], 'r').readlines():
infile = open("in.asm", 'r')
# Build symbol table
sysmboltable = {}
for line in infile.readlines():
	tokens = string.split(string.lower(line))
	firsttoken = tokens[0]
	if firsttoken.isdigit():
		curaddr = int(tokens[0])
		tokens = tokens[1:]
	if firsttoken == ';':
		continue
	if firsttoken == 'go':
		startexecptr = (int(tokens[1]) & ((2**wordsize)-1)) # data
		continue
	if firsttoken[0] == '.':
		sysmboltable[firsttoken] = curaddr
	curaddr = curaddr + 1
print sysmboltable
infile.close()
infile = open("in.asm", 'r')
for line in infile.readlines():
	tokens = string.split(string.lower(line))
	firsttoken = tokens[0]
	if firsttoken.isdigit():
		curaddr = int(tokens[0])
		tokens = tokens[1:]
	if firsttoken == ';':
		continue
	if firsttoken == 'go':
		startexecptr = (int(tokens[1]) & ((2**wordsize)-1)) # data
		continue
	if firsttoken[0] == '.':
		sysmaddr = sysmboltable[firsttoken]
		tokens = tokens[1:]
	curaddr = curaddr + 1
	memdata = 0
	instype = opcode[tokens[0]][0]
	memdata = (opcode[tokens[0]][1]) << opcodeposition
	if instype == 4:
		memdata = (int(tokens[1]) & ((2**wordsize)-1))
	elif instype == 0:
		memdata = memdata
	elif instype == 1:
		memdata = memdata + (regval(tokens[1]) << reg1position)
	elif instype == 2:
		memdata = memdata + (regval(tokens[1]) << reg1position) + (regval(tokens[2]) << reg2position)
	elif instype == 3:
		token2 = tokens[2]
		if token2.isdigit():
			memaddr = int(tokens[2])
		else:
			memaddr = sysmboltable[token2]
		memdata = memdata + (regval(tokens[1]) << reg1position) + memaddr
	mem[curaddr] = memdata
	curaddr = curaddr + 1
outfile = open("a.out",'w')
outfile.write('go' + '%d' % startexecptr)
outfile.write("\n")
for i  in range(memloadsize):
	outfile.write(hex(mem[i]) + "    " + '%d'%i)
	outfile.write("\n")
outfile.close()