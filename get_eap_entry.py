import requests
import bs4
import re


class EAPFileList:

    COLLECTIONS_FILE = 'collections.txt'
    EAP_FILE = 'eap_files.txt'
    URL_FOR_FILE = 'https://eap.bl.uk/archive-file/'
    URL_FOR_COLL = 'https://eap.bl.uk/collection/'

    @staticmethod
    def page_exists(uri):
        page = requests.get(uri)
        if page.status_code == 404:
            return False, ""
        else:
            html = bs4.BeautifulSoup(page.text, "lxml")
        return True, html

    def get_eap_list(self):
        with open(self.COLLECTIONS_FILE) as f:
            collections = f.read().splitlines()
        return collections

    def generate_download_list(self, collections):
        download_list = []
        for collection in collections:
            print('Now adding files from collection ' + collection + ' to download list...')
            converted_url = self.URL_FOR_FILE + collection.replace('/', '-')
            collection_conv_url = self.URL_FOR_COLL + collection.replace('/', '-')
            coll_exists, coll_content = self.page_exists(collection_conv_url)
            if not coll_exists:
                print(collection + ' is not a collection')
            else:
                try:
                    search_desc = coll_content.find("span", class_='search-description').get_text()
                except AttributeError:
                    print('No documents found in ' + collection_conv_url)
                    continue
                total_results = re.search(".*of(.*)results.*", search_desc.replace(',', '')).group(1).strip()
                if not self.page_exists(converted_url + '-' + total_results):
                    print('This collection probably has sub-collections. Please use those instead')
                else:
                    for i in range(1, int(total_results) + 1):
                        download_list.append(collection.replace('-', '/') + '/' + str(i))
        return download_list

    def write_to_file(self, eap_link):
        with open(self.EAP_FILE, 'a') as f:
            for entry in eap_link:
                f.write(entry + '\n')

    def run(self):
        collections = self.get_eap_list()
        if not collections:
            print('collections.txt is empty')
        else:
            self.write_to_file(self.generate_download_list(collections))


if __name__ == '__main__':
    EAPFileList().run()
