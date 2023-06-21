import os


def rename(folder, newNameFromOldName, dry=True):
    """
    @param folder: folder where the the files to rename live
    @param: newNameFromOldName: function that takes old file name
            and returns new filename. You must pass this function.
    @param dry: specifies if you want to actually make the changes
    """
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
