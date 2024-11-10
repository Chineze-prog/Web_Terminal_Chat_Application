import os
import os.path

textFiles = ['.html', '.py', '.js', '.txt']


def isAFileICanPrint(filename):
    for suffix in textFiles:
        if filename.endswith(suffix):
            return True
    return False


def getFileContent(filename):
  # make the path to this file
  content = None
  wholePath = os.path.join(os.getcwd(), filename)
  
  if os.path.isfile(wholePath) and isAFileICanPrint(filename):
    with open(wholePath, 'r') as theFile:
        content = theFile.read()
  elif os.path.isfile(wholePath):
    print(wholePath)
    with open(wholePath, 'rb') as binaryFile: 
      content = binaryFile.read()

  return content