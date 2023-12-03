# routes for courses (will integrate with penn course review)
GET /api/course?id={}

# routes for requirements
GET /api/degree
- returns the mega object that contains requirements and courses that satisfy each requirement (necessary?)

POST /api/degree
- updates the degree? need to figure this out in more detail (what about dual degree/programs like viper huntsman)

# routes for plans

GET /api/plan?id={}
- this returns a degree plan object. 
- eg. {"Fall 2023": ["CIS 160", "CIS 161", "CIS 162"], "Spring 2023": [...]}
- there will be multiple degree plans for a user, so need to come up with some identifier for each (could let the user create a name for each plan lol)

POST /api/plan?id={}
- create a new degree plan

DELETE /api/plan?id={}
- delete the degree plan with the specified id

POST /api/plan?semester={}
- the frontend will send the updated list of courses planned for the semester specified by the route parameter
- the backend needs to update the degree plan with the updated list of courses
- on top of that, the backend will also need to update the degree requirements status for the user, since updating the course plan might result in some requirements being fulfilled/no longer fulfilled

Things to think about:
- how is authentication done/integration with pennkey, does that affect these routes? eg include a secret web token as a route parameter