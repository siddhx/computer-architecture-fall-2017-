#! python

import sys, string, time
wordsize 		= 24
numregbits 		= 3
opcodesize		= 5
addrsize		= wordsize - (opcodesize + numregbits + 1)
memloadsize 	= 1024
numregs 		= 2**numregbits
