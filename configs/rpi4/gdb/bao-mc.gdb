############# Bao multicore
# Enable logging for bao multicore
define baoLog
set logging file bao-mc.txt
set logging enabled on
end

# create alias for connecting and switching between cores
define core0
target extended-remote :3333
info threads
end

define core1
target extended-remote :3334
info threads
end

define core2
target extended-remote :3335
info threads
end

define core3
target extended-remote :3336
info threads
end

define stepBreakpoint
set var $arg0 = $arg1
n
end

define sb1
stepBreakpoint b 0
end

define sb2
stepBreakpoint a 0
end

define myTui
tui new-layout my_lay {-horizontal src 1 asm 1} 2 regs 1 status 0 cmd 1
lay my_lay
end

##################
define baoMulticore
# overcome the SW breakpoint on each core (start with 0: default)
core0
stepBreakpoint

core1
stepBreakpoint

core2
stepBreakpoint

core3
stepBreakpoint
end
# Start recording (not available for the current architecture)
# record
