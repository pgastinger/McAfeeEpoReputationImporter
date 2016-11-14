# McAfeeEpoReputationImporter

*Import File Reputations for all files from a specified directory (simple tkinter gui)*

This is a rather simple Python 3.5-tkinter-interface for reading all the files from a chosen directory, calculating MD5/SHA1-hashes for every file and sending them to the McAfee EPO server with a specified reputation value. Its main purpose is to whitelist all the files to build a golden image (for client/server installations). 

## Credits
For building this interface, I used a couple of documentations as influence:
  * Sample script: https://community.mcafee.com/message/406190#406190
  * Another sample: https://community.mcafee.com/message/368038#368038
  * Explanation of ePO Web API and where to find Web API documentation: https://kc.mcafee.com/corporate/index?page=content&id=KB81322
  * ePolicy Orchestrator 5.1.0 Web API Scripting Reference Guide: https://kc.mcafee.com/corporate/index?page=content&id=PD24810
  * Alternative, non-standard library: https://pypi.python.org/pypi/mcafee-epo/1.0.1
  
## Run the Python script
It is a simple as this command:
```
C:\py352\python.exe eporeputations.py
```

There are a couple of default parameters/configurations options, which can be modified in epo.cfg:
```
[DEFAULT]
# available languages: de, en
default_language = en

[EPO]
username = webapi
password = 
url = 
requests_timeout = 5
hashes_per_request = 10
default_reputation = 99
```

** I highly recommend using the latest Python 3.x version with a virtual environment. Just download the latest Python 3.x version from https://www.python.org/downloads/ (or use a portable version), create a virtual environment and install all the dependencies using pip **

### Brief explanations
Instead of the original library (issued by McAfee) I chose an alternative library, which has full Python 3 compatibility,  uses requests as module and can be easily installed with pip (https://pypi.python.org/pypi/mcafee-epo/1.0.1).

  1. Open directory
  2. Change default values, add missing values
  3. Send file hashes to EPO server
  4. Download hashes as CSV file

### Screenshots
This is the main GUI:

![gui](https://cloud.githubusercontent.com/assets/3997488/20257671/669da942-aa4b-11e6-9c37-7f307ebd1189.png)

## Create a Windows executable with PyInstaller
Usually, standard Windows clients and servers do not have a Python 3 installation. To be able to use this program without installation Python 3 (with dependencies), I modified the source to be used with PyInstaller to create a standard Windows executable file. I added a .spec-file, which packs everything necessary into one .exe-file. 
```
C:\py352\Scripts\pyinstaller eporeputations.spec
759 INFO: PyInstaller: 3.2
760 INFO: Python: 3.5.2
761 INFO: Platform: Windows-7-6.1.7601-SP1
765 INFO: UPX is not available.
787 INFO: Extending PYTHONPATH with paths
788 INFO: checking Analysis
789 INFO: Building Analysis because out00-Analysis.toc is non existent
789 INFO: Initializing module dependency graph...
801 INFO: Initializing module graph hooks...
810 INFO: Analyzing base_library.zip ...
5206 INFO: running Analysis out00-Analysis.toc
...
22033 INFO: Writing RT_ICON 1 resource with 1128 bytes
22033 INFO: Writing RT_ICON 2 resource with 4264 bytes
22033 INFO: Writing RT_ICON 3 resource with 9640 bytes
22034 INFO: Writing RT_ICON 4 resource with 67624 bytes
22126 INFO: Appending archive to EXE dist\eporeputations.exe
```
After clicking on this .exe-file, everything will be extracted to a temporary directory and executed without dependencies.

