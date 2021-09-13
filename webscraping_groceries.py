from typing import ItemsView
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import json
from pprint import pprint
import matplotlib.pyplot as plt


from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re


measurements = ["TBSP", "TSP", "CUP"]


class FileDriver:
    def __init__(self, filename):
        self.filename=filename
    
    def write_to_file(self, content):
        f = open(self.filename, "a")
        f.write(content)
        f.close()    

    def write_to_clear_file(self, content):
        f = open(self.filename, "w")
        f.close()    
        f = open(self.filename, "a")
        f.write(content)
        f.close()    


class WebDriver:
    def setUp(self):
        self.driver = webdriver.Chrome("C:/Users/lombr/Downloads/chromedriver_win32_v93/chromedriver.exe")
    
    def change_page(self, page):
        driver = self.driver
        driver.get(page)

        #    This one isnt working very well because it needs to wait for the JS to load the items
    def page_search(self, search_element_name, search_term, file):
        driver = self.driver
        elem = driver.find_element_by_name(search_element_name)
        
        
        current_url = driver.current_url
        print(current_url)
        elem.send_keys(search_term)
        elem.send_keys(Keys.RETURN)
        WebDriverWait(driver, 15).until(EC.url_changes(current_url))
        new_url = driver.current_url
        print(new_url)
        
        delay = 20 # seconds    
        file.write_to_clear_file(driver.page_source)
        
    
    def tearDown(self):
        self.driver.close()
        
    def extract_by_class_woolworths(self, file):
        driver = self.driver
        # Waits for the presence of the class which is most important to us
        delay = 10 # seconds
        try:
            WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'shelfProductTile')))
        except:
            print("failed to return in time")
            return {"Error": "Didnt return Any Elements for this name"}
        
        
        file.write_to_clear_file(driver.page_source)
        AllProducts = driver.find_elements(By.CLASS_NAME, 'shelfProductTile')
        # Print out everything!! 
        # for e in AllProducts:
        #     print(e.text)
        ItemOutOfStockN = 0
        FoundStock = False
        # Should only run once, however if the first item doesnt have stock or a error occurs when extracting then it will get the next one 
        for Product in AllProducts:
            try: 
                 # we are only using the first product to show up in the search to determine the price
                # Elements extracted from the page
                Dollars = Product.find_elements(By.CLASS_NAME, 'price-dollars')[0].text
                Cents = Product.find_elements(By.CLASS_NAME, 'price-cents')[0].text
                ValueRation = Product.find_elements(By.CLASS_NAME, 'shelfProductTile-cupPrice')[0].text
                itemName = Product.find_elements(By.CLASS_NAME, 'shelfProductTile-descriptionLink')[0].text
                FoundStock=True
            except:
                print("Didnt Have Stock, had to get second best")
                ItemOutOfStockN+=1
                continue
                
            # Elements logically calculated
            Value=ValueRation.split("/")[0]
            Metric=ValueRation.split("/")[1]
            
            # Sanitisation of data
            replace_letters = ["$", " ", "\n"]
            for letter in replace_letters:
                Metric = Metric.replace(letter,"")
                Value = Value.replace(letter,"")
            
            # Splits the string into 2 array if number followed by character characters 
            match = None
            match = re.match(r"([0-9]+)([a-z]+)", Metric, re.I)
            
            RatioAmount = None
            RatioType = None
            if match:
                RatioAmount = match.groups()[0]
                RatioType = match.groups()[1]
            
            
            ReturnItem = {
                "Item Name": itemName,
                "Total Dollars": Dollars,
                "Total Cents": Cents,
                "Value / Ratio": ValueRation,
                "Value": Value,
                "Ratio": Metric,
                "Ratio Amount": RatioAmount,
                "Ratio Type": RatioType.upper() # So we have a consistency 
            }
            return ReturnItem
        if (len(AllProducts) <1):
            print("failed to return in time")
            return {"Error": "Didnt return Any Elements for this name"}
        if (FoundStock == False):
            print("Didnt Find any stock")
            return {"Error": "Didnt Find any stock"}
        # for e in elements:
        #     if (e.class)
        #     print(e.text)
        # print(elem)s
        # print(elem.html)
        # print(elem.size())
        
    def extract_taste(self, file):
        driver = self.driver
        # Waits for the presence of the class which is most important to us
        delay = 20 # seconds
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'tabIngredients')))
        
        # file.write_to_clear_file(str(driver.page_source))
        itemList = driver.find_elements(By.ID, 'tabIngredients')[0]
        AllProducts = itemList.find_elements(By.CLASS_NAME, 'ingredient-description')
        AllProductsReturn = []
          
        # Print out everything!! 
        # Print out everything!! 
        # for e in AllProducts:
        #     print(e.text)
        for product in AllProducts:     
            ItemReturn = {
                "Raw_text": product.text,
            }
            AllProductsReturn.append(ItemReturn)
        return AllProductsReturn
        
    def normalise_taste(self, rawItems):
        ItemN = 0
        allItems = []
        for item in rawItems:
            rawText= item["Raw_text"]
            Item_Normalised = rawText.split(",")[0]
            
            match = re.findall(r'\(.*?\)', Item_Normalised)
            # If we find one with some () inside then remove the brackets and whats inside of them. Most of the time it is cup conversion
            if (len(match) >= 1):
                match= match[0]
                Item_Normalised = Item_Normalised.replace(match, "")
            
            match = None
            
            # for measure in measurements:
            #     match = re.match(r"([0-9]+)(["+measure+"])([a-z]+)", Item_Normalised.upper(), re.I)
            #     if match:
            #         break
            # if match: 
            #     print(match.groups())    
            
            WordSplit = Item_Normalised.split(" ")
            returnItem={
                "Raw_text": rawText,
                "Raw_normalised": Item_Normalised                
            }
            match = None
            # See if the string starts with a number then a letter. eg. 9ml (without a space)
            match = re.match(r"([0-9]+)([a-z]+)", Item_Normalised, re.I)
            if match:
                fullMatch = match.groups()[0] + match.groups()[1] + " "
                returnItem["Item Name"] = Item_Normalised.replace(fullMatch, "")
                returnItem["Ratio Type"] = match.groups()[1].upper()
                returnItem["Ratio Amount"] = match.groups()[0]
                returnItem["Other Details"] = "X-Measure"
                # print(returnItem)
            else:   
                  
                if (len(WordSplit) == 1):
                    # If we just have one word, we assume its a single quantity product
                    returnItem["Item Name"] = WordSplit[0]    
                    returnItem["Ratio Type"] = "EA" 
                    returnItem["Ratio Amount"] = 1
                    returnItem["Other Details"] = "EA not specified (assumed 1)"
                else: 
                    match = re.match(r"([0-9]+)([ ])", Item_Normalised, re.I)    
                    if match:
                        if (WordSplit[1].upper() in measurements):
                            # 1 tsp with a space, this is using the measure array at the top to find it 
                            fullMatch = WordSplit[0] + " "+ WordSplit[1] + " "
                            returnItem["Item Name"] = Item_Normalised.replace(fullMatch, "")
                            returnItem["Ratio Type"] =  WordSplit[1]
                            returnItem["Ratio Amount"] = WordSplit[0]
                            returnItem["Other Details"] = "SPOON Measurement"
                        else: 
                            returnItem["Item Name"] = Item_Normalised.replace(WordSplit[0]+ " ", "")
                            returnItem["Ratio Type"] =  "EA"
                            returnItem["Ratio Amount"] = WordSplit[0]
                            returnItem["Other Details"] = "Amount of EA Specified"
                    else:
                        # This is for weird long versions of the single item 
                        returnItem["Item Name"] = Item_Normalised
                        returnItem["Ratio Type"] = "EA" 
                        returnItem["Ratio Amount"] = 1
                        returnItem["Other Details"] = "EA not specified (assumed 1) LONG"
            returnItem["ID"]= ItemN
            ItemN +=1        
            allItems.append(returnItem)
            
        return allItems

def WoolworthsScan(InputsList, woolworthsConfig, driver, file):
    ItemN = 0
    ItemInfoList= []
    for ItemName in InputsList:
        # This is for fixing the Search URL, we may need to add more of these in, its unicode being encoded in the Search
        if ("&" in ItemName):
            ItemName = ItemName.replace("&", "%26")
        if (" " in ItemName): 
            ItemName = ItemName.replace("&", "%20")
        driver.change_page(woolworthsConfig["home_url"]+ItemName)

        # driver.page_search(woolworthsConfig["search_element_name"], "beans", file)
        # Get the items from the recipe


        # FOR blah blah, run through and find the items on woolworths page
        Item = driver.extract_by_class_woolworths(file)
        Item["ID"] = ItemN
        ItemN+=1
        ItemInfoList.append(Item)

        print(json.dumps(Item, 
                        default=lambda obj: vars(obj),
                        indent=1))

    
    # END
    # a ={
    #  "Dollar": "5",
    #  "Cents": "00",
    #  "Amount Ration": "$1.63 / 100G",
    #  "Item Name": "Nestle Kitkat Large Share Pack 18 Pack"
    # }

    # b={
    #  "Dollar": "3",
    #  "Cents": "59",
    #  "Amount Ration": "$1.20 / 1L",
    #  "Item Name": "Woolworths Drought Relief Full Cream Milk 3l"
    # }
    # ItemInfoList= [a,b]

    ItemFrame = pd.DataFrame(ItemInfoList)
    ItemFrame["Total Cents"] = pd.to_numeric(ItemFrame ["Total Cents"])
    ItemFrame["Total Dollars"] = pd.to_numeric(ItemFrame ["Total Dollars"])
    TotalPriceColumn = ItemFrame["Total Dollars"] + ItemFrame["Total Cents"]*0.01
    # Adding cents and dollars to get the total product value
    ItemFrame["Total Amount"] = TotalPriceColumn
    ItemFrame["Ratio Amount"] = pd.to_numeric(ItemFrame ["Ratio Amount"])
    return ItemFrame         

        

    
def TasteScan(tasteConfig, driver, file):
    ItemInfoList= []
    driver.change_page(tasteConfig["recipe_url"])

    # driver.page_search(woolworthsConfig["search_element_name"], "beans", file)
    # Get the items from the recipe


        # FOR blah blah, run through and find the items on woolworths page
    RawItemInfoList= driver.extract_taste(file)
    ItemInfoList = driver.normalise_taste(RawItemInfoList)
    ItemFrame = pd.DataFrame(ItemInfoList)
    return ItemFrame
    


taste_url = "https://www.taste.com.au/recipes/curried-pumpkin-soup-chicken-recipe/3zehjn7s"
 
# START 
woolworthsConfig = {'home_url': "https://www.woolworths.com.au/shop/search/products?searchTerm=", 'search_element_name': "headerSearch"}
tasteConfig = {'home_url': "https://www.taste.com.au/",'recipe_url': taste_url, 'search_element_name': ""}
# Setting up the selenium driver
driver= WebDriver()
driver.setUp()
# Setting up the file driver
file = FileDriver("test.html")

# Works but we need to get it going again 
ScannedIngreds = TasteScan(tasteConfig,driver,file)





# Input List
# InputsList= ['vegetable oil', 'small brown onion', 'finely grated fresh ginger', 'garlic cloves', 'small red apple', 'packet S&B Golden Curry Sauce Mix', ' Massel vegetable liquid stock', 'carrots', 'shiitake mushrooms', 'firm tofu', ' plain flour', 'egg', ' panko breadcrumbs', 'packet roasted seaweed snacks', 'Steamed rice', 'Pickled radish', 'Cucumber']

# InputsList= ['packet S&B Golden Curry Sauce Mix']

InputsList= ScannedIngreds["Item Name"].values.tolist()
# Output List
ItemInfoList=WoolworthsScan(InputsList,woolworthsConfig,driver,file)

driver.tearDown()

# Doing the output and logging of what happened
print(ItemInfoList)
print("\n")
print(ScannedIngreds)
print("\n")
Joined = ScannedIngreds.join(ItemInfoList.set_index('ID'), on='ID',lsuffix='_taste',rsuffix='_woolworths')
print(Joined)


# Joined.plot(x ='Item Name_taste', y='Total Amount', kind = 'bar')
Joined.plot(kind='pie', y = 'Total Amount', autopct='%1.1f%%', 
 startangle=90, shadow=False, labels=Joined['Item Name_taste'], legend = False, fontsize=7)

plt.show()