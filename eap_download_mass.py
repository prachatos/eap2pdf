import multiprocessing
import os
import re
import sys
import urllib.request
from urllib.error import HTTPError
from fpdf import FPDF
import PyPDF2
import time
import _helpers


class EAPBookFetch:
    EAP_BASE_URL = 'https://images.eap.bl.uk'
    EAP_ARCHIVE_URL = 'https://eap.bl.uk/archive-file/'
    EAP_LIST_FILENAME = 'eap_files.txt'
    EAP_DONE_FILENAME = 'eap_done.txt'
    EAP_FILENAME = 'default.jpg'
    DEFAULT_HEIGHT = 1200
    DEFAULT_WIDTH = 1200 * 0.8
    JPEG_PATH = 'jpgs'
    PDF_PATH = 'pdfs'
    DELETE_ORIG_PDF = True

    @staticmethod
    def join_url(*args):
        joined_url = ''
        for arg in args:
            joined_url = joined_url + arg + '/'
        return joined_url

    @staticmethod
    def set_rotate(angle):
        if angle == 90 or angle == 180 or angle == 270:
            return angle
        else:
            return 0

    def download_jpg(self, url):
        base_eap = url.split('/')[0]
        eap_url_for_entry = url.replace('/', '_')
        combined_url = self.join_url(self.EAP_BASE_URL, base_eap, eap_url_for_entry)
        pg = 1
        can_go = True
        file_list = []
        if not os.path.exists(self.JPEG_PATH):
            os.makedirs(self.JPEG_PATH)
        while can_go:
            if self.type == 'p':
                dl_url = self.join_url(combined_url, str(pg) + '.jp2', 'full', str(self.height) + ',' +
                                       str(self.DEFAULT_WIDTH), str(self.rotation),
                                       self.EAP_FILENAME + '?t=' + str(int(time.time() * 1000)))
            else:
                dl_url = self.join_url(combined_url, str(pg) + '.jp2', 'full', str(self.DEFAULT_WIDTH) + ',' +
                                       str(self.height), str(self.rotation),
                                       self.EAP_FILENAME + '?t=' + str(int(time.time() * 1000)))
            print(dl_url)
            title = os.path.join(self.JPEG_PATH, eap_url_for_entry + '_' + str(pg) + '.jpg')
            if os.path.isfile(title):
                # if file exists, don't download iff next file also exists
                # note that this effectively means that we can't parallelize at a page level
                download_this = True
                while True:
                    new_title = os.path.join(self.JPEG_PATH, eap_url_for_entry + '_' + str(pg + 1) + '.jpg')
                    old_title = os.path.join(self.JPEG_PATH, eap_url_for_entry + '_' + str(pg) + '.jpg')
                    if os.path.isfile(new_title):
                        print('Skipping ' + old_title)
                        file_list.append(old_title)
                        pg = pg + 1
                        download_this = False
                    else:
                        break
                if not download_this:
                    continue
            pg = pg + 1
            print('Downloading ' + title)
            try:
                urllib.request.urlretrieve(dl_url, title)
                file_list.append(title)
            except HTTPError:
                can_go = False

        pdf = FPDF(orientation=self.type, unit='pt', format=(self.height + 50, self.DEFAULT_WIDTH + 50))
        pdf.add_page(orientation=self.type)

        for image in file_list:
            print('Adding ' + image + ' to PDF')
            if self.type == 'p':
                pdf.image(image, h=self.DEFAULT_WIDTH, w=self.height)
            else:
                pdf.image(image, h=self.height, w=self.DEFAULT_WIDTH)
        page_count = pdf.page_no()
        if not os.path.exists(self.PDF_PATH):
            os.makedirs(self.PDF_PATH)
        pdf.output(os.path.join(self.PDF_PATH, eap_url_for_entry + '.pdf'))

        if page_count > len(file_list):
            # delete pg 1
            infile = PyPDF2.PdfFileReader(os.path.join(self.PDF_PATH, eap_url_for_entry + '.pdf'))
            outfile = PyPDF2.PdfFileWriter()
            pg = 1
            print('Deleting blank page...')
            while pg < page_count:
                p = infile.getPage(pg)
                pg = pg + 1
                outfile.addPage(p)
            exists, eap_file = _helpers.page_exists(self.EAP_ARCHIVE_URL + url.replace('/', '-'))
            if not exists:
                eap_filename = eap_url_for_entry
            else:
                eap_filename = eap_file.title.text.split('|')[0].strip()
                eap_filename = re.sub(r'[^\w]', '', eap_filename)
            with open(os.path.join(self.PDF_PATH, eap_filename + '.pdf'), 'wb') as f:
                outfile.write(f)
                print('Writing to ' + eap_filename + '.pdf')
                with open(self.EAP_DONE_FILENAME, 'a') as f:
                    f.write(url + '\n')
            if self.DELETE_ORIG_PDF:
                try:
                    os.remove(os.path.join(self.PDF_PATH, eap_url_for_entry + '.pdf'))
                except OSError:
                    pass

    def run(self):

        if len(sys.argv) < 2:
            print("Limiting number of files downloaded to 50")
        else:
            try:
                self.dl_count = int(sys.argv[2])
            except ValueError:
                pass

        try:
            with open(self.EAP_DONE_FILENAME) as f:
                urls_done = f.read().splitlines()
        except FileNotFoundError:
            urls_done = []
            open(self.EAP_DONE_FILENAME, 'w')

        try:
            with open(self.EAP_LIST_FILENAME) as f:
                urls = f.read().splitlines()
        except FileNotFoundError:
            urls = []
            open(self.EAP_LIST_FILENAME, 'w')

        urls_not_done = list(set(urls) - set(urls_done))[::-1]
        if not urls_not_done:
            print('No remaining file in list to download')
            return 0
        if len(urls_not_done) >= self.dl_count:
            urls_not_done = urls_not_done[0:self.dl_count]

        pool = multiprocessing.Pool(processes=len(urls_not_done))
        pool.map(self.download_jpg, urls_not_done)
        return len(urls_not_done)

    def __init__(self):
        self.rotation = 0
        self.height = self.DEFAULT_HEIGHT
        self.type = 'p'  # probably broken for landscape
        self.dl_count = 50


if __name__ == '__main__':
    start_time = time.time()
    downloaded = EAPBookFetch().run()
    elapsed_time_secs = time.time() - start_time
    print("Downloaded " + str(downloaded) + " files in " + str(elapsed_time_secs) + " seconds")
