##### Helper Functions #####

import os
from io import BytesIO
import win32clipboard
from PIL import Image
import subprocess

def fname_generator(directory:str,proposed_filebase:str,file_ending:str):
    """
    Generates a new filename based on the proposed_filebase and file_ending.
    If the suggested filename already exists, it will add '_'+str(i) to the filebase (e.g. myfile_1.dat)

    "filename_out = fname_generator(self,directory,proposed_filebase,file_ending)"

    Inputs:
        directory: the directory where the file will be saved
        suggested_filebase: the filename that the user wants to use (without file_ending and '.') (e.g. 'myfile')
        file_ending: the file_ending of the file without '.' (e.g. 'dat')

    Outputs:
        new_filename: the new filename that will be used
    
    """
    files_in_dir = os.listdir(directory)
    proposed_filename = proposed_filebase +'.'+ file_ending
    if proposed_filename in files_in_dir:

        filename_base = proposed_filename.split('.')[-2]
        filename_ending = proposed_filename.split('.')[-1]

        # Search for the next available filename
        i = 1
        while proposed_filename in files_in_dir:
            proposed_filename = filename_base + '_' + str(i) + '.' + filename_ending
            i += 1
        filename_out = proposed_filename
    else:
        filename_out = proposed_filename
    return filename_out

def copy_to_clipboard(pltfigure, save_file_format, dpi):
    """
    Copies the current figure to the clipboard as a .png file.
    Note: Not implemented for .svg files and only works on Windows.
    
    Inputs:
        pltfigure: matplotlib figure
        save_file_format: 'png' or 'svg'
        dpi_slider: dpi slider value
    """
    if save_file_format == 'png':

        def send_to_clipboard(clip_type, data):
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(clip_type, data)
            win32clipboard.CloseClipboard()
    
        # Create temporary file
        filepath = "temp.png"
        fig = pltfigure
        fig.savefig(filepath,dpi=dpi)
        image = Image.open(filepath)
        output = BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        # Remove temporary file
        os.remove(filepath)

        # Send to clipboard
        send_to_clipboard(win32clipboard.CF_DIB, data)
    
    if save_file_format == 'svg':
        print('db_manager.copy_to_clipboard: copying .svg to clipboard is not yet implemented')

def copy_to_clipboard_powershell(db,fig,format,dpi):
    """
    Copies a matplotlib figure to the clipboard using powershell commands.

    Input:
        fig: matplotlib figure or list of matplotlib figures
        format: image format 'png' or 'svg'
        dpi: image resolution
    """
    if os.name != 'nt':
        raise ValueError('copy_to_clipboard: only implemented for Windows')

    if format == 'png':

        if isinstance(fig,list):
            fig_list = fig
        else:
            fig_list = [fig]
        
        # Create temporary directory
        tempdir = tempdir_maker(db)
        if os.path.isabs(tempdir):
            pass
        else:
            tempdir = os.path.abspath(tempdir)

        # Create temporary file
        counter = 0
        image_paths = []
        for fig in fig_list:
            filepath = tempdir+'\\' + 'clipboard_copy_file_' + str(counter) + ".png"
            fig.savefig(filepath,dpi=dpi)
            image_paths.append(filepath)
            counter += 1
        
        # Make powershell command
        powershell_command = r'$imageFilePaths = @("'
        for image_path in image_paths:
            powershell_command += image_path + '","'
        powershell_command = powershell_command[:-2] + '); '
        powershell_command += r'Set-Clipboard -Path $imageFilePaths;'

        # Execute Powershell
        completed = subprocess.run(["powershell", "-Command", powershell_command], capture_output=True)
        
    elif format == 'svg':
        print('copy_to_clipboard: svg format not supported yet')
    else:
        raise ValueError('copy_to_clipboard: format must be png or svg')

def tempdir_maker(db):
    """
    Creates a temporary directory in the current directory.

    Inputs:
        db: db_manager object
    """
    if db.directory.endswith('/') or db.directory.endswith('\\'):
        tempdir = db.directory+'temp_files'
    else:
        tempdir = db.directory+'\\temp_files'
    
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    return tempdir
