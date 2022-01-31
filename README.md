# PowerMaker

An open-source Intelligent Web Application manages solar-generated energy for the home or business and optimises buying and selling decisions onto the spot market.  

Developed in Python, Flask, Bootstrap 5 and MySQL.  PowerMaker runs on Linux, Windows and Mac OS.  The following installation instructions have been tested on Ubuntu 20.04 and will need to be modified for other OS.

sudo apt update  
sudo apt upgrade -y

sudo apt install python3-pip mysql-server libfreetype6-dev git -y  
sudo pip install pymodbus pymysql flask matplotlib numpy

sudo mysql  
    create database pm;  
    create user pm@localhost identified by 'SecurePasswordOfYourChoice';  
    grant all on pm.* to pm@localhost;  
    exit  

cd  
git clone https://github.com/New-Zealand-Zero/PowerMaker.git  

cd PowerMaker  
cp exampleconfig.py config.py  
update config.py depending on your environment and requirements  

Run the following script to setup the database
./setupdb.py

Run the following script which controls the import and exporting of power
./powermaker.py

In a new terminal run the following script to start the web server  
./webapp.py

To host on Apache from improved security etc

sudo apt install apache2 libapache2-mod-wsgi-py3 -y

update the following lines in webapp.wsgi  
    sys.path.insert(0, '/home/pi/PowerMaker') --> change to your application path
    application.secret_key = 'PowerMaker' --> change to a secret key of your choice  

create the Apache config file for our flask application  
    cd /etc/apache2/sites-available  
    sudo nano powermaker.conf  

    <VirtualHost *:80>
     # Add machine's IP address (use ifconfig command)
     ServerName 10.170.180.104
     # Give an alias to to start your website url with
     WSGIScriptAlias / /home/pi/PowerMaker/webapp.wsgi
     <Directory /home/pi/PowerMaker/>
      # set permissions as per apache2.conf file
            Options FollowSymLinks
            AllowOverride None
            Require all granted
     </Directory>
     ErrorLog ${APACHE_LOG_DIR}/error.log
     LogLevel warn
     CustomLog ${APACHE_LOG_DIR}/access.log combined
    </VirtualHost>

    sudo a2ensite powermaker.conf 
    sudo a2dissite 000-default.conf

    give access to the apache user to update the graphs
    cd  
    chmod 777 PowerMaker/static/actualIE.png
    chmod 777 PowerMaker/static/spotprice.png

    sudo systemctl reload apache2
