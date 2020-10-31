# coding: utf-8

import util
import time
import requests
from selenium import webdriver


if __name__ == '__main__':

    url = "https://mbff.yuegowu.com/customer/addressList"

    payload = {}
    headers = {
        'Host': 'mbff.yuegowu.com',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInppcCI6IkRFRiJ9.eNpkjz1qAzEQhe-i2iwaSTsjuUuZJlV6M5LGsMS7a_bHBIxr38Fg17lDzmOTY0QbCCnSvu97PN5RjXNUawW1r3WNlhDUSjU8qTWgdhrRE61Umsepb2V4zsU1KUCirSETxbEmDWRtRsDgDEZL6s9_Sqmfu-nfwC9_4VYKfFw_vs6f99tl2d4vNpkKqDK68rZkkwxt0_HutX-TbsFZC0byPiAbY63VjqnmEGELiSGWyoF3s2w4Z8mbUYZDk2QszeOpMHnf_9xDckQ2nL4BAAD__w.Bo59vOq7qWAc9HIwmNIO7eV5vDDO-fznrsEeDd7J3Ds'
    }

    response = requests.request("GET", url, headers=headers, data=payload, verify=False)

    print(response.text.encode('utf8'))

    pass
