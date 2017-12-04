#! python
# (c) DL, UTA, 2009 - 2016
import  sys, string, time
wordsize = 24                                        # everything is a word
numregbits = 3                                       # actually +1, msb is indirect bit
opcodesize = 5

w, h = 2, 4;                                         # 4 x 2
I_Cache = [[0 for x in range(w)] for y in range(h)]
D_Cache = [[0 for x in range(w)] for y in range(h)]

I_tag = [0 for y in range(h)]
I_valid = [0 for y in range(h)]
I_Hit = 0
I_Miss = 0
I_Com_Miss=0
I_Con_Miss=0
I_Cap_Miss=0
D_Hit = 0
D_Miss = 0
D_Com_Miss=0
D_Con_Miss=0
D_Cap_Miss=0
addrsize = wordsize - (opcodesize+numregbits+1)      # num bits in address
memloadsize = 1024                                   # change this for larger programs
numregs = 2**numregbits
regmask = (numregs*2)-1                              # including indirect bit
addmask = (2**(wordsize - addrsize)) -1
nummask = (2**(wordsize))-1
opcposition = wordsize - (opcodesize + 1)            # shift value to position opcode
reg1position = opcposition - (numregbits +1)            # first register position
reg2position = reg1position - (numregbits +1)
memaddrimmedposition = reg2position                  # mem address or immediate same place as reg2
realmemsize = memloadsize * 1                        # this is memory size, should be (much) bigger than a program
#memory management regs
codeseg = numregs - 1                                # last reg is a code segment pointer
dataseg = numregs - 2                                # next to last reg is a data segment pointer
#ints and traps
trapreglink = numregs - 3                            # store return value here
trapval     = numregs - 4                            # pass which trap/int
mem = [0] * realmemsize                              # this is memory, init to 0 
reg = [0] * numregs                                  # registers
clock = 1                                            # clock starts ticking
ic = 0                                               # instruction count
numcoderefs = 0                                      # number of times instructions read
numdatarefs = 0                                      # number of times data read
starttime = time.time()
curtime = starttime
def startexechere ( p ):
    # start execution at this address
    reg[ codeseg ] = p    
def loadmem():                                       # get binary load image
  curaddr = 0
  for line in open("a.out", 'r').readlines():
    token = string.split( string.lower( line ))      # first token on each line is mem word, ignore rest
    if ( token[ 0 ] == 'go' ):
        startexechere(  int( token[ 1 ] ) )
    else:    
        mem[ curaddr ] = int( token[ 0 ], 0 )                
        curaddr = curaddr = curaddr + 1
def getcodemem ( a ):                               # Instruction Cache (4 x 2) 
    # get code memory at this address
    # getcodecache(memval)
    return getcodecache(a)
def getcodecache(a):    
    global I_tag, I_valid, I_Miss, I_Hit,I_Cap_Miss,I_Com_Miss,I_Con_Miss
    address = a + reg[ codeseg ]
    word =  address & 0x1
    block =  (address >> 1 ) & 0x3    
    tagval = address >> 3  
    memval = mem[ address ]

    # misses, if address is even then cold/compulsory miss
    # compulsory miss for the word 1
    if ((I_Cache[block][word] == 0) and (I_valid[block] == 0)):
      # increase the compulsory miss counter
      I_Com_Miss = I_Com_Miss + 1
    else:
      # increase the conflict miss counter      
      if((address % 2 == 0) and (I_valid[block] == 1) ):
        I_Con_Miss = I_Con_Miss + 1      

      if(I_Cache[block][word] == memval):
          I_Hit = I_Hit + 1
          return ( I_Cache[block][word] )
    I_Miss = I_Miss + 1
    I_Cache[block][word] = memval

    # check for tags on miss, if tag even, add the same and next memory location content
    
    # first case, for address 0 in memory
    if(address % 2 == 0):
      I_tag[block] = tagval
      I_valid[block] = 1
      # get the details for the next memory block
      address_even = (a + reg[ codeseg ]) + 1    
      word_even =  address_even & 0x1
      block_even =  (address_even >> 1 ) & 0x3                      
      I_Cache[block_even][word_even] = mem[ address_even ]
    
    # check for tags on miss, if tag odd, add the same and previous memory location content    
    if(address % 2 == 1):
      # get the details for the previous memory block
      address_odd = (a + reg[ codeseg ]) - 1    
      word_odd =  address_odd & 0x1
      block_odd =  (address_odd >> 1 ) & 0x3    
      tagval = address_odd >> 3
      I_tag[block_odd] = tagval
      I_valid[block_odd] = 1              
      I_Cache[block_odd_even][word_odd] = mem[ address_odd ]
    
    return (I_Cache[block][word])
def getdatamem ( a ):                               # Data Cache (4 x 2)
    # get code memory at this address
    return getdatacache( a )
def getdatacache(a):
    global D_Miss, D_Hit
    address = a + reg[ dataseg ]        
    word = address  & 0x1
    block = (  address  >> 1 ) & 0x3
    memval = mem[ address ]
    if(D_Cache[block][word] == memval):
        D_Hit = D_Hit + 1
        return ( D_Cache[block][word] )
    D_Miss = D_Miss + 1
    D_Cache[block][word] = memval
    return (D_Cache[block][word])
def getregval ( r ):
    # get reg or indirect value
    if ( (r & (1<<numregbits)) == 0 ):               # not indirect
       rval = reg[ r ] 
    else:
       rval = getdatamem( reg[ r - numregs ] )       # indirect data with mem address
    return ( rval )
def checkres( v1, v2, res):
    v1sign = ( v1 >> (wordsize - 1) ) & 1
    v2sign = ( v2 >> (wordsize - 1) ) & 1
    ressign = ( res >> (wordsize - 1) ) & 1
    if ( ( v1sign ) & ( v2sign ) & ( not ressign ) ):
      return ( 1 )
    elif ( ( not v1sign ) & ( not v2sign ) & ( ressign ) ):
      return ( 1 )
    else:
      return( 0 )
def dumpstate ( d ):
    if ( d == 1 ):
        print reg
    elif ( d == 2 ):
        print mem
    elif ( d == 3 ):
        print 'clock=', clock, 'IC=', ic, 'I_Hit=', I_Hit, 'I_Miss=', I_Miss, 'D_Hit=', 'I_Com_Miss=', I_Com_Miss,'I_Con_Miss=', I_Con_Miss,'D_Hit=',D_Hit, 'D_Miss=', D_Miss, 'Coderefs=', numcoderefs,'Datarefs=', numdatarefs, 'Run Time=', time.time()- starttime 
def trap ( t ):
    # unusual cases
    # trap 0 illegal I
    # trap 1 arithmetic overflow
    # trap 2 sys call
    # trap 3+ user
    rl = trapreglink                            # store return value here
    rv = trapval
    if ( ( t == 0 ) | ( t == 1 ) ):
       dumpstate( 1 )
       dumpstate( 2 )
       dumpstate( 3 )
    elif ( t == 2 ):                          # sys call, reg trapval has a parameter
       what = reg[ trapval ] 
       if ( what == 1 ):
           a = a        #elapsed time
    return ( -1, -1 )
    return ( rv, rl )
# opcode type (1 reg, 2 reg, reg+addr, immed), mnemonic  
opcodes = { 1: (2, 'add'), 2: ( 2, 'sub'), 
            3: (1, 'dec'), 4: ( 1, 'inc' ),
            7: (3, 'ld'),  8: (3, 'st'), 9: (3, 'ldi'),
           12: (3, 'bnz'), 13: (3, 'brl'),
           14: (1, 'ret'),
           16: (3, 'int') }
startexechere( 0 )                                  # start execution here if no "go"
loadmem()                                           # load binary executable
ip = 0                                              # start execution at codeseg location 0
# while I is not halt
while( 1 ):
   ir = getcodemem( ip )                            # - fetch
   ip = ip + 1
   opcode = ir >> opcposition                       # - decode
   reg1   = (ir >> reg1position) & regmask
   reg2   = (ir >> reg2position) & regmask
   addr   = (ir) & addmask
   ic = ic + 1
                                                    # - operand fetch
   if not (opcodes.has_key( opcode )):
      tval, treg = trap(0) 
      if (tval == -1):                              # illegal I
         break
   memdata = 0                                      #     contents of memory for loads
   if opcodes[ opcode ] [0] == 1:                   #     dec, inc, ret type
      operand1 = getregval( reg1 )                  #       fetch operands
   elif opcodes[ opcode ] [0] == 2:                 #     add, sub type
      operand1 = getregval( reg1 )                  #       fetch operands
      operand2 = getregval( reg2 )
   elif opcodes[ opcode ] [0] == 3:                 #     ld, st, br type
      operand1 = getregval( reg1 )                  #       fetch operands
      operand2 = addr                     
   elif opcodes[ opcode ] [0] == 0:                 #     ? type
      break
   if (opcode == 7):                                # get data memory for loads
      memdata = getdatamem( operand2 )
   # execute
   if opcode == 1:                     # add
      result = (operand1 + operand2) & nummask
      if ( checkres( operand1, operand2, result )):
         tval, treg = trap(1) 
         if (tval == -1):                           # overflow
            break
   elif opcode == 2:                   # sub
      result = (operand1 - operand2) & nummask
      if ( checkres( operand1, operand2, result )):
         tval, treg = trap(1) 
         if (tval == -1):                           # overflow
            break
   elif opcode == 3:                   # dec
      result = operand1 - 1
   elif opcode == 4:                   # inc
      result = operand1 + 1
   elif opcode == 7:                   # load
      result = memdata
   elif opcode == 9:                   # load immediate
      result = operand2
   elif opcode == 12:                  # conditional branch
      result = operand1
      if result <> 0:
         ip = operand2
   elif opcode == 13:                  # branch and link
      result = ip
      ip = operand2
   elif opcode == 14:                   # return
      ip = operand1
   elif opcode == 16:                   # interrupt/sys call
      result = ip
      tval, treg = trap(reg1)
      if (tval == -1):
        break
      reg1 = treg
      ip = operand2
   # write back
   if ( (opcode == 1) | (opcode == 2 ) | 
         (opcode == 3) | (opcode == 4 ) ):     # arithmetic
        reg[ reg1 ] = result
   elif ( (opcode == 7) | (opcode == 9 )):     # loads
        reg[ reg1 ] = result
   elif (opcode == 13):                        # store return address
        reg[ reg1 ] = result
   elif (opcode == 16):                        # store return address
        reg[ reg1 ] = result
   # end of Instruction loop     
# end of execution

   
