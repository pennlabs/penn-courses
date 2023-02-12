import {createSlice} from '@reduxjs/toolkit';

/*
nav: 
{
    showFourYearPlan: false,
    showCart: false,
    hideSearchBar: false,
    onCheckoutPage: false,
    onContentPage: false  // true if on fourYearPlan page or on searchResult page; false otherwise
    
}
some notes on navigation:
    front page contains: navbar, searchbar
    content page has either of the following two pages:
        fourYearPlan page which shows Cart, Detail, and fourYearPlan
        searchResult page which shows list of Courses, Detail, and Cart
*/

const slice = createSlice({
    name: 'nav',
    initialState: {
        showFourYearPlan: false,
        showCart: false,
        hideSearchBar: false,
        onContentPage: false,
        onCheckoutPage: false
    },
    reducers: {
        showFourYearPlanSet: (nav, action) => {
            nav.showFourYearPlan = !nav.showFourYearPlan;
            /* if on fourYearPlan page, we automatically
              show cart and hide search bar */
            if (nav.showFourYearPlan) {
                nav.showCart = true;
                nav.onContentPage = true;
                nav.hideSearchBar = true;
            } else {
                nav.hideSearchBar = false;
            }
            /* no data has been loaded 
                and we should not return to content page */
            if (!action.payload) { 
                nav.onContentPage = false;
            }
        },
        searchBarSet: (nav) => {
            nav.hideSearchBar = !nav.hideSearchBar;
        },
        showCartSet: (nav) => {
            nav.showCart = !nav.showCart;
        },
        onContentPageSet: (nav, action) => {
            nav.onContentPage = action.payload;
        },
        showFourYearPlanReset: (nav) => {
            nav.showFourYearPlan = false;
            nav.hideSearchBar = false;
        },
        frontPageReturned: (nav) => {
            nav.onContentPage = false;
            nav.showFourYearPlan = false;
            nav.hideSearchBar = false;
        },
        checkOutPageSet: (nav, action) => {
            nav.onCheckoutPage = action.payload;
        }
    }
    
})

export const {
    showFourYearPlanSet, 
    onContentPageSet, 
    showCartSet, 
    showFourYearPlanReset, 
    searchBarSet, 
    checkOutPageSet,
    frontPageReturned} = slice.actions;
export default slice.reducer;
