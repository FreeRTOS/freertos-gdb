import gdb

class FreeRTOS(gdb.Command):
    def __init__(self):
        #TODO: choose a gdb.COMMAND_ class for these commands?
        super(FreeRTOS, self).__init__('freertos', gdb.COMMAND_NONE, gdb.COMPLETE_NONE, True)

FreeRTOS()
