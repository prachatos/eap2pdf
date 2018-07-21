import multiprocessing
import os
import sys
import time
import urllib.request
from urllib.error import HTTPError
from fpdf import FPDF
import PyPDF2


class EAPBookFetch:

    EAP_BASE_URL = 'https://images.eap.bl.uk'
    EAP_FILENAME = 'default.jpg'
    DEFAULT_HEIGHT = 1200
    DEFAULT_WIDTH = 1200 * 0.8
    JPEG_PATH = 'jpgs'
    PDF_PATH = 'pdfs'

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
            dl_url = self.join_url(combined_url, str(pg) + '.jp2', 'full', str(self.height) + ',' +
                                   str(self.DEFAULT_WIDTH), str(self.rotation),
                                   self.EAP_FILENAME + '?t=' + str(int(time.time() * 1000)))

            title = os.path.join(self.JPEG_PATH, eap_url_for_entry + '_' + str(pg) + '.jpg')
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
            with open(os.path.join(self.PDF_PATH, eap_url_for_entry + '_nofirst.pdf'), 'wb') as f:
                outfile.write(f)
            try:
                os.remove(os.path.join(self.PDF_PATH, eap_url_for_entry + '.pdf'))
            except OSError:
                pass

    def run(self):
        if len(sys.argv) < 2:
            raise Exception("No URL to download")
        else:
            # shitty code, sorry
            if len(sys.argv) < 3:

                url = sys.argv[1]
                self.download_jpg(url)
            else:
                urls = []
                for arg in sys.argv:
                    if arg.find("EAP") != -1:
                        urls.append(arg)
                pool = multiprocessing.Pool(processes=len(sys.argv) - 1)
                pool.map(self.download_jpg, urls)

    def __init__(self):
        self.rotation = 0
        self.height = self.DEFAULT_HEIGHT
        self.type = 'p'  # probably broken for landscape


if __name__ == '__main__':
    EAPBookFetch().run()
