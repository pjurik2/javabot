use = ['0', '1', '2', '13']
final = 660
ops = ['^', '&', '*', '-', '+', '|']

x = 0

c_use = [] + use
c_ops = [] + ops
c_eval = 0
c_done = []
c_comp = ''
c_comp_list = []
c_use_num = 0

while c_eval != final:
    
    c_eval = eval(c_comp)
    
