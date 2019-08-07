#! /usr/bin/python
import json
import time
from common import *

output = get_cmd_output("aws iam list-roles")

roles = json.loads(output)

jobs = {}
rolesUsingS3 = []

count = 0

for role in roles["Roles"]:
    print('''Getting info of %s role''' % role["Arn"])
    jobIdJson = get_cmd_output('''aws iam generate-service-last-accessed-details --arn %s''' % (role["Arn"]))
    jobId = json.loads(jobIdJson)
    jobs[jobId["JobId"]] = role["Arn"]
    print('''Received JobId: %s''' % jobId["JobId"])
    print('''Getting roles policies for %s''' % role["Arn"])
    policies_attached_json = get_cmd_output('''aws iam list-attached-role-policies --role-name %s''' % role["RoleName"])
    policies_attached = json.loads(policies_attached_json)
    role_policies_json = get_cmd_output('''aws iam list-role-policies --role-name %s'''% role["RoleName"])
    role_policies = json.loads(role_policies_json)
    role_policies_names_list = []
    for attached in policies_attached["AttachedPolicies"]:
        policyDescriptionJson = get_cmd_output('aws iam get-policy --policy-arn %s' % attached["PolicyArn"])
        policyDescription = json.loads(policyDescriptionJson)
        policyVersionJson = get_cmd_output('''aws iam get-policy-version --policy-arn %s --version-id %s''' % (attached["PolicyArn"], policyDescription["Policy"]["DefaultVersionId"]))
        if check_any_s3_access_policy_diocument(policyVersionJson):
            rolesUsingS3.append(role["Arn"])
            break
    if role["Arn"] not in rolesUsingS3:
        for inline in role_policies["PolicyNames"]:
            policyVersionJson = get_cmd_output('aws iam get-role-policy --role-name %s --policy-name %s' % (role["RoleName"], inline))
            if check_any_s3_access_policy_diocument(policyVersionJson):
                rolesUsingS3.append(role["Arn"])
                break
    count += 1
    #if count > 20:
     #  break

print("Sleeping 10 secs")
time.sleep(10)
print("Starting to get data of services")

rolesAccordingToS3 = {}

for job in jobs.keys():
    servicesJson = get_cmd_output('''aws iam get-service-last-accessed-details --job-id %s''' % job)
    services = json.loads(servicesJson)
    print("Processing %s..." % jobs[job])
    for service in services["ServicesLastAccessed"]:
        if service["ServiceName"] == "Amazon S3":
            if job not in rolesAccordingToS3:
                rolesAccordingToS3[job] = {"jobId": job, "service": service, "countOfservices": len(services["ServicesLastAccessed"])}
                break

print("Showing roles according to S3")

for s3role in rolesAccordingToS3.keys():
    result_string = '''Role: %s, services count: %s''' % (jobs[rolesAccordingToS3[s3role]["jobId"]], rolesAccordingToS3[s3role]["countOfservices"])

    #print(result_string)

    add_string_to_file(file_name="rolesAccordingS3.json", string_to_add=result_string)

usedRolesAccordingToProdS3 = {}
s3FullAcceessRolesAccordingToProdS3 = {}

for s3role in rolesAccordingToS3.keys():
    policiesJson = get_cmd_output('''aws iam list-policies-granting-service-access --arn %s --service-namespaces s3''' % (jobs[rolesAccordingToS3[s3role]["jobId"]]))
    policies = json.loads(policiesJson)
    for policy in policies["PoliciesGrantingServiceAccess"][0]["Policies"]:
        roleArn = jobs[rolesAccordingToS3[s3role]["jobId"]]
        if "PolicyArn" in policy:
            print('''Analyzing policy %s with ARN from role: %s''' % (policy["PolicyName"], roleArn))
            policyDescriptionJson = get_cmd_output('aws iam get-policy --policy-arn %s' % policy["PolicyArn"])
            policyDescription = json.loads(policyDescriptionJson)
            policyVersionJson = get_cmd_output('''aws iam get-policy-version --policy-arn %s --version-id %s''' % (policy["PolicyArn"], policyDescription["Policy"]["DefaultVersionId"]))
            if check_policy_diocument(policyVersionJson):
                usedRolesAccordingToProdS3[roleArn] = rolesAccordingToS3[s3role]
            if check_full_access_policy_diocument(policyVersionJson):
                s3FullAcceessRolesAccordingToProdS3[roleArn] = rolesAccordingToS3[s3role]
        else:
            print('''Analyzing policy %s WITHOUT ARN from role: %s''' % (policy["PolicyName"], roleArn))
            slashPosition = roleArn.index(':role/')
            policyVersionJson = get_cmd_output('aws iam get-role-policy --role-name %s --policy-name %s' % (roleArn[slashPosition + 6:], policy["PolicyName"]))
            if check_policy_diocument(policyVersionJson):
                usedRolesAccordingToProdS3[roleArn] = rolesAccordingToS3[s3role]
            if check_full_access_policy_diocument(policyVersionJson):
                s3FullAcceessRolesAccordingToProdS3[roleArn] = rolesAccordingToS3[s3role]

for s3role in usedRolesAccordingToProdS3.keys():
    result_string = '''Role: %s, services count: %s''' % (jobs[usedRolesAccordingToProdS3[s3role]["jobId"]], usedRolesAccordingToProdS3[s3role]["countOfservices"])

    print(result_string)

    add_string_to_file(file_name="prodRolesAccordingS3.json", string_to_add=result_string)

print("*********************S3 Full Access Roles: ************************")

for s3role in s3FullAcceessRolesAccordingToProdS3.keys():
    result_string = '''Role: %s, services count: %s''' % (jobs[usedRolesAccordingToProdS3[s3role]["jobId"]], usedRolesAccordingToProdS3[s3role]["countOfservices"])

    print(result_string)

    add_string_to_file(file_name="s3FullAcceessRolesAccordingToProdS3.json", string_to_add=result_string)


showRoleList = True

if showRoleList:
    print("////////////////////////////////////////////////")

    for s3role in rolesAccordingToS3.keys():
        print('''Role arn according to s3 %s''', jobs[rolesAccordingToS3[s3role]["jobId"]])

    print("////////////////////////////////////////////////")

    for roleHasS3 in rolesUsingS3:
        print('''Role using S3 %s''' % roleHasS3)

print("**********************Roles that have S3 permission but don't use it*********************************")

rolesArnAccordingToS3 = []

for s3role in rolesAccordingToS3.keys():
    rolesArnAccordingToS3.append(jobs[rolesAccordingToS3[s3role]["jobId"]])

for roleHasS3 in rolesUsingS3:
    if roleHasS3 not in rolesArnAccordingToS3:
        print('''!!!!!**** %s''' % roleHasS3)
        add_string_to_file(file_name="role_that_has_S3_but_dont_use_it.json", string_to_add=result_string)

for roleAccording in rolesArnAccordingToS3:
    if roleAccording not in rolesUsingS3:
        print('''?????? %s''' % roleAccording)

print("Done!")
