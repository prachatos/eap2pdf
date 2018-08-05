import requests
import os
import re
import configparser
import urllib.request
from urllib.error import HTTPError
from fpdf import FPDF
import PyPDF2
import time
import _helpers


class EAPBookFetch:
    EAP_BASE_URL = 'https://images.eap.bl.uk'
    EAP_ARCHIVE_URL = 'https://eap.bl.uk/archive-file/'
    EAP_CONFIG_FILENAME = 'eap_conf.ini'
    EAP_FILENAME = 'default.jpg'
    DEFAULT_HEIGHT = 1200
    DEFAULT_WIDTH = 1200 * 0.8
    JPEG_PATH = 'jpgs'
    PDF_PATH = 'pdfs'
    API_BASE_URL = 'https://commons.wikimedia.org/w/api.php'
    CHUNK_SIZE = 1000000

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
            pdf = FPDF(orientation=str(self.type), unit='pt', format=(self.DEFAULT_WIDTH + 50, int(self.height) + 50))
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
            exists, eap_file = _helpers.page_exists(self.EAP_ARCHIVE_URL + self.url.replace('/', '-'))
            if not exists:
                eap_filename = eap_url_for_entry
            else:
                eap_filename = eap_file.title.text.split('|')[0].strip()
                eap_filename = re.sub(r'[^\w]', '', eap_filename)
            with open(os.path.join(self.PDF_PATH, eap_filename + '.pdf'), 'wb') as f:
                outfile.write(f)
                print('Writing to ' + eap_filename + '.pdf')
            try:
                os.remove(os.path.join(self.PDF_PATH, eap_url_for_entry + '.pdf'))
            except OSError:
                pass
            return eap_filename
        return ''

    def read_config(self):
        config_parser = configparser.ConfigParser()
        config_parser.read(self.EAP_CONFIG_FILENAME)
        self.url = config_parser.get('download', 'url')
        if config_parser.has_option('download', 'rotation'):
            self.rotation = config_parser.get('download', 'rotation')
        if config_parser.has_option('download', 'height'):
            self.height = int(config_parser.get('download', 'height'))
        if config_parser.has_option('download', 'orientation'):
            self.type = config_parser.get('download', 'orientation')  # does not work!
        try:
            self.username = config_parser.get('wiki', 'username')
            self.password = config_parser.get('wiki', 'pwd')
            if config_parser.has_option('wiki', 'summary'):
                self.summary = config_parser.get('wiki', 'summary')
            self.title = config_parser.get('wiki', 'title')
            self.filename = config_parser.get('wiki', 'filename')
            self.description = config_parser.get('wiki', 'desc')
            self.author = config_parser.get('wiki', 'author')
            self.license = config_parser.get('wiki', 'license')
            self.date = config_parser.get('wiki', 'date')
        except Exception:
            pass

    def get_token(self):
        session = requests.Session()
        login_t = session.get(self.API_BASE_URL, params={
            'format': 'json',
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
        })
        login_t.raise_for_status()
        login = session.post(self.API_BASE_URL, data={
            'format': 'json',
            'action': 'login',
            'lgname': self.username,
            'lgpassword': self.password,
            'lgtoken': login_t.json()['query']['tokens']['logintoken'],
        })
        if login.json()['login']['result'] != 'Success':
            raise RuntimeError(login.json()['login']['reason'])

        # get edit token
        tokens = session.get(self.API_BASE_URL, params={
            'format': 'json',
            'action': 'query',
            'meta': 'tokens',
        })
        return session, tokens.json()['query']['tokens']['csrftoken']

    def upload_file(self, session, filename):
        can_go = True
        filename = os.path.join(self.PDF_PATH, filename + '.pdf')
        filekey = ''
        filesize = os.path.getsize(filename)
        print(self.token)
        offset = 0
        i = 1
        page_content = "=={{int:filedesc}}==\n" + \
                       "{{Book\n" + \
                       "| Author       = " + self.author + "\n" + \
                       "| Title        = " + self.title + "\n" + \
                       "| Date         = " + self.date + "\n" + \
                       "| Language     = {{language|bn}}\n" + \
                       "| Wikisource   = s:bn:নির্ঘণ্ট:{{PAGENAME}}\n" + \
                       "| Description  = " + self.description + "\n" + \
                       "| Source       =  {{Endangered Archives Programme|url=" + self.EAP_ARCHIVE_URL + self.url.replace('/', '-') + \
                       "}}{{Institution:British Library}}\n" + \
                       "| Image        =  {{PAGENAME}}\n" + \
                       "}}\n" + \
                       "=={{int:license-header}}==\n" + self.license + "\n" + \
                       "[[Category:Uploaded with eap2pdf]]\n" + \
                       "[[Category:PDF-files in Bengali]]"
        with open(filename, 'rb') as f:
            while can_go:
                chunk = f.read(self.CHUNK_SIZE)
                if offset == 0:
                    upload = session.post(self.API_BASE_URL, data={
                        'format': 'json',
                        'action': 'upload',
                        'filename': self.filename + '.pdf',
                        'filesize': filesize,
                        'offset': offset,
                        'chunk': chunk,
                        'token': self.token
                    }, files={'chunk': chunk,
                              'filename': self.filename + '.pdf'})
                    print('Uploaded ' + str(i) + ' MB...')
                    i = i + 1
                    try:
                        filekey = upload.json()['upload']['filekey']
                    except (KeyError, NameError):
                        print(upload.json())
                        raise RuntimeError('Upload failed - try manually!')
                else:
                    upload = session.post(self.API_BASE_URL, data={
                        'format': 'json',
                        'action': 'upload',
                        'filename': self.filename + '.pdf',
                        'filesize': filesize,
                        'filekey': filekey,
                        'offset': offset,
                        'chunk': chunk,
                        'token': self.token
                    }, files={'chunk': chunk,
                              'filename': self.filename + '.pdf'})
                    print('Uploaded ' + str(i) + ' MB...')
                    i = i + 1
                    try:
                        filekey = upload.json()['upload']['filekey']
                    except (KeyError, NameError):
                        print(upload.json())
                        raise RuntimeError('Upload failed - try manually!')
                if upload.json()['upload']['result'] == 'Success':
                    done = session.post(self.API_BASE_URL, data={
                        'format': 'json',
                        'action': 'upload',
                        'filename': self.filename + '.pdf',
                        'filekey': filekey,
                        'comment': self.summary,
                        'token': self.token,
                        'text': page_content
                    }, files={'filename': self.filename + '.pdf'})
                    if 'error' in done.json():
                        raise RuntimeError('Could not complete upload. You probably got caught by an abuse filter')
                    else:
                        print('Done!')
                    break
                elif upload.json()['upload']['result'] == 'Continue':
                    try:
                        offset = upload.json()['upload']['offset']
                    except (KeyError, NameError):
                        print(upload.json())
                        raise RuntimeError('Upload failed - try manually!')
                else:
                    print(upload.json())
                    raise RuntimeError('Upload failed - try manually!')

    def run(self):
        try:
            with open(self.EAP_CONFIG_FILENAME) as f:
                self.read_config()
        except FileNotFoundError:
            print('No configuration file found!')
            return 0
        filename = self.download_jpg()
        try:
            session, self.token = self.get_token()
            self.upload_file(session, filename)
        except (RuntimeError, HTTPError) as e:
            print(e)
            print('Could not upload file. Please verify your credentials.')

        return 1

    def __init__(self):
        self.rotation = 0
        self.height = self.DEFAULT_HEIGHT
        self.type = 'p'  # probably broken for landscape
        self.url = ''
        self.username = ''
        self.password = ''
        self.summary = 'Uploaded via EAP2PDF'
        self.title = ''
        self.description = ''
        self.author = ''
        self.token = ''
        self.date = ''
        self.license = ''
        self.filename = ''


if __name__ == '__main__':
    start_time = time.time()
    downloaded = EAPBookFetch().run()
    elapsed_time_secs = time.time() - start_time
    print("Uploaded " + str(downloaded) + " files in " + str(elapsed_time_secs) + " seconds")
