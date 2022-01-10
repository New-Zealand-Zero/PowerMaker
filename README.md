# PowerMaker
Install

sudo apt install pip mysql libfreetype6-dev -y

sudo pip install pymodbus pymysql flask matplotlib numpy

sudo mysql 
create database pm;
create user pm@localhost identified by 'SecurePasswordOfYourChoice';
grant all on pm.* to pm@localhost;
exit

git clone https://github.com/carthorseZ/PowerMaker.git

cd PowerMaker

cp exampleconfig.py config.py
update config


