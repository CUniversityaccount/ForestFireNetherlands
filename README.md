# Fire categorization of the Netherlands

The analyzing code is written in python while the queries that are used to get the data is in the dialect of postgresql.
The structure is set up with database migration script (needs to be done in steps), data part for inserting the data and visualization to make the used figures.

The code needs an .env file to setup the db account and the set the location of various files with following setup:

| File locations                           |
| ---------------------------------------- |
| LOCALDATA*VIIRS = \_file_location*       |
| SHAPEFILE*NETHERLANDS = \_file_location* |
| RASTER*CORINE = \_file_location*         |
| NATURA2000 = _file_location_             |

| DATABASE Variables        |
| ------------------------- |
| HOST = _hostname_         |
| PORT = _port_             |
| DATABASE = _databasename_ |
| USER = _username_         |
| PASSWORD = _password_     |

The packages can be installed with
pip install -r requirements

The necessary files are mentioned in the method of the thesis.

## Migration scripts

The sql scripts needs to be inserted seperately foreach do $$ .. end $$.
This can possibly solved in the future.
