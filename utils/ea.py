########### Python 3.2 #############
import http.client, urllib.request, urllib.parse, urllib.error, base64, time, json, ast
from datetime import datetime

headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': 'd53e065901b9410a9ae56900ab16af7e',
}



#try:
lowest = 1
highest = 0;

while(1):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    # print(now)
    params = urllib.parse.urlencode({
            '$filter': 'PointOfConnectionCode eq \'CML0331\'',
            '&filter': 'TradingDate eq datetime'+now+''
    })
    conn = http.client.HTTPSConnection('emi.azure-api.net')
    conn.request("GET", "/real-time-prices/?%s" % params, "{body}", headers)
    response = conn.getresponse()
    # print (response)
    data = response.read()
    json_data = json.loads(data.decode('utf-8'))
    # print('xxxxx')
    # print (data)
    # print('-----')
    # print (json_data)
    # print('-----')
    # print(json_data[0].items())    
    # print('-----')
    value = json_data[0]['DollarsPerMegawattHour']/1000
    if value > highest:
        highest = value
    if value < lowest:
        lowest = value

    print(now,":$",value," per kwh - highest:" , highest, " lowest: ", lowest)



    #print(json_obj['DollarsPerMegawattHour']) # prints the string with 'source_name' key
   
    time.sleep(60)
    conn.close()
# except Exception as e:
#     print("[Errno {0}] {1}".format(e.errno, e.strerror))

####################################