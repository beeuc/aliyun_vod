# aliyun_vod
An ODOO module which integrates w/ aliyun VOD service

This ODOO module includes a page that can list some of video media in one particular Alyun VOD account and a player page that can play one of them.

The module is tested against with ODOO version 11 and python version 3.6. 

## Prerequisites

1. This module, as an example, stores the Aliyun API Key and Secrect in the ODOO configuration file. In a real production module, it's recommended to save them in the database.

In the configuration file add a line for aliyun_vod_key and a line for aliyun_vod_secret. The value of them is the Aliyun API key and secret accordingly.

2. This module depends some Aliyun SDK, run the following commands to have them installed. 

```
pip3 install aliyun-python-sdk-core
pip3 install aliyun-python-sdk-vod
```

For more details, refer to https://help.aliyun.com/document_detail/61060.html?spm=a2c4g.11186623.6.730.Pf8pwd for the Aliyun VOD service user guide. 
