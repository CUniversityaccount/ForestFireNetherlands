from dotenv import load_dotenv
import os
import psycopg2

class Connection:
    def __init__(self):
        self.conn = None
        self.start()

    def start(self):
        if not load_dotenv():
            raise FileNotFoundError('env') 
        elif os.getenv("HOST") is None:
            raise KeyError('Host not defined in environment')
        elif os.getenv("DATABASE") is None:
            raise KeyError('DATABASE not defined in environment')        
        elif os.getenv("USER") is None:
            raise KeyError('USER of databse is not defined in environment')        
        elif os.getenv("PORT") is None:
            raise KeyError('PORT of the database not defined in environment')
            
        try: 
            self.conn = psycopg2.connect(
                host = os.getenv("HOST"),
                database = os.getenv("DATABASE"),
                user = os.getenv("USER"),
                password = os.getenv("PASSWORD"),
                port = os.getenv("PORT")
            )

            if self.conn is not None:
                print("Has Connection!")
            else:
                raise ConnectionError("Has no connection!")
                
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
    
    def close(self):
        if (self.conn is not None):
            try:
                self.conn.close()
            except (Exception) as error:
                print(error)

if __name__ == '__main__':

    conn = Connection()
    conn.close()
