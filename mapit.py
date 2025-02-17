import datetime, hashlib, hmac, requests
from settings import *
import json
from pymongo import MongoClient
import oracledb
import time
import logging
import argparse
import os

class RequestFailedException(Exception):
    pass

class TokenExpiredException(Exception):
    pass

class Mapit:
  
  def __init__(self, username, password,mappit_identityPoolId, mappit_userPoolId,mappit_userPoolWebClientId, oracle_user, oracle_passoword, oracle_dns, logger, debug=False):
    self.logger = logger
    self.debug = debug
    self.try_count = 0
    self.identityPoolId=mappit_identityPoolId
    self.userPoolId= mappit_userPoolId
    self.userPoolWebClientId= mappit_userPoolWebClientId
    self.authenticationFlowType="USER_PASSWORD_AUTH"
    self.service = 'execute-api'
    self.host = 'core.prod.mapit.me'
    self.region = 'eu-west-1'
    self.url_idp = f"cognito-idp.{self.region}.amazonaws.com"
    self.url_identity = f"cognito-identity.{self.region}.amazonaws.com"
    self.mongoUrl = "mongodb://localhost:27017/"
    self.logger.debug("Mapit initialized with username: %s", username)
    self.username=username
    self.password=password
    self.oracle_user= oracle_user
    self.oracle_password = oracle_password
    self.oracle_dns = oracle_dns
    self.getAllTokens(username, password)

  def storeOracle(self, response):
    self.logger.info("Storing data in Oracle DB: %s", response)
    # Oracle Autonomous DB connection details
    mypath=os.path.dirname(os.path.realpath(__file__))
    connection=oracledb.connect(
     config_dir=f"{mypath}/wallet",
     user=self.oracle_user,
     password=self.oracle_password,
     dsn=self.oracle_dns,
     wallet_location=f"{mypath}/wallet",
     wallet_password=oracle_password)

    print("Successfully connected to Oracle Database")

    cursor = connection.cursor()

    # Create a table
    try:
      cursor.execute('''create table vehicle_data (
          id number generated always as identity,
          lng VARCHAR(255), 
          lat VARCHAR(255), 
          speed VARCHAR(255), 
          status VARCHAR(255), 
          creation_ts timestamp with time zone default current_timestamp,
          primary key (id)
      )''')
    except:
      print("Table already exists")

    # dictionary to tuple conversion
    response = [response]
    # Insert data into the table
    cursor.executemany("INSERT INTO vehicle_data (lng, lat, speed, status) VALUES (:lng, :lat, :speed, :status)", response)

    # Commit the transaction
    connection.commit()

    print("Data stored in Oracle DB successfully")

  def storeMongo(self, response):
    self.logger.debug("Storing data in MongoDB: %s", response)
    to_store = response
    to_store["datetime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Connect to MongoDB
    client = MongoClient(self.mongoUrl)
    db = client['mapit']
    collection = db['speed']

  # Store the response in MongoDB
    collection.insert_one(to_store)

    print("Data stored in MongoDB successfully")
    self.logger.debug("Data stored in MongoDB successfully")

  def sign(self, key, msg):
    self.logger.debug("Signing message: %s", msg)
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

  def getSignatureKey(self, key, dateStamp):
    self.logger.debug("Getting signature key for date: %s", dateStamp)
    kDate = self.sign(('AWS4' + key).encode('utf-8'), dateStamp)
    kRegion = self.sign(kDate, self.region)
    kService = self.sign(kRegion, self.service)
    kSigning = self.sign(kService, 'aws4_request')
    return kSigning

  def createAuthValue(self, method, spacename, canonical_querystring='' ):
    self.logger.debug("Creating auth value for method: %s, spacename: %s", method, spacename)
    t = datetime.datetime.now()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d')
    canonical_headers = 'accept:' + 'application/json' + '\n' 'host:' + self.host + '\n' + 'x-amz-date:' + amz_date + '\n'
    signed_headers = 'accept;host;x-amz-date'
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = datestamp + '/' + self.region + '/' + self.service + '/' + 'aws4_request'
    payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()
    canonical_request = method + '\n' + spacename + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
    string_to_sign = algorithm + '\n' + amz_date + '\n' + credential_scope + '\n' + hashlib.sha256(
        canonical_request.encode('utf-8')).hexdigest()
    signing_key = self.getSignatureKey(self.secret_key, datestamp)
    signature = hmac.new(signing_key, (string_to_sign).encode("utf-8"), hashlib.sha256).hexdigest()
    Auth_value = f"AWS4-HMAC-SHA256 Credential={self.access_key}/{datestamp}/{self.region}/{self.service}/aws4_request, SignedHeaders=accept;host;x-amz-date Signature={signature}"
    return Auth_value, amz_date

  def sendRequest(self, url, headers, contentype='application/x-amz-json-1.1', method='POST', payload=None, url_type='https://'):
    self.logger.debug("Sending request to URL: %s with headers: %s and payload: %s", url, headers, payload)
    headers['content-type'] = contentype
    response = requests.request(method, url_type+url, headers=headers, json=payload)
    ## Check if the response is 200
    if self.debug:
      if self.try_count > 10:
        self.try_count = 0
        raise TokenExpiredException("Token expired")
      self.try_count += 1
    if response.status_code == 403:
      print("Token expired. Getting new tokens")
      raise TokenExpiredException("Token expired")
    if response.status_code != 200:
      print(f"Error on {url}: ", response.status_code)
      print(response.text)
      raise RequestFailedException(f"Error on request: {response.status_code}")
    return response.json()
  
  def getTokens(self, username, password):
    self.logger.debug("Getting tokens for username: %s", username)
    payload = { "AuthFlow": self.authenticationFlowType,
                "ClientId": self.userPoolWebClientId,
                "AuthParameters": {"USERNAME": username,"PASSWORD": password},    
                "ClientMetadata": {}}
    headers = {'x-amz-target': 'AWSCognitoIdentityProviderService.InitiateAuth'}

    response = self.sendRequest(self.url_idp, headers, payload=payload)
    self.idToken = response['AuthenticationResult']['IdToken']
    self.accessToken = response['AuthenticationResult']['AccessToken']
    return response
     
  def getIdentity(self):
    self.logger.debug("Getting identity")
    payload = {  
      "IdentityPoolId": self.identityPoolId, 
      "Logins":{f"{self.url_idp}/{self.userPoolId}": self.idToken }}
    headers = {'x-amz-target': 'AWSCognitoIdentityService.GetId'}

    response = self.sendRequest(self.url_identity, headers, payload=payload)
    self.identityId = response['IdentityId']
    return response
  
  def getCredentials(self):
    self.logger.debug("Getting credentials")
    payload = {"IdentityId":self.identityId,
               "Logins":{f"{self.url_idp}/{self.userPoolId}":self.idToken}}
    headers = {'x-amz-target': 'AWSCognitoIdentityService.GetCredentialsForIdentity'}

    response = self.sendRequest(self.url_identity, headers, payload=payload)
    self.access_key = response['Credentials']['AccessKeyId']
    self.secret_key = response['Credentials']['SecretKey']
    self.sessionToken = response['Credentials']['SessionToken']
    return response
  
  def getUser(self):
    self.logger.debug("Getting user information")
    payload = {"AccessToken":self.accessToken}
    headers = {'x-amz-target': 'AWSCognitoIdentityProviderService.GetUser'}

    user = self.sendRequest(self.url_idp, headers, payload=payload)
    return user

  def authorizedRequest(self, spacename, canonical_querystring='', method='GET', payload=None):
    self.logger.debug("Making authorized request to spacename: %s", spacename)
    Auth_value, amz_date = self.createAuthValue(method, spacename, canonical_querystring)
    url = self.host + spacename + '?' + canonical_querystring
    headers = {
        'host': self.host,
        'Accept': 'application/json',
        'X-Amz-Security-Token': self.sessionToken,
        'X-Id-Token': self.idToken,
        'x-amz-date': amz_date,
        'Authorization': Auth_value,
    }
    return self.sendRequest(url, headers, method=method, payload=payload)
  
  def getId(self, account):
    self.logger.debug("Getting ID for account: %s", account)
    spacename = '/v1/accounts'
    canonical_querystring = 'email=' + account

    response = self.authorizedRequest(spacename, canonical_querystring)
    self.id = response[0]['id']
    return response
  
  def getSummary(self):
    self.logger.debug("Getting summary for ID: %s", self.id)
    spacename = '/v1/accounts/' + self.id + '/summary'

    try:
      response = self.authorizedRequest(spacename)
    except TokenExpiredException:
      self.logger.info("Token expired, refreshing tokens")
      self.generateTokens(self.username, self.password)
      self.store_tokens_to_file()
      response = self.authorizedRequest(spacename)
      self.logger.debug("Token refreshed")
    return response
  
  def generateTokens(self, username, password):
    self.TokensResponse = self.getTokens(username, password)
    self.IdentityResponse = self.getIdentity()
    self.CredentialsResponse = self.getCredentials()
    self.IdResponse = self.getId(username.replace('@', '%40')) 
  
  def getAllTokens(self, username, password):
    self.logger.debug("Getting all tokens for username: %s", username)
    if os.path.exists('tokens.json'):
      self.load_tokens_from_file()
    else:
      self.generateTokens(username, password)
      self.store_tokens_to_file()

  def store_tokens_to_file(self):
    tokens = {
      'access_key': self.access_key,
      'secret_key': self.secret_key,
      'session_token': self.sessionToken,
      'identity_id': self.identityId,
      'id_token': self.idToken,
      'access_token': self.accessToken,
      'id': self.id
    }
    with open('tokens.json', 'w') as f:
      json.dump(tokens, f)
    self.logger.debug("Tokens stored to file successfully")

  def load_tokens_from_file(self):
    with open('tokens.json', 'r') as f:
      tokens = json.load(f)
    self.access_key = tokens['access_key']
    self.secret_key = tokens['secret_key']
    self.sessionToken = tokens['session_token']
    self.identityId = tokens['identity_id']
    self.idToken = tokens['id_token']
    self.accessToken = tokens['access_token']
    self.id = tokens['id']
    self.logger.debug("Tokens loaded from file successfully")

  
  def checkStatus(self):
    self.logger.debug("Checking if moving")
    response = self.getSummary()
    lng = response['vehicles'][0]['device']['state']['lng']
    lat = response['vehicles'][0]['device']['state']['lat']
    speed = response['vehicles'][0]['device']['state']['speed']
    status = response['vehicles'][0]['device']['state']['status']
    return lng, lat, speed, status, response


def setup_logging(level=logging.INFO):
    logging.basicConfig(level=level,
              format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
              datefmt='%H:%M:%S %d-%m-%Y')
    logger = logging.getLogger()
    return logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mapit script')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--continuous', action='store_true', help='all ways checker time')
    parser.add_argument('--checker', action='store_true', help='only stores if changes in latitude and longitude')
    parser.add_argument('--sleep_time', type=int, default=1, help='Sleep time under checker mode')
    args = parser.parse_args()

    logger = setup_logging(logging.DEBUG if args.debug else logging.INFO)
    logger.debug("Starting main process")
    
    mapit = Mapit(mappit_username, mappit_password, mappit_identityPoolId,mappit_userPoolId, mappit_userPoolWebClientId,  oracle_user, oracle_password, oracle_dns, logger=logger, debug=args.debug)
    if args.continuous:
      second = 0
      try:
        while True:
          lng, lat, speed, status, response = mapit.checkStatus()
          logger.info(f"Summary retrieved on {second}: {lng}, {lat}, {status} at {speed} km/h")
          second += 5
          time.sleep(5)
      except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    elif args.checker:
      try:
        last_lng, last_lat = 0,0
        while True:
          #lng, lat, speed, status, response = mapit.checkStatus()
          #if status == "AT_REST":
          #if status == "MOVING":
          #  logger.info(f"Vehicle is at rest: {lng}, {lat}")
          #  mapit.storeOracle({"lng": lng, "lat": lat, "speed": speed, "status": status})
          #  exit(0)
          #else:
            #while status == "AT_REST":
            #while status == "MOVING":
          lng, lat, speed, status, response = mapit.checkStatus()
          if (lng,lat) != (last_lng, last_lat): 
            logger.info(f"Vehicle is moving: {lng}, {lat} at {speed} km/h ({last_lng}, {last_lat})")
            mapit.storeOracle({"lng": lng, "lat": lat, "speed": speed, "status": status})
            last_lng, last_lat = lng, lat
          time.sleep(sleep_time)
      except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    else:
      response = mapit.getSummary()
      logger.info(json.dumps(response, indent=2))
