# These commands must only be used after pxCurrentTCB is initialized.

import enum
import gdb

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
        while curr_node != self.end_marker.address:
            tmp_node = curr_node.dereference()
            data = tmp_node['pvOwner'].cast(self.cast_type)
            yield data
            curr_node = tmp_node['pxNext']

#All FreeRTOS task lists to display tasks from. Does not include any currently running tasks.
class TaskLists(enum.Enum):
  READY = 'pxReadyTasksLists' #Ready
  #TODO: not supposed to be accesssed unless in critical section?
  #This list is not shown in vTaskList, so we might not want to show it here either?
  #PEND_READ = 'xPendingReadyList' 
  SUSPENDED = 'xSuspendedTaskList' #Suspended
  DELAYED_1 = 'xDelayedTaskList1' #Blocked
  DELAYED_2 = 'xDelayedTaskList2' #Blocked
  WAIT_TERM = 'xTasksWaitingTermination' #Deleted

  def __init__(self, symbol):
    self.symbol = symbol

#The variables of the TCB_t to display.
class TaskVariables(enum.Enum):
  PRIORITY = ('uxPriority', 'get_int_var')
  STACK = ('pxStack', 'get_int_var') #get hex var
  NAME = ('pcTaskName', 'get_string_var')
  #MUTEXES = ('uxMutexesHeld', 'get_int_var')

  def __init__(self, var_name, get_var_fn):
    self.var_name = var_name
    self.get_var_fn = getattr(self, get_var_fn)

  def get_string_var(self, tcb):
    return tcb[self.var_name].string()

  def get_int_var(self, tcb):
    return int(tcb[self.var_name])

#TODO: consider multiple current tasks, could this happen in a multiprocessor?
def get_current_tcb():
  current_tcb = gdb.parse_and_eval('pxCurrentTCB')
  return current_tcb

#Takes a task list List_t as a gdb.Value. Returns an array of arrays, each subarray has the contents of the TCB
def tasklist_to_rows(tasklist):
  rows = []
  freertos_list = FreeRTOSList(tasklist, 'TCB_t')

  for task_ptr in freertos_list:
    if task_ptr == 0:
      print("Task pointer is NULL. Stack corruption?")
    
    row = []
    task_tcb = task_ptr.referenced_value()
    
    for tcb_var in TaskVariables:
      row.append(tcb_var.get_var_fn(task_tcb))

    rows.append(row)

  return rows

class FreeRTOS(gdb.Command):
    def __init__(self):
        #TODO: choose a gdb.COMMAND_ class for these commands?
        super(FreeRTOS, self).__init__('freertos', gdb.COMMAND_NONE, gdb.COMPLETE_NONE, True)

class FreeRTOSTaskInfo(gdb.Command):
  """Shows FreeRTOS tasks"""
  
  def __init__ (self):
    super (FreeRTOSTaskInfo, self).__init__ ("freertos tasks", gdb.COMMAND_NONE)

  def invoke (self, arg, from_tty):
    if gdb.parse_and_eval('uxCurrentNumberOfTasks') == 0:
      print ("There are currently no tasks. The program may not have created any tasks.")
      return

    table = []

    for tasklist_type in TaskLists:
      tasklist_val = gdb.parse_and_eval(tasklist_type.symbol)

      if tasklist_val.type.code == gdb.TYPE_CODE_ARRAY:
        #only used for pxReadyTaskLists, because it has a list for every priority.
        r = tasklist_val.type.range()
        for i in range(r[0], r[1] + 1):
          rows = tasklist_to_rows(tasklist_val[i])
          table.append(rows)
      else:
        rows = tasklist_to_rows(tasklist_val)
        table.append(rows)

    if len(table) == 0:
      return

    #TODO: some fancier printing function
    print(table)

FreeRTOS()
FreeRTOSTaskInfo()
