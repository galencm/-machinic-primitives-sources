#!/usr/bin/python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import sys
import argparse
import glob
import io
import os
import redis
import uuid
from sourceprimitives import boook
import zerorpc
from logzero import logger
import consul

#change source:<name> from get/set to hmset
#currently:
#get "source:bar"
#"/tmp/5ce00059-01ee-4d3b-858b-7a42e86f0158"

#as new sourcetype?
#add state
#images would not be removed and instead
#device position would determine what is
#returned
#source:<name>
#location:
#<device_name1>:position start:None
#<device_name2>:position start:dev1+1
#start position None,0
#end position lastitem,None
#topologize -> ie turn page dev1+1,dev2+1 or dev1-1,dev2-1

def lookup(service):
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    for k in services.keys():
        if services[k]['Service'] == service:
                service_ip,service_port = services[k]['Address'],services[k]['Port']
                return service_ip,service_port
                break
    return None,None
    
redis_ip,redis_port = lookup('redis')
r = redis.StrictRedis(host=redis_ip, port=str(redis_port),decode_responses=True)

class Source():
    def __init__(self,**kwargs):
        self.directory = kwargs['directory']

    def source(self,device_name,*args):
        #use args to catch device name
        directory = self.directory

        container = io.BytesIO()
        files = sorted(glob.glob(os.path.join(directory,"*.jpg")))
        file = files.pop(0)
        logger.info("opening {}".format(file))
        with open(file,'rb') as f:
            container = io.BytesIO(f.read())
        container.seek(0)
        #print(container.getvalue())
        logger.info("removing {}".format(file))
        os.remove(file)
        logger.info("returning: bytes")
        return container.getvalue()

def main():
    tutorial_string = """
    Usage:

        $ primitives-source-simple --source boook --source-name bookendpoint

    """
    parser = argparse.ArgumentParser(description=tutorial_string,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", help="host ip",default="127.0.0.1", required=False)
    parser.add_argument("-p", "--port", help="port number",default="4242", required=False)
    parser.add_argument("-d", "--directory", help="directory")
    parser.add_argument("-s", "--source", help="source")
    parser.add_argument("--source-name", help="source name")

    source_key_prefix = "source:"
    args = parser.parse_args()
    source_uuid = str(uuid.uuid4())
    source_path = "/tmp/{}".format(source_uuid)

    if args.source_name:
        source_state_exists = r.get(source_key_prefix+args.source_name)
        logger.info("{} found at {}".format(args.source_name,source_state_exists))
        if source_state_exists:
            logger.info("using existing: {}".format(source_path,source_state_exists))
            source_path = source_state_exists

        if not os.path.isdir(source_path) or not source_state_exists:
            logger.warn("{} not found, creating".format(source_path))
            if args.source == 'boook':
                logger.info("creating boook at {}".format(args.source_name))
                #need to pass in params here...
                b = boook.Boook('texxt',[('toc',1,'partial'),('index',5,'partial'),('bar',5,'full'),('baz',5,'full'),('zab',5,'full'),('zoom',5,'full')],output_directory=source_path)
                b.generate()
                logger.info("{} set to {}".format(args.source_name,source_path))
                r.set(source_key_prefix+args.source_name,source_path)

    s = zerorpc.Server(Source(directory=source_path))
    bind_address = "tcp://{host}:{port}".format(host=args.host,port=args.port)
    logger.info("binding server to: {}".format(bind_address))
    logger.info("sourcing from: {}".format(source_path))
    s.bind(bind_address)
    logger.info("running...")
    s.run()