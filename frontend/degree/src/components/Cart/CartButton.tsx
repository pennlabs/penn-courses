import {useDispatch} from 'react-redux';
import { currentCartSet } from '../../store/reducers/courses';
import { ICart } from '../../store/configureStore';

interface CartButtonProps {
    cart: ICart
}

const CartButton = ({cart} : CartButtonProps) => {
    const handleClickOnCart = () => {
        dispatch(currentCartSet(cart));
    }
    
    const dispatch = useDispatch();
    return (
        <div onClick={handleClickOnCart}>
            <li key={cart.name} className="bg-light list-group-item">
                <div>{cart.name} </div>
            </li>
        </div>
    )
}

export default CartButton;