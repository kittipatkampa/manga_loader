import urllib.request
import os
from bs4 import BeautifulSoup

# Send files to kindle
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import json


class MangaLoader():

    def __init__(self, name=None, url_seed=None, start_page=None, stop_page=None, out_pdf=None):
        self.name = name
        self.url_seed = url_seed
        self.start_page = start_page
        self.stop_page = stop_page
        self.out_pdf = out_pdf

    def get_html_page(self, url, user_agent=None):
        if user_agent is None:
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19'
        try:
            html_obj = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': user_agent}))
            page = html_obj.read()
        except:
            print("the page probably does not exist")
            page = None
        return page

    def get_image_url(self, url):
        page = self.get_html_page(url)
        try:
            soup = BeautifulSoup(page, "lxml")

            if 'readms' in url:
                img_tag = soup.find(id="manga-page")
            elif 'mangareader' in url:
                img_tag = soup.find(id="imgholder").find(id="img")
            elif 'mangadoom' in url:
                img_tag = soup.findAll('img')[1]
            else:
                img_tag = None

            if img_tag != None:
                img_url = img_tag.get("src",None)
            else:
                img_url = None
        except:
            img_url = None
        return img_url

    def create_image_url_list(self, seed_url, start_page, stop_page, verbose=False):
        img_urls = []
        for i in range(start_page, stop_page+1):
            url = '{0}{1}'.format(seed_url,i)
            if verbose:
                print('retriving image from ',url,'...')
            img_urls.append( self.get_image_url(url) )
        self.img_urls = img_urls
        return img_urls

    def get_image_filename(self, img_url):
        for s in img_url.split('/'):
            if ('.jpg' in s) or ('.png' in s):
                return s
        return None

    def clean_img_filename(self, img_filename):
        import re
        if '.jpg' in img_filename:
            return re.sub('.jpg.*','.jpg', img_filename)
        elif '.png' in img_filename:
            return re.sub('.png.*','.png', img_filename)
        elif '.bmp' in img_filename:
            return re.sub('.bmp.*','.bmp', img_filename)
        else:
            return None

    def generate_image_filenames(self, img_urls):
        # remove None from the list
        img_urls = [u for u in img_urls if u is not None]
        img_urls = [u for u in img_urls if ('jpg' in u) or ('png' in u) or ('bmp' in u)]
        img_filenames = []
        for img_url in img_urls:
            img_filenames.append( self.clean_img_filename(self.get_image_filename(img_url)) )
        return img_filenames

    def download_images_from_urls(self, img_urls):
        # remove None from the list
        img_urls = [u for u in img_urls if u is not None]
        img_urls = [u for u in img_urls if ('jpg' in u) or ('png' in u) or ('bmp' in u)]
        # download images from urls
        cnt = 1
        for img_url in img_urls:
            img_filename = self.clean_img_filename(self.get_image_filename(img_url))
            os.system("wget -O {0} {1}".format(img_filename, img_url))
            cnt = cnt + 1
        return '{0} images downloaded'.format(cnt)

    def convert_images_to_pdf(self, img_filenames, output_filename):
        output_filename = output_filename.replace(' ','_')
        result = os.system("convert "+' '.join(img_filenames)+' '+output_filename)
        if result == 0:
            return 'the output pdf = {0}'.format(output_filename)
        else:
            return 'failed'

    def clean_up(self):
        # remove all the downloaded images
        for img_filename in self.img_filenames:
            os.system("rm {0}".format(img_filename))
        return 1

    def run(self, cleanup=True, verbose=True):
        self.img_urls = self.create_image_url_list( self.url_seed, self.start_page, self.stop_page, verbose)
        self.img_filenames = self.generate_image_filenames(self.img_urls)
        self.download_images_from_urls(self.img_urls)
        self.convert_images_to_pdf(self.img_filenames, self.out_pdf+'.pdf')
        if cleanup:
            self.clean_up()
        return 1


def send_mail_with_attachment(send_from, send_to, subject, text, gmail_user, gmail_pwd, files=None,
              server="127.0.0.1"):
    assert isinstance(send_to, list)

    msg = MIMEMultipart(
        From=send_from,
        To=COMMASPACE.join(send_to),
        Date=formatdate(localtime=True),
        Subject=subject
    )
    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            msg.attach(MIMEApplication(
                fil.read(),
                Content_Disposition='attachment; filename="%s"' % basename(f),
                Name=basename(f)
            ))

    try:
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(gmail_user, gmail_pwd)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()
        print('successfully sent the mail')
    except:
        print("failed to send mail")



def get_credential(credential_file, account):
    '''
    Get the credential in order to send email.
    The credential file (e.g. '.credentials') is in the following json format:

    {"default": {
      "user": "youraccountname"
      , "pwd": "kulhsjfhuyjgdfh"
      , "from": "whateverwhitelistedsender@gmail.com"
      , "kindle": ["yourkindleaccount@kindle.com"]
      },
    "projx": {
      "user": "youraccountname2"
      , "pwd": "tfsdejybhsdse"
      , "from": "whateverwhitelistedsender2@gmail.com"
      , "kindle": ["yourkindleaccount@kindle.com"]
      }
    }

    '''
    with open(credential_file) as cred:
        credentials = json.load(cred)

    return credentials[account]



if __name__ == '__main__':

    # get credential for sending email to kindle
    credential = get_credential('.credentials', 'default')

    # setting parameters for your manga download
    name = '20thCB'
    start_page = 1
    stop_page = 40
    chapter_start = 36
    chapter_end = 60

    # loop to download your manga
    for chapter in range(chapter_start, chapter_end+1):
        out_pdf = '20th Century Boys v{0}'.format(chapter)
        url_seed = 'http://www.mangareader.net/20th-century-boys/{0}/'.format(chapter)
        print("downloading vol.{0}".format(chapter))
        MangaLoader(name, url_seed, start_page, stop_page, out_pdf).run(cleanup=True, verbose=True)

        print("sending vol.{0}".format(chapter))
        send_mail_with_attachment(credential['from'], credential['kindle'], 'This is subject', 'body',
                                  credential['user'], credential['pwd'],
                                  ['/Users/kittipat.kampa/Dropbox/research/manga_loader/20th_Century_Boys_v{0}.pdf'.format(chapter)])

