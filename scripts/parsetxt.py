from ftplib import FTP

def main(ftp, username, password):
    read_files(ftp, username, password)
    return

def read_files(ftp, username, password):
    ftp_connection = FTP(ftp, user=username, passwd = password)
    
    ftp_connection.login()
    
    
    ftp.abort()
    ftp.close()
    return

if __name__ == "__main__":
    username = "fire"
    password = "burnt"
    ftp = "fuoco.geog.umd.edu"
    main(ftp, username, password)
    