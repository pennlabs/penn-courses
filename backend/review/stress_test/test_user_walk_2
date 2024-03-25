import requests

BASE_URL = 'https://penncoursereview.com'
API_ENDPOINT = '/api/...'
HEADERS = {'Content-Type': 'application/json'}
DATA = {...} # User data for creating a test user
COURSE_ID = 'course_id'

# Step 1: Create a Test User using a POST request 
response = requests.post(f'{BASE_URL}{API_ENDPOINT}/create_user', headers=HEADERS, json=DATA)
user = response.json()

if response.status_code != 200:
    raise Exception("User creation failed")

# Step 2: Simulate User Actions 
login_response = requests.post(f'{BASE_URL}{API_ENDPOINT}/login', headers=HEADERS, json=login_data)
login_info = login_response.json()
token = login_info.get('token')

# View a course review
review_response = requests.get(f'{BASE_URL}{API_ENDPOINT}/courses/{course_id}/reviews', headers={'Authorization': f'Bearer {token}'})
reviews = review_response.json()

# ADD OTHER COURSE REVIEW ACTIONS HERE

# Step 3: Clean Up - Remove the Test User and any associated data
cleanup_response = requests.post(f'{BASE_URL}{API_ENDPOINT}/delete_user', headers={'Authorization': f'Bearer {token}'}, json={'user_id': user['id']})

# Validate the cleanup was successful
if cleanup_response.status_code != 200:
    raise Exception("Cleanup failed")
