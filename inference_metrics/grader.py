
import sys
v = sys.version[:3]

assert(v in ('3.5', '3.6', '3.7')), "Python version 3.5 or 3.6 or 3.7 is required to run this grader!"

if v == '3.5':
    from graders.grader35 import *
elif v == '3.6':
    from graders.grader36 import *
else: 
    from graders.grader37 import *
    
print("Using grader version: {}".format(version))
