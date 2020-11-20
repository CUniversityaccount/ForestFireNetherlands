from ftplib import FTP

def main(ftp, username, password, path):
    read_files(ftp, username, password, path)
    return

def read_files(ftp, username, password, path):
    ftp_connection = FTP(ftp, user=username, passwd = password)
    ftp_connection.cwd(path)
    print(ftp_connection.nlst())
    files = list(filter(lambda x: (".txt" in x) and ("2020" in x) and ("all_variables" not in x) and ("allvariables" not in x), ftp_connection.nlst()))
    for filename in files:
        ftp_connection.retrbinary("RETR " + filename , open(filename, 'wb').write)

    ftp_connection.abort()
    ftp_connection.close()
    return

if __name__ == "__main__":
    username = "fire"
    password = "burnt"
    ftp = "fuoco.geog.umd.edu"
    path = "/VIIRS/VNP14IMGML"
    main(ftp, username, password, path)
    