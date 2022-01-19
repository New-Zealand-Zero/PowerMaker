# PowerMaker

An open-source Intelligent Web Application manages solar-generated energy for the home or business and optimises buying and selling decisions onto the spot market.  

Developed in Python, Flask, Bootstrap 5 and MySQL.  PowerMaker runs on Linux, Windows and Mac OS.  The following installation instructions have been tested on Ubuntu 20.04 and will need to be modified for other OS.

sudo apt update
sudo apt upgrade -y

sudo apt install pip mysql libfreetype6-dev -y

sudo pip install pymodbus pymysql flask matplotlib numpy

sudo mysql 
    create database pm;
    create user pm@localhost identified by 'SecurePasswordOfYourChoice';
    grant all on pm.* to pm@localhost;
    exit

git clone https://github.com/New-Zealand-Zero/PowerMaker.git

cd PowerMaker
cp exampleconfig.py config.py
update config.py depending on your environment and requirements.

Run the following script to setup the database
./setupdb.py

Run the following script which controls the import and exporting of power
./powermaker.py

Run the following script to start the web server
./webapp.py


