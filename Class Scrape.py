import pandas as pd
import random
import time
import numpy as np
import psycopg2
import ast
import numpy as np

from datetime import datetime
from datetime import date

from sqlalchemy import create_engine
from selenium import webdriver
from fake_useragent import UserAgent

class get_idealista_structure(object):
    
    fake_user_counter = 0 # counter used to chage the user agent
    df_floors_url = pd.DataFrame() # dataframe with all floors in the minor unit
    
    
    def __init__(self):
        
        self._driver =  webdriver.Chrome()
    
    # get fake user agent    
    def fake_user_agent(self):
        # we change the user agent a we realise some adjust to avoid been detected
        self._driver.close()
        options = webdriver.ChromeOptions()   
        options.add_argument("window-size=1420,1080")
        options.add_argument("start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # added after read the sctackoverflow question
        options.add_argument('--disable-extensions')
        options.add_argument('--profile-directory=Default')
        options.add_argument("--incognito")
        options.add_argument("--disable-plugins-discovery");
        # added after read the sctackoverflow question
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # Get a fakeuser agent
        ua = UserAgent()
        user_agent = ua['google chrome']
        print(user_agent)
        options.add_argument(f'user-agent={user_agent}')
         # disable images
#         chrome_prefs = {}
#         options.experimental_options["prefs"] = chrome_prefs
#         chrome_prefs["profile.default_content_settings"] = {"images": 2}
#         chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
        # initialize the webdriver with the new options
        self._driver = webdriver.Chrome(chrome_options=options)
        time.sleep(4.5 + random.random())
        self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._driver.delete_all_cookies() 
    
    # try several user agent until get one that works    
    def rotate_fake_agent(self, url):
        
        get_idealista_structure.fake_user_counter = random.uniform(0,22)
        for i in range(0,25):
            try:
                self._driver.find_element_by_xpath('//*[@id="copyright"]').text[:17]
                print("pillado")
                self.fake_user_agent()
                time.sleep( random.uniform(random.uniform(0,5),random.uniform(15,25)) )
                self._driver.get(url) # use get an not get.page to avoid create an infinite loop
                self._driver.find_element_by_xpath('//*[@id="copyright"]').text[:17]
            except:
                break    
    
    # call different strategies to avoid been detected
    def avoid_been_detected(self):
        
        number = random.uniform(0,100)
        # Random Sleep
        if number>20:
            low , up = random.choice( [[2,3], [3,4], [2,4], [1,5], [3,5], [2,5] ] )
            time.sleep(random.uniform(low, up) + random.random())
        # Quick Sleep
        elif number<20:
            time.sleep(2.5 + random.random()) 
        # change user agent    
        if get_idealista_structure.fake_user_counter >50 :
            print("cambio")
            self.fake_user_agent()
            get_idealista_structure.fake_user_counter = random.uniform(0,18)
            
        get_idealista_structure.fake_user_counter +=1
    
    # we use this function to follow any url
    def get_page(self, url):
        #self._driver.execute_script("window.scrollTo(0, 5);")
        # before follow the url avoid been detected
        self.avoid_been_detected()
        self._driver.get(url)
        # test (try) if the captcha has appeared
        try: 
            self._driver.find_element_by_xpath('//*[@id="copyright"]').text[:17]
            self.rotate_fake_agent(url)
            self._driver.find_element_by_xpath('//*[@id="copyright"]').text[:17]
            input("Press Enter to continue...")
        except:
            pass
    
    # get the main regions in the province
    def get_province_regions(self, province_name, province_url):
#                                                                     provinces_excluded
        # before follow the url avoid been detected
        self.get_page(province_url)
        regions_url = self._driver.find_elements_by_xpath('//*[@id="map-mapping"]/area')
        
        # dict where stored all the regions in the province
        regions_dict = {}
        for region in range( 0,len(regions_url) ):
            region_url = self._driver.find_element_by_xpath('//*[@id="map-mapping"]/area[%s]' % (region + 1) ).get_property("href")
            region_name = region_url[:-5] #[:-5] we eliminate the term  /mapa from the url
            region_name = region_name[-1* region_name[::-1].find("/")  : ] # last part of the url is the name of the region
            # if the region has not link (not flats or houses) but appears in the map of the provinces continue
            if region_url == "" or  region_url == [] or region_url == np.nan:
                continue
            # if the name of the region (key) appears in the url we add the information into the dict
            if province_name in region_url:                
                regions_dict.update( { region_name : [region_url] } )
                
#         # Drop references of other provinces (know this part can be eliminated)
#         for key_avoid in regions_dict.copy():
#             for province in provinces_excluded:
#                 if province == key_avoid or "provincia" in key_avoid :
#                     del regions_dict[key_avoid]
#                     break

#         regions_avoid = list(regions_dict.keys()) # + provinces_excluded
#         regions_dict = get_regions_subelements(self, regions_dict, regions_avoid) 

            get_idealista_structure.df_floors_url= pd.DataFrame() # initialize / empty the values of the dataframe

        return regions_dict
    
    # follow the link of the main regions until arrive to the floors pool
    def get_regions_subelements (self, regions_dict , regions_avoid, province_name) :

        for key in regions_dict:

            # get the page where we test (try) if the captcha has appeared
            self.get_page(regions_dict[key][0])        
            sub_regions_url = self._driver.find_elements_by_xpath('//*[@id="map-mapping"]/area')
            
            # We see if there are more subdivision or not if not more subdivision we are in the pool floors and we get all url floors         
            if sub_regions_url==[]:
                self.get_all_url_floors(houses_flats_url = regions_dict[key][0], minor_unit =key, date = date.today()) 
                # get all floors url   
            else:
                # dict where store all subregions of the regions in the province
                sub_regions_dict = {}    
                for sub_region in range( 0,len(sub_regions_url) ):
                    sub_region_url = self._driver.find_element_by_xpath('//*[@id="map-mapping"]/area[%s]' % (sub_region + 1) ).get_property("href")
                    sub_region_name = sub_region_url[:-5] #[:-5] we eliminate the term  /mapa from the url
                    sub_region_name = sub_region_name[-1* sub_region_name[::-1].find("/")  : ] # last part of the url is the name of the region
                    # if the subregion has not link (not flats or houses) but appears in the map continue
                    if sub_region_url == "" or  sub_region_url == [] or sub_region_url == np.nan:
                        continue
                    # if the name of the region (key) appears in a specific postion in url we add the information into the dict
                    if key in sub_region_url.split("/")[-3:] :                
                        sub_regions_dict.update( { sub_region_name : [sub_region_url] } )
                    # elif we test if this region have been analyze before and we test if the name of the province is in url
                    elif (sub_region_name in regions_avoid) == False and province_name in sub_region_url.split("/")[-3:]:
                        sub_regions_dict.update( { sub_region_name : [sub_region_url] } )  
                    # idealista errors as Mairena del Aljafare
                    elif sub_region_url.split("/")[-3].split("-")[0] == key.split("-")[0] and sub_region_name != province_name and  sub_region_url.split("/")[-3].split("-")>2:
                        sub_regions_dict.update( { sub_region_name : [sub_region_url] } )

                # Drop references of other provinces, regions or subregions that have been included or should not been included   
#                 for key_avoid in sub_regions_dict.copy():
#                     for region in regions_avoid:
#                         if region == key_avoid or "provincia" in key_avoid or region in key_avoid:
#                             del sub_regions_dict[key_avoid]
#                             break

                regions_avoid = list(sub_regions_dict.keys()) + regions_avoid
                regions_dict[key] = [ regions_dict[key][0], 
                                             self.get_regions_subelements(sub_regions_dict, regions_avoid, province_name )] 
            
        return regions_dict  
    
    # get all url in each page of each floors pool
    def get_all_url_floors(self, houses_flats_url,minor_unit, date ):
        
        # recordar que esta función se ejecutrá cuando estamos ya en la pagina dnde se encuentran los pisos para comprar
        types_transactions = {
            "comprar": "venta-viviendas",
         "alquiler" : "alquiler-viviendas",
         "compartir" : "alquiler-habitacion",
         "promociones_inmobiliarias" : "venta-obranueva",
        }
        
        # transaction =  Comprar / Alquilar / compartir/ Obra nueva
        # Recordar que al llamar a la funcion ya estamos en la página de compra vivienda segunda mano
        for transaction in types_transactions:
            if transaction != "comprar": # evitar hacer un llamada de más ya que nos econtrmaos en la compra de segunda mano
                    self.get_page( houses_flats_url.replace("venta-viviendas",types_transactions[transaction]) )
            transaction_name = transaction
            
            # vamos cogiendo todos los url de los pisos hasta que no hay "siguiente" en la paginación
            while True:  
                # número de la página en la que nos encontramos
                try:
                    n_page = self._driver.find_element_by_xpath('//*[@id="main-content"]/section/div/ul/li[@class="selected"]').text
                except:
                    n_page = "1"
                # Para controlar la posición de cada piso en la página web
                n_floor_inpage = 0
                
                # todos los pisos que hay en la página y vamos cogiendo los url uno por uno meiante el bucle
                pool_floors = self._driver.find_elements_by_xpath('//*[@id="main-content"]/section/article') 
                for floor in range(0, len(pool_floors)):
                    # obtener el url_floor, el precio y si el anuncio pertenece a una inmobiliaria
                    path = [ '//*[@id="main-content"]/section/article[%s]/div/a' % (floor + 1), ]
                    try: # a veces en vez de una piso hay un anuncio
                        url_floor= self._driver.find_element_by_xpath( '//*[@id="main-content"]/section/article[%s]/div/a' % (floor + 1)).get_property("href")
                        price = self._driver.find_element_by_xpath('//*[@id="main-content"]/section/article[%s]/div/div[1]/span[1]' % (floor + 1) ).text[:-1].replace(".", "")
                        telephone=self._driver.find_element_by_xpath('//*[@id="main-content"]/section/article[%s]/div/div[3]/span' % (floor + 1)).text
                        n_floor_inpage += 1
                        # Vemos si el piso en anuncio pertenece a una inmobiliaria si esta destacado y si es de obra nueva
                        try:
                            inmobiliaria = self._driver.find_element_by_xpath('//*[@id="main-content"]/section/article[%s]/div/picture/a' % (floor + 1)).get_property("title")
                        except: 
                            inmobiliaria = ""
                        try: #destacado
                            attribute_1 = self._driver.find_element_by_xpath('//*[@id="main-content"]/section/article[%s]/picture/span'%(floor + 1)).text
                        except:
                            attribute_1 = ""
                        try: # obra nueva
                            attribute_2 = self._driver.find_element_by_xpath('//*[@id="main-content"]/section/article[%s]/picture/div[3]/div'%(floor+1)).text
                        except: 
                            attribute_2 = ""
                            
                    except: 
                        continue
                    # creamos un dict con los datos y lo unimos aun dataframe donde estarán todos los pisos
                    dict_data = {url_floor.split("/")[-2]: [url_floor.split("/")[-2], minor_unit,  houses_flats_url, transaction_name, 
                                                            url_floor, date, price, inmobiliaria, telephone,
                                                            n_page, n_floor_inpage, attribute_1, attribute_2, 'No'] } #
                    # AQUI NOMBRE DE LA COLUMNA DE LA TABLA historical_floors_url
                    columns = ["floor_id", "minor_unit_territory", "houses_flats_url_pool", "idealista_transaction_group", 
                               "url_floor_info", "date", "price", "seller_company_logoname", "seller_number" ,"n_page", 
                               "n_floor_in_page", "attribute_1", "attribute_2", 'info_floor_images' ]
                    dict_data = pd.DataFrame.from_dict(dict_data, orient ="index", columns = columns)
                    get_idealista_structure.df_floors_url= pd.concat([get_idealista_structure.df_floors_url, dict_data], ignore_index=True)

                # Ver si hay que romper el bucle while
                # numeros de url en paginación al final de la página
                n_pages = self._driver.find_elements_by_xpath('//*[@id="main-content"]/section/div/ul/li')
                # si no hay siguiente o solo hay una página en el tipo de transacción rompemos el bucle
                try:
                    if self._driver.find_element_by_xpath('//*[@id="main-content"]/section/div/ul/li[%s]' % len(n_pages) ).text == "Siguiente":
                        url_next_page = self._driver.find_element_by_xpath('//*[@id="main-content"]/section/div/ul/li[%s]/a' % len(n_pages) ).get_property("href")
                        self.get_page(url_next_page)
                    else:
                        break
                except:
                    break
                    
    
    
    def first_floor_scrap(self, floor_url, floor_id, date):
        credentials = ast.literal_eval(open(r"C:\Users\pablo\OneDrive - unizar.es\Python\credentials.txt", "r").read())
        self.get_page(floor_url)       
        # if try okey the advert has disappeared
        try:
            date_disappear = self._driver.find_element_by_xpath('//*[@id="main"]/div/div/main/section/div/p[1]').text
            date_disappear = datetime.strptime(date_disappear[-11:-1], '%d/%m/%Y' ).strftime("%Y/%m/%d")
            self.advert_dissappear_todb(floor_url, floor_id, date, date_disappear, credentials)
            
        except:                 
            self.get_idealista_floor_information(floor_url, floor_id, date)
            self.get_idealista_floor_images(floor_url, floor_id)
                    
    def get_idealista_floor_information (self, floor_url, floor_id, date):

        info_features = ["meters", "rooms", "floor_height", "garage"]
        dict_info_components = {'floor_idealista_id' : floor_id, 'floor_idealista_url' : floor_url, 'date': date}

        for feature in range(1, len(info_features)+1):
            try:
                element=self._driver.find_element_by_xpath('/html/body/div[1]/div/div/main/section[1]/div[5]/span[%s]/span' % (feature,) ).get_attribute("innerHTML")
            except:
                element = ""
            # add the components into dict
            dict_info_components.update({info_features[feature-1]: element })

        # details of the property
        details_name = ["basic_features", "building", "equipment"]
        details_path = ['//*[@id="details"]/div/div[1]/div/ul','//*[@id="details"]/div/div[2]/div[1]/ul','//*[@id="details"]/div/div[2]/div[2]/ul']

        for name, path in zip(details_name, details_path):
            try:
                element = self._driver.find_element_by_xpath(path).text.split("\n")
            except:
                element = ""

            dict_info_components.update({name: element })
            
        # Hay veces que el texto es muy largo y aparece de distinta forma
        try:
            text_description = self._driver.find_element_by_xpath('//*[@id="main"]/div/main/section[1]/div[8]/div[2]/div').text.replace("\n", "")
        except:
            text_description = self._driver.find_element_by_xpath('//*[@id="main"]/div/main/section[1]/div[8]/div[2]/div').text.replace("\n", "")
            
        location = self._driver.find_element_by_xpath('//*[@id="headerMap"]/ul').text.replace("\n", ", ")
        seller_name = self._driver.find_element_by_xpath('//*[@id="side-content"]/section/div/div[6]/div[1]/span').text
        seller_number = self._driver.find_element_by_xpath('//*[@id="side-content"]/section/div/div[5]/div/div/div/p').text
        last_update = self._driver.find_element_by_xpath('//*[@id="stats"]/p').text
        dict_info_components.update({"location":location, "text_description": text_description, "seller_name" : seller_name,
                                     "seller_number" : seller_number, "last_update": last_update, 
                                     'advertiser_removed': np.nan })
        df_info_components = pd.DataFrame.from_dict(dict_info_components,orient='index').T
        
        engine = create_engine(credentials['sqlalchemy'][0] + 'idealista_floors' )
        try:
            df_info_components.to_sql('idealista_floors_information', engine, if_exists = "append",  method ='multi', index=False)
        except:
            time.sleep(20)
            df_info_components.to_sql('idealista_floors_information', engine, if_exists = "append",  method ='multi', index=False)
            
    def get_idealista_floor_images(self, floor_url, floor_id):

        import urllib.request
        from sqlalchemy.types import LargeBinary
        
        df_images = pd.DataFrame() # df to store the information
        n_images_elements = self._driver.find_elements_by_xpath('/html/body/div[1]/div/div/main/div[2]/div/div')

        for n_image in range(1 , len( n_images_elements  ) + 1 ):
            # the xpath of the fourth image change a litlle a cause of the "see more images"
            try: # xpath of horizontal images
                xpath = '/html/body/div[1]/div/div/main/div[2]/div/div[%s]/img' % n_image 
                xpath = xpath if n_image != 4 else xpath.replace('/img', '/div/img') # image 4 has special characteristics
                self._driver.find_element_by_xpath(xpath).get_property("title")
            except: 
                try:
                    # xpath of vertical images
                    xpath = '/html/body/div[1]/div/div/main/div[2]/div/div[%s]/div/img' % n_image
                    xpath = xpath if n_image != 4 else xpath.replace('/img', '/div/img')
                    self._driver.find_element_by_xpath(xpath).get_property("title")
                except:
                    continue

            # get the elements of each image that we are interested in
            image_title       =   self._driver.find_element_by_xpath(xpath).get_property("title")
            image_url         =   self._driver.find_element_by_xpath(xpath).get_attribute("data-ondemand-img")
            # the image is visible or you need to click "see more images"
            hide_show         =   self._driver.find_element_by_xpath(xpath).get_attribute("class") 
            image_position    =   self._driver.find_element_by_xpath(xpath).get_attribute("data-relative-position")
            orientation       =   self._driver.find_element_by_xpath(xpath).get_attribute("data-orientation")
            # the name that appears when you put the cursor on the image, for example "cocina"
            image_keyword_tag =   self._driver.find_element_by_xpath(xpath.replace("img", "span") ).get_attribute("innerHTML")

            img= urllib.request.urlopen(image_url).read() #bytes


            info_image = {'floor_idealista_id' : floor_id, 'floor_idealista_url' : floor_url, 
                          'image_position' : image_position, 'image_keyword_tag': image_keyword_tag, 'image_url' : image_url, 
                          'hide_show' : hide_show, 'orientation' : orientation, 'image_title' : image_title, 
                         'binary_image_file' : img}

            df_images = pd.concat([df_images, pd.DataFrame(info_image, index = [0] ) ], axis = 0)
        
        engine = create_engine(credentials['sqlalchemy'][0] + 'idealista_floors' )
        try:
            df_images.to_sql("idealista_floor_images", engine, if_exists = "append", dtype = {'binary_image_file' : LargeBinary}, 
                         method ='multi', index=False)
        except:
            time.sleep(20)
            df_images.to_sql("idealista_floor_images", engine, if_exists = "append", dtype = {'binary_image_file' : LargeBinary}, 
                         method ='multi', index=False)
    
    def advert_dissappear_todb(self, floor_url, floor_id, date, date_disappear, credentials):

        try:
            conn = psycopg2.connect(dbname="idealista_floors", user=credentials['psycopg2'][0], 
                 password=credentials['psycopg2'][1], host=credentials['psycopg2'][2], port =credentials['psycopg2'][3])
            cur = conn.cursor()
            cur.execute('''
            INSERT INTO idealista_floors_information(floor_idealista_url, floor_idealista_id, date , advertiser_removed)
            VALUES (%s)
            ''' % ("'" + floor_url +"','"+ floor_id + "','" + date.strftime("%Y/%m/%d") + "','" + date_disappear + "'"))
            conn.commit()
            conn.close()
        except:
            time.sleep(10)
            conn = psycopg2.connect(dbname="idealista_floors", user=credentials['psycopg2'][0], 
                 password=credentials['psycopg2'][1], host=credentials['psycopg2'][2], port =credentials['psycopg2'][3])
            cur = conn.cursor()
            cur.execute('''
            INSERT INTO idealista_floors_information(floor_idealista_url, floor_idealista_id, date , advertiser_removed)
            VALUES (%s)
            ''' % ("'" + floor_url +"','"+ floor_id + "','" + date.strftime("%Y/%m/%d") + "','" + date_disappear + "'"))
            conn.commit()
            conn.close()
