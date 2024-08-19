from pprintpp import pprint
import requests

key = '19551e80c49c486b2e0cc25ef58e291d'

endOfDay = "http://api.marketstack.com/v1/eod?access_key="+key

intraday = "http://api.marketstack.com/v1/intraday?access_key="+key

queryIntraday = {"symbols":"PETR4","interval":"15min"}

queryEndOfDay = {"symbols":"PETR3.BVMF"}

response = requests.get(intraday, params=queryIntraday)

pprint(response.json())