# E2log2SC
### Convert ElarmS E2 module stdout log to SeisComP3 event xml.
Created by Ran Novitsky Nof (http://ran.rnof.info), 2015 @ BSL
#### DEPENDENCIES:
Python modules:
* argparse
* sys
* os
* re
* seiscomp3 (IO,DataModel,Core)

#### USAGE:
<pre>
E2log2SC.py [-h] [-o OutXML] [-i InXML [InXML ...]]

optional arguments:
  -h, --help            show this help message and exit
  -o OutXML             Output xml file (Seiscomp3), Use - for stdout
  -i InXML [InXML ...]  input E2 log file(s) (ElarmS).
</pre>

Seiscomp3 xml can be fed to Seicomp3 database using scdb.  
_Examples:_
```
   E2log2SC.py -i events_20150214.log -o SCXML  
   scdb -i SCXML -d mysql://sysop:sysop@localhost/seiscomp3
``` 
or:
```
   cat [ELARMSXMLFILE] | E2log2SC.py | scdb -i - -d mysql://sysop:sysop@localhost/seiscomp3  
``` 
or:
```
   E2log2SC.py -i events_*.log | scdb -i - -d mysql://sysop:sysop@localhost/seiscomp3  
```

#### LICENSE:
```
Copyright (C) by Ran Novitsky Nof                                            
                                                                              
E2log2SC.py is free software: you can redistribute it and/or modify              
it under the terms of the GNU Lesser General Public License as published by  
the Free Software Foundation, either version 3 of the License, or            
(at your option) any later version.                                          
                                                                                 
This program is distributed in the hope that it will be useful,              
but WITHOUT ANY WARRANTY; without even the implied warranty of               
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                
GNU Lesser General Public License for more details.                          

You should have received a copy of the GNU Lesser General Public License     
along with this program.  If not, see <http://www.gnu.org/licenses/>. 
```
=======
>>>>>>> d26cd1951ebb408ec4c25a887014e3a16fa8dc40
