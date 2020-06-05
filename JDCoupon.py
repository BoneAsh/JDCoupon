from requests import session
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
from time import time, sleep
from random import randint
from os import path, popen, remove
from json import loads, dumps
from multiprocessing import Process as process
from matplotlib import pyplot
from PIL import Image as image

class JDCoupon():
    def __init__(self):
        self.__qrcodeName = "扫描登录京东.png"
        self.__qrcodePath = "{0}\\{1}".format(path.abspath(path.dirname(__file__)), self.__qrcodeName)
        self.__session = session()
        self.__session.keep_alive = False
        self.__token = None
        self.__ticket = None
        self.__cookies = None
        self.__cookieFile = "cookie.dat"
        self.__userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"
        # get qrcode
        self.__getQrcodeUrl = "https://qr.m.jd.com/show"
        self.__getQrcodeHeader = {
            "User-Agent": self.__userAgent,
            "Referer": "https://passport.jd.com/new/login.aspx"
        }
        self.__getQrcodeParam = {
            "appid": 133,
            "size": 147,
            "t": None
        }
        # check qrcode
        self.__checkQrcodeUrl = "https://qr.m.jd.com/check"
        self.__checkQrcodeHeader = {
            "User-Agent": self.__userAgent,
            "Referer": "https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fwww.jd.com%2F"
        }
        self.__checkQrcodeParam = {
            "appid": "133",
            "callback": "jQuery{0}".format(randint(1000000, 9999999)),
            "token": None,
            "_": None
        }
        # test ticket
        self.__testTicketUrl = "https://passport.jd.com/uc/qrCodeTicketValidation"
        self.__testTicketHeader = {
            "User-Agent": self.__userAgent,
            "Referer": "https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fwww.jd.com%2F"
        }
        self.__testTicketParam = {
            "t": None
        }
        self.__testTicketResponse = {
            "returnCode": 0,
            "url": "https://www.jd.com/"
        }
        # coupon
        self.__couponTypeList = []
        self.__getCouponTypeUrl = "https://a.jd.com/indexAjax/getCatalogList.html"
        self.__getCouponTypeHeader = {
            "User-Agent": self.__userAgent,
            "Referer": "https://a.jd.com"
        }
        self.__getCouponTypeParam = {
            "callback": "jQuery{0}".format(randint(1000000, 9999999)),
            "_": None
        }
        self.__couponListDic = {}
        self.__getCouponListUrl = "https://a.jd.com/indexAjax/getCouponListByCatalogId.html"
        self.__getCouponListHeader = {
            "User-Agent": self.__userAgent,
            "Referer": None
        }
        self.__getCouponListParam = {
            "callback": "jQuery{0}".format(randint(1000000, 9999999)),
            "catalogId": None,
            "page": None,
            "pageSize": "9",
            "_": None
        }
        self.__getCouponListInterval = 0.1
        self.__getCouponUrl = "https://a.jd.com/indexAjax/getCoupon.html"
        self.__getCouponHeader = {
            "User-Agent": self.__userAgent,
            "Referer": None
        }
        self.__getCouponParam = {
            "callback": "jQuery{0}".format(randint(1000000, 9999999)),
            "key": None,
            "type": "1",
            "_": None
        }
        self.__getCouponInterval = 0.5
        # try cookie
        self.__tryCookieUrl = "https://home.jd.com"
        self.__tryCookieHeader = {
            "User-Agent": self.__userAgent
        }
        self.__tryCookieResponse = "<title>我的京东</title>"
        # other
        self.__printText = None
        self.__cookieIsValid = False
        self.__couponTypeSelected = None
        self.__retryTimes = 3
        # init
        self.__loadCookie()
        self.__tryCookie()

    def __parseJson(self, text):
        return loads(text[text.find("{"):text.rfind("}") + 1])

    def __printOnce(self, text):
        if text != self.__printText:
            self.__printText = text
            print(text)

    def __saveCookie(self):
        with open(self.__cookieFile, "w") as cookieFile:
            cookieFile.write(dumps(dict_from_cookiejar(self.__cookies)))

    def __loadCookie(self):
        try:
            with open(self.__cookieFile, "rb") as cookieFile:
                self.__cookies = cookiejar_from_dict(loads(cookieFile.read()))
        except:
            self.__cookies = None

    def __tryCookie(self):
        if self.__cookies != None:
            self.__session.cookies = self.__cookies
            response = self.__session.get(url=self.__tryCookieUrl, headers=self.__tryCookieHeader)
            if self.__tryCookieResponse in response.text:
                self.__cookieIsValid = True
                print("使用保存的Cookies登陆成功！")
            else:
                self.__session.cookies = cookiejar_from_dict({})

    def __getQrcode(self):
        self.__getQrcodeParam["t"] = str(int(time()) * 1000)
        response = self.__session.get(url=self.__getQrcodeUrl, headers=self.__getQrcodeHeader,
                                      params=self.__getQrcodeParam)
        self.__token = self.__session.cookies.get("wlfstk_smdl")
        return response

    def __createQrcode(self, content):
        with open(self.__qrcodePath, "wb") as qrcode:
            for qrcodeContent in content.iter_content(chunk_size=1024):
                qrcode.write(qrcodeContent)

    def showQrcode(self):
        # system("rundll32.exe shimgvw.dll,ImageView_Fullscreen {0}".format(self.__qrcodePath))
        img = image.open(self.__qrcodePath)
        pyplot.rcParams["toolbar"] = "None"
        pyplot.figure("Scan Qrcode To Login JD", figsize=(4, 4))
        pyplot.axis("off")
        pyplot.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        pyplot.margins(0, 0)
        pyplot.imshow(img)
        pyplot.show()

    def __closeQrcode(self, pid):
        popen("taskkill /pid {0} -t -f".format(pid))
        remove(self.__qrcodePath)

    def __checkQrcode(self):
        self.__checkQrcodeParam["token"] = self.__token
        self.__checkQrcodeParam["_"] = str(int(time()) * 1000)
        response = self.__session.get(url=self.__checkQrcodeUrl, headers=self.__checkQrcodeHeader,
                                      params=self.__checkQrcodeParam)
        responseJson = self.__parseJson(response.text)
        if "ticket" in responseJson:
            self.__ticket = responseJson["ticket"]
            return True
        else:
            self.__printOnce("{0}\n{1}".format(responseJson["msg"], "如果误关二维码界面，请重启本程序！"))
            return False

    def __testTicket(self):
        self.__testTicketParam["t"] = self.__ticket
        response = self.__session.get(url=self.__testTicketUrl, headers=self.__testTicketHeader,
                                      params=self.__testTicketParam)
        if self.__parseJson(response.text) == self.__testTicketResponse:
            self.__cookies = response.cookies
            self.__saveCookie()
            print("登陆成功！")
            return True
        else:
            print(response.text)
            return False

    def login(self):
        if not self.__cookieIsValid:
            self.__createQrcode(self.__getQrcode())
            showQrcodeProcess = process(target=self.showQrcode)
            showQrcodeProcess.start()
            while not self.__checkQrcode():
                sleep(1)
                pass
            self.__closeQrcode(showQrcodeProcess.pid)
            self.__testTicket()

    def __getCouponTypeList(self):
        self.__getCouponTypeParam["_"] = str(int(time()) * 1000)
        response = self.__session.get(url=self.__getCouponTypeUrl, headers=self.__getCouponTypeHeader,
                                      params=self.__getCouponTypeParam)
        responseJson = self.__parseJson(response.text)
        if responseJson["success"] == True:
            self.__couponTypeList = responseJson["catalogList"]

        else:
            print("获取优惠券分类信息失败！")

    def __showCouponTypeList(self):
        print("\n序号\t类别\t")
        print("1\t全部\t")
        for couponType in self.__couponTypeList:
            print("{0}\t{1}\t".format(self.__couponTypeList.index(couponType) + 2, couponType["categoryName"]))
        while True:
            index = input("选择优惠券类别：")
            if 1 <= int(index) <= len(self.__couponTypeList) + 1:
                break
            else:
                print("输入值错误，请重新输入！")
        if int(index) == 1:
            self.__couponTypeSelected = "all"
            print("已选择 全部")
        else:
            self.__couponTypeSelected = self.__couponTypeList[int(index) - 2]
            print("已选择 {0}".format(self.__couponTypeList[int(index) - 2]["categoryName"]))

    def __getCouponList(self):
        self.__getCouponTypeList()
        for couponType in self.__couponTypeList:
            typeId = couponType["categoryId"]
            typeName = couponType["categoryName"]
            self.__couponListDic[typeId] = []
            self.__getCouponListHeader["Referer"] = "https://a.jd.com/?cateId={0}".format(typeId)
            self.__getCouponListParam["catalogId"] = typeId
            self.__getCouponListParam["_"] = str(int(time()) * 1000)
            for page in range(1, 100):
                self.__getCouponListParam["page"] = str(page)
                response = self.__session.get(url=self.__getCouponListUrl, headers=self.__getCouponListHeader,
                                              params=self.__getCouponListParam)
                responseJson = self.__parseJson(response.text)
                if responseJson["totalNum"] == 1:
                    self.__couponListDic[typeId].extend(responseJson["couponList"])
                    print("\r{0}\t 类别已收集优惠券 {1}张              ".format(typeName, len(self.__couponListDic[typeId])),
                          end="")
                else:
                    print()
                    break
                sleep(self.__getCouponListInterval)
        print("收集优惠券完成!")

    def getCoupon(self):
        self.__getCouponList()
        self.__showCouponTypeList()
        if self.__couponTypeSelected == "all":
            for couponTypeItem in self.__couponTypeList:
                self.__getCouponHeader["Referer"] = "https://a.jd.com/?cateId={0}".format(couponTypeItem["categoryId"])
                self.__getCouponParam["_"] = str(int(time()) * 1000)
                num = 1
                for coupon in self.__couponListDic[couponTypeItem["categoryId"]]:
                    self.__getCouponParam["key"] = coupon["key"]
                    retryTimes = 0
                    result = False
                    while retryTimes < self.__retryTimes and not result:
                        try:
                            response = self.__session.get(url=self.__getCouponUrl, headers=self.__getCouponHeader,
                                                          params=self.__getCouponParam)
                            responseJson = self.__parseJson(response.text)
                            print("{0}\t类别第{1}张优惠券领取结果：\t{2}".format(couponTypeItem["categoryName"], num,
                                                                     responseJson["message"]))
                            sleep(self.__getCouponInterval)
                            result = True
                            num += 1
                        except:
                            retryTimes += 1
                            if retryTimes == self.__retryTimes:
                                break

        else:
            self.__getCouponHeader["Referer"] = "https://a.jd.com/?cateId={0}".format(
                self.__couponTypeSelected["categoryId"])
            self.__getCouponParam["_"] = str(int(time()) * 1000)
            num = 1
            for coupon in self.__couponListDic[self.__couponTypeSelected["categoryId"]]:
                self.__getCouponParam["key"] = coupon["key"]
                retryTimes = 0
                result = False
                while retryTimes < self.__retryTimes and not result:
                    try:
                        response = self.__session.get(url=self.__getCouponUrl, headers=self.__getCouponHeader,
                                                      params=self.__getCouponParam)
                        responseJson = self.__parseJson(response.text)
                        print("{0}\t类别第{1}张优惠券领取结果：\t{2}".format(self.__couponTypeSelected["categoryName"], num,
                                                                 responseJson["message"]))
                        sleep(self.__getCouponInterval)
                        result = True
                        num += 1
                    except:
                        retryTimes += 1
                        if retryTimes == self.__retryTimes:
                            break
        print("领取结束！")


if __name__ == "__main__":
    print("京东自动抢优惠券小工具  By BoneAsh")
    jdCoupon = JDCoupon()
    jdCoupon.login()
    jdCoupon.getCoupon()
