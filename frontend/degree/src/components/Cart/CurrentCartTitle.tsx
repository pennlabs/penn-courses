import {useSelector, useDispatch} from 'react-redux';
import { cartString } from '../../services/CartServices';
import { toastWarn } from '../../services/NotificationServices';
import { useNavigate } from "react-router-dom";
import { checkOutPageSet } from '../../store/reducers/nav';
import { RootState } from '../../store/configureStore';

const CurrentCartTitle = () => {
    const handleCheckout = () => {
        if (courses.length > 0) { 
            dispatch(checkOutPageSet(true));
            navigate(`/Checkout/${cartString(courses)}`);
        }
        else toastWarn('Need to check out at least one course!');
    }

    const navigate = useNavigate();
    const dispatch = useDispatch();
    const cart = useSelector((store : RootState) => store.entities.cart);
    const courses = cart.courses;

    return (
        <>
            <div className="d-flex justify-content-between">
                <h4 className="mt-2">{cart.name} Cart</h4>
                <button className="ms-2 btn btn-light" onClick={() => handleCheckout()}>
                    Checkout
                </button>
            </div>
        </>
    )
}

export default CurrentCartTitle;