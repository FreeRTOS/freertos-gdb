# These commands must only be used after pxCurrentTCB is initialized.

import enum
import gdb

from tabulate import tabulate

#Python representation of List_t in FreeRTOS.
class FreeRTOSList():
    def __init__(self, list_, cast_type_str):
        self.uxNumberOfItems = list_['uxNumberOfItems']
        self.pxIndex = list_['pxIndex']
        self.end_marker = list_['xListEnd']

        self.head = self.end_marker['pxNext']  # ptr to start item
        self.cast_type = gdb.lookup_type(cast_type_str).pointer() # type of elements in list

    def __iter__(self):
        curr_node = self.head
        while self.uxNumberOfItems > 0 and curr_node != self.end_marker.address:
            tmp_node = curr_node.dereference()
            data = tmp_node['pvOwner'].cast(self.cast_type)
            yield data
            curr_node = tmp_node['pxNext']

#All FreeRTOS task lists to display tasks from. Does not include any currently running tasks.
class TaskLists(enum.Enum):
  READY = ('pxReadyTasksLists', 'R') #Ready
  SUSPENDED = ('xSuspendedTaskList', 'S') #Suspended
  DELAYED_1 = ('xDelayedTaskList1', 'B') #Blocked
  DELAYED_2 = ('xDelayedTaskList2', 'B') #Blocked
  WAIT_TERM = ('xTasksWaitingTermination', 'D') #Deleted (awaiting cleanup)

  def __init__(self, symbol, state):
    self.symbol = symbol
    self.state = state

#The variables of the TCB_t to display.
#Refer to FreeRTOS' task.c file for documentation
class TaskVariables(enum.Enum):
  PRIORITY = ('uxPriority', 'get_int_var', '')
  STACK = ('pxStack', 'get_hex_var', '')
  NAME = ('pcTaskName', 'get_string_var', '')
  STACK_END = ('pxEndOfStack', 'get_hex_var', 'configRECORD_STACK_HIGH_ADDRESS')
  CRITICAL_NESTING = ('uxCriticalNesting', 'get_int_var', 'portCRITICAL_NESTING_IN_TCB')
  TCB_NUM = ('uxTCBNumber', 'get_int_var', 'configUSE_TRACE_FACILITY')
  MUTEXES = ('uxMutexesHeld', 'get_int_var', 'configUSE_MUTEXES')
  RUN_TIME = ('ulRunTimeCounter', 'get_int_var', 'configGENERATE_RUN_TIME_STATS')

  def __init__(self, symbol, get_var_fn, config_check):
    self.symbol = symbol
    self.get_var_fn = getattr(self, get_var_fn)
    self.config_check = config_check

  def is_valid(self):
    return (self.config_check == '' or gdb.parse_and_eval(self.config_check))

  def get_int_var(self, tcb):
    return int(tcb[self.symbol])

  def get_hex_var(self, tcb):
    return hex(int(tcb[self.symbol]))

  def get_string_var(self, tcb):
    return tcb[self.symbol].string()

def get_current_tcbs():
  current_tcb_arr = []
  
  current_tcb = gdb.parse_and_eval('pxCurrentTCB')

  if current_tcb.type.code == gdb.TYPE_CODE_ARRAY:
    r = current_tcb.type.range()
    for i in range(r[0], r[1] + 1):
      current_tcb_arr.append(current_tcb[i])
  else:
    current_tcb_arr.append(current_tcb)
  
  return current_tcb_arr

#Takes a task list List_t as a gdb.Value. Returns an array of arrays, each subarray has the contents of the TCB
def tasklist_to_rows(tasklist, state, current_tcbs):
  rows = []
  pythonic_list = FreeRTOSList(tasklist, 'TCB_t')

  for task_ptr in pythonic_list:
    if task_ptr == 0:
      print("Task pointer is NULL. Stack corruption?")
    
    row = []
    task_tcb = task_ptr.referenced_value()
    
    row.append(str(task_ptr))
    row.append(state)
    if task_ptr in current_tcbs:
      row.append(current_tcbs.index(task_ptr))
    else:
      row.append('')
    for tcb_var in TaskVariables:
      if tcb_var.is_valid():
        row.append(tcb_var.get_var_fn(task_tcb))

    rows.append(row)

  return rows

def get_header():
  headers = ["ID", "STATE", "CPU"]

  for taskvar in TaskVariables:
    if taskvar.is_valid():
      headers.append(taskvar.name)

  return headers

#table is given as an array of rows. Each row is an array of elements.
def print_table(table):
  print (tabulate(table, headers=get_header()))

class FreeRTOS(gdb.Command):
    def __init__(self):
        #TODO: choose a gdb.COMMAND_ class for these commands?
        super(FreeRTOS, self).__init__('freertos', gdb.COMMAND_NONE, gdb.COMPLETE_NONE, True)

class FreeRTOSTaskInfo(gdb.Command):
  """Shows FreeRTOS tasks"""
  
  def __init__ (self):
    super (FreeRTOSTaskInfo, self).__init__ ("freertos tasks", gdb.COMMAND_NONE)

  def invoke (self, arg, from_tty):
    table = []
    current_tcbs = get_current_tcbs()

    for tasklist in TaskLists:
      tasklist_val = gdb.parse_and_eval(tasklist.symbol)

      if tasklist_val.type.code == gdb.TYPE_CODE_ARRAY:
        #only used for pxReadyTaskLists, because it has a list for every priority.
        r = tasklist_val.type.range()
        for i in range(r[0], r[1] + 1):
          table.extend(tasklist_to_rows(tasklist_val[i], tasklist.state, current_tcbs))
      else:
        table.extend(tasklist_to_rows(tasklist_val, tasklist.state, current_tcbs))

    if len(table) == 0:
      print ("There are currently no tasks. The program may not have created any tasks yet.")
      return

    print_table(table)

FreeRTOS()
FreeRTOSTaskInfo()
