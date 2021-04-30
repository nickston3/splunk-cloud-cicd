import os
import requests
import json
import subprocess
import shlex
import sys
from xml.dom import minidom

print ' === Argument List: ', str(sys.argv)

directory = os.path.join(sys.argv[2], sys.argv[3], "default") 
appname = sys.argv[3]
server_url = sys.argv[1]
verify_cert = False

def rest_auth(server_url,verify_cert):
    """Implement your own validation logic to validate the input stanza configurations"""

    username = "admin"
    password= "hot-bucket"

    auth_headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    server_content = requests.request(
        'POST',
        server_url + '/services/auth/login',
        verify=verify_cert,
        headers=auth_headers,
        data={
            'username':username,
            'password':password
        }
    )
    req = server_content.text
    print(req)
    session_key = (minidom.parseString(req)
        .getElementsByTagName('sessionKey')[0]
        .childNodes[0]
        .nodeValue
    )

    return session_key

def rest_post(data,session_key,server_url,verify_cert):
    headers = {
        'Authorization': 'Splunk %s' % session_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    resp = requests.request(
        'POST',
        server_url,
        data=data,
        verify=verify_cert,
        headers=headers
    )

    return resp

session_key = rest_auth(server_url,verify_cert)
print(session_key)

for filename in os.listdir(directory):

    if filename.endswith(".conf") :
        print "#######################################################################\n"
        print("###     Processing configuration file : {}".format(filename))
        print "#######################################################################\n\n\n"
        conf_file_name = filename.replace(".conf","")


        conf = open(os.path.join(directory, filename), 'r') 
        Lines = conf.readlines() 
        
        count = 0

        request_url = server_url + '/servicesNS/nobody/'+appname+'/configs/conf-'+conf_file_name
        print("   |__ request URL : "+ request_url + "\n\n")
        data = {}
        # Strips the newline character 
        for line in Lines: 
            
            if line.strip().startswith("[") :

                print "   |__ Request data :"
                print(json.dumps(data))
                print("\n")
                #response = requests.post(request_url, data=data, verify=False, auth=("admin", "hot-bucket"))
                response = rest_post(data,session_key,request_url,verify_cert)
                print ("   |__  Request response :" + response.content + "\n\n")

                if '<msg type="ERROR">An object with name=' in response.content :
                    print ("   |__  Stanza configuration already exists, delete it then re-submit the new definition!")
                    cmd = '''curl -k -u  admin:hot-bucket  --request DELETE {}'''.format(request_url+"/"+data['name'])
                    args = shlex.split(cmd)
                    process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    
                    print ("   |__  Delete request response :" + stdout + "\n\n")

                    #response = requests.post(request_url, data=data, verify=False, auth=("admin", "hot-bucket"))
                    response = rest_post(data,session_key,request_url,verify_cert)
                    print ("   |__  Request response :" + response.content + "\n\n")

                if '<msg type="ERROR">Action forbidden.</msg>' in response.content :
                    print "Action forbidden , this is probably due to missing application target in your deployment server"
                    exit(1)

                print("   |__ Processing new stanza: {}".format(line.strip().replace("[","").replace("]","")))
                data = {}
                data = { 'name' : line.strip().replace("[","").replace("]","") }
            
            if not line.strip().startswith("#") :
                if "=" in line :
                    data[line.split("=")[0].strip()] = line.split("=")[1].strip()

        print "   |__  Request data :"
        print(json.dumps(data))
        print("\n")
        #response = requests.post(request_url, data=data, verify=False, auth=('admin', 'hot-bucket'))
        response = rest_post(data,session_key,request_url,verify_cert)
        print ("   |__  Request response :" + response.content + "\n\n")

        if '<msg type="ERROR">An object with name=' in response.content :
            print ("   |__  Stanza configuration already exists, delete it then re-submit the new definition!")
            
            cmd = '''curl -k -u  admin:hot-bucket  --request DELETE {}'''.format(request_url+"/"+data['name'])
            args = shlex.split(cmd)
            process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            print ("   |__  Delete request response :" + stdout + "\n\n")

            #response = requests.post(request_url, data=data, verify=False, auth=('admin', 'hot-bucket'))
            response = rest_post(data,session_key,request_url,verify_cert)
            print ("   |__  Request response :" + response.content + "\n\n")

        if '<msg type="ERROR">Action forbidden.</msg>' in response.content :
            print "Action forbidden , this is probably due to missing application target in your deployment server"
            exit(1)
            
        continue
    else:
        continue
