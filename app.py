import os
import sys
import time
import urllib.request
from urllib.error import HTTPError
from fpdf import FPDF
from PyPDF2 import PdfFileWriter, PdfFileReader

class EAPBookFetch:

    EAP_BASE_URL = 'https://images.eap.bl.uk'
    EAP_FILENAME = 'default.jpg'
    DEFAULT_HEIGHT = 1200
    DEFAULT_WIDTH = 1200 * 0.8

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

    def download_jpg(self):
        base_eap = self.url.split('/')[0]
        eap_url_for_entry = self.url.replace('/', '_')
        combined_url = self.join_url(self.EAP_BASE_URL, base_eap, eap_url_for_entry)
        pg = 1
        can_go = True
        file_list = []
        while can_go:
            dl_url = self.join_url(combined_url, str(pg) + '.jp2', 'full', str(self.height) + ',' + str(self.DEFAULT_WIDTH),
                                   str(self.rotation), self.EAP_FILENAME + '?t=' + str(int(time.time() * 1000)))
            if not os.path.exists('jpgs'):
                os.makedirs('jpgs')
            title = os.path.join('jpgs', eap_url_for_entry + '_' + str(pg) + '.jpg')
            pg = pg + 1
            print('Downloading ' + title)
            try:
                urllib.request.urlretrieve(dl_url, title)
                file_list.append(title)
            except HTTPError:
                can_go = False

        if self.type == 'p':
            pdf = FPDF(orientation=self.type, unit='pt', format=(self.DEFAULT_WIDTH + 50, self.height + 50))
            pdf.add_page(orientation=self.type)
        else:
            pdf = FPDF(orientation=self.type, unit='pt', format=(self.height + 50, self.DEFAULT_WIDTH + 50))
            pdf.add_page(orientation=self.type)

        for image in file_list:
            print('Adding ' + image + ' to PDF')
            if self.type == 'p':
                pdf.image(image, h=self.height, w=self.DEFAULT_WIDTH)
            else:
                pdf.image(image, h=self.height, w=self.DEFAULT_WIDTH)
        page_count = pdf.page_no()
        if not os.path.exists('pdfs'):
            os.makedirs('pdfs')
        pdf.output(os.path.join('pdfs', eap_url_for_entry + '.pdf'))
        if page_count > len(file_list):
            # delete pg 1
            infile = PdfFileReader(os.path.join('pdfs', eap_url_for_entry + '.pdf'))
            outfile = PdfFileWriter()
            pg = 1
            print('Deleting blank page...')
            print(page_count)
            while pg < page_count:
                p = infile.getPage(pg)
                print(pg)
                pg = pg + 1
                outfile.addPage(p)
            with open(os.path.join('pdfs', eap_url_for_entry + '_nofirst.pdf'), 'wb') as f:
                outfile.write(f)


    def run(self):
        if len(sys.argv) < 2:
            raise Exception("No URL to download")
        else:
            self.url = sys.argv[1]
            # shitty code, sorry
            if len(sys.argv) == 3:
                self.rotation = self.set_rotate(sys.argv[2])
            if len(sys.argv) == 4:
                self.height = sys.argv[3]
            if len(sys.argv) == 5:
                self.type = str(sys.argv[4])
        self.download_jpg()

    def __init__(self):
        self.url = ''
        self.rotation = 0
        self.height = self.DEFAULT_HEIGHT
        self.type = 'p'  # probably broken for landscape


EAPBookFetch().run()