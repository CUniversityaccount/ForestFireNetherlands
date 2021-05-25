-- Check if the database exists
do $$
begin 
	IF (NOT EXISTS(SELECT * FROM pg_catalog.pg_database WHERE datname = 'FireDB')) THEN
		RAISE NOTICE 'FireDB does not exists!';
	end if;
end $$

-- Check if the extension postgis is installed with the version
do $$
BEGIN 
    IF (NOT EXISTS (SELECT * FROM pg_catalog.pg_extension WHERE extname = 'postgis' AND extversion = '3.1.1')) THEN
        RAISE NOTICE 'POSTGIS is not installed!'; 
    END IF;
END $$

-- insert schema 
CREATE SCHEMA IF NOT EXISTS pixel;

-- Insert tables
DO $$
BEGIN 
    IF (NOT EXISTS(SELECT * FROM pg_catalog.pg_tables WHERE schemaname = 'pixel' and tablename = 'firepixel')) THEN
        CREATE TABLE pixel.FIREPIXEL(
            Id        uuid NOT NULL,
            Date      date NOT NULL,
            Time      time NOT NULL,
            Satellite varchar(3) NOT NULL,
            Latitude  numeric(8,6) NOT NULL,
            Longitude numeric(9,6) NOT NULL,
            T_I4      numeric(6, 3) NOT NULL,
            T_I5      numeric(6, 3) NOT NULL,
            Sample    bigint NOT NULL,
            Area      numeric(4, 1) NOT NULL,
            FRP       numeric(6,3) NOT NULL,
            Confidence varchar(7) NOT NULL,
            type      numeric(1) NOT NULL,
            CONSTRAINT PK_FIREPIXEL PRIMARY KEY(Id)
        );
    END IF;
END $$

-- Insert tables
DO $$
BEGIN 
    IF (NOT EXISTS(SELECT * FROM pg_catalog.pg_tables WHERE schemaname = 'pixel' and tablename = 'firepixelcharacteristics')) THEN
        CREATE TABLE pixel.FIREPIXELDETAIL(
            Id        uuid NOT NULL,
            FirePixelId uuid NOT NULL,
            Pixel    geometry NOT NULL,
            Landcovertype varchar(40) NOT NULL,   
            CONSTRAINT PK_FIREPIXELCHARACTERISTICS PRIMARY KEY(Id),
            CONSTRAINT FK_FirePixelCharacteristics_FirePixel FOREIGN KEY(FirePixelId) REFERENCES pixel.FIREPIXEL(Id)
        );
    END IF;
END $$


