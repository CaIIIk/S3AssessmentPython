import subprocess

prod_buckets = [
"alice-es-manual-snapshot-repo-prod",
"alice-prod-diagnostics-repository",
"alice-prod-terraform-logs",
"alice-reporting-datayak3-prod",
"alice-spring-miller-prod",
"doc-print-prod-763386454006",
"doc-print-prod-duplicate-archive-for-investigation-763386454006",
"prod-assets-1.aliceapp.com",
"prod-assets-2.aliceapp.com",
"prod-assets.aliceapp.com",
"prod-db-auditlogs-763386454006",
"prod-mv.aliceapp.com",
"prod-v22-origin.aliceapp.com",
"prod.images.alice-app.com",
"prod.marketing.aliceapp.com",
"prod.pms.aliceapp.com",
"prod.static.aliceapp.com",
"prod.temp.aliceapp.com",
"prod.videos.alice-app.com",
"s3:*"
]

def add_string_to_file(file_name, string_to_add):
    """Adds the given string to the given file name"""
    try:
        with open(file_name, "a") as f:
            f.write("%s\n" % (string_to_add))
    except:
        logger.log.critical("Error adding %s to %s: %s" % (string_to_add, file_name, get_exception().replace("\n", " ")))

debug = True

def get_cmd_output(command):
    'Get output from a given command'
    if debug:
        print("""Running command %s""" % command)

    p = subprocess.Popen(command,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         shell=True, )
    output, error = p.communicate()
    return output.decode('unicode_escape').strip()

def check_policy_diocument(document):
    for s3bucket in prod_buckets:
        if s3bucket in document:
            return True
    return False

def check_full_access_policy_diocument(document):
    if '''"Action": "s3:*"''' in document:
        return True
    return False

def check_full_access_resource_diocument(document):
    if '''"Resource": "*"''' in document:
        return True
    return False

def check_any_s3_access_policy_diocument(document):
    if '''"Action": "s3:*"''' in document:
        return True
    elif '''"s3:''' in document:
        return True
    elif '''"arn:aws:s3:::''' in document:
        return True
    return False
