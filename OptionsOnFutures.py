import requests as req
import json
import time


account = 27574
user = 'ALGO_RINALDI'
passw = 'XXXXX'
prop = 'ISV_PBCP'

#result = req.post('https://api.primary.com.ar/auth/getToken', headers={"X-Username":user,"X-Password":passw})
#print(result.headers['X-Auth-Token'])
#authHeader = result.headers['X-Auth-Token'] 

authHeader = '2GzdeEivzvXyA8tE5pa2fdg/C6LVQnGC6nQPpC8zZEg='
print(authHeader)

for i in range(0,1):
    ##Variables
    acumulado_Bid = 0
    acumulado_Off = 0
    bid = 0
    off = 0
    delta_B = 0
    delta_O = 0
    size = 11
    cargaBid = 10
    diffSpread = 1.2
    rushCut = 1
    notFirstTime = False
    cancelOrder = False
    contador = 0
    ticker = 'DOJul18'
    print(ticker)
    tickerCompra = 'DOMar18'
    contadorReq = 0

    ##Market Data Inicial

    ##Code
    while acumulado_Bid < size or acumulado_Off < size:
        contador=contador+1
        if(contador%480==0):
            if cancelOrder == True:
                cancel_bid = req.get('https://api.primary.com.ar/rest/order/cancelById?clOrdId='+ bid_order['order']['clientId'] +'&proprietary='+prop,headers={'X-Auth-Token':authHeader}, timeout=5)
                cancel_off = req.get('https://api.primary.com.ar/rest/order/cancelById?clOrdId='+ off_order['order']['clientId'] +'&proprietary='+prop,headers={'X-Auth-Token':authHeader}, timeout=5)
                cancelOrder = False
                contadorReq = contadorReq + 2
                print('Ordenes de '+ticker+' canceladas, por descanso' + ' La cant de req es de' + str(contadorReq))
            else:

                print('No hay ordenes '+ticker+' para cancelar, descanso' + ' La cant de req es de' + str(contadorReq))
            time.sleep(60)
        else:
            time.sleep(0.5)
        if contador%50 == 0:
            print(contador, contadorReq)
        ##Puntas
        front = json.loads(req.get('https://api.primary.com.ar/rest/marketdata/get?marketId=ROFX&symbol='+tickerCompra+'&entries=BI,OF,LA&depth=2', headers={'X-Auth-Token':authHeader}, timeout=5).text)
        back = json.loads(req.get('https://api.primary.com.ar/rest/marketdata/get?marketId=ROFX&symbol='+ticker+'&entries=BI,OF,LA&depth=2', headers={'X-Auth-Token':authHeader}, timeout=5).text)
        contadorReq = contadorReq + 2
        try:
            spreadFront = front['marketData']['OF'][0]['price'] - front['marketData']['BI'][0]['price']
            spreadBack = back['marketData']['OF'][0]['price'] - back['marketData']['BI'][0]['price']

            if spreadBack > diffSpread*spreadFront and (abs(front['marketData']['OF'][0]['price'] - front['marketData']['LA']['price']) < rushCut) and (abs(front['marketData']['BI'][0]['price'] - front['marketData']['LA']['price']) < rushCut) :

                if notFirstTime == True:
                    ##Offer order
                    orderOff = json.loads(req.get('https://api.primary.com.ar/rest/order/id?clOrdId='+off_order['order']['clientId']+'&proprietary='+prop, headers={'X-Auth-Token':authHeader}, timeout=5).text)
                    refillOff = orderOff['order']['cumQty']
                    ##Bid order
                    orderBid = json.loads(req.get('https://api.primary.com.ar/rest/order/id?clOrdId='+bid_order['order']['clientId']+'&proprietary='+prop, headers={'X-Auth-Token':authHeader}, timeout=5).text)
                    refillBid = orderBid['order']['cumQty'] + cargaBid
                    contadorReq = contadorReq + 2

                    ## Hedging in front
                    if acumulado_Off<orderOff['order']['cumQty']:
                        delta_O = orderOff['order']['cumQty'] - acumulado_Off
                        compra = req.get('https://api.primary.com.ar/rest/order/newSingleOrder?marketId=ROFX&symbol='+ tickerCompra +'&price='+ str(front['marketData']['OF'][0]['price']) +'&orderQty='+str(delta_O)+'&ordType=Limit&side=Buy&timeInForce=Day&account='+str(account)+'&cancelPrevious=true', headers={'X-Auth-Token':authHeader}, timeout=5)
                        acumulado_Off = orderOff['order']['cumQty']
                        contadorReq = contadorReq + 1
                        print('Compra a Off', acumulado_Off,'La cant de req es de', contadorReq)

                    if acumulado_Bid<orderBid['order']['cumQty']:
                        delta_B = orderBid['order']['cumQty'] - acumulado_Bid
                        venta = req.get('https://api.primary.com.ar/rest/order/newSingleOrder?marketId=ROFX&symbol='+ tickerCompra +'&price='+ str(front['marketData']['BI'][0]['price']) +'&orderQty='+str(delta_B)+'&ordType=Limit&side=Sell&timeInForce=Day&account='+str(account)+'&cancelPrevious=true', headers={'X-Auth-Token':authHeader}, timeout=5)
                        acumulado_Bid = orderBid['order']['cumQty']
                        contadorReq = contadorReq + 1
                        print('Venta a Bid', acumulado_Bid,'La cant de req es de', contadorReq)
                else:
                    refillOff = 0
                    refillBid = 0 + cargaBid

                ## Refill/Update
                if off!=str(back['marketData']['OF'][0]['price']) and (size - refillOff)!=0:
                    off = str(round(back['marketData']['OF'][0]['price'] - 0.001, 3))
                    print('Refill Offer ' + str(size - refillOff) + ' La cant de req es de' + str(contadorReq))
                    off_order = json.loads(req.get('https://api.primary.com.ar/rest/order/newSingleOrder?marketId=ROFX&symbol='+ ticker +'&price='+ off +'&orderQty='+str(size - refillOff)+'&ordType=Limit&side=Sell&timeInForce=Day&account='+ str(account) +'&cancelPrevious=true', headers={'X-Auth-Token':authHeader}, timeout=5).text)
                    cancelOrder = True
                    contadorReq = contadorReq + 1

                if bid!=str(back['marketData']['BI'][0]['price']) and (size - refillBid)!=0:
                    bid = str(round(back['marketData']['BI'][0]['price'] + 0.001, 3))
                    print('Refill Bid '+ str(size - refillBid) + ' La cant de req es de' + str(contadorReq))
                    bid_order = json.loads(req.get('https://api.primary.com.ar/rest/order/newSingleOrder?marketId=ROFX&symbol='+ ticker +'&price='+ bid +'&orderQty='+str(size - refillBid)+'&ordType=Limit&side=Buy&timeInForce=Day&account='+ str(account) +'&cancelPrevious=true', headers={'X-Auth-Token':authHeader}, timeout=5).text)
                    cancelOrder = True
                    contadorReq = contadorReq + 1
                    
                notFirstTime = True

            else:
                if cancelOrder == True:
                    cancel_bid = req.get('https://api.primary.com.ar/rest/order/cancelById?clOrdId='+ bid_order['order']['clientId'] +'&proprietary='+prop,headers={'X-Auth-Token':authHeader}, timeout=5)
                    cancel_off = req.get('https://api.primary.com.ar/rest/order/cancelById?clOrdId='+ off_order['order']['clientId'] +'&proprietary='+prop,headers={'X-Auth-Token':authHeader}, timeout=5)
                    cancelOrder = False
                    contadorReq = contadorReq + 2
                    print('Ordenes de '+ticker+' canceladas')
                else:
                    if contador%50 == 0:
                        print('No hay ordenes '+ticker+' para cancelar' + ' La cant de req es de' + str(contadorReq))
                    
        except:
            if cancelOrder == True:
                cancel_bid = req.get('https://api.primary.com.ar/rest/order/cancelById?clOrdId='+ bid_order['order']['clientId'] +'&proprietary='+prop,headers={'X-Auth-Token':authHeader}, timeout=5)
                cancel_off = req.get('https://api.primary.com.ar/rest/order/cancelById?clOrdId='+ off_order['order']['clientId'] +'&proprietary='+prop,headers={'X-Auth-Token':authHeader}, timeout=5)
                cancelOrder = False
                contadorReq = contadorReq + 2
                print('Ordenes de '+ticker+' canceladas, por no cumplimiento' + ' La cant de req es de' + str(contadorReq))
            else:
                if contador%50 == 0:
                        print('No hay ordenes '+ticker+' para cancelar' + ' La cant de req es de' + str(contadorReq))
