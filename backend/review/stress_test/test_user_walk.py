import requests

# Endpoint Configuration
COURSE_CODE = 'CIS-1210' 
SEMESTER = '2024C'  
TOKEN = 'MY_ACCESS_TOKEN'  

# The API endpoint with query parameters
URL = f'https://penncoursereview.com/api/review/course/{COURSE_CODE}'
PARAMS = {
    'token': TOKEN,
    'semester': SEMESTER
}

def fetch_course_reviews():
    # Make the GET request to the API endpoint
    response = requests.get(URL, params=PARAMS)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response as JSON
        reviews = response.json()
        print("Course Reviews Fetched Successfully:")
        print(reviews)
    else:
        print(f"Failed to fetch course reviews. Status code: {response.status_code}")

if __name__ == "__main__":
    fetch_course_reviews()
