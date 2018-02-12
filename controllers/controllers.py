# -*- coding: utf-8 -*-
import json
import time
import base64
import requests
import datetime
import logging

from odoo import http, api
from odoo.http import request
from odoo.tools import config
from aliyunsdkcore import client, acs_exception
from aliyunsdkvod.request.v20170321 import GetPlayInfoRequest # 每个接口都需要引入对应的类，此处以调用GetPlayInfo接口为例
from aliyunsdkvod.request.v20170321 import GetVideoPlayAuthRequest
from aliyunsdkvod.request.v20170321 import GetVideoListRequest

_logger = logging.getLogger(__name__)

class AliyunVod(http.Controller):

    def __init__(self):
        self.aliyun_key = config['aliyun_vod_key']
        self.aliyun_secret = config['aliyun_vod_secret']

    def _init_vod_client(self):
        regionId = 'cn-shanghai'  
        # 点播服务所在的Region，国内请填cn-shanghai，不要填写别的区域
        return client.AcsClient(self.aliyun_key, self.aliyun_secret, regionId, auto_retry=True, max_retry_time=3)

    def _get_play_info(self, clt, videoId):
        request = GetPlayInfoRequest.GetPlayInfoRequest()
        request.set_accept_format('JSON')
        request.set_VideoId(videoId)
        response = json.loads(clt.do_action_with_exception(request))
        return response

    def _get_video_playauth(self, clt, videoId):
        request = GetVideoPlayAuthRequest.GetVideoPlayAuthRequest()
        request.set_accept_format('JSON')
        request.set_VideoId(videoId)
        request.set_AuthInfoTimeout(3600)    
        # 播放凭证过期时间，默认为100秒，取值范围100~3600；
        # 注意：播放凭证用来传给播放器自动>换取播放地址，凭证过期时间不是播放地址的过期时间
        response = json.loads(clt.do_action_with_exception(request))
        return response

    def _get_video_list(self, clt, fromtimestamp=0, pagesize=100, pageno=1):
        request = GetVideoListRequest.GetVideoListRequest()
        utcNow = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        utcStart = datetime.datetime.utcfromtimestamp(fromtimestamp).strftime("%Y-%m-%dT%H:%M:%SZ")
        request.set_StartTime(utcStart)   # 视频创建的起始时间，为UTC格式
        request.set_EndTime(utcNow)          # 视频创建的结束时间，为UTC格式
        request.set_PageNo(pageno)
        request.set_PageSize(pagesize) 
        request.set_accept_format('JSON')
        try:
            response = json.loads(clt.do_action_with_exception(request))
        except acs_exception.exceptions.ServerException as e:
            response = ''
            #no new video exists

        return response

    @api.model
    def _fetch_data(self, base_url, data, content_type=False, extra_params=False):
        result = {'values': dict()}
        try:
            response = requests.get(base_url, params=data)
            response.raise_for_status()
            if content_type == 'json':
                result['values'] = response.json()
            elif content_type in ('image', 'pdf'):
                result['values'] = base64.b64encode(response.content)
            else:
                result['values'] = response.content
        except requests.exceptions.HTTPError as e:
            result['error'] = e.response.content
        except requests.exceptions.ConnectionError as e:
            result['error'] = str(e)
        return result

    @http.route('/aliyunvod/load/', auth='public')
    def load(self, **kw):
        
        slidemodel = request.env['slide.slide']

        slide_records = slidemodel.search([('mime_type','=','aliyun')], limit=1, order='create_date desc')

        for slide in slide_records:
            _logger.info("last imported slide name is %s", slide['name'])
            _logger.info("last imported slide create date is %s", slide['create_date'])

        if not slide_records:
            from_datetime = datetime.datetime.utcfromtimestamp(0)
        else:
            for slide in slide_records:
                dt = datetime.datetime.strptime(slide['create_date'], "%Y-%m-%d %H:%M:%S")
                from_datetime = dt.timestamp()

                
        clt = self._init_vod_client()
        response = self._get_video_list(clt, from_datetime, 100);

        if response and response['Total'] > 100:
            '''
            logic for getting pages from No. 2 to the end
            '''
        values = ""
        if response:
            for video in response['VideoList']['Video']:
               values = {'slide_type': 'video', 'document_id': video['VideoId']} 

               values.update({ 
                   'name': video['Title'],
                   'channel_id': 1, # default channel is 'Public Channel'
                   'website_published': False, # video is not published by default
                   'image': self._fetch_data(video['CoverURL'], {}, 'image')['values'],
                   'mime_type': 'aliyun',})

               slide_id = request.env['slide.slide'].create(values)

               _logger.info("new slide imported : <<< %s >>>", values['name'])

        if values and values['name']:
            return  values['name']
        else:
            return ""


    @http.route('/aliyunvod/player/', auth='public')
    def player(self, **kw):
        
        clt = self._init_vod_client()
        videoList = self._get_video_list(clt)

        return http.request.render('aliyun_vod.videolist', {
            'VideoList': videoList['VideoList']['Video'],})

    @http.route('/aliyunvod/player/<videoId>', auth='public')
    def vidplayer(self, videoId):

        clt = self._init_vod_client()
        playAuth = self._get_video_playauth(clt, videoId)

        return http.request.render('aliyun_vod.player', {
            'vid': videoId, 
            'playAuth': playAuth['PlayAuth'],})

