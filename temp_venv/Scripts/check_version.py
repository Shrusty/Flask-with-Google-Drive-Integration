import pkg_resources
print(pkg_resources.get_distribution("google-api-python-client").version)

import googleapiclient.discovery
print("Google API Client imported successfully!")
