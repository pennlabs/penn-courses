# Pass@Penn 

To run the app, download the zip and run the following commands in terminal:

```
npm install
npm start
```
## Frameworks/Technologies/Packages
React, TypeScript, Redux, Bootstrap, react-toastify, typescript-eslint, react-beautiful-dnd, axios, react-router-dom

## Main Features
**Search for a course:**

user can search for courses using keyword, course department/number, and filter by quality, difficulty, and instructor quality. 

Makes api call to the penncourses backend using Redux RTK query and the search result is cached for 60 seconds on the client side to enable fast reponse time and lower burden on the backend.

**Add a course to cart:**

User can add no more than 7 courses to cart. A react-toastify warning will be given if user exceeds the limit. A course added to cart will have a ✅ in front of its title.

User can have multiple carts and give them different names. They can switch between the carts by clicking on the cart's name in the "All carts" section. You can choose a cart and checkout courses in it.

User can click on course title in the cart to view details of the course; they can also drag courses to rank them in terms of preference.

**Four Year Plan:**

To go to four years plan mode, click on "Four Year Plan" on the nav bar. A table with all 8 semesters will be shown as well as the user's cart. To plan a course for a semester, drag the course title from the cart to the corrresponding semester box.

**Take Note For A Course**

To take a note for a course, go to course detail and add a note in the text box at the bottom. The note will also be shown along with the course title in cart so you can compare the notes for different courses easily and make decisions more easily. A course with a note added will have a ✏️ emoji next to its title.

## Design Thinking

**Redux state management**

Used React Redux to manage states. Having a global state is helpful especially in this case since the application has many moving parts, and if one of them is updated the other ones must be updated simultaneously. 

For example, if in the course detail section's text area a note is added to a course that is already in cart. The ✏️ emoji must be added to the course title in the search result section; the note content must persist in the text box in the course detail section for future edits; and the note must also appear under the corresponding course title in cart.

The redux store essentially serves as a database on the frontend. All the data will persist unless the page is manually refreshed by the user. 

**TypeScript and Eslint**

The app is built with TypeScript with eslint, strictNullChecks, and noImplicitAny enabled. This makes it robust and less prone to errors.

