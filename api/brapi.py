from pprintpp import pprint
import requests
 
url = "https://brapi.dev/api/quote/PETR4"
#url = "https://brapi.dev/api/quote/PETR4,?&dividends=true&token=f3S9CVBqGnpWkmNHyuyY9G"
params = {
    #'range': '5d',
    #'interval': '1d',
    'fundamental': 'true',
    #'dividends': 'true',
    #'modules': 'balanceSheetHistory',
    'token': 'f3S9CVBqGnpWkmNHyuyY9G',
}
 
response = requests.get(url, params=params)
#response = requests.get(url)
 
if response.status_code == 200:
    data = response.json()
    pprint(data)
else:
    print(f"Request failed with status code {response.status_code}")