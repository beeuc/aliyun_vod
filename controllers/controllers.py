# -*- coding: utf-8 -*-
import json
import time
import datetime


from odoo import http
from odoo.tools import config
from aliyunsdkcore import client
from aliyunsdkvod.request.v20170321 import GetPlayInfoRequest # 每个接口都需要引入对应的类，此处以调用GetPlayInfo接口为例
from aliyunsdkvod.request.v20170321 import GetVideoPlayAuthRequest
from aliyunsdkvod.request.v20170321 import GetVideoListRequest

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

    def _get_video_list(self, clt):
        request = GetVideoListRequest.GetVideoListRequest()
        utcNow = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        utcMonthAgo = datetime.datetime.utcfromtimestamp(time.time() - 30*86400).strftime("%Y-%m-%dT%H:%M:%SZ")
        request.set_StartTime(utcMonthAgo)   # 视频创建的起始时间，为UTC格式
        request.set_EndTime(utcNow)          # 视频创建的结束时间，为UTC格式
        request.set_PageNo(1)
        request.set_PageSize(20)
        request.set_accept_format('JSON')
        response = json.loads(clt.do_action_with_exception(request))
        return response


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

