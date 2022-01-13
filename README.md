# PowerMaker
Install

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
update config

ToDo
Import at 1 SD below 2SD all install

Graphs to web
Web app page to import and export
Instructions


