# eap2pdf
Converts books from EAP (eap.bl.uk) to PDF

# Scripts
This repository has 2 scripts - one for mass downloading, the other for individual downloading and uploading to Wikimedia Commons.

# Installation
- Python 3.6
- Clone repo
- pip install -r requirements.txt 

# Mass downloader

- The recommended mass downloader is **eap_download_mass.py**
- To use this, at first, all collections containing books you want to download must be added to collections.txt
- Format for collections - EAPabc/x/y. Ensure that you're adding collections (note the URL) and not archive file or projects
- Run *python3 get_eap_entry.py*. This is required only for the **first run**. This generates eap_files.txt.
- Now run *python3 eap_download_mass.py*. Optionally add a limit of number of books to be downloaded as an argument (defaults to 50)
- This should download all PDFs to the /pdf folder. This also generates eap_done.txt which is used to keep track of files you've already downloaded
- The alternative file *eap_download_cl.py* allows more customization (i.e. rotation, orientation), but requires a command line input of files to be downloaded

# Individual book uploader

- The file for this is **eap_download_sel.py**
- This relies on the **eap_conf.ini** file. All parameters are compulsory.
- Run *python3 eap_download_sel.py* after completing the configuration file requirements
- The file uploaded has the {{Book}} template auto-added along with [[Category:PDF-files in Bengali]]
- License templates have to be specified or later edited manually
