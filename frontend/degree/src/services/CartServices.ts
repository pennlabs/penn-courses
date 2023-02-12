import { ICourse } from "../store/configureStore";

/* Create a cart string to use as params for the receipt page url */
export const cartString = (courses: ICourse[]) => {
    let result = "";
    for (let i = 0; i < courses.length; i++) {
      result += `+${courses[i].dept}-${courses[i].number}`;
    }
    return result.substring(1);
  }