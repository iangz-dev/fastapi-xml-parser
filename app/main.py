#   PriceController XML
#   v:  1.0.2402.2400
#   Ian Gabriel Zayas

_version="1.0.2402.2400"
# Necessary libraries
from fastapi import FastAPI, status
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from http.client import HTTPException
import datetime
import xml.etree.ElementTree as ET
import glob
import logging

# Logging configuration
logging.basicConfig(filename='app.log', level=logging.INFO,format='%(asctime)s:%(levelname)s:%(message)s')
ET.register_namespace('',"urn:pos-schema")

# BODY request xml-price-update
class PriceModRequest(BaseModel):
    SKU: int
    precio: float

# Here comes the app
app = FastAPI()
load_dotenv()
ruta_volumen=os.getenv("CIFS_PATH_PRICING")
pricing_directory = "/productpricing"

# Health
@app.get("/", tags=["Salud"])
async def root():
    return {"status": f"service available.", "environment": "localhost","volume":f"{ruta_volumen}", "version:":_version}

# Getting the newest XML file
@app.get("/get-latest-xmlfile", tags=["Newest XML file"])
def obtenerPath():
    files_in_directory = glob.glob(os.path.join(pricing_directory, "*.xml"))
    if not files_in_directory:
        return {f"Empty folder - path: {pricing_directory}"}
    else:
        latest_pricing_xml = max(files_in_directory, key=os.path.getctime)
        return {"latest_pricing_xml": latest_pricing_xml}

# Modifying the latest XML file and creating a new one with a unique name
@app.put("/xml-price-update/", tags=["XML Controller"])
def priceModXML(params: PriceModRequest):
    filesInDirectory = glob.glob(os.path.join(pricing_directory, "*.xml"))
    latestPricingXML = max(filesInDirectory, key=os.path.getctime)
    logging.info("Most recent file: "+latestPricingXML)
    tree = ET.parse(latestPricingXML)
    root = tree.getroot()
    logging.info("XML open success.")
    priceXPath="./{urn:pos-schema}Product/[@productCode="+"'"+str(params.SKU)+"'"+"]/{urn:pos-schema}PriceList/{urn:pos-schema}Currency/{urn:pos-schema}Pricing"
    root.find(priceXPath).attrib['catalogPrice']=str(params.precio)
    logging.info("Price modification success. {SKU: "+str(params.SKU)+", EATIN catalogPrice: "+str(params.precio)+"}")
    utc_datetime = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    outputFileName = f"{pricing_directory}/SIA_productPricing-{utc_datetime}.xml"
    tree.write(outputFileName,encoding='UTF-8',xml_declaration=True)
    logging.info("New file created: "+outputFileName)
    return{"Update price. {SKU: "+str(params.SKU)+", EATIN catalogPrice: "+str(params.precio)+"}"}