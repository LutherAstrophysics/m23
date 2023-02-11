import os


### Dry specifies if you want to actually make the changes
### or just see what the changes will be
###
def rename(folder, newNameFromOldName, dry=True):
    files = os.listdir(folder)
    for file in files:
        if dry:
            print(f"{file} -> {newNameFromOldName(file)}")
        else:
            renameFile(file, folder, newNameFromOldName)


def renameFile(fileName, folderName, renameFunction):
    newName = renameFunction(fileName)
    oldFilePath = os.path.join(folderName, fileName)
    newFilePath = os.path.join(folderName, newName)
    os.rename(oldFilePath, newFilePath)
