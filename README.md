# lemin 42 visualization

> __NOTE__
> this is __only__ a __visualization__ for lemin 42 project
> there is __NO__ solution for lemin 42 problem in this repo

visualization is implemented in __python 3__
using [pyside2](https://pypi.org/project/PySide2/) - Qt framework port for python - for graphics


# installing dependencies
```
$ pip install pyside2
```

# running visualization
map data and solution data can be provided to lemin_visual.py in two ways:

via standart input like:
```
$ ./lemin < [map] | python3 lemin_visual.py
```
where `./lemin < [map]` is running __your__ lemin42 resolver with map data from map file 

or as a commad line arguments like:
```
$ python3 lemin_visual.py ./maps/map42.map solution42.txt
```
with map filename being __first__ arg and solution file being __second__ arg

P.S.
actually this is __not__ my code, the code __owned by__ [Alina-](https://github.com/mapryl)
i just host it :-)