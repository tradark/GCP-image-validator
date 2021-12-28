from pprint import pprint
import re
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import datetime as dt
def image_invalidator(request):
   date=re.sub(r'-',"",str(dt.date.today() - dt.timedelta(days=1)))
   credentials = GoogleCredentials.get_application_default()

   service = discovery.build('compute', 'v1', credentials=credentials)
   os_details = {"ubuntu": 26, "centos": 8}
   image_name = []
   image_date = []
   project = 'gcf-init'
   count = 0
   request = service.images().list(project=project)
   zone = "us-central1-a"
   while request is not None:
      response = request.execute()
      for image in response['items']:
         if "labels" in image:
               if "os_family" in image['labels']:
                  if image['labels']['os_family'] in os_details:
                     os_ver=re.sub(r'-',".",str(image['labels']['os_version']))
                     if(float(os_ver) <= os_details[image['labels']['os_family']] - 3 and re.sub(r'|T.*|-|',"",image['creationTimestamp']) >= date):
                           image_date.append(re.sub(r'|T.*|-|',"",image['creationTimestamp']))
                           image_name.append(image['name'])
                           print(image['name'],":",image['labels']['os_family'],"with version no =",os_ver,"not valid and going to be delete")
                           delete_request = service.images().delete(project=project, image=image['name']).execute()
                     if(float(os_ver) <= os_details[image['labels']['os_family']] - 3):
                           image_date.append(re.sub(r'|T.*|-|',"",image['creationTimestamp']))
                           image_name.append(image['name'])
                           print(image['name'],":",image['labels']['os_family'],"with version no =",os_ver,"not valid and going to be delete")
                           deprecate_time=dt.date.today()
                           deprecation_status_body = {
                              "state": ["DEPRECATED"],
                              "replacement": "",
                              "deprecated" : deprecate_time
                           }
                           deprecate_request = service.images().deprecate(project=project, image=image['name'], body=deprecation_status_body).execute()
                     else:
                           print(image['name'],":",image['labels']['os_family'],"with version no =",os_ver,"is not valid")
      request = service.images().list_next(previous_request=request, previous_response=response)
   instance_request = service.instances().list(project=project, zone=zone)
   while instance_request is not None:
      instance_response = instance_request.execute()
      for instance in instance_response['items']:
            source_image=instance["disks"][0]["deviceName"]
            disk_request = service.disks().get(project=project, zone=zone, disk=source_image)
            disk_response = disk_request.execute()
            if(re.sub(r'.*/',"",disk_response["sourceImage"]) in image_name):
               labelFingerprint=instance["labelFingerprint"]
               instances_set_labels_request_body = {
                  "labels": {
                     "non-complient" : "true"
                     },
                     "labelFingerprint": labelFingerprint
               }
               label_request = service.instances().setLabels(project=project, zone=zone, instance=source_image, body=instances_set_labels_request_body)
               label_response = label_request.execute()
               print("Instance name is = ",source_image," image name is = ",re.sub(r'.*/',"",disk_response["sourceImage"]))

      instance_request = service.instances().list_next(previous_request=instance_request, previous_response=instance_response)


