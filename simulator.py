import os
import argparse

class IMEM(object):
    def __init__(self, iodir):
        self.size = pow(2, 16) # Can hold a maximum of 2^16 instructions.
        self.filepath = os.path.abspath(os.path.join(iodir, "Code.asm"))
        self.instructions = []

        try:
            with open(self.filepath, 'r') as insf:
                self.instructions = [ins.strip() for ins in insf.readlines()]
            print("IMEM - Instructions loaded from file:", self.filepath)
            # print("IMEM - Instructions:", self.instructions)
        except:
            print("IMEM - ERROR: Couldn't open file in path:", self.filepath)

    def Read(self, idx): # Use this to read from IMEM.
        if idx < self.size:
            return self.instructions[idx]
        else:
            print("IMEM - ERROR: Invalid memory access at index: ", idx, " with memory size: ", self.size)

class DMEM(object):
    # Word addressible - each address contains 32 bits.
    def __init__(self, name, iodir, addressLen):
        self.name = name
        self.size = pow(2, addressLen)
        self.min_value  = -pow(2, 31)
        self.max_value  = pow(2, 31) - 1
        self.ipfilepath = os.path.abspath(os.path.join(iodir, name + ".txt"))
        self.opfilepath = os.path.abspath(os.path.join(iodir, name + "OP.txt"))
        self.data = []

        try:
            with open(self.ipfilepath, 'r') as ipf:
                self.data = [int(line.strip()) for line in ipf.readlines()]
            print(self.name, "- Data loaded from file:", self.ipfilepath)
            # print(self.name, "- Data:", self.data)
            self.data.extend([0x0 for i in range(self.size - len(self.data))])
        except:
            print(self.name, "- ERROR: Couldn't open input file in path:", self.ipfilepath)

    def Read(self, idx): # Use this to read from DMEM.
        pass # Replace this line with your code here.

    def Write(self, idx, val): # Use this to write into DMEM.
        pass # Replace this line with your code here.

    def dump(self):
        try:
            with open(self.opfilepath, 'w') as opf:
                lines = [str(data) + '\n' for data in self.data]
                opf.writelines(lines)
            print(self.name, "- Dumped data into output file in path:", self.opfilepath)
        except:
            print(self.name, "- ERROR: Couldn't open output file in path:", self.opfilepath)

class RegisterFile(object):
    def __init__(self, name, count, length = 1, size = 32):
        self.name       = name
        self.reg_count  = count
        self.vec_length = length # Number of 32 bit words in a register.
        self.reg_bits   = size
        self.min_value  = -pow(2, self.reg_bits-1)
        self.max_value  = pow(2, self.reg_bits-1) - 1
        self.registers  = [[0x0 for e in range(self.vec_length)] for r in range(self.reg_count)] # list of lists of integers

    def Read(self, idx):
        pass # Replace this line with your code.

    def Write(self, idx, val):
        pass # Replace this line with your code.

    def dump(self, iodir):
        opfilepath = os.path.abspath(os.path.join(iodir, self.name + ".txt"))
        try:
            with open(opfilepath, 'w') as opf:
                row_format = "{:<13}"*self.vec_length
                lines = [row_format.format(*[str(i) for i in range(self.vec_length)]) + "\n", '-'*(self.vec_length*13) + "\n"]
                lines += [row_format.format(*[str(val) for val in data]) + "\n" for data in self.registers]
                opf.writelines(lines)
            print(self.name, "- Dumped data into output file in path:", opfilepath)
        except:
            print(self.name, "- ERROR: Couldn't open output file in path:", opfilepath)

class Core():
    def __init__(self, imem, sdmem, vdmem):
        self.IMEM = imem
        self.SDMEM = sdmem
        self.VDMEM = vdmem

        self.PC = 0
        self.branch = False
        self.maskreg = [False]*64
        self.VLR = 0 #vector length register

        #self.LS_flag = False
        self.RegW = False

        self.RFs = {"SRF": RegisterFile("SRF", 8),
                    "VRF": RegisterFile("VRF", 8, 64)}
        
        # Your code here.
        
    def decode(self, instr):
        format = ["op",'r1','r2','r3']
        instr = instr.split()
        parsed_instr = dict(zip(format,instr))
        return parsed_instr
    
    def read_RF(self,idx):
        if 'VR' in idx:
            return self.RFs['VRF'].Read(idx.replace('VR',''))
        elif 'SR' in idx:
            return self.RFs['SRF'].Read(idx.replace('SR',''))
        else: return int(idx)  #for immediate values

    def write_RF(self,idx):
        if 'VR' in idx:
            self.RFs['VRF'].Write(idx.replace('VR',''))
        elif 'SR' in idx:
            self.RFs['SRF'].Write(idx.replace('SR',''))
        
    def execute_V(self,operand1, operand2, opcode):
        result=[0]*self.VLR
        if (opcode == 'ADDVV'): 
            self.RegW = True
            for i in range(self.VLR):
                result[i]=((operand1[i]+operand2[i])*self.maskreg[i])
        elif (opcode == 'ADDVS'):  
            self.RegW = True
            for i in range(self.VLR):
               result[i]=((operand1[i]+operand2)*self.maskreg[i])
        elif (opcode == 'SUBVV'):  
            self.RegW = True
            for i in range(self.VLR):
                result[i]=((operand1[i]-operand2[i])*self.maskreg[i])
        elif (opcode == 'SUBVS'):  
            self.RegW = True
            for i in range(self.VLR):
               result[i]=((operand1[i]-operand2)*self.maskreg[i])
        elif (opcode == 'MULVV'):  
            self.RegW = True
            for i in range(self.VLR):
               result[i]=((operand1[i]*operand2[i])*self.maskreg[i])
        elif (opcode == 'MULVS'):  
            self.RegW = True
            for i in range(self.VLR):
               result[i]=((operand1[i]*operand2)*self.maskreg[i])
        elif (opcode == 'DIVVV'):  
            self.RegW = True
            for i in range(self.VLR):
               result[i]=((operand1[i]/operand2[i])*self.maskreg[i])
        elif (opcode == 'MULVS'): 
            self.RegW = True 
            for i in range(self.VLR):
               result[i]=((operand1[i]/operand2)*self.maskreg[i])
        elif ('S' in opcode and 'VV' in opcode): 
            self.mask_reg_opVV(opcode,operand1,operand2)
            return None
        elif ('S' in opcode and 'VS' in opcode):  # need to change
            self.mask_reg_opVS(opcode,operand1,operand2)
            return None
        elif (opcode == 'LV'):  
            self.RegW = True
            for i in range(self.VLR):
                result[i]=(self.VDMEM.Read(operand1+i))*self.maskreg[i]
        elif (opcode == 'SV'):
            for i in range(self.VLR):
                self.VDMEM.Write((operand1+i)*self.maskreg[i])
            return None
        elif (opcode == 'LVWS'):  
            self.RegW = True
            for i in range(self.VLR):
                result[i]=((self.VDMEM.Read(operand1+i*operand2))*self.maskreg[i])
        elif (opcode == 'SVWS'):
            for i in range(self.VLR):
                self.VDMEM.Write((operand1+i*operand2)*self.maskreg[i])
            return None
        elif (opcode == 'LVI'):  
            self.RegW = True
            for i in range(self.VLR):
                result[i]=(self.VDMEM.Read(operand1+operand2[i])*self.maskreg[i])
        elif (opcode == 'SVI'):
            for i in range(self.VLR):
                self.VDMEM.Write((operand1+operand2[i])*self.maskreg[i])
                return None
        return result
    
    def mask_reg_opVV(self, condition, operand1, operand2):
        if(condition == 'SEQVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]==operand2[i])
        elif(condition == 'SNEVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]!=operand2[i])
        elif(condition == 'SGTVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]>operand2[i])
        elif(condition == 'SLTVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]<operand2[i])
        elif(condition == 'SGEVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]>=operand2[i])
        elif(condition == 'SLEVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]<=operand2[i])

    def mask_reg_opVS(self, condition, operand1, operand2):
        if(condition == 'SEQVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]==operand2)
        elif(condition == 'SNEVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]!=operand2)
        elif(condition == 'SGTVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]>operand2)
        elif(condition == 'SLTVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]<operand2)
        elif(condition == 'SGEVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]>=operand2)
        elif(condition == 'SLEVV'):
            for i in range(self.VLR):
                self.maskreg[i] = (operand1[i]<=operand2)

        
    def execute_S(self,operand1,operand2, opcode):
        
        if (opcode == 'CVM'): 
            self.maskreg = [True]*64
            return None
        elif (opcode == 'POP'): 
            return sum(self.maskreg)
        elif (opcode == 'MTCL'): 
            self.VLR = operand1
            return None
        elif (opcode == 'MFCL'): 
            return self.VLR 
        elif (opcode == 'LS'):
            return self.SDMEM.Read(operand1+operand2)
        elif (opcode == 'SS'):
            self.SDMEM.Write(operand1+operand2)
            return None
        elif (opcode == 'ADD'):
            self.RegW = True
            return operand1 + operand2
        elif (opcode == 'SUB'):  
            self.RegW = True
            return operand1 + operand2
        elif (opcode == 'AND'):  
            self.RegW = True
            return operand1 & operand2
        elif (opcode == 'OR'):  
            self.RegW = True
            return operand1 | operand2
        elif (opcode == 'XOR'):  
            self.RegW = True
            return operand1 ^ operand2
        elif (opcode == 'SLL'):  
            self.RegW = True
            return operand1 << operand2
        elif (opcode == 'SLR'):  
            self.RegW = True
            return operand1 >> operand2
        elif (opcode == 'SRA'):  
            self.RegW = True
            pass
        
    def branch(self, condition, operand1, operand2, operand3):
        if(condition == 'BEQ'):
            return(self.PC + operand3 if (operand1 == operand2) else self.PC + 1)
        elif(condition == 'BNE'):
            return(self.PC + operand3 if (operand1 != operand2) else self.PC + 1)
        elif(condition == 'BGT'):
            return(self.PC + operand3 if (operand1 > operand2) else self.PC + 1)
        elif(condition == 'BLT'):
            return(self.PC + operand3 if (operand1 < operand2) else self.PC + 1)
        elif(condition == 'BGE'):
            return(self.PC + operand2 if (operand1 >= operand2) else self.PC + 1)
        elif(condition == 'BLE'):
            return(self.PC + operand2 if (operand1 <= operand2) else self.PC + 1)

    def run(self):
        while(True):

            #instruction fetch and decode
            instr = self.decode(self.IMEM.read(self.PC))
            opcode = instr['op']

            if (opcode.startswith('B')):
                next_PC = self.branch(opcode,self.read_RF(instr['r1']),self.read_RF(instr['r2']).self.read_RF(instr['r3']))
                #next_PC = self.PC + self.read_RF(instr['r3']) if (self.read_RF(instr['r1']) > instr.read_RF(instr['r2'])) else self.PC + 1
                #continue
            elif(opcode == 'HALT') : break
            else:
                #reading the values
                operand1 = self.read_RF(instr['r2'])
                operand2 = self.read_RF(instr['r3'])
                
                if ('V' in opcode): 
                    result = []
                    result = self.execute_V(operand1,operand2,opcode)
                else:
                    result = 0
                    result = self.execute_V(operand1,operand2,opcode)

                next_PC = self.PC + 1

            #write to the register files and clear the flag
            if(result != None and self.RegW == True): self.write_RF(instr['r1'])
            self.RegW = False

            #increment the program counter if no exception is encountered
            self.PC = next_PC


    def dumpregs(self, iodir):
        for rf in self.RFs.values():
            rf.dump(iodir)

if __name__ == "__main__":
    #parse arguments for input file location
    parser = argparse.ArgumentParser(description='Vector Core Performance Model')
    parser.add_argument('--iodir', default="", type=str, help='Path to the folder containing the input files - instructions and data.')
    args = parser.parse_args()

    iodir = os.path.abspath(args.iodir)
    print("IO Directory:", iodir)

    # Parse IMEM
    imem = IMEM(iodir)  
    # Parse SMEM
    sdmem = DMEM("SDMEM", iodir, 13) # 32 KB is 2^15 bytes = 2^13 K 32-bit words.
    # Parse VMEM
    vdmem = DMEM("VDMEM", iodir, 17) # 512 KB is 2^19 bytes = 2^17 K 32-bit words. 

    # Create Vector Core
    vcore = Core(imem, sdmem, vdmem)

    # Run Core
    vcore.run()   
    vcore.dumpregs(iodir)

    sdmem.dump()
    vdmem.dump()

    # THE END
