# freertos-gdb
GDB extension to display FreeRTOS tasks and set task-specific breakpoints.

## Commands
```freertos``` can be used to display supported subcommands.
```
(gdb) freertos
"freertos" must be followed by the name of a subcommand.
List of freertos subcommands:

freertos break -- Create a breakpoint that will only get tripped by the specific task.
freertos tasks -- Displays FreeRTOS tasks and information.
```

### Tasks Display
```freertos tasks``` reads through FreeRTOS task lists and displays information from the TCB of each task. The default data shown are:
* ID: The memory address of the task's TCB_t
* STATE: One of the following task statuses:
  * 'B' - Blocked
  * 'R' - Ready
  * 'D' - Deleted (waiting clean up)
  * 'S' - Suspended, or Blocked without a timeout
* CPU: The core a currently running task is running on.
* NAME: The descriptive string name assigned to the task on creation.
* STACK: The starting address of the task's stack.
* PRIORITY: The priority of the task. 0 is the lowest priority.
* STACK_END: The highest valid address for the stack. Only shown if ```configRECORD_STACK_HIGH_ADDRESS``` is enabled.
* CRITICAL_NESTING: The critical section nesting depth for ports that do not maintain their own count in the port layer. Only shown if ```portCRITICAL_NESTING_IN_TCB``` is enabled.
* TCB_NUM: The number of TCBs that have been created before and including this one. It allows debuggers to determine when a task has been deleted and then recreated. Only shown if ```configUSE_TRACE_FACILITY``` is enabled.
* MUTEXES: The number of FreeRTOS mutexes held by the task. Only shown if ```configUSE_MUTEXES``` is enabled.
* RUN_TIME: The amount of time the task has spent in the Running state. Only shown if ```configGENERATE_RUN_TIME_STATS``` is enabled.
```
(gdb) freertos tasks 
ID                            STATE    CPU    NAME     STACK         MUTEXES    PRIORITY
----------------------------  -------  -----  -------  ----------  ---------  ----------
0x2000f5bc <xIdleTaskTCB.3>   R        0      IDLE     0x2000f618          0           0
0x20000758 <ucHeap+884>       B               TX       0x20000608          0           1
0x2000f758 <xTimerTaskTCB.1>  B               Tmr Svc  0x2000f7b4          0           5
0x200005a0 <ucHeap+444>       S               Rx       0x20000450          0           2
```

### Breakpoints
```freertos break [task_name] [target_location]``` sets a special breakpoint at ```[target_location]``` that will only get stopped if ```[task_name]``` is the currently running task. The breakpoint can then be interacted with using GDB's builtin breakpoint commands for actions such as deleting, enable/disabling, etc.

```[task_name]``` should be the descriptive string name of the task, equivalent to the TCB's ```pcTaskName```.

```[target_location``` should be a location in a format recognized by the GDB's builtin break command.

This command may have undefined behavior in multiprocess environments.
```
(gdb) freertos break Rx xQueueReceive
Breakpoint 1 at 0x1bf8: file ./../../../..//Source/queue.c, line 1382.
```

## References
[Espressif's FreeRTOS GDB Extension](https://github.com/espressif/freertos-gdb)
