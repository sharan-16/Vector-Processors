from queue import Queue
from collections import Counter
class Instr():
    def __init__(self):
        self.instr_type =  None # scalar/vector comp or memory op
        self.exe_time = [0]*4
        self.regs_used = []*4

class arch_state():
    def __init__(self, a, b, c):
        #all parameters from config file
        self.data_queue_depth = a
        self.comp_queue_depth = b
        self.num_lanes = c
        

        #busy boards
        self.sreg_flags = [0]*8
        self.vreg_flags = [0]*8
        self.busy_board = []
        self.busy_lanes = [0]*self.num_lanes

        #arch state
        self.WB = Instr()
        self.vcomp_exe = [Instr()]*self.num_lanes
        self.vls_exe = Instr()
        self.scalar_exe = Instr()
        self.decode = Instr()
        self.fetch = Instr()

        self.vls_queue = Queue(maxsize=self.data_queue_depth)
        self.vcomp_queue = Queue(maxsize=self.comp_queue_depth)
        self.scalar_queue = Queue(maxsize=1)

        #pipline flags
        self.pipeline_busy = 0
        self.mem_busy = 0

    def shift(self, instr):


        #WB stage --> udating the busy board, busy lanes and 
        #clear the busy board --> empty list
        for i in range(0,self.num_lanes):
            if self.vcomp_exe[i].exe_time[2] == 0:
                self.busy_lanes[i] = 0
            else:
                self.busy_lanes = 1
                self.busy_board = list(set().union(set(self.vcomp_exe[i].regs), set(self.busy_board)))
        
        if self.vls_exe[i].exe_time == 0:
                pass # do nothing the exe comlted instr is overwritten by a new one
        else:
            self.busy_board = list(set().union(set(self.vls_exe[i].regs), set(self.busy_board)))

        if self.scalar_exe[i].exe_time == 0:
                pass
        else:
            self.busy_board = list(set().union(set(self.scalar_exe[i].regs), set(self.busy_board)))


        #execution stage
        for i in range(0,self.num_lanes):
            if self.busy_lanes[i] == 0 and not(self.vcomp_queue.empty()):
                if not(self.vcomp_queue.queue[0].regs_used in self.busy_board):
                    self.vcomp_exe[i] = self.vcomp_queue.get()
        if self.vls_exe.exe_time[2] == 0 and not(self.vls_queue.empty()):
            if not(self.vls_queue.queue[0].regs_used in self.busy_board):
                self.vls_exe = self.vls_queue.get()
        if self.scalar_exe.exe_time[2] == 0 and not(self.scalar_queue.empty()):
            self.scalar_exe = self.scalar_queue.get()

        #shifting into queues
        if self.vls_queue.empty() and (Vmips.decode.instr_type == 'v_ls'):
            self.vls_queue.put(Vmips.decode)
            self.pipeline_busy = 0
        elif self.vcomp_queue.empty() and Vmips.decode.instr_type == 'v_comp':
            self.vcomp_queue.put(Vmips.decode)
            self.pipeline_busy = 0
        elif self.scalar_queue.empty() and Vmips.decode.instr_type == 'scalar':
            self.scalar_queue.put(Vmips.decode)
            self.pipeline_busy = 0
        else:
            self.pipeline_busy = 1

        #decode stage
        if self.fetch.exe_time[0] == 0 and not(self.pipeline_busy):
            self.decode = self.fetch
        if self.decode.instr_type == 'HALT':
            global Halt_condition
            Halt_condition = 1

        #fetch stage
        if not(self.pipeline_busy):
            self.fetch = instr

    def execute_one_cycle(self):
        #execution stage
        for i in range(0,self.num_lanes):
            self.vcomp_exe[i].exe_time[2] = self.vcomp_exe[i].exe_time[2] - 1 if self.vcomp_exe[i].exe_time[2] - 1 > 0 else 0
        self.vls_exe[i].exe_time[2] = self.vls_exe[i].exe_time[2] - 1 if self.vls_exe[i].exe_time[2] - 1 > 0 else 0


mul_pipe_depth = 1
add_pipe_depth = 1
div_pipe_depth = 1
num_banks = 1
vls_pipe_depth = 1
program_counter = 0
Halt_condition = 0
sreg = ['SR0', 'SR1', 'SR2', 'SR3', 'SR4', 'SR5', 'SR6', 'SR7']
vreg = ['VR0', 'VR1', 'VR2', 'VR3', 'VR4', 'VR5', 'VR6', 'VR7']


def decode(instr=str):
    instr = instr.split('')

    if 'VV' or 'VS' in instr[0]:
        a = Instr()
        a.instr_type = 'v_comp'
        a.exe_time[0] = 1 #fetch
        a.exe_time[1] = 1 #decode
        a.exe_time[3] = 1 #WB

        if 'ADD' or 'SUB' in instr[0]:
            a.exe_time[2] = add_pipe_depth
        elif 'MUL' in instr[0]:
            a.exe_time[2] = mul_pipe_depth
        elif 'DIV' in instr[0]:
            a.exe_time[2] = div_pipe_depth
        else:
            a.exe_time[2] = 1
        a.regs_used = instr[1:] # registers used
    elif 'LV' or 'SV' in instr[0]:
        a = Instr()
        a.instr_type = 'v_ls'
        a.exe_time = [1,1,vls_time(list(eval(instr[-1][1:-1],1)))]
        a.regs_used = instr[1:-1] # registers used
    elif 'B' in instr[0]:
        a = Instr()
        a.instr_type = 'scalar'
        a.exe_time = [1,1,1,1]
        global program_counter
        program_counter = int(instr[-1][1:-1])
    elif "HALT" == instr[0]:
        a = Instr()
        a.instr_type = 'HALT'
    else:
        a = Instr()
        a.instr_type = 'scalar'
        a.exe_time = [1,1,1,1]
        a.regs_used = instr[1:] # registers used
    return a

def vls_time(q):
    temp = [a%num_banks for a in q]
    temp = Counter(temp).values()
    return vls_pipe_depth + (max(list) - 1)


Vmips = arch_state(4,4,4)
instr = 'None' #read from the file

Vmips.fetch = decode(instr)

#decode it

while (True):

    #fetch stage
    # should break if halt condition is observed and 
   

    if (Halt_condition == 1 and Vmips.busy_lanes == [0]* Vmips.num_lanes and Vmips.vls_exe.exe_time == 0 and Vmips.scalar_exe.exe_time == 0 
        and Vmips.vcomp_queue.empty() and Vmips.vls_queue.empty() and Vmips.scalar_queue.empty()):
        break
    else:
        instr = 'None' #read from the file
        Vmips.shift(instr)
        Vmips.execute_one_cycle()
