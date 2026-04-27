import schedule
import time

def atualizar():
    print('atualizando')

schedule.every().sunday.at("02:00").do(atualizar)

while True:
    schedule.run_pending()
    time.sleep(60)