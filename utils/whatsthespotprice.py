import http.client, urllib.request, urllib.parse, urllib.error, base64, time, json, ast, datetime, math, keys


import logging
logging.basicConfig(filename='io.log', level=logging.INFO, format='%(asctime)s %(message)s')

headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': keys.OCP_APIM_SUBSCRIPTION_KEY,
}


def get_spot_price():
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")

    # print(now)
    params = urllib.parse.urlencode({
            '$filter': 'PointOfConnectionCode eq \'CML0331\'',
            '&filter': 'TradingDate eq datetime'+now+''
    })
    conn = http.client.HTTPSConnection('emi.azure-api.net')
    conn.request("GET", "/real-time-prices/?%s" % params, "{body}", headers)
    response = conn.getresponse()
    data = response.read()
    json_data = json.loads(data.decode('utf-8'))
    value = json_data[0]['DollarsPerMegawattHour']/1000
    
    logging.info("SPOT PRICE:$%s" ,value)
    conn.close()
    return value


while(1):
    print(get_spot_price())
    time.sleep(60)