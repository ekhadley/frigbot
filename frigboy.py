from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time, os
from bot import *

if "ekhad" in os.listdir("C:\\Users"):
    dpath = "C:\\Users\\ekhad\\Desktop\\frig\\chrome103\\chromedriver.exe"
    pwd = open("C:\\Users\\ekhad\\Desktop\\frig\\notthepassword.txt", "r").readline()
else:
    dpath = "D:\\frigdrivers\\chrome80driver\\chromedriver.exe"
    pwd = open("D:\\frigdrivers\\pass\\notthepassword.txt", "r").readline()

driver = webdriver.Chrome(dpath)
driver.switch_to.window(driver.window_handles[1])
driver.get("https://discord.com/login")

time.sleep(.5)

driver.find_element_by_name("email").send_keys("21438709a@gmail.com")
driver.find_element_by_name("password").send_keys(pwd)
driver.find_element_by_css_selector('[type=submit]').click()

time.sleep(3)
while 1:
    try:
        driver.find_element_by_css_selector('.overflow-1wOqNV').click()
        break
    except:
        time.sleep(.5)

time.sleep(.3)

frig = bot(driver)
print("friggbot initiated . . .")
time.sleep(1)

while 1:
    frig.readLast()
    #frig.intro()
    frig.enforceName()
    #print(frig.c4challenges, frig.c4games, )