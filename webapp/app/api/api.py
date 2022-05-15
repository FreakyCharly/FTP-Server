from ftplib import FTP

class API:
    """
    API interface HTTP <-> FTP.
    """
    
    def __init__(self):
        self.ftp = FTP()
        self.ftp.set_pasv(val=False)
        self.ftp.connect('localhost', 8887)
        self.ftp.login('eps', 'eps')

    def list_dir(self, dir=None, root=False):
        """
        Gets all files/folders from current directory.
        """

        if not self.ftp:
            return
        
        directory = []
        try:
            if dir:
                self.ftp.cwd(dir)
                self.ftp.retrlines('LIST', lambda a: directory.append(a))
            elif root is True:
                self.ftp.cwd('/')
                self.ftp.retrlines('LIST', lambda a: directory.append(a))
            else:
                self.ftp.retrlines('LIST', lambda a: directory.append(a))
        except:
            self.ftp.cwd('/')
            self.ftp.retrlines('LIST', lambda a: directory.append(a))
        
        ret = []
        for item in directory:
            """
            [4]: Size
            [5]: Month
            [6]: Day
            [7]: HH:MM
            [8]: Title.ext
            """
            item_info = item.split(' ')
            ret.append(
                {
                    'title': item_info[8],
                    'date': item_info[7] + ', ' + item_info[6] + '/' + item_info[5],
                    'size': item_info[4] + 'KB'
                }
            )
        return ret
    
    def get_file_content(self, title):
        """
        Get's the content of a given file.
        """
        if '.' in title:
            content = []
            try:
                a = self.ftp.retrbinary('RETR ' + title, lambda a: content.append(a))
            except:
                pass
            return 'file', content
        else:
            return 'directory', self.list_dir(dir=title)
    
    def store_file(self, file):
        try:
            self.ftp.storbinary('STOR '+file.filename, file)
        except:
            return 'Something went wrong. Can\'t upload file.'
        return 'File uploaded succesfully.'