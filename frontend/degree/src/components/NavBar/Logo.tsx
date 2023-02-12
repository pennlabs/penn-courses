import { Link } from "react-router-dom";
import { checkOutPageSet, frontPageReturned } from '../../store/reducers/nav';
import { querySet} from '../../store/reducers/search';
import { detailViewed } from '../../store/reducers/courses';
import { useDispatch} from 'react-redux';

// constants
const logo = "Pass@Penn";

const Logo = () => {
    const returnToFrontPage = () => {
        dispatch(frontPageReturned());
        dispatch(querySet("")); // reset query in store when returning to the main page
        dispatch(detailViewed(null)); // reset current course to null
        dispatch(checkOutPageSet(false));
    }

    const dispatch = useDispatch();
    return (
        <Link to="/" className="">
            <label onClick={returnToFrontPage}>
                <h2 className="m-2"> 
                    {logo} 
                </h2>
            </label>
        </Link>
    )
}

export default Logo;