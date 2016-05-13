#encoding=utf-8

import sys
import pygame
import wave
import urllib, urllib2, pycurl
import os
import base64
import json

import numpy as np
import time
from pyaudio import PyAudio, paInt16
from datetime import datetime
import re

#define machine params
curAngle = 0;
curOrient = 0;#0代表向左，1代表向右
curRange = 0;



#define params
NUM_SAMPLES = 2000
framerate = 8000
channels = 1
sampwidth = 2
TIME = 10
cuid = "wdsdjiofjdf1205"
asrServer = 'http://vop.baidu.com/server_api'
pruServer = 'http://tsn.baidu.com/text2audio'
robotServer = 'http://www.tuling123.com/openapi/api'






def getResultForOrient(a, encoding="utf-8"):
    if isinstance(a, str):
        a = a.decode(encoding)
    if a == u'左':
        return 0
    elif a == u'右':
        return 1
    else:
        pass

def getResultForDigit(a, encoding="utf-8"):
    refer ={u'零':0, u'一':1, u'二':2, u'三':3, u'四':4, u'五':5, u'六':6, u'七':7, u'八':8, u'九':9, u'十':10, u'百':100, u'千':1000, u'万':10000,
           u'０':0, u'１':1, u'２':2, u'３':3, u'４':4, u'５':5, u'６':6, u'７':7, u'８':8, u'９':9,
                    u'壹':1, u'贰':2, u'叁':3, u'肆':4, u'伍':5, u'陆':6, u'柒':7, u'捌':8, u'玖':9, u'拾':10, u'佰':100, u'仟':1000, u'萬':10000,
           u'亿':100000000}
    if isinstance(a, str):
        a = a.decode(encoding)
    count = 0
    result = 0
    tmp = 0
    Billion = 0
    while count < len(a):
        tmpChr = a[count]
        #print tmpChr
        tmpNum = refer.get(tmpChr, None)
        #如果等于1亿
        if tmpNum == 100000000:
            result = result + tmp
            result = result * tmpNum
            #获得亿以上的数量，将其保存在中间变量Billion中并清空result
            Billion = Billion * 100000000 + result
            result = 0
            tmp = 0
        #如果等于1万
        elif tmpNum == 10000:
            result = result + tmp
            result = result * tmpNum
            tmp = 0
        #如果等于十或者百，千
        elif tmpNum >= 10:
            if tmp == 0:
                tmp = 1
            result = result + tmpNum * tmp
            tmp = 0
        #如果是个位数
        elif tmpNum is not None:
            tmp = tmp * 10 + tmpNum
        count += 1
    result = result + tmp
    result = result + Billion
    return result



def GetToken():
    apiKey = "69U2DGUSlAOdVezitceulpFg"
    secretKey = "5e5b008d0e58f91a55e0f9d02c271dca"
    authUrl = "https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id=" + apiKey + "&client_secret=" + secretKey;
    res = urllib.urlopen(authUrl)
    jsonData = res.read()
    print jsonData
    return json.loads(jsonData)['access_token']

def SaveWaveFile(filename, data):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes("".join(data))
    wf.close()

def DumpRes(buf):
    print buf

def RecordWave():
    pa = PyAudio()
    devinfo = pa.get_device_info_by_index(1)
    '''
    if pa.is_format_supported(8000, input_device=devinfo['index'],
                              input_channels=devinfo['maxInputChannels'],
                              input_format=paInt16):
        print 'Yes'
    '''
    stream = pa.open(format=paInt16, channels=1, rate=framerate, input=True,
                     frames_per_buffer = NUM_SAMPLES)
    saveBuffer = []
    count = 0
    print 'please say anything'
    while count < TIME*2:
        stringAudioData = stream.read(NUM_SAMPLES)
        saveBuffer.append(stringAudioData)
        count += 1
    filename = datetime.now().strftime("2")+".wav"
    SaveWaveFile(filename, saveBuffer)
    print filename, "saved"

def UseCloud(token):
    fp = wave.open(r"2.wav", 'rb')
    nf = fp.getnframes()
    fLen = nf*2
    audioData = fp.readframes(nf)

    
    srvUrl = 'http://vop.baidu.com/server_api' + '?cuid=' + cuid + '&token=' + token
    httpHeader = [
        'Content-Type: audio/pcm; rate=8000',
        'Content-Length: %d' %fLen
    ]

    c = pycurl.Curl()
    c.setopt(pycurl.URL, str(srvUrl))
    c.setopt(c.HTTPHEADER, httpHeader)
    c.setopt(c.POST, 1)
    c.setopt(c.CONNECTTIMEOUT, 30)
    c.setopt(c.TIMEOUT, 30)
    c.setopt(c.WRITEFUNCTION, DumpRes)
    c.setopt(c.POSTFIELDS, audioData)
    c.setopt(c.POSTFIELDSIZE, fLen)
    c.perform()



def BaiduAsr(filename, token):
    with open(filename, 'rb') as f:
        speechData = f.read()
    speechBase64 = base64.b64encode(speechData).decode('utf-8')
    speechLength = len(speechData)
    dataDict = {'format':'wav', 'rate':8000, 'channel':1,
                'cuid':cuid, 'token':token, 'lan':'zh',  'speech':speechBase64, 'len':speechLength}
    jsonData = json.dumps(dataDict).encode('utf-8')
    jsonLength = len(jsonData)
    request = urllib2.Request(url=asrServer)
    request.add_header("Content-Type", "application/json")
    request.add_header("Content-Length", jsonLength)
    fs = urllib2.urlopen(url=request, data=jsonData)
    resultStr = fs.read().decode('utf-8')
    jsonResp = json.loads(resultStr)
    return jsonResp['result'][0].encode('utf-8')


def BaiduPru(text, token):
    if isinstance(text, unicode):
        tex = text.encode('utf-8')
    else:
        tex = text
    lan = "zh"
    tok = token
    ctp = "1"
    vol = "9"
    inputDict = {'tex':tex, 'lan':lan, 'cuid':cuid, 'ctp':ctp, 'tok':tok, 'vol':vol}
    #inputData = "text=" + tex + "&lan=" + lan + "&cuid=" + cuid + "&ctp=" + ctp + "&tok=" + tok
    inputData = urllib.urlencode(inputDict)
    request = urllib2.Request(url=pruServer)
    fs = urllib2.urlopen(url=request, data=inputData)
    temp = fs.read()
    f = open("3.mp3", 'wb')
    f.write(temp)
    f.close()
    play("3.mp3")



def TulingText(text):
    if isinstance(text, unicode):
        text = text.encode('utf-8')
    robotKey = "c0c26f4a1d064d13654048672003eb79"
    loc = "广东省广州市"
    userid = "william1244"
    inputDict = {
            'key': robotKey,
            'info':text,
            'userid':userid,
            'loc':loc
        }
    jsonData = json.dumps(inputDict).encode('utf-8')
    request = urllib2.Request(url=robotServer)
    request.add_header("Content-Type", "application/json")
    fs = urllib2.urlopen(url=request, data=jsonData)
    resultStr = fs.read().decode('utf-8')
    jsonResp = json.loads(resultStr)
    return jsonResp['text']

def play(filename):
    os.system(filename)
    
    os.close(filename)
    #pygame.mixer.init()
    
    #track = pygame.mixer.music.load(filename)
    #pygame.mixer.music.play()
    
def process(cmd):
    
    digit = u"[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u96f6]+"
    orient = u"[\u53f3\u5de6]"
    digitPat = re.compile(digit)
    orientPat = re.compile(orient)

    cmd = unicode(cmd, 'utf-8')

    digitResult = re.search(digitPat, cmd).group()
    oritentResult = re.search(orientPat, cmd).group()
    print type(digitResult)
    cmdObj = {}
    cmdObj['range'] = getResultForDigit(digitResult)
    cmdObj['orient'] = getResultForOrient(oritentResult)
    print cmdObj['range']
    print cmdObj['orient']
        




if __name__ == "__main__":

    
    RecordWave()
    time.sleep(1)
    token = GetToken()
    result = BaiduAsr("2.wav", token)
    #process(result)
    

    #token = GetToken()
    #BaiduPru(u'您好吗', token)
    #play("temp.mp3")
    #print getResultForDigit(u"四十五")
    response = TulingText(result)
    print response
    BaiduPru(response, token)

    
    #print sys.getdefaultencoding()

