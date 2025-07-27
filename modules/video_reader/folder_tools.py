import os, glob
from natsort import natsorted

folder_tools = None
class Folder_Tools:    
    def list_files(self, folder, file_extension="mp4", sort_by="name"):
        # Create the search pattern for files with the given extension
        search_pattern = os.path.join(folder, f"*.{file_extension}")
        
        # Get the list of files
        filepaths = glob.glob(search_pattern)
        
        # Sort the files based on the specified method
        if sort_by == 'name':
            filepaths = natsorted(filepaths)
        elif sort_by == 'date':
            filepaths.sort(key=os.path.getmtime)
        else:
            raise ValueError("sort_by must be 'name' or 'date'")
        
        # Get filenames without extension
        filenames = [os.path.splitext(os.path.basename(file))[0] for file in filepaths]
        
        return (filepaths, filenames)

folder_tools =Folder_Tools()