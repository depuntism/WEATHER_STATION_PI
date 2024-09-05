# -*- coding:utf-8 -*-
import crontab
import datetime
import os
import time
from crontab import CronTab
from datetime import datetime

now = datetime.now()
date_time = now.strftime("%d/%m/%y à %H:%M:%S")
cron = CronTab("pi")
basic_iter = cron.find_comment("Start Weather News Sation")
list_comment = []

print("Redémarrage effectué le",date_time)
time.sleep(1)
print("Vérification de l'existence du job pour lancer la station en cours...")
time.sleep(2)
for item in basic_iter:
	list_comment.append(item)

if len(list_comment) == 0:
	print("Le job n'existe pas. Création en cours...")
	time.sleep(1)
	job = cron.new(command="/usr/bin/python3 /home/pi/Assistant_main.py >> /home/pi/Assistant_main.log") 
	job.minute.every(15)
	job.set_comment("Start Weather News Sation")
	job.enable()
	cron.write()
	time.sleep(1)
	now = datetime.now()
	date_time = now.strftime("%d/%m/%y à %H:%M:%S")
	print("Job créé avec succès le",date_time)
else:
	print("Le job existe déjà, pas besoin de le recréer")

time.sleep(1)
now = datetime.now()
date_time = now.strftime("%d/%m/%y à %H:%M:%S")
print("Vérification terminée le",date_time)
print("------------")
