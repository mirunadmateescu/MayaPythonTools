# MayaPythonTools
Stuff made for my own use that might come in useful.


## SmartBridge_workingV001.py
Got some help with the maths behind finding the relevant groups of verts on a side so I've been finally able get a prototype out for this one. Will bridge between two sets of edges that don't match in numbers, the further away the first vertex is from the last in an edge selection the better, but will work in organic surfaces. For long distances it works better to get it done in a few smaller bits rather than bridging it all at once.
Run script, load in Side A, pick first vert, same with Side B and then Bridge. Reloading the tool doesn't always work so just running the script again before you bridge a new set might be safer. Will get out a slightly less buggy version that can pick between multiple ways of bridging the gap rather than stopping at the first one it finds when I have the time.
