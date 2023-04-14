from kivymd.app import MDApp
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.behaviors import FakeRectangularElevationBehavior
from kivy.core.window import Window
 
from kivymd.uix.snackbar import Snackbar
from kivy.utils import get_color_from_hex
from pyzbar.pyzbar import ZBarSymbol
import datetime
from firebase import firebase
import collections
from varname import nameof #Requires pip install
import string
from kivy.properties import StringProperty
from kivy.properties import NumericProperty
from kivymd.uix.datatables import MDDataTable
import numpy as np
import os
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
 
class Panel(MDFloatLayout,FakeRectangularElevationBehavior):
    pass

class TTApp(MDApp):

    userName = StringProperty()
    userScore = NumericProperty()
    userDiscountCode = StringProperty()

    descriptionNutrientLabel = StringProperty() 
    nutrientBreakdownA = StringProperty()
    nutrientBreakdownC = StringProperty() 
    
 
    def build(self):
        global SC 
        SC = ScreenManager()
        SC.add_widget(Builder.load_file("main.kv"))
        SC.add_widget(Builder.load_file("QR Code Reveal Screen.kv"))
        SC.add_widget(Builder.load_file("QR Scan Screen.kv"))
        SC.add_widget(Builder.load_file("Post Scan Screen.kv"))
        SC.add_widget(Builder.load_file("User Metrics.kv"))
        return SC
    
    
    def psw(self):
        if SC.get_screen("z").ids.password.password==True:
            SC.get_screen("z").ids.password.password=False
            print("test")
            SC.get_screen("z").ids.l.icon="eye"
        else:
            SC.get_screen("z").ids.password.password=True
            print("test2")
            SC.get_screen("z").ids.l.icon="eye-off"
    def delete(self):
        SC.get_screen("z").ids.password.password=False
        SC.get_screen("z").ids.password.text=" "

        SC.get_screen("z").ids.username.text=" "
    def settings(self):
        print("settings tested") 
    #firebase
    def login(self,username,password): 

        userData=firebase.FirebaseApplication('https://healthy-world-app-v1-b744b-default-rtdb.firebaseio.com/')

        rs =userData.get('Users/{0}'.format(username), '') 

        if rs["name"]==username:
                if rs["password"]==password:
                    self.userName = str(username) 
                    self.userScore = rs["userNutritionalScore"]
                    self.userDiscountCode = rs["userDiscountCode"]
                    SC.current="QR Code Reveal Screen" #screen name 
                else:
                    snb =Snackbar(text="Invalid entry",bg_color=get_color_from_hex("#67DA49"))
                    snb.open() 


    def discountCodeManipulator(self,finalKey): 
        userScore = self.userScore #From 0 to 10 
        userScoreTruncated = int(userScore)  
        finalKey = str(finalKey[0]) + self.userName
        def shift(alphabet):
            return alphabet[userScoreTruncated:] + alphabet[:userScoreTruncated]
        includedAlphabets = (string.ascii_lowercase, string.ascii_uppercase, string.digits)
        shiftedAlphabets = tuple(map(shift, includedAlphabets))
        joinedAlphabets = ''.join(includedAlphabets)
        joinedShiftedAlphabets = ''.join(shiftedAlphabets) 
        table = str.maketrans(joinedAlphabets, joinedShiftedAlphabets)
        self.userDiscountCode = finalKey.translate(table)
        print((self.userDiscountCode)) 
        
        
    def userScoreGenerator(self):

        userData = firebase.FirebaseApplication('https://healthyworldapp--foodlog-default-rtdb.firebaseio.com/',None) 
        maxItemScore = 40 #Sum of all maxed A categories subtract the minimum of all C values would equal 40
        userScanned = False

        userLog = userData.get('Users/', '')
        if userLog != None:
            userScanned = True

        if userScanned == True:
            userFoodLog = userLog[self.userName]
            userFoodLogKeys = ",".join(list(userFoodLog.keys()))
            userFoodLogKeysList = (userFoodLogKeys.split(","))
            userFoodLogKeysList = ([eval(i) for i in userFoodLogKeysList])  #sorted may work here keep checking that outputs in time are correct
                                                                            #Stores keys as plaintext
    
            
            keys = []

            for key in userFoodLog:
                keys.append(key) 

            count = 0

            scoreSum = 0

            for key in (keys[-20:]):  
                    
                relevantLog = userFoodLog[key]
                score = relevantLog["score"]
                scoreSum = scoreSum + score
                count += 1 

                    
            averageScore = scoreSum / count
            self.userScore = (averageScore / maxItemScore) * 10 # Integral as caesar cipher support only under 26
            finalKey = userFoodLogKeysList[-1:] 
            TTApp.discountCodeManipulator(self,finalKey)
        else:
            self.userDiscountCode = "OOPS! Start Scanning Food Items to Unlock This Option!" 

        
    def scannedItemBreakdown(self, itemName, boundaryDict, cScoreDict): 

        descriptionNutrientLabel = "{0} Nutrient Breakdown:".format(itemName)
        nutrientBreakdownA = "Item Energy (kJ): {0}\nItem Saturated Fat (g): {1}\nTotal sugar (g): {2}\nSodium content (mg): {3}".format(boundaryDict["Energy"],boundaryDict["satFats"],boundaryDict["totalSugar"],boundaryDict["sodium"]) 
        nutrientBreakdownC = "\nFruit, Veg & Nuts (%): {0}\nNSP Fibre (g): {1}\nAOAC Fibre (g): {2}\nProtein (g): {3}".format(cScoreDict["FVN"],cScoreDict["fibreNSP"],cScoreDict["fibreAOAC"],cScoreDict["protein"]) 
        
        self.descriptionNutrientLabel = descriptionNutrientLabel
        self.nutrientBreakdownA = nutrientBreakdownA
        self.nutrientBreakdownC = nutrientBreakdownC 


    def userFoodLogAdder(self, itemName, totalItemScore, boundaryDict, cScoreDict): 
        username = self.userName
        datetimeItem = str(datetime.datetime.now())
        datetimeItemFormatted = ''.join(filter(str.isalnum, datetimeItem))

        userData = firebase.FirebaseApplication('https://healthyworldapp--foodlog-default-rtdb.firebaseio.com/',None)

        data={ 

            "item name":itemName, 
            "score":totalItemScore,
            "datetime":datetimeItem,
            "A values":boundaryDict,
            "C values":cScoreDict, 
                }

        userData.patch('Users/{0}/{1}'.format(username,datetimeItemFormatted),data) 

    def scanQR(self,codeVal):
        codeValFormatted = codeVal[5:]
        foodMacros = codeValFormatted.split(",") 
        SC.current="QR Scan Screen" 

        itemName = foodMacros[0]
        itemEnergy = float(foodMacros[1])
        itemSatFats = float(foodMacros[2])
  
        itemTotalSugar = float(foodMacros[3])
        itemSodium = float(foodMacros[4])

        itemFVN = float(foodMacros[5])
        itemProtein = float(foodMacros[8]) 

        itemFibreNSP= float(foodMacros[6])
        itemFibreAOAC = float(foodMacros[7])

        # A - points
        boundaryHolder = []
        allBoundaries = [[0,335,670,1005,1340,1675,2010,2345,2680,3015,3350],[0,1,2,3,4,5,6,7,8,9,10],[0,4.5,9,13.5,18,22.5,27,31,36,40,45],[0,90,180,270,360,450,540,630,720,810,900]]
        allAvalues = [itemEnergy,itemSatFats,itemTotalSugar,itemSodium]
        categoryPos = 0 
        for category in allAvalues:
            relevantBoundaryList = allBoundaries[categoryPos]
            categoryPos = categoryPos + 1
            primaryCategoryBoundary = relevantBoundaryList[0] #Boundary realisation
            for boundaryValue in relevantBoundaryList: 
                if category > boundaryValue:
                    primaryCategoryBoundary = boundaryValue
            boundaryHolder.append(primaryCategoryBoundary)

        boundaryDict = {"totalAscore":0,"Energy": 0, "satFats": 0,"totalSugar": 0,"sodium": 0}
        for itemBoundary in boundaryHolder:
            boundaryIndex = boundaryHolder.index(itemBoundary)          #Scoring
            relevantBoundaryList = allBoundaries[boundaryIndex]
            score = relevantBoundaryList.index(itemBoundary)
            fields = ["Energy","satFats","totalSugar","sodium"] 
            relevantField = fields[boundaryIndex]
            boundaryDict[relevantField] = score
        boundaryDict["totalAscore"] = boundaryDict["Energy"] + boundaryDict["satFats"] + boundaryDict["totalSugar"] + boundaryDict["sodium"]

        # C - points

        boundaryHolderC = []
        allBoundariesC = [[0,40,60,60,60,80],[0,0.7,1.4,2.1,2.8,3.5],[0,0.9,1.9,2.8,3.7,4.7],[0,1.6,3.2,4.8,6.4,8.0]]
        allCvalues = [itemFVN,itemFibreNSP,itemFibreAOAC,itemProtein]
        categoryPos = 0
        for cCategory in allCvalues:
            relevantBoundaryListC = allBoundariesC[categoryPos]
            categoryPos = categoryPos + 1
            secondaryCategoryBoundary = relevantBoundaryListC[0] #Boundary realisation
            for boundaryValue in relevantBoundaryListC:
                if cCategory > boundaryValue:
                    secondaryCategoryBoundary = boundaryValue
            boundaryHolderC.append(secondaryCategoryBoundary)
            

        cScoreDict = {"totalCscore":0, "FVN": 0,"fibreNSP": 0, "fibreAOAC": 0,"protein": 0}
        for itemBoundary in boundaryHolderC:
            boundaryIndex = boundaryHolderC.index(itemBoundary)          #Scoring
            relevantBoundaryList = allBoundariesC[boundaryIndex]
            score = relevantBoundaryList.index(itemBoundary)
            fields = ["FVN","fibreNSP","fibreAOAC","protein"] 
            relevantField = fields[boundaryIndex]
            cScoreDict[relevantField] = score
        cScoreDict["totalCscore"] = cScoreDict["FVN"]  + cScoreDict["fibreNSP"] + cScoreDict["fibreAOAC"] + cScoreDict["protein"]
        

        totalItemScore  = 0

        if boundaryDict["totalAscore"] < 11:

                totalItemScore = boundaryDict["totalAscore"] - cScoreDict["totalCscore"]

        else:
                if cScoreDict["FVN"] == 5:
                    totalItemScore = boundaryDict["totalAscore"] - cScoreDict["totalCscore"]

                else:
                    totalItemScore = boundaryDict["totalAscore"] - ((cScoreDict["totalCscore"]) - cScoreDict["protein"])

        print("{0} total nutritional score: {1}".format(itemName, totalItemScore).lower())

        TTApp.scannedItemBreakdown(self, itemName, boundaryDict, cScoreDict) 

        TTApp.userFoodLogAdder(self, itemName, totalItemScore, boundaryDict, cScoreDict)
    

    #QR scan ZBARCAM
    def on_symbols(self,instance,symbols): 
        codeVal = ""
        if not symbols == "":
            for symbol in symbols:
                
                codeVal="QR : {}".format(symbol.data.decode())

                TTApp.scanQR(self,codeVal)
                SC.current="Post Scan Screen" #screen name  
        
TTApp().run() 
